"""Tests for evaluator refusal-to-be-negative handling."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.evaluator import (
    EvaluationResult,
    EvaluatorAgent,
    REFUSAL_RE_PROMPT,
    SuiteResult,
    Verdict,
)
from harnessa.telemetry.models import BenchmarkScore, BugReport, CanonicalResponse, Severity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def agent(tmp_path: Path) -> EvaluatorAgent:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return EvaluatorAgent(model_id="test-model", work_dir=work_dir)


def _high_scores_result(scores: list[tuple[str, float]] | None = None) -> EvaluationResult:
    """Build a result with all-high scores (refusal pattern)."""
    if scores is None:
        scores = [("Functionality", 8.0), ("Quality", 7.5), ("Security", 9.0)]
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion=name, score=score, justification="Looks good")
            for name, score in scores
        ],
        verdict=Verdict.PASS,
    )


def _failing_tests() -> SuiteResult:
    """Build a test result with failures."""
    return SuiteResult(passed=3, failed=2, errors=0, output="2 failed in 1.0s")


def _passing_tests() -> SuiteResult:
    return SuiteResult(passed=5, failed=0, errors=0, output="5 passed in 1.0s")


def _low_scores_llm_response() -> CanonicalResponse:
    """LLM response with honest low scores."""
    return CanonicalResponse(
        text=json.dumps({
            "scores": [
                {"criterion": "Functionality", "score": 3, "justification": "Tests fail"},
                {"criterion": "Quality", "score": 5, "justification": "Decent"},
                {"criterion": "Security", "score": 6, "justification": "OK"},
            ],
            "bugs": [],
        }),
        stop_reason="end_turn",
        model="test-model",
        tokens_in=50,
        tokens_out=100,
        cost=0.005,
        truncated=False,
    )


def _still_high_scores_llm_response() -> CanonicalResponse:
    """LLM response that still refuses to give low scores."""
    return CanonicalResponse(
        text=json.dumps({
            "scores": [
                {"criterion": "Functionality", "score": 7, "justification": "Pretty good"},
                {"criterion": "Quality", "score": 8, "justification": "Nice"},
                {"criterion": "Security", "score": 7.5, "justification": "Solid"},
            ],
            "bugs": [],
        }),
        stop_reason="end_turn",
        model="test-model",
        tokens_in=50,
        tokens_out=100,
        cost=0.005,
        truncated=False,
    )


# ---------------------------------------------------------------------------
# Refusal detection
# ---------------------------------------------------------------------------


class TestRefusalDetection:
    """Tests that refusal is correctly detected."""

    def test_detects_refusal_when_tests_fail_all_high(
        self, agent: EvaluatorAgent
    ) -> None:
        result = _high_scores_result()
        test_result = _failing_tests()
        assert agent._is_refusal(result, test_result) is True

    def test_no_refusal_when_tests_pass(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _passing_tests()
        assert agent._is_refusal(result, test_result) is False

    def test_no_refusal_when_low_scores_present(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result([("A", 3.0), ("B", 8.0)])
        test_result = _failing_tests()
        assert agent._is_refusal(result, test_result) is False

    def test_no_refusal_with_empty_scores(self, agent: EvaluatorAgent) -> None:
        result = EvaluationResult(scores=[], verdict=Verdict.PASS)
        test_result = _failing_tests()
        assert agent._is_refusal(result, test_result) is False

    def test_refusal_on_errors_too(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = SuiteResult(passed=3, failed=0, errors=2)
        assert agent._is_refusal(result, test_result) is True


# ---------------------------------------------------------------------------
# Re-prompt on first refusal
# ---------------------------------------------------------------------------


class TestRePromptOnRefusal:
    """First refusal triggers re-prompt with explicit instructions."""

    def test_reprompt_resolves_refusal(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _failing_tests()

        with patch.object(agent, "call_llm", return_value=_low_scores_llm_response()):
            updated = agent._handle_refusal(result, test_result)

        assert updated.refusal_detected is True
        assert updated.refusal_recovery == "re_prompt"
        # Should have low scores now
        has_low = any(s.score < 5 for s in updated.scores)
        assert has_low is True

    def test_reprompt_calls_llm(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _failing_tests()

        with patch.object(agent, "call_llm", return_value=_low_scores_llm_response()) as mock_llm:
            agent._handle_refusal(result, test_result)

        mock_llm.assert_called_once()
        prompt = mock_llm.call_args[0][0]
        assert "MUST give scores below 5" in prompt or "scores below 5" in prompt


# ---------------------------------------------------------------------------
# Fallback on persistent refusal
# ---------------------------------------------------------------------------


class TestFallbackOnPersistentRefusal:
    """Persistent refusal (after re-prompt) triggers fallback grading."""

    def test_persistent_refusal_triggers_fallback(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _failing_tests()

        with patch.object(agent, "call_llm", return_value=_still_high_scores_llm_response()):
            updated = agent._handle_refusal(result, test_result)

        assert updated.refusal_detected is True
        assert updated.refusal_recovery == "fallback"
        assert updated.degraded_evaluation is True
        assert updated.verdict == Verdict.FAIL

    def test_fallback_on_llm_error(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _failing_tests()

        with patch.object(agent, "call_llm", side_effect=RuntimeError("LLM down")):
            updated = agent._handle_refusal(result, test_result)

        assert updated.refusal_detected is True
        assert updated.refusal_recovery == "fallback"
        assert updated.degraded_evaluation is True


# ---------------------------------------------------------------------------
# refusal_detected flag
# ---------------------------------------------------------------------------


class TestRefusalDetectedFlag:
    """The refusal_detected flag is set correctly in results."""

    def test_flag_set_on_refusal(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _failing_tests()

        with patch.object(agent, "call_llm", return_value=_low_scores_llm_response()):
            updated = agent._handle_refusal(result, test_result)

        assert updated.refusal_detected is True

    def test_flag_not_set_when_no_refusal(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result([("A", 3.0), ("B", 8.0)])
        test_result = _failing_tests()

        updated = agent._handle_refusal(result, test_result)
        assert updated.refusal_detected is False

    def test_flag_not_set_when_tests_pass(self, agent: EvaluatorAgent) -> None:
        result = _high_scores_result()
        test_result = _passing_tests()

        updated = agent._handle_refusal(result, test_result)
        assert updated.refusal_detected is False

    def test_refusal_recovery_field_defaults_empty(self) -> None:
        result = EvaluationResult()
        assert result.refusal_detected is False
        assert result.refusal_recovery == ""


# ---------------------------------------------------------------------------
# Integration with grade() method
# ---------------------------------------------------------------------------


class TestGradeIntegrationWithRefusal:
    """grade() correctly invokes _handle_refusal."""

    def test_grade_calls_handle_refusal(
        self, agent: EvaluatorAgent, tmp_path: Path
    ) -> None:
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        eval_dir = tmp_path / "_eval"
        eval_dir.mkdir()
        output_dir = tmp_path / "output"

        criteria_file = tmp_path / "criteria.yaml"
        criteria_file.write_text(
            """\
criteria:
  - name: Functionality
    weight: HIGH
    threshold: 6
    description: Does it work?
""",
            encoding="utf-8",
        )

        # LLM returns high scores despite test failures
        llm_response = json.dumps({
            "scores": [
                {"criterion": "Functionality", "score": 8, "justification": "Looks fine"},
            ],
            "bugs": [],
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
                stdout="3 passed, 2 failed in 0.5s", stderr="", returncode=1
            )
            result = agent.grade(code_dir, eval_dir, criteria_file, output_dir)

        # Either refusal was handled or verdict was set to FAIL
        assert result.verdict == Verdict.FAIL
