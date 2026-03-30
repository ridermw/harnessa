"""Calibration harness — tests evaluator behavior against known-quality archetypes.

Each case in golden_set.json has:
- A description of the code quality
- Expected verdict (PASS/FAIL)
- Expected score range (min/max)
- What the evaluator "should" do

We mock the LLM response for each case and verify the evaluator's
verdict logic, rubber-stamp detection, and refusal handling work correctly.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from harnessa.agents.evaluator import EvaluatorAgent, EvaluationResult, SuiteResult, Verdict
from harnessa.criteria.loader import Criterion, Weight
from harnessa.telemetry.models import BenchmarkScore, BugReport, CanonicalResponse, Severity


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def golden_set() -> dict:
    path = Path(__file__).parent / "golden_set.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def agent(tmp_path: Path) -> EvaluatorAgent:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return EvaluatorAgent(model_id="test-model", work_dir=work_dir)


@pytest.fixture()
def criteria_file(tmp_path: Path) -> Path:
    path = tmp_path / "criteria.yaml"
    path.write_text(
        "criteria:\n"
        "  - name: Functionality\n"
        "    weight: HIGH\n"
        "    threshold: 6\n"
        "    description: Does the fix resolve the bug?\n"
        "  - name: Code Quality\n"
        "    weight: MEDIUM\n"
        "    threshold: 5\n"
        "    description: Is the code clean?\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def sample_criteria() -> list[Criterion]:
    return [
        Criterion(
            name="Functionality",
            weight=Weight.HIGH,
            threshold=6,
            description="Does the fix resolve the bug without regressions?",
        ),
        Criterion(
            name="Code Quality",
            weight=Weight.MEDIUM,
            threshold=5,
            description="Is the code clean, minimal, and well-structured?",
        ),
    ]


# ---------------------------------------------------------------------------
# Canned LLM responses calibrated to each archetype
# ---------------------------------------------------------------------------

_CANNED_RESPONSES: dict[str, dict] = {
    "perfect-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 9, "justification": "Clean one-line fix resolves the bug, all eval tests pass, edge cases handled"},
            {"criterion": "Code Quality", "score": 8, "justification": "Minimal change follows existing conventions, no unnecessary refactoring"},
        ],
        "bugs": [],
    },
    "broken-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 2, "justification": "Fix introduces a regression — compute() returns wrong results for positive inputs"},
            {"criterion": "Code Quality", "score": 3, "justification": "Change is poorly structured and breaks existing behavior"},
        ],
        "bugs": [
            {"id": "reg-001", "severity": "critical", "description": "Regression: compute(10, 2) now returns 0 instead of 5", "file": "app.py", "line": 2},
        ],
    },
    "over-engineered-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 7, "justification": "Fix works and all tests pass"},
            {"criterion": "Code Quality", "score": 5, "justification": "Unnecessary rewrite of 50+ lines to fix a one-line bug; adds complexity"},
        ],
        "bugs": [],
    },
    "partial-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 4, "justification": "Only resolves 1 of 2 failing tests — fix is incomplete"},
            {"criterion": "Code Quality", "score": 5, "justification": "Code change is reasonable but incomplete"},
        ],
        "bugs": [
            {"id": "partial-001", "severity": "high", "description": "Second failing test still not addressed", "file": "app.py", "line": 5},
        ],
    },
    "sneaky-stub": {
        "scores": [
            {"criterion": "Functionality", "score": 1, "justification": "Tests pass ONLY because test expectations were weakened — actual bug untouched"},
            {"criterion": "Code Quality", "score": 2, "justification": "Modifying tests instead of code is a serious integrity violation"},
        ],
        "bugs": [
            {"id": "sneaky-001", "severity": "critical", "description": "Test file was modified to lower expectations instead of fixing the code", "file": "test_app.py", "line": 4},
        ],
    },
    "rubber-stamp-trap": {
        "scores": [
            {"criterion": "Functionality", "score": 2, "justification": "Code is obviously broken — tests fail with clear errors"},
            {"criterion": "Code Quality", "score": 2, "justification": "No meaningful change was made to address the issue"},
        ],
        "bugs": [
            {"id": "trap-001", "severity": "critical", "description": "No fix applied; original bug persists", "file": "app.py", "line": 2},
        ],
    },
}

# Rubber-stamp LLM response: all scores >= 9 despite broken code
_RUBBER_STAMP_RESPONSE = {
    "scores": [
        {"criterion": "Functionality", "score": 9, "justification": "Great job!"},
        {"criterion": "Code Quality", "score": 9, "justification": "Well done!"},
    ],
    "bugs": [],
}

# Refusal-to-be-negative LLM response: all scores >= 7 despite test failures
_REFUSAL_RESPONSE = {
    "scores": [
        {"criterion": "Functionality", "score": 8, "justification": "Looks reasonable"},
        {"criterion": "Code Quality", "score": 7, "justification": "Acceptable quality"},
    ],
    "bugs": [],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_canonical(data: dict) -> CanonicalResponse:
    """Build a CanonicalResponse from a canned dict."""
    return CanonicalResponse(
        text=json.dumps(data),
        stop_reason="end_turn",
        model="test-model",
        tokens_in=100,
        tokens_out=200,
        cost=0.005,
        truncated=False,
    )


def _setup_workspace(tmp_path: Path, case_id: str) -> tuple[Path, Path]:
    """Create mock code_dir and eval_dir for a golden case."""
    code_dir = tmp_path / f"code_{case_id}"
    code_dir.mkdir(parents=True)
    eval_dir = tmp_path / f"eval_{case_id}"
    eval_dir.mkdir(parents=True)
    (code_dir / "app.py").write_text(
        "def compute(x, y):\n"
        "    if y == 0:\n"
        "        return 0\n"
        "    return x / y\n",
        encoding="utf-8",
    )
    return code_dir, eval_dir


def _mock_subprocess(stdout: str, returncode: int):
    """Return a mock subprocess result."""
    return type("Result", (), {
        "stdout": stdout, "stderr": "", "returncode": returncode
    })()


# ---------------------------------------------------------------------------
# Calibration harness
# ---------------------------------------------------------------------------


class TestCalibrationHarness:
    """Run evaluator against all 6 golden set archetypes."""

    def test_perfect_fix(
        self, golden_set: dict, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Perfect fix: clean minimal change, all tests pass → PASS, scores 7-10."""
        case = next(c for c in golden_set["cases"] if c["id"] == "perfect-fix")
        code_dir, eval_dir = _setup_workspace(tmp_path, "perfect-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["perfect-fix"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("2 passed, 0 failed", 0)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.PASS
        for score in result.scores:
            assert case["expected_score_range"]["min"] <= score.score <= case["expected_score_range"]["max"], (
                f"{score.criterion}: {score.score} not in [{case['expected_score_range']['min']}, {case['expected_score_range']['max']}]"
            )
        assert not result.suspicious_approval
        assert not result.refusal_detected
        assert len(result.bugs) == 0

    def test_broken_fix(
        self, golden_set: dict, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Broken fix: introduces regression → FAIL, scores 1-4."""
        case = next(c for c in golden_set["cases"] if c["id"] == "broken-fix")
        code_dir, eval_dir = _setup_workspace(tmp_path, "broken-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["broken-fix"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("0 passed, 2 failed", 1)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        for score in result.scores:
            assert score.score <= case["expected_score_range"]["max"], (
                f"{score.criterion}: {score.score} exceeds max {case['expected_score_range']['max']}"
            )
        assert len(result.bugs) > 0, "Broken fix should report bugs"

    def test_over_engineered_fix(
        self, golden_set: dict, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Over-engineered: works but unnecessarily complex → PASS, scores 4-7."""
        case = next(c for c in golden_set["cases"] if c["id"] == "over-engineered-fix")
        code_dir, eval_dir = _setup_workspace(tmp_path, "over-engineered-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["over-engineered-fix"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("2 passed, 0 failed", 0)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.PASS
        for score in result.scores:
            assert case["expected_score_range"]["min"] <= score.score <= case["expected_score_range"]["max"], (
                f"{score.criterion}: {score.score} not in expected range"
            )
        # Code Quality should be penalized relative to Functionality
        func_score = next(s for s in result.scores if s.criterion == "Functionality")
        quality_score = next(s for s in result.scores if s.criterion == "Code Quality")
        assert quality_score.score <= func_score.score, (
            "Over-engineered code should have Code Quality <= Functionality"
        )

    def test_partial_fix(
        self, golden_set: dict, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Partial fix: 1 of 2 bugs fixed → FAIL, scores 3-6."""
        case = next(c for c in golden_set["cases"] if c["id"] == "partial-fix")
        code_dir, eval_dir = _setup_workspace(tmp_path, "partial-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["partial-fix"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("1 passed, 1 failed", 1)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        func_score = next(s for s in result.scores if s.criterion == "Functionality")
        assert func_score.score < 6, "Partial fix should score below functionality threshold"
        for score in result.scores:
            assert case["expected_score_range"]["min"] <= score.score <= case["expected_score_range"]["max"], (
                f"{score.criterion}: {score.score} not in expected range"
            )

    def test_sneaky_stub(
        self, golden_set: dict, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Sneaky: modified tests instead of code → FAIL, scores 1-3."""
        case = next(c for c in golden_set["cases"] if c["id"] == "sneaky-stub")
        code_dir, eval_dir = _setup_workspace(tmp_path, "sneaky-stub")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["sneaky-stub"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            # Tests "pass" because expectations were weakened
            mock_sub.return_value = _mock_subprocess("2 passed, 0 failed", 0)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        for score in result.scores:
            assert score.score <= case["expected_score_range"]["max"], (
                f"{score.criterion}: {score.score} too high for sneaky stub"
            )
        # Must have a bug report about test modification
        assert len(result.bugs) > 0, "Sneaky stub should be reported as a bug"
        bug_descriptions = " ".join(b.description.lower() for b in result.bugs)
        assert "test" in bug_descriptions, "Bug report should mention test modification"

    def test_rubber_stamp_trap(
        self, golden_set: dict, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Obviously broken code — evaluator MUST NOT give scores above 5.
        If all scores >= 7, the evaluator is rubber-stamping (people-pleasing)."""
        case = next(c for c in golden_set["cases"] if c["id"] == "rubber-stamp-trap")
        code_dir, eval_dir = _setup_workspace(tmp_path, "rubber-stamp-trap")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["rubber-stamp-trap"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("0 passed, 2 failed", 1)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        for score in result.scores:
            assert score.score <= 5, (
                f"Rubber-stamp trap: {score.criterion} scored {score.score} — "
                "evaluator must not score above 5 for obviously broken code"
            )
        assert len(result.bugs) > 0, "Obviously broken code should report bugs"


class TestRubberStampDetection:
    """Verify _detect_rubber_stamp() flags suspiciously high scores."""

    def test_all_nines_flagged(self, agent: EvaluatorAgent) -> None:
        """All scores >= 9 should trigger rubber-stamp detection."""
        scores = [
            BenchmarkScore(criterion="Functionality", score=9.0, justification="Great"),
            BenchmarkScore(criterion="Code Quality", score=9.5, justification="Perfect"),
        ]
        assert agent._detect_rubber_stamp(scores) is True

    def test_mixed_scores_not_flagged(self, agent: EvaluatorAgent) -> None:
        """Mix of high and moderate scores should not trigger detection."""
        scores = [
            BenchmarkScore(criterion="Functionality", score=9.0, justification="Great"),
            BenchmarkScore(criterion="Code Quality", score=7.0, justification="Good"),
        ]
        assert agent._detect_rubber_stamp(scores) is False

    def test_empty_scores_not_flagged(self, agent: EvaluatorAgent) -> None:
        """Empty score list should not trigger detection."""
        assert agent._detect_rubber_stamp([]) is False

    def test_rubber_stamp_with_failing_tests_triggers_flag(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """LLM rubber-stamps (all >= 9) with failing tests — should be flagged
        and ultimately result in FAIL via refusal handling."""
        code_dir, eval_dir = _setup_workspace(tmp_path, "rubber-stamp-flag")

        call_count = 0

        def mock_call_llm(prompt: str) -> CanonicalResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_canonical(_RUBBER_STAMP_RESPONSE)
            # Re-prompt: still rubber-stamping
            return _make_canonical(_RUBBER_STAMP_RESPONSE)

        with patch.object(agent, "call_llm", side_effect=mock_call_llm), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("0 passed, 3 failed", 1)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.suspicious_approval or result.refusal_detected, (
            "Evaluator should detect rubber-stamping when all scores >= 9 despite failing tests"
        )
        assert result.verdict == Verdict.FAIL


class TestRefusalToBelNegative:
    """Verify refusal-to-be-negative detection and handling."""

    def test_refusal_detected_high_scores_failing_tests(
        self, agent: EvaluatorAgent,
    ) -> None:
        """Tests fail but evaluator gives all scores >= 7 — people-pleasing detected."""
        failing_tests = SuiteResult(passed=2, failed=3, errors=0, output="3 failed in 1.0s")
        high_result = EvaluationResult(
            scores=[
                BenchmarkScore(criterion="Functionality", score=8.0, justification="Looks good"),
                BenchmarkScore(criterion="Code Quality", score=7.5, justification="Fine"),
            ],
            verdict=Verdict.PASS,
        )
        assert agent._is_refusal(high_result, failing_tests) is True

    def test_no_refusal_when_tests_pass(
        self, agent: EvaluatorAgent,
    ) -> None:
        """No refusal when tests pass — high scores are legitimate."""
        passing_tests = SuiteResult(passed=5, failed=0, errors=0, output="5 passed")
        high_result = EvaluationResult(
            scores=[
                BenchmarkScore(criterion="Functionality", score=9.0, justification="All pass"),
                BenchmarkScore(criterion="Code Quality", score=8.0, justification="Clean"),
            ],
            verdict=Verdict.PASS,
        )
        assert agent._is_refusal(high_result, passing_tests) is False

    def test_no_refusal_with_honest_low_scores(
        self, agent: EvaluatorAgent,
    ) -> None:
        """Tests fail and at least one score is low — no refusal."""
        failing_tests = SuiteResult(passed=1, failed=2, errors=0, output="2 failed")
        honest_result = EvaluationResult(
            scores=[
                BenchmarkScore(criterion="Functionality", score=3.0, justification="Broken"),
                BenchmarkScore(criterion="Code Quality", score=7.0, justification="OK style"),
            ],
            verdict=Verdict.FAIL,
        )
        assert agent._is_refusal(honest_result, failing_tests) is False

    def test_handle_refusal_falls_back_on_persistent_refusal(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """If re-prompting doesn't fix the refusal, evaluator falls back to
        test-only grading and forces FAIL."""
        code_dir, eval_dir = _setup_workspace(tmp_path, "persistent-refusal")

        # Both initial and re-prompt return high scores despite failing tests
        def mock_call_llm(prompt: str) -> CanonicalResponse:
            return _make_canonical(_REFUSAL_RESPONSE)

        with patch.object(agent, "call_llm", side_effect=mock_call_llm), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("1 passed, 2 failed", 1)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        assert result.refusal_detected is True
        assert result.refusal_recovery == "fallback"

    def test_handle_refusal_resolved_by_reprompt(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Re-prompting succeeds: second LLM call returns honest low scores."""
        code_dir, eval_dir = _setup_workspace(tmp_path, "refusal-resolved")

        honest_response = {
            "scores": [
                {"criterion": "Functionality", "score": 3, "justification": "Tests fail — code broken"},
                {"criterion": "Code Quality", "score": 5, "justification": "Decent structure but doesn't work"},
            ],
            "bugs": [
                {"id": "b1", "severity": "high", "description": "Main function broken", "file": "app.py", "line": 1},
            ],
        }

        call_count = 0

        def mock_call_llm(prompt: str) -> CanonicalResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: refusal (all scores >= 7)
                return _make_canonical(_REFUSAL_RESPONSE)
            # Re-prompt: honest low scores
            return _make_canonical(honest_response)

        with patch.object(agent, "call_llm", side_effect=mock_call_llm), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("1 passed, 2 failed", 1)

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        assert result.refusal_detected is True
        assert result.refusal_recovery == "re_prompt"

    def test_legacy_detection_overrides_to_fail(
        self, agent: EvaluatorAgent,
    ) -> None:
        """Legacy _detect_refusal_to_be_negative: tests failed, no score < 5 → FAIL."""
        failing_tests = SuiteResult(passed=3, failed=1, errors=0, output="1 failed")
        # All scores are 5-6 (not >= 7 so _is_refusal won't trigger,
        # but no score < 5 so legacy detection should catch it)
        result = EvaluationResult(
            scores=[
                BenchmarkScore(criterion="Functionality", score=6.0, justification="Mostly ok"),
                BenchmarkScore(criterion="Code Quality", score=5.5, justification="Acceptable"),
            ],
            verdict=Verdict.PASS,
        )
        updated = agent._detect_refusal_to_be_negative(result, failing_tests)
        assert updated.verdict == Verdict.FAIL
        assert updated.suspicious_approval is True


class TestVerdictCalculation:
    """Verify _compute_verdict threshold logic with golden-set-calibrated scores."""

    def test_all_above_threshold_passes(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion],
    ) -> None:
        """Scores at or above thresholds → PASS."""
        scores = [
            BenchmarkScore(criterion="Functionality", score=7.0, justification="Good"),
            BenchmarkScore(criterion="Code Quality", score=6.0, justification="OK"),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.PASS

    def test_one_below_threshold_fails(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion],
    ) -> None:
        """Any score below its threshold → FAIL."""
        scores = [
            BenchmarkScore(criterion="Functionality", score=5.0, justification="Below threshold"),
            BenchmarkScore(criterion="Code Quality", score=8.0, justification="Great"),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.FAIL

    def test_exact_threshold_passes(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion],
    ) -> None:
        """Score exactly at threshold → PASS (not strictly less than)."""
        scores = [
            BenchmarkScore(criterion="Functionality", score=6.0, justification="Just enough"),
            BenchmarkScore(criterion="Code Quality", score=5.0, justification="Bare minimum"),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.PASS

    def test_unknown_criterion_ignored(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion],
    ) -> None:
        """Scores for unknown criteria don't cause FAIL."""
        scores = [
            BenchmarkScore(criterion="Functionality", score=8.0, justification="Good"),
            BenchmarkScore(criterion="Code Quality", score=7.0, justification="Good"),
            BenchmarkScore(criterion="UnknownCriterion", score=1.0, justification="Low"),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.PASS


class TestOutputArtifacts:
    """Verify evaluator writes output files atomically."""

    def test_eval_output_file_written(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """grade() should write eval_iter1.json to the output directory."""
        code_dir, eval_dir = _setup_workspace(tmp_path, "output-check")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["perfect-fix"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("2 passed, 0 failed", 0)

            agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        output_file = tmp_path / "evaluations" / "eval_iter1.json"
        assert output_file.exists(), "Evaluation output file should be written"
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data["verdict"] in ("PASS", "FAIL")
        assert "scores" in data

    def test_eval_output_parseable_as_evaluation_result(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Written JSON should deserialize back to EvaluationResult."""
        code_dir, eval_dir = _setup_workspace(tmp_path, "roundtrip")

        with patch.object(agent, "call_llm", return_value=_make_canonical(_CANNED_RESPONSES["perfect-fix"])), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
            mock_sub.return_value = _mock_subprocess("2 passed, 0 failed", 0)

            agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        output_file = tmp_path / "evaluations" / "eval_iter1.json"
        roundtrip = EvaluationResult.model_validate_json(output_file.read_text(encoding="utf-8"))
        assert roundtrip.verdict == Verdict.PASS
        assert len(roundtrip.scores) == 2
