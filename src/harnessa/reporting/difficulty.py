"""Difficulty analyzer — classifies benchmark difficulty via solo/trio comparison."""

from __future__ import annotations

import logging
import statistics

from harnessa.telemetry.models import (
    BenchmarkScore,
    DifficultyAnalysis,
    DifficultyZone,
    RunManifest,
)

logger = logging.getLogger(__name__)

_FAIL_THRESHOLD = 5.0


class DifficultyAnalyzer:
    """Analyze solo vs trio score distributions to classify benchmark difficulty.

    Used to calibrate the GAN loop — if both modes ace or both modes fail,
    the benchmark needs adjustment.
    """

    def __init__(
        self,
        easy_threshold: float = 9.0,
        hard_threshold: float = 5.0,
        trio_margin: float = 1.5,
    ) -> None:
        """Initialize with zone thresholds.

        Args:
            easy_threshold: Average score above this (both modes) is "too easy".
            hard_threshold: Average score below this (both modes) is "too hard".
            trio_margin: Minimum trio-over-solo delta for "in_zone".
        """
        self.easy_threshold = easy_threshold
        self.hard_threshold = hard_threshold
        self.trio_margin = trio_margin

    def analyze(
        self,
        solo_manifest: RunManifest,
        trio_manifest: RunManifest,
    ) -> DifficultyAnalysis:
        """Classify difficulty by comparing solo and trio score distributions.

        Classification rules (evaluated in order):
            1. Both modes avg >= easy_threshold  → TOO_EASY
            2. Both modes avg < hard_threshold   → TOO_HARD
            3. Trio wins by >= trio_margin points → IN_ZONE
            4. Solo avg > trio avg               → TRIO_OVERHEAD
            5. Otherwise                         → MARGINAL

        Args:
            solo_manifest: RunManifest from a solo-mode run.
            trio_manifest: RunManifest from a trio-mode run.

        Returns:
            DifficultyAnalysis with zone classification and recommendation.
        """
        solo_values = [s.score for s in solo_manifest.scores]
        trio_values = [s.score for s in trio_manifest.scores]

        solo_avg = statistics.mean(solo_values) if solo_values else 0.0
        trio_avg = statistics.mean(trio_values) if trio_values else 0.0

        all_values = solo_values + trio_values
        overall_avg = statistics.mean(all_values) if all_values else 0.0
        variance = statistics.variance(all_values) if len(all_values) > 1 else 0.0

        zone, rec = self._classify(solo_avg, trio_avg)

        logger.info(
            "Difficulty analysis: zone=%s solo_avg=%.1f trio_avg=%.1f var=%.2f",
            zone,
            solo_avg,
            trio_avg,
            variance,
        )

        return DifficultyAnalysis(
            zone=zone,
            avg_score=round(overall_avg, 1),
            score_variance=round(variance, 2),
            recommendation=rec,
            solo_avg=round(solo_avg, 1),
            trio_avg=round(trio_avg, 1),
        )

    def _classify(self, solo_avg: float, trio_avg: float) -> tuple[DifficultyZone, str]:
        if solo_avg >= self.easy_threshold and trio_avg >= self.easy_threshold:
            return DifficultyZone.TOO_EASY, "Add edge cases"
        if solo_avg < self.hard_threshold and trio_avg < self.hard_threshold:
            return DifficultyZone.TOO_HARD, "Simplify acceptance criteria"
        if trio_avg - solo_avg >= self.trio_margin:
            return DifficultyZone.IN_ZONE, "Good benchmark"
        if solo_avg > trio_avg:
            return (
                DifficultyZone.TRIO_OVERHEAD,
                "Trio overhead exceeds value for this task size",
            )
        return (
            DifficultyZone.MARGINAL,
            "Consider more runs for statistical significance",
        )

    # Keep a convenience helper for analysing a flat list of scores.
    def analyze_scores(self, scores: list[BenchmarkScore]) -> DifficultyAnalysis:
        """Classify difficulty from a flat score list (no solo/trio split).

        Args:
            scores: List of benchmark scores to analyze.

        Returns:
            DifficultyAnalysis with zone classification and recommendation.
        """
        if not scores:
            return DifficultyAnalysis(
                zone=DifficultyZone.IN_ZONE,
                avg_score=0.0,
                score_variance=0.0,
                recommendation="No scores to analyze",
            )

        values = [s.score for s in scores]
        avg = statistics.mean(values)
        variance = statistics.variance(values) if len(values) > 1 else 0.0

        if avg >= self.easy_threshold:
            zone = DifficultyZone.TOO_EASY
            rec = "Increase benchmark difficulty or add harder criteria"
        elif avg < self.hard_threshold:
            zone = DifficultyZone.TOO_HARD
            rec = "Reduce benchmark scope or relax thresholds"
        else:
            zone = DifficultyZone.IN_ZONE
            rec = "Difficulty is well-calibrated"

        return DifficultyAnalysis(
            zone=zone,
            avg_score=round(avg, 1),
            score_variance=round(variance, 2),
            recommendation=rec,
        )
