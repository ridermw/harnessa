"""Telemetry collector — accumulates metrics and writes the final RunManifest."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    RunManifest,
)

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Accumulates agent metrics and scores during a run, then serializes them.

    Usage:
        collector = TelemetryCollector(run_id="abc123", benchmark="todo-app", mode="solo")
        collector.add_agent_metrics(metrics)
        collector.add_score(score)
        collector.finalize(output_dir)
    """

    def __init__(self, run_id: str, benchmark: str, mode: str) -> None:
        self.run_id = run_id
        self.benchmark = benchmark
        self.mode = mode
        self._agents: list[AgentMetrics] = []
        self._scores: list[BenchmarkScore] = []
        self._started_at = datetime.now()

    def add_agent_metrics(self, metrics: AgentMetrics) -> None:
        """Record metrics for one agent."""
        self._agents.append(metrics)

    def add_score(self, score: BenchmarkScore) -> None:
        """Record a single evaluation score."""
        self._scores.append(score)

    def build_manifest(self) -> RunManifest:
        """Build the final RunManifest from accumulated data."""
        total_cost = sum(a.cost_usd for a in self._agents)
        total_duration = sum(a.duration_s for a in self._agents)

        return RunManifest(
            run_id=self.run_id,
            benchmark=self.benchmark,
            mode=self.mode,
            agents=self._agents,
            scores=self._scores,
            cost_usd=total_cost,
            duration_s=total_duration,
            started_at=self._started_at,
            finished_at=datetime.now(),
        )

    def finalize(self, output_dir: Path) -> Path:
        """Write the RunManifest as JSON atomically.

        Returns the path to the written manifest file.
        """
        manifest = self.build_manifest()
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / f"{self.run_id}.json"
        self._atomic_write_json(target, manifest.model_dump(mode="json"))
        logger.info("Wrote manifest to %s", target)
        return target

    @staticmethod
    def _atomic_write_json(path: Path, data: dict) -> None:
        """Write JSON atomically: write to temp file, then rename."""
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        tmp_path.rename(path)
