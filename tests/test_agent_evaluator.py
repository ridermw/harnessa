"""Tests for the Evaluator agent."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.evaluator import (
    SYSTEM_PROMPT_TEMPLATE,
    EvaluationResult,
    EvaluatorAgent,
    SuiteResult,
    Verdict,
)
from harnessa.criteria.loader import Criterion, CriteriaLoader, Weight
from harnessa.telemetry.models import BenchmarkScore, BugReport, CanonicalResponse, Severity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def work_dir(tmp_path: Path) -> Path:
    return tmp_path / "work"


@pytest.fixture()
def agent(work_dir: Path) -> EvaluatorAgent:
    work_dir.mkdir(parents=True, exist_ok=True)
    return EvaluatorAgent(model_id="test-model", work_dir=work_dir)


@pytest.fixture()
def sample_criteria() -> list[Criterion]:
    return [
        Criterion(
            name="Functionality",
            weight=Weight.HIGH,
            threshold=6,
            description="Does it work?",
        ),
        Criterion(
            name="Code Quality",
            weight=Weight.MEDIUM,
            threshold=5,
            description="Is the code clean?",
        ),
    ]


@pytest.fixture()
def criteria_file(tmp_path: Path) -> Path:
    path = tmp_path / "criteria.yaml"
    path.write_text(
        """\
criteria:
  - name: Functionality
    weight: HIGH
    threshold: 6
    description: Does it work?
  - name: Code Quality
    weight: MEDIUM
    threshold: 5
    description: Is the code clean?
