"""Tests for the ScoreReconciler with full cross-model reconciliation."""

from __future__ import annotations

import pytest

from harnessa.agents.evaluator import EvaluationResult, SuiteResult, Verdict
from harnessa.reconciler import Disagreement, ReconciledResult, ScoreReconciler
from harnessa.telemetry.models import BenchmarkScore, BugReport, Severity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_eval(
    scores: list[tuple[str, float]],
    verdict: Verdict = Verdict.PASS,
    bugs: list[BugReport] | None = None,
) -> EvaluationResult:
    """Helper to build an EvaluationResult from (criterion, score) pairs."""
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion=name, score=score, justification="")
            for name, score in scores
        ],
        bugs=bugs or [],
        verdict=verdict,
    )


def _make_bug(file: str, line: int, desc: str = "bug") -> BugReport:
    return BugReport(
        id=f"{file}-{line}",
        severity=Severity.MEDIUM,
        description=desc,
        file=file,
        line=line,
    )


# ---------------------------------------------------------------------------
# Agreement case — scores within ±1 → average scores
# ---------------------------------------------------------------------------


class TestAgreement:
    def test_exact_same_scores_agree(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("Functionality", 7.0), ("Quality", 6.0)])
        eval_b = _make_eval([("Functionality", 7.0), ("Quality", 6.0)])
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 1.0
        assert len(result.disagreements) == 0
        assert len(result.final_scores) == 2
        scores_map = {s.criterion: s.score for s in result.final_scores}
        assert scores_map["Functionality"] == 7.0
        assert scores_map["Quality"] == 6.0

    def test_within_tolerance_uses_average(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("Functionality", 7.0)])
        eval_b = _make_eval([("Functionality", 8.0)])
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 1.0
        assert len(result.disagreements) == 0
        assert result.final_scores[0].score == 7.5

    def test_exactly_at_tolerance_boundary_agrees(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("X", 5.0)])
        eval_b = _make_eval([("X", 6.0)])
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 1.0
        assert result.final_scores[0].score == 5.5


# ---------------------------------------------------------------------------
# Disagreement case — >1 gap → lower score used
# ---------------------------------------------------------------------------


class TestDisagreement:
    def test_large_gap_uses_lower_score(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("Functionality", 8.0)])
        eval_b = _make_eval([("Functionality", 4.0)])
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 0.0
        assert len(result.disagreements) == 1
        assert result.final_scores[0].score == 4.0  # conservative lower

    def test_disagreement_logged_with_details(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("Security", 9.0)])
        eval_b = _make_eval([("Security", 3.0)])
        result = reconciler.reconcile(eval_a, eval_b)

        d = result.disagreements[0]
        assert d.criterion == "Security"
        assert d.score_a == 9.0
        assert d.score_b == 3.0
        assert d.delta == 6.0

    def test_mixed_agree_disagree(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("A", 7.0), ("B", 9.0)])
        eval_b = _make_eval([("A", 7.5), ("B", 3.0)])
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 0.5
        assert len(result.disagreements) == 1
        scores_map = {s.criterion: s.score for s in result.final_scores}
        assert scores_map["A"] == 7.2 or scores_map["A"] == pytest.approx(7.25, abs=0.1)
        assert scores_map["B"] == 3.0  # conservative

    def test_just_over_tolerance_disagrees(self) -> None:
        reconciler = ScoreReconciler(tolerance=1.0)
        eval_a = _make_eval([("X", 5.0)])
        eval_b = _make_eval([("X", 6.5)])
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 0.0
        assert len(result.disagreements) == 1
        assert result.final_scores[0].score == 5.0


# ---------------------------------------------------------------------------
# Verdict: FAIL if either evaluator fails
# ---------------------------------------------------------------------------


