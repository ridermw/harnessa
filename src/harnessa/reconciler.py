"""Score reconciler — reconcile scores from multiple evaluators."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from harnessa.agents.evaluator import EvaluationResult, Verdict
from harnessa.telemetry.models import BenchmarkScore, BugReport

logger = logging.getLogger(__name__)


class Disagreement(BaseModel):
    """A single criterion where two evaluators disagree."""

    model_config = {"strict": True}

    criterion: str = Field(description="Criterion name")
    score_a: float = Field(description="Score from evaluator A")
    score_b: float = Field(description="Score from evaluator B")
    delta: float = Field(description="Absolute difference between scores")


class ReconciledResult(BaseModel):
    """Result of reconciling two EvaluationResults."""

    model_config = {"strict": True}

    final_scores: list[BenchmarkScore] = Field(default_factory=list)
    final_bugs: list[BugReport] = Field(default_factory=list)
    verdict: Verdict = Field(default=Verdict.FAIL)
    agreement_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    disagreements: list[Disagreement] = Field(default_factory=list)


# Keep the legacy dataclass for backward compatibility
@dataclass
class ReconciliationResult:
    """Legacy result type — use ReconciledResult for new code."""

    final_scores: list[BenchmarkScore]
    agreement_rate: float
    disagreements: list[str]


class ScoreReconciler:
    """Reconcile scores from two evaluators and compute agreement metrics.

    When two evaluators score the same criteria, this class merges
    them into a single final score set and tracks how often they agree.

    Agreement: scores within ±1 per criterion.
    Disagreement: >1 point gap → conservative (lower score used).
    Verdict: FAIL if either evaluator says FAIL.
    Bugs: union of both, deduplicated by file+line.
    """

    def __init__(self, tolerance: float = 1.0) -> None:
        """Initialize with a score tolerance for agreement.

        Args:
            tolerance: Maximum score difference to consider "agreement".
                Default is 1.0 (±1 point).
        """
        self.tolerance = tolerance

    def reconcile(
        self,
        eval_a: EvaluationResult,
        eval_b: EvaluationResult,
    ) -> ReconciledResult:
        """Reconcile two EvaluationResults into a single ReconciledResult.

        Agreement (scores within ±tolerance): final score = average.
        Disagreement (>tolerance gap): final score = lower (conservative).
        Verdict: FAIL if either evaluator says FAIL.
        Bugs: union of both evaluator bug lists, deduplicated by file+line.

        Args:
            eval_a: EvaluationResult from evaluator A.
            eval_b: EvaluationResult from evaluator B.

        Returns:
            A ReconciledResult with merged scores, bugs, and verdict.
        """
        map_a = {s.criterion: s for s in eval_a.scores}
        map_b = {s.criterion: s for s in eval_b.scores}

        all_criteria = sorted(set(map_a.keys()) | set(map_b.keys()))
        final_scores: list[BenchmarkScore] = []
        disagreements: list[Disagreement] = []
        agreements = 0
        paired = 0

        for criterion in all_criteria:
            a = map_a.get(criterion)
            b = map_b.get(criterion)

            if a and b:
                paired += 1
                diff = abs(a.score - b.score)
                if diff <= self.tolerance:
                    # Agreement: use average
                    agreements += 1
                    final_score = round((a.score + b.score) / 2, 1)
                    justification = (
                        f"Agreed (avg): {a.score:.1f} + {b.score:.1f}"
                    )
                else:
                    # Disagreement: use lower score (conservative)
                    final_score = min(a.score, b.score)
                    justification = (
                        f"Disagreed (conservative lower): "
                        f"{a.score:.1f} vs {b.score:.1f}"
                    )
                    disagreements.append(Disagreement(
                        criterion=criterion,
                        score_a=a.score,
                        score_b=b.score,
                        delta=round(diff, 1),
                    ))
                    logger.info(
                        "Disagreement on %s: %.1f vs %.1f (delta=%.1f)",
                        criterion, a.score, b.score, diff,
                    )

                final_scores.append(BenchmarkScore(
                    criterion=criterion,
                    score=final_score,
                    justification=justification,
                ))
            elif a:
                final_scores.append(a)
            elif b:
                final_scores.append(b)

        # Verdict: FAIL if either evaluator says FAIL
        if eval_a.verdict == Verdict.FAIL or eval_b.verdict == Verdict.FAIL:
            verdict = Verdict.FAIL
        else:
            verdict = Verdict.PASS

        # Bugs: union with dedup by file+line
        final_bugs = self._deduplicate_bugs(eval_a.bugs, eval_b.bugs)

        rate = agreements / paired if paired > 0 else 0.0

        return ReconciledResult(
            final_scores=final_scores,
            final_bugs=final_bugs,
            verdict=verdict,
            agreement_rate=round(rate, 4),
            disagreements=disagreements,
        )

    def agreement_rate(self, results: list[ReconciledResult]) -> float:
        """Compute the average agreement rate across multiple reconciled results.

        Args:
            results: List of ReconciledResult from multiple runs.

        Returns:
            Average agreement rate as a float between 0.0 and 1.0.
        """
        if not results:
            return 0.0
        return sum(r.agreement_rate for r in results) / len(results)

    @staticmethod
    def _deduplicate_bugs(
        bugs_a: list[BugReport], bugs_b: list[BugReport]
    ) -> list[BugReport]:
        """Union of bug lists, deduplicated by (file, line).

        When both evaluators report the same file+line, keep the first
        occurrence (from evaluator A).
        """
        seen: set[tuple[str, int]] = set()
        result: list[BugReport] = []

        for bug in [*bugs_a, *bugs_b]:
            key = (bug.file, bug.line)
            if key not in seen:
                seen.add(key)
                result.append(bug)

        return result
