"""Replay manager — re-evaluate previous runs with new or updated criteria."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from harnessa.telemetry.models import RunManifest

logger = logging.getLogger(__name__)


class ReplayManager:
    """Manage replay of previous benchmark runs.

    Loads artifact snapshots from completed runs and re-runs the evaluator
    to produce new scores — enabling A/B testing of evaluator criteria
    without re-executing the generator.
    """

    def replay(
        self,
        run_id: str,
        runs_dir: Path,
        evaluator_prompt_override: Path | None = None,
    ) -> RunManifest:
        """Replay a previous run by re-evaluating its saved artifacts.

        Args:
            run_id: ID of the original run.
            runs_dir: Root directory containing per-run subdirectories.
            evaluator_prompt_override: Optional path to alternative criteria
                file.  When provided the original criteria are ignored.

        Returns:
            A new RunManifest with ``replayed_from`` set to the original
            *run_id* and fresh scores from the re-evaluation.

        Raises:
            FileNotFoundError: If the run directory, manifest, or artifact
                snapshot cannot be found.
        """
        run_dir = runs_dir / run_id
        manifest_path = run_dir / "manifest.json"
        artifacts_dir = run_dir / "artifacts"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        if not artifacts_dir.exists():
            raise FileNotFoundError(f"Artifacts not found: {artifacts_dir}")

        original = RunManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )

        # Resolve evaluator criteria
        if evaluator_prompt_override is not None:
            criteria_path = evaluator_prompt_override
        else:
            criteria_path = run_dir / "criteria.yaml"

        criteria_text: str | None = None
        if criteria_path.exists():
            criteria_text = criteria_path.read_text(encoding="utf-8")

        new_manifest = self._evaluate_artifacts(
            original=original,
            artifacts_dir=artifacts_dir,
            criteria_text=criteria_text,
        )

        # Persist the new manifest alongside the original run data
        new_manifest_path = run_dir / f"{new_manifest.run_id}.json"
        new_manifest_path.write_text(
            new_manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info(
            "Replay of %s saved as %s", run_id, new_manifest.run_id
        )

        return new_manifest

    # ------------------------------------------------------------------
    # Internal — evaluator hook
    # ------------------------------------------------------------------

    def _evaluate_artifacts(
        self,
        original: RunManifest,
        artifacts_dir: Path,
        criteria_text: str | None,
    ) -> RunManifest:
        """Re-evaluate artifacts from a previous run.

        In production this invokes the full evaluator agent pipeline.
        The base implementation returns a new manifest shell; subclasses
        or callers can override ``_evaluate_artifacts`` to wire in the
        real evaluator.
        """
        new_run_id = uuid.uuid4().hex[:12]
        return RunManifest(
            run_id=new_run_id,
            benchmark=original.benchmark,
            mode=original.mode,
            model_info=original.model_info,
            agents=[],
            scores=[],
            cost_usd=0.0,
            duration_s=0.0,
            started_at=datetime.now(),
            replayed_from=original.run_id,
        )

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_replayable_runs(self, runs_dir: Path) -> list[dict]:
        """Scan *runs_dir* for runs that have saved artifact snapshots.

        Args:
            runs_dir: Root directory containing per-run subdirectories.

        Returns:
            A list of dicts, each with keys ``run_id``, ``benchmark``,
            ``mode``, ``timestamp``, and ``has_artifacts``.
        """
        if not runs_dir.exists():
            return []

        results: list[dict] = []
        for entry in sorted(runs_dir.iterdir()):
            if not entry.is_dir():
                continue

            manifest_path = entry / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                manifest = RunManifest.model_validate_json(
                    manifest_path.read_text(encoding="utf-8")
                )
            except Exception:
                logger.warning("Skipping unreadable manifest in %s", entry)
                continue

            results.append({
                "run_id": manifest.run_id,
                "benchmark": manifest.benchmark,
                "mode": manifest.mode,
                "timestamp": manifest.started_at.isoformat(),
                "has_artifacts": (entry / "artifacts").is_dir(),
            })

        return results
