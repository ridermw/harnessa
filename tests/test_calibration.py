"""Evaluator calibration tests — verify evaluator behavior against a golden set."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from harnessa.agents.evaluator import EvaluatorAgent, EvaluationResult, SuiteResult, Verdict
from harnessa.criteria.loader import Criterion, Weight
from harnessa.telemetry.models import BenchmarkScore, BugReport, CanonicalResponse, Severity


# ---------------------------------------------------------------------------
# Load golden set
# ---------------------------------------------------------------------------

GOLDEN_SET_PATH = Path(__file__).parent / "calibration" / "golden_set.json"


@pytest.fixture(scope="module")
def golden_set() -> dict:
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def agent(tmp_path: Path) -> EvaluatorAgent:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return EvaluatorAgent(model_id="test-model", work_dir=work_dir)


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


# ---------------------------------------------------------------------------
# Canned LLM responses per golden case
# ---------------------------------------------------------------------------

_CANNED_LLM_RESPONSES: dict[str, dict] = {
    "perfect-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 9, "justification": "Clean one-line fix, all tests pass, handles edge case correctly"},
            {"criterion": "Code Quality", "score": 8, "justification": "Minimal change, well-structured, follows existing conventions"},
        ],
        "bugs": [],
    },
    "broken-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 2, "justification": "Fix introduces a new regression — compute() now returns wrong results for positive inputs"},
            {"criterion": "Code Quality", "score": 3, "justification": "Poorly structured change that breaks existing behavior"},
        ],
        "bugs": [
            {"id": "reg-001", "severity": "critical", "description": "Regression: compute(10, 2) now returns 0 instead of 5", "file": "app.py", "line": 2},
        ],
    },
    "over-engineered-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 7, "justification": "Fix works and passes all tests"},
            {"criterion": "Code Quality", "score": 5, "justification": "Unnecessary rewrite of 50+ lines to fix a one-line bug; adds complexity"},
        ],
        "bugs": [],
    },
    "partial-fix": {
        "scores": [
            {"criterion": "Functionality", "score": 4, "justification": "Only resolves 1 of 2 failing tests — incomplete fix"},
            {"criterion": "Code Quality", "score": 5, "justification": "Code change is reasonable but incomplete"},
        ],
        "bugs": [
            {"id": "partial-001", "severity": "high", "description": "Second failing test still not addressed", "file": "app.py", "line": 5},
        ],
    },
    "sneaky-stub": {
        "scores": [
            {"criterion": "Functionality", "score": 1, "justification": "Tests pass ONLY because test expectations were weakened — the actual bug is untouched"},
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

# Rubber-stamp version: all scores >= 9 despite broken code (should be caught)
_RUBBER_STAMP_RESPONSE = {
    "scores": [
        {"criterion": "Functionality", "score": 9, "justification": "Great job!"},
        {"criterion": "Code Quality", "score": 9, "justification": "Well done!"},
    ],
    "bugs": [],
}


def _make_canonical_response(case_id: str) -> CanonicalResponse:
    """Build a CanonicalResponse with the canned LLM output for a given case."""
    data = _CANNED_LLM_RESPONSES[case_id]
    return CanonicalResponse(
        text=json.dumps(data),
        stop_reason="end_turn",
        model="test-model",
        tokens_in=100,
        tokens_out=200,
        cost=0.005,
        truncated=False,
    )


def _make_rubber_stamp_response() -> CanonicalResponse:
    return CanonicalResponse(
        text=json.dumps(_RUBBER_STAMP_RESPONSE),
        stop_reason="end_turn",
        model="test-model",
        tokens_in=100,
        tokens_out=200,
        cost=0.005,
        truncated=False,
    )


def _setup_code_dir(tmp_path: Path, case_id: str) -> tuple[Path, Path]:
    """Create mock code_dir and eval_dir matching the golden case description."""
    code_dir = tmp_path / f"code_{case_id}"
    code_dir.mkdir(parents=True)
    eval_dir = tmp_path / f"eval_{case_id}"
    eval_dir.mkdir(parents=True)

    # Base app file
    (code_dir / "app.py").write_text(
        "def compute(x, y):\n"
        "    if y == 0:\n"
        "        return 0\n"
        "    return x / y\n",
        encoding="utf-8",
    )

    return code_dir, eval_dir


# ---------------------------------------------------------------------------
# Tests per golden case
# ---------------------------------------------------------------------------


class TestGoldenSetLoading:
    """Verify the golden set file is valid and loadable."""

    def test_golden_set_loads(self, golden_set: dict) -> None:
        assert "cases" in golden_set
        assert len(golden_set["cases"]) == 6

    def test_all_cases_have_required_fields(self, golden_set: dict) -> None:
        required = {"id", "description", "expected_verdict", "expected_score_range", "evaluator_should"}
        for case in golden_set["cases"]:
            missing = required - set(case.keys())
            assert not missing, f"Case {case.get('id', '?')} missing: {missing}"


class TestPerfectFix:
    """Case: perfect-fix — clean minimal fix, should PASS with high scores."""

    def test_verdict_and_scores(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path, golden_set: dict
    ) -> None:
        case = next(c for c in golden_set["cases"] if c["id"] == "perfect-fix")
        code_dir, eval_dir = _setup_code_dir(tmp_path, "perfect-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical_response("perfect-fix")), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "2 passed, 0 failed", "stderr": "", "returncode": 0
            })()

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


class TestBrokenFix:
    """Case: broken-fix — regression, should FAIL with low scores."""

    def test_verdict_and_scores(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path, golden_set: dict
    ) -> None:
        case = next(c for c in golden_set["cases"] if c["id"] == "broken-fix")
        code_dir, eval_dir = _setup_code_dir(tmp_path, "broken-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical_response("broken-fix")), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "0 passed, 2 failed", "stderr": "", "returncode": 1
            })()

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
        assert len(result.bugs) > 0


class TestOverEngineeredFix:
    """Case: over-engineered — works but unnecessarily complex, PASS with medium scores."""

    def test_verdict_and_scores(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path, golden_set: dict
    ) -> None:
        case = next(c for c in golden_set["cases"] if c["id"] == "over-engineered-fix")
        code_dir, eval_dir = _setup_code_dir(tmp_path, "over-engineered-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical_response("over-engineered-fix")), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "2 passed, 0 failed", "stderr": "", "returncode": 0
            })()

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.PASS
        for score in result.scores:
            assert case["expected_score_range"]["min"] <= score.score <= case["expected_score_range"]["max"], (
                f"{score.criterion}: {score.score} not in range"
            )


class TestPartialFix:
    """Case: partial-fix — only fixes 1 of 2 tests, should FAIL."""

    def test_verdict_and_scores(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path, golden_set: dict
    ) -> None:
        case = next(c for c in golden_set["cases"] if c["id"] == "partial-fix")
        code_dir, eval_dir = _setup_code_dir(tmp_path, "partial-fix")

        with patch.object(agent, "call_llm", return_value=_make_canonical_response("partial-fix")), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "1 passed, 1 failed", "stderr": "", "returncode": 1
            })()

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        assert result.verdict == Verdict.FAIL
        func_score = next(s for s in result.scores if s.criterion == "Functionality")
        assert func_score.score < 6, "Partial fix should score below functionality threshold"


class TestSneakyStub:
    """Case: sneaky-stub — modifies tests instead of code, should FAIL."""

    def test_detects_test_modification(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path, golden_set: dict
    ) -> None:
        case = next(c for c in golden_set["cases"] if c["id"] == "sneaky-stub")
        code_dir, eval_dir = _setup_code_dir(tmp_path, "sneaky-stub")

        with patch.object(agent, "call_llm", return_value=_make_canonical_response("sneaky-stub")), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            # Tests "pass" because they were weakened
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "2 passed, 0 failed", "stderr": "", "returncode": 0
            })()

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
        # Should have a bug report about test modification
        assert len(result.bugs) > 0
        bug_descriptions = " ".join(b.description.lower() for b in result.bugs)
        assert "test" in bug_descriptions, "Bug report should mention test modification"


class TestRubberStampTrap:
    """Case: rubber-stamp-trap — evaluator must not give high scores to broken code."""

    def test_honest_evaluator_gives_low_scores(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path, golden_set: dict
    ) -> None:
        """When the LLM returns honest low scores, verify they're preserved."""
        case = next(c for c in golden_set["cases"] if c["id"] == "rubber-stamp-trap")
        code_dir, eval_dir = _setup_code_dir(tmp_path, "rubber-stamp-trap")

        with patch.object(agent, "call_llm", return_value=_make_canonical_response("rubber-stamp-trap")), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "0 passed, 2 failed", "stderr": "", "returncode": 1
            })()

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

    def test_rubber_stamp_detection_flags_suspicious_approval(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path
    ) -> None:
        """When the LLM rubber-stamps (all >= 9), the agent should flag it."""
        code_dir, eval_dir = _setup_code_dir(tmp_path, "rubber-stamp-detect")

        # LLM gives all 9s despite failing tests — should be flagged
        call_count = 0

        def mock_call_llm(prompt: str) -> CanonicalResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: rubber-stamp response (all 9s)
                return _make_rubber_stamp_response()
            # Re-prompt response: still rubber-stamping
            return _make_rubber_stamp_response()

        with patch.object(agent, "call_llm", side_effect=mock_call_llm), \
             patch("harnessa.agents.evaluator.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = type("Result", (), {
                "stdout": "0 passed, 3 failed", "stderr": "", "returncode": 1
            })()

            result = agent.grade(
                code_dir=code_dir,
                eval_dir=eval_dir,
                criteria_path=criteria_file,
                output_dir=tmp_path,
            )

        # The rubber-stamp detection should have flagged this
        assert result.suspicious_approval or result.refusal_detected, (
            "Evaluator should detect rubber-stamping when all scores >= 9 despite failing tests"
        )
        # Verdict should be FAIL due to failing tests + refusal handling
        assert result.verdict == Verdict.FAIL


class TestGoldenSetCompleteness:
    """Meta-test: verify every golden case ID has a corresponding canned response."""

    def test_all_cases_have_canned_responses(self, golden_set: dict) -> None:
        for case in golden_set["cases"]:
            assert case["id"] in _CANNED_LLM_RESPONSES, (
                f"Missing canned LLM response for case: {case['id']}"
            )