""",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------

class TestInstantiation:
    def test_creates_evaluator(self, agent: EvaluatorAgent) -> None:
        assert agent.agent_id == "evaluator"
        assert agent.model_id == "test-model"

    def test_has_criteria_loader(self, agent: EvaluatorAgent) -> None:
        assert isinstance(agent._loader, CriteriaLoader)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

class TestSystemPrompt:
    def test_contains_skepticism_instructions(self, agent: EvaluatorAgent) -> None:
        prompt = agent.system_prompt
        assert "skeptical by default" in prompt
        assert "do NOT praise mediocre work" in prompt.lower() or "do NOT praise mediocre work" in prompt

    def test_contains_anti_people_pleasing(self, agent: EvaluatorAgent) -> None:
        prompt = agent.system_prompt
        assert "people-pleasing" in prompt.lower()

    def test_contains_rubber_stamp_warning(self, agent: EvaluatorAgent) -> None:
        prompt = agent.system_prompt
        assert "rubber-stamping" in prompt

    def test_contains_scoring_instructions(self, agent: EvaluatorAgent) -> None:
        prompt = agent.system_prompt
        assert "1-10" in prompt
        assert "JSON" in prompt


# ---------------------------------------------------------------------------
# Rubber-stamp detection
# ---------------------------------------------------------------------------

class TestRubberStampDetection:
    def test_all_scores_gte_9_is_suspicious(self, agent: EvaluatorAgent) -> None:
        scores = [
            BenchmarkScore(criterion="A", score=9.0, justification=""),
            BenchmarkScore(criterion="B", score=10.0, justification=""),
            BenchmarkScore(criterion="C", score=9.5, justification=""),
        ]
        assert agent._detect_rubber_stamp(scores) is True

    def test_mixed_scores_not_suspicious(self, agent: EvaluatorAgent) -> None:
        scores = [
            BenchmarkScore(criterion="A", score=9.0, justification=""),
            BenchmarkScore(criterion="B", score=7.0, justification=""),
        ]
        assert agent._detect_rubber_stamp(scores) is False

    def test_empty_scores_not_suspicious(self, agent: EvaluatorAgent) -> None:
        assert agent._detect_rubber_stamp([]) is False

    def test_one_below_9_clears_suspicion(self, agent: EvaluatorAgent) -> None:
        scores = [
            BenchmarkScore(criterion="A", score=9.0, justification=""),
            BenchmarkScore(criterion="B", score=8.9, justification=""),
        ]
        assert agent._detect_rubber_stamp(scores) is False


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

class TestVerdictLogic:
    def test_all_above_threshold_passes(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        scores = [
            BenchmarkScore(criterion="Functionality", score=7.0, justification=""),
            BenchmarkScore(criterion="Code Quality", score=6.0, justification=""),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.PASS

    def test_one_below_threshold_fails(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        scores = [
            BenchmarkScore(criterion="Functionality", score=5.0, justification=""),
            BenchmarkScore(criterion="Code Quality", score=8.0, justification=""),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.FAIL

    def test_exact_threshold_passes(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        scores = [
            BenchmarkScore(criterion="Functionality", score=6.0, justification=""),
            BenchmarkScore(criterion="Code Quality", score=5.0, justification=""),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.PASS

    def test_unknown_criterion_ignored(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        scores = [
            BenchmarkScore(criterion="Functionality", score=7.0, justification=""),
            BenchmarkScore(criterion="Code Quality", score=6.0, justification=""),
            BenchmarkScore(criterion="Unknown", score=1.0, justification=""),
        ]
        assert agent._compute_verdict(scores, sample_criteria) == Verdict.PASS


# ---------------------------------------------------------------------------
# Fallback grading
# ---------------------------------------------------------------------------

class TestFallbackGrading:
    def test_sets_degraded_flag(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        test_result = SuiteResult(passed=5, failed=5)
        result = agent._fallback_grade(test_result, None, sample_criteria, iteration=2)
        assert result.degraded_evaluation is True
        assert result.iteration == 2

    def test_pass_rate_maps_to_score(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        test_result = SuiteResult(passed=8, failed=2)
        result = agent._fallback_grade(test_result, None, sample_criteria, iteration=1)
        for s in result.scores:
            assert s.score == 8.0  # 80% pass rate → score 8

    def test_all_pass_gives_max_score(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        test_result = SuiteResult(passed=10, failed=0)
        result = agent._fallback_grade(test_result, None, sample_criteria, iteration=1)
        for s in result.scores:
            assert s.score == 10.0

    def test_regression_forces_fail(
        self, agent: EvaluatorAgent, sample_criteria: list[Criterion]
    ) -> None:
        test_result = SuiteResult(passed=10, failed=0)
        regression = SuiteResult(passed=5, failed=1)
        result = agent._fallback_grade(test_result, regression, sample_criteria, iteration=1)
        assert result.verdict == Verdict.FAIL


# ---------------------------------------------------------------------------
# _run_test_suite with mocked subprocess
# ---------------------------------------------------------------------------

class TestRunTestSuite:
    def test_pytest_runner(self, agent: EvaluatorAgent, tmp_path: Path) -> None:
        eval_dir = tmp_path / "_eval"
        eval_dir.mkdir()
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        mock_result = MagicMock()
        mock_result.stdout = "5 passed, 2 failed in 1.23s"
        mock_result.stderr = ""

        with patch("harnessa.agents.evaluator.subprocess.run", return_value=mock_result):
            result = agent._run_test_suite(eval_dir, code_dir)

        assert result.passed == 5
        assert result.failed == 2
        assert result.errors == 0

    def test_timeout_returns_error(self, agent: EvaluatorAgent, tmp_path: Path) -> None:
        import subprocess as sp

        eval_dir = tmp_path / "_eval"
        eval_dir.mkdir()
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        with patch(
            "harnessa.agents.evaluator.subprocess.run",
            side_effect=sp.TimeoutExpired(cmd=["pytest"], timeout=120),
        ):
            result = agent._run_test_suite(eval_dir, code_dir)

        assert result.errors == 1
        assert "timed out" in result.output.lower()

    def test_npm_test_detected(self, agent: EvaluatorAgent, tmp_path: Path) -> None:
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "package.json").write_text("{}", encoding="utf-8")

        cmd = agent._detect_test_command(tmp_path, code_dir)
        assert "npm" in cmd


# ---------------------------------------------------------------------------
# Refusal to be negative detection
# ---------------------------------------------------------------------------

class TestRefusalToBeNegative:
    def test_tests_fail_but_high_scores_flags_suspicious(
        self, agent: EvaluatorAgent
    ) -> None:
        result = EvaluationResult(
            scores=[
                BenchmarkScore(criterion="A", score=7.0, justification=""),
                BenchmarkScore(criterion="B", score=8.0, justification=""),
            ],
            verdict=Verdict.PASS,
        )
        test_result = SuiteResult(passed=3, failed=2)
        updated = agent._detect_refusal_to_be_negative(result, test_result)
        assert updated.verdict == Verdict.FAIL
        assert updated.suspicious_approval is True

    def test_tests_fail_with_low_scores_is_fine(
        self, agent: EvaluatorAgent
    ) -> None:
        result = EvaluationResult(
            scores=[
                BenchmarkScore(criterion="A", score=3.0, justification=""),
                BenchmarkScore(criterion="B", score=8.0, justification=""),
            ],
            verdict=Verdict.FAIL,
        )
        test_result = SuiteResult(passed=3, failed=2)
        updated = agent._detect_refusal_to_be_negative(result, test_result)
        assert updated.suspicious_approval is not True or updated.verdict == Verdict.FAIL


# ---------------------------------------------------------------------------
# Full grade() integration (mocked LLM)
# ---------------------------------------------------------------------------

class TestGradeIntegration:
    def test_grade_with_mocked_llm(
        self, agent: EvaluatorAgent, tmp_path: Path, criteria_file: Path
    ) -> None:
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        eval_dir = tmp_path / "_eval"
        eval_dir.mkdir()
        output_dir = tmp_path / "output"

        llm_response = json.dumps({
            "scores": [
                {"criterion": "Functionality", "score": 7, "justification": "Works well"},
                {"criterion": "Code Quality", "score": 6, "justification": "Decent"},
            ],
            "bugs": [
                {
                    "id": "bug-1",
                    "severity": "medium",
                    "description": "Missing error handling",
                    "file": "app.py",
                    "line": 42,
                },
            ],
        })

        with patch.object(
            agent,
            "call_llm",
            return_value=CanonicalResponse(
                text=llm_response,
                stop_reason="end_turn",
                model="test-model",
                tokens_in=100,
                tokens_out=200,
                cost=0.01,
                truncated=False,
            ),
        ), patch("harnessa.agents.evaluator.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="2 passed in 0.5s", stderr="", returncode=0
            )
            result = agent.grade(code_dir, eval_dir, criteria_file, output_dir)

        assert result.verdict == Verdict.PASS
        assert len(result.scores) == 2
        assert len(result.bugs) == 1
        assert result.bugs[0].file == "app.py"
        assert (output_dir / "evaluations" / "eval_iter1.json").exists()

    def test_grade_fallback_on_llm_failure(
        self, agent: EvaluatorAgent, tmp_path: Path, criteria_file: Path
    ) -> None:
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        eval_dir = tmp_path / "_eval"
        eval_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.object(
            agent, "call_llm", side_effect=RuntimeError("LLM down")
        ), patch("harnessa.agents.evaluator.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="3 passed, 1 failed in 0.5s", stderr="", returncode=1
            )
            result = agent.grade(code_dir, eval_dir, criteria_file, output_dir)

        assert result.degraded_evaluation is True
        assert result.verdict == Verdict.FAIL  # 75% pass rate → score 7.5, below threshold
