"""Difficulty analyzer — classifies benchmark difficulty for GAN calibration."""

from __future__ import annotations

import logging
import statistics

from harnessa.telemetry.models import BenchmarkScore, DifficultyAnalysis, DifficultyZone

logger = logging.getLogger(__name__)


class DifficultyAnalyzer:
    """Analyze score distributions to classify benchmark difficulty.

    Used to calibrate the GAN loop — if scores are consistently too high
    or too low, the benchmark or attacker needs adjustment.
    """

    def __init__(self, easy_threshold: float = 8.0, hard_threshold: float = 4.0) -> None:
        """Initialize with zone thresholds.

        Args:
            easy_threshold: Average score above this is "too easy".
            hard_threshold: Average score below this is "too hard".
        """
        self.easy_threshold = easy_threshold
        self.hard_threshold = hard_threshold

    def analyze(self, scores: list[BenchmarkScore]) -> DifficultyAnalysis:
        """Classify difficulty based on score distribution.

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
        elif avg <= self.hard_threshold:
            zone = DifficultyZone.TOO_HARD
            rec = "Reduce benchmark scope or relax thresholds"
        else:
            zone = DifficultyZone.IN_ZONE
            rec = "Difficulty is well-calibrated"

        logger.info("Difficulty analysis: zone=%s avg=%.1f var=%.2f", zone, avg, variance)

        return DifficultyAnalysis(
            zone=zone,
            avg_score=round(avg, 1),
            score_variance=round(variance, 2),
            recommendation=rec,
        )