class TestVerdict:
    def test_both_pass(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 7.0)], verdict=Verdict.PASS)
        eval_b = _make_eval([("A", 7.0)], verdict=Verdict.PASS)
        result = reconciler.reconcile(eval_a, eval_b)
        assert result.verdict == Verdict.PASS

    def test_a_fails(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 3.0)], verdict=Verdict.FAIL)
        eval_b = _make_eval([("A", 7.0)], verdict=Verdict.PASS)
        result = reconciler.reconcile(eval_a, eval_b)
        assert result.verdict == Verdict.FAIL

    def test_b_fails(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 7.0)], verdict=Verdict.PASS)
        eval_b = _make_eval([("A", 3.0)], verdict=Verdict.FAIL)
        result = reconciler.reconcile(eval_a, eval_b)
        assert result.verdict == Verdict.FAIL

    def test_both_fail(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 2.0)], verdict=Verdict.FAIL)
        eval_b = _make_eval([("A", 3.0)], verdict=Verdict.FAIL)
        result = reconciler.reconcile(eval_a, eval_b)
        assert result.verdict == Verdict.FAIL


# ---------------------------------------------------------------------------
# Bug deduplication — same file+line from both evaluators
# ---------------------------------------------------------------------------


class TestBugDeduplication:
    def test_same_bug_deduplicated(self) -> None:
        reconciler = ScoreReconciler()
        bug1 = _make_bug("app.py", 42, "null check missing")
        bug2 = _make_bug("app.py", 42, "missing null check")  # same file+line

        eval_a = _make_eval([("A", 7.0)], bugs=[bug1])
        eval_b = _make_eval([("A", 7.0)], bugs=[bug2])
        result = reconciler.reconcile(eval_a, eval_b)

        assert len(result.final_bugs) == 1
        assert result.final_bugs[0].file == "app.py"
        assert result.final_bugs[0].line == 42

    def test_different_bugs_kept(self) -> None:
        reconciler = ScoreReconciler()
        bug1 = _make_bug("app.py", 42)
        bug2 = _make_bug("api.py", 10)

        eval_a = _make_eval([("A", 7.0)], bugs=[bug1])
        eval_b = _make_eval([("A", 7.0)], bugs=[bug2])
        result = reconciler.reconcile(eval_a, eval_b)

        assert len(result.final_bugs) == 2

    def test_same_file_different_lines_kept(self) -> None:
        reconciler = ScoreReconciler()
        bug1 = _make_bug("app.py", 42)
        bug2 = _make_bug("app.py", 100)

        eval_a = _make_eval([("A", 7.0)], bugs=[bug1])
        eval_b = _make_eval([("A", 7.0)], bugs=[bug2])
        result = reconciler.reconcile(eval_a, eval_b)

        assert len(result.final_bugs) == 2

    def test_no_bugs_returns_empty(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 7.0)])
        eval_b = _make_eval([("A", 7.0)])
        result = reconciler.reconcile(eval_a, eval_b)
        assert len(result.final_bugs) == 0


# ---------------------------------------------------------------------------
# agreement_rate() across multiple results
# ---------------------------------------------------------------------------


class TestAgreementRateAcrossRuns:
    def test_single_result(self) -> None:
        reconciler = ScoreReconciler()
        r = ReconciledResult(agreement_rate=0.75)
        assert reconciler.agreement_rate([r]) == 0.75

    def test_multiple_results_averaged(self) -> None:
        reconciler = ScoreReconciler()
        results = [
            ReconciledResult(agreement_rate=1.0),
            ReconciledResult(agreement_rate=0.5),
            ReconciledResult(agreement_rate=0.0),
        ]
        assert reconciler.agreement_rate(results) == pytest.approx(0.5)

    def test_empty_results(self) -> None:
        reconciler = ScoreReconciler()
        assert reconciler.agreement_rate([]) == 0.0

    def test_all_perfect_agreement(self) -> None:
        reconciler = ScoreReconciler()
        results = [
            ReconciledResult(agreement_rate=1.0),
            ReconciledResult(agreement_rate=1.0),
        ]
        assert reconciler.agreement_rate(results) == 1.0
