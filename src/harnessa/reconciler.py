"""Score reconciler — reconcile scores from multiple evaluators."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from harnessa.telemetry.models import BenchmarkScore

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of reconciling scores from multiple evaluators."""

    final_scores: list[BenchmarkScore]
    agreement_rate: float
    disagreements: list[str]


class ScoreReconciler:
    """Reconcile scores from two evaluators and compute agreement metrics.

    When two evaluators score the same criteria, this class merges
    them into a single final score set and tracks how often they agree.
    """

    def __init__(self, tolerance: float = 1.5) -> None:
        """Initialize with a score tolerance for agreement.

        Args:
            tolerance: Maximum score difference to consider "agreement".
        """
        self.tolerance = tolerance

    def reconcile(
        self,
        scores_a: list[BenchmarkScore],
        scores_b: list[BenchmarkScore],
    ) -> ReconciliationResult:
        """Reconcile two sets of scores into a final set.

        Strategy: average scores, flag disagreements beyond tolerance.

        Args:
            scores_a: Scores from evaluator A.
            scores_b: Scores from evaluator B.

        Returns:
            ReconciliationResult with final scores and agreement metrics.
        """
        map_a = {s.criterion: s for s in scores_a}
        map_b = {s.criterion: s for s in scores_b}

        all_criteria = sorted(set(map_a.keys()) | set(map_b.keys()))
        final_scores: list[BenchmarkScore] = []
        disagreements: list[str] = []
        agreements = 0

        for criterion in all_criteria:
            a = map_a.get(criterion)
            b = map_b.get(criterion)

            if a and b:
                avg = (a.score + b.score) / 2
                diff = abs(a.score - b.score)
                if diff <= self.tolerance:
                    agreements += 1
                else:
                    disagreements.append(
                        f"{criterion}: {a.score:.1f} vs {b.score:.1f} (diff={diff:.1f})"
                    )
                final_scores.append(BenchmarkScore(
                    criterion=criterion,
                    score=round(avg, 1),
                    justification=f"Average of evaluators: {a.score:.1f} + {b.score:.1f}",
                ))
            elif a:
                final_scores.append(a)
            elif b:
                final_scores.append(b)

        total = len([c for c in all_criteria if c in map_a and c in map_b])
        agreement_rate = agreements / total if total > 0 else 0.0

        return ReconciliationResult(
            final_scores=final_scores,
            agreement_rate=agreement_rate,
            disagreements=disagreements,
        )
