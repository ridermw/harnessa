"""Tests for ReplayManager."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from harnessa.replay import ReplayManager
from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    ModelInfo,
    RunManifest,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_manifest(
    run_id: str = "orig-run-001",
    benchmark: str = "small-bugfix-python",
    mode: str = "solo",
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        benchmark=benchmark,
        mode=mode,
        model_info=[
            ModelInfo(provider="anthropic", model_id="claude-sonnet-4-20250514", temperature=0.7, max_tokens=8192),
        ],
        agents=[
            AgentMetrics(model_id="claude-sonnet-4-20250514", tokens_in=1000, tokens_out=500, cost_usd=0.10),
        ],
        scores=[
            BenchmarkScore(criterion="Functionality", score=8.0, justification="Works"),
        ],
        cost_usd=0.10,
        duration_s=45.0,
        started_at=datetime(2025, 6, 1, 12, 0, 0),
    )


def _setup_run_dir(
    runs_dir: Path,
    run_id: str = "orig-run-001",
    *,
    with_artifacts: bool = True,
    with_criteria: bool = True,
) -> Path:
    """Create a realistic run directory structure for testing."""
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True)

    manifest = _make_manifest(run_id=run_id)
    (run_dir / "manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )

    if with_artifacts:
        artifacts = run_dir / "artifacts"
        artifacts.mkdir()
        (artifacts / "main.py").write_text("print('hello')", encoding="utf-8")

    if with_criteria:
        (run_dir / "criteria.yaml").write_text(
            "criteria:\n  - name: Functionality\n    weight: 1.0\n",
            encoding="utf-8",
        )

    return run_dir


# ------------------------------------------------------------------
# list_replayable_runs
# ------------------------------------------------------------------

class TestListReplayableRuns:
    def test_empty_dir(self, tmp_path: Path) -> None:
        mgr = ReplayManager()
        assert mgr.list_replayable_runs(tmp_path) == []

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        mgr = ReplayManager()
        assert mgr.list_replayable_runs(tmp_path / "nope") == []

    def test_lists_run_with_artifacts(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "run-aaa", with_artifacts=True)
        mgr = ReplayManager()
        runs = mgr.list_replayable_runs(tmp_path)
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run-aaa"
        assert runs[0]["benchmark"] == "small-bugfix-python"
        assert runs[0]["has_artifacts"] is True

    def test_lists_run_without_artifacts(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "run-bbb", with_artifacts=False)
        mgr = ReplayManager()
        runs = mgr.list_replayable_runs(tmp_path)
        assert len(runs) == 1
        assert runs[0]["has_artifacts"] is False

    def test_skips_non_directories(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "run-ccc")
        (tmp_path / "random.txt").write_text("ignored", encoding="utf-8")
        mgr = ReplayManager()
        runs = mgr.list_replayable_runs(tmp_path)
        assert len(runs) == 1

    def test_skips_dirs_without_manifest(self, tmp_path: Path) -> None:
        (tmp_path / "orphan-dir").mkdir()
        mgr = ReplayManager()
        runs = mgr.list_replayable_runs(tmp_path)
        assert runs == []

    def test_multiple_runs_sorted(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "alpha")
        _setup_run_dir(tmp_path, "beta")
        mgr = ReplayManager()
        runs = mgr.list_replayable_runs(tmp_path)
        assert [r["run_id"] for r in runs] == ["alpha", "beta"]


# ------------------------------------------------------------------
# replay
# ------------------------------------------------------------------

class TestReplay:
    def test_replay_returns_manifest_with_replayed_from(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "orig-001")
        mgr = ReplayManager()
        result = mgr.replay("orig-001", tmp_path)
        assert result.replayed_from == "orig-001"
        assert result.run_id != "orig-001"
        assert result.benchmark == "small-bugfix-python"

    def test_replay_saves_new_manifest(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "orig-002")
        mgr = ReplayManager()
        result = mgr.replay("orig-002", tmp_path)
        new_path = tmp_path / "orig-002" / f"{result.run_id}.json"
        assert new_path.exists()

    def test_replay_raises_on_missing_manifest(self, tmp_path: Path) -> None:
        (tmp_path / "no-manifest").mkdir()
        (tmp_path / "no-manifest" / "artifacts").mkdir()
        mgr = ReplayManager()
        with pytest.raises(FileNotFoundError, match="Manifest not found"):
            mgr.replay("no-manifest", tmp_path)

    def test_replay_raises_on_missing_artifacts(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "no-artifacts", with_artifacts=False)
        mgr = ReplayManager()
        with pytest.raises(FileNotFoundError, match="Artifacts not found"):
            mgr.replay("no-artifacts", tmp_path)

    def test_replay_with_evaluator_prompt_override(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "orig-003")
        override = tmp_path / "custom_criteria.yaml"
        override.write_text("criteria:\n  - name: Security\n    weight: 1.0\n", encoding="utf-8")

        mgr = ReplayManager()
        result = mgr.replay("orig-003", tmp_path, evaluator_prompt_override=override)
        assert result.replayed_from == "orig-003"

    def test_replay_preserves_original_model_info(self, tmp_path: Path) -> None:
        _setup_run_dir(tmp_path, "orig-004")
        mgr = ReplayManager()
        result = mgr.replay("orig-004", tmp_path)
        assert len(result.model_info) == 1
        assert result.model_info[0].model_id == "claude-sonnet-4-20250514"

    def test_replay_invokes_evaluate_artifacts(self, tmp_path: Path) -> None:
        """Ensure _evaluate_artifacts is called with the right arguments."""
        _setup_run_dir(tmp_path, "orig-005")
        mgr = ReplayManager()

        called_with: dict = {}

        original_evaluate = mgr._evaluate_artifacts

        def spy(*, original, artifacts_dir, criteria_text):
            called_with["original"] = original
            called_with["artifacts_dir"] = artifacts_dir
            called_with["criteria_text"] = criteria_text
            return original_evaluate(
                original=original,
                artifacts_dir=artifacts_dir,
                criteria_text=criteria_text,
            )

        mgr._evaluate_artifacts = spy  # type: ignore[assignment]
        mgr.replay("orig-005", tmp_path)

        assert called_with["original"].run_id == "orig-005"
        assert called_with["artifacts_dir"] == tmp_path / "orig-005" / "artifacts"
        assert called_with["criteria_text"] is not None
