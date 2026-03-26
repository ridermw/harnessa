"""Tests for CLI wiring — commands call the right modules."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from harnessa.cli import app
from harnessa.telemetry.models import RunManifest

runner = CliRunner()


class TestListCommand:
    """Test 'harnessa list' finds benchmarks."""

    def test_list_finds_benchmarks(self) -> None:
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "small-bugfix-python" in result.output

    def test_list_shows_language(self) -> None:
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Python" in result.output

    def test_list_shows_description(self) -> None:
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # First line of TASK.md should appear
        assert "Task" in result.output or "Fix" in result.output

    def test_list_shows_header(self) -> None:
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Name" in result.output
        assert "Language" in result.output


class TestRunCommand:
    """Test 'harnessa run' with mocked orchestrator."""

    def test_run_calls_orchestrator(self) -> None:
        mock_manifest = MagicMock()
        mock_manifest.benchmark = "test-bench"
        mock_manifest.mode = "solo"
        mock_manifest.verdict = "PASS"
        mock_manifest.cost_usd = 0.05
        mock_manifest.duration_s = 12.5
        mock_manifest.scores = []
        mock_manifest.run_id = "testcli001"

        with patch("harnessa.orchestrator.Orchestrator") as mock_orch_cls, \
             patch("harnessa.reporting.markdown.MarkdownReporter") as mock_reporter_cls:
            mock_orch_cls.return_value.start_run.return_value = mock_manifest
            result = runner.invoke(app, ["run", "test-bench"])

            assert result.exit_code == 0
            mock_orch_cls.return_value.start_run.assert_called_once()

    def test_run_prints_summary(self) -> None:
        mock_manifest = MagicMock()
        mock_manifest.benchmark = "my-bench"
        mock_manifest.mode = "trio"
        mock_manifest.verdict = "PASS"
        mock_manifest.cost_usd = 0.123
        mock_manifest.duration_s = 45.6
        mock_manifest.scores = []
        mock_manifest.run_id = "testcli002"

        with patch("harnessa.orchestrator.Orchestrator") as mock_orch_cls, \
             patch("harnessa.reporting.markdown.MarkdownReporter") as mock_reporter_cls:
            mock_orch_cls.return_value.start_run.return_value = mock_manifest
            result = runner.invoke(app, ["run", "my-bench", "--mode", "trio"])

            assert result.exit_code == 0
            assert "my-bench" in result.output
            assert "trio" in result.output
            assert "PASS" in result.output

    def test_run_invalid_mode_rejected(self) -> None:
        result = runner.invoke(app, ["run", "bench", "--mode", "invalid"])
        assert result.exit_code == 1

    def test_run_generates_report(self) -> None:
        mock_manifest = MagicMock()
        mock_manifest.benchmark = "test-bench"
        mock_manifest.mode = "solo"
        mock_manifest.verdict = "PASS"
        mock_manifest.cost_usd = 0.0
        mock_manifest.duration_s = 0.0
        mock_manifest.scores = []
        mock_manifest.run_id = "testcli003"

        with patch("harnessa.orchestrator.Orchestrator") as mock_orch_cls, \
             patch("harnessa.reporting.markdown.MarkdownReporter") as mock_reporter_cls:
            mock_orch_cls.return_value.start_run.return_value = mock_manifest
            result = runner.invoke(app, ["run", "test-bench"])

            assert result.exit_code == 0
            mock_reporter_cls.return_value.generate.assert_called_once()


class TestReportCommand:
    """Test 'harnessa report' with a saved manifest."""

    def test_report_with_saved_manifest(self, tmp_path: Path) -> None:
        run_id = "reporttest001"
        run_dir = Path(f"runs/{run_id}")
        telemetry_dir = run_dir / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)

        manifest = RunManifest(
            run_id=run_id,
            benchmark="test-bench",
            mode="solo",
            verdict="PASS",
        )
        manifest_path = telemetry_dir / "run-manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        try:
            result = runner.invoke(app, ["report", run_id])
            assert result.exit_code == 0
            assert "test-bench" in result.output
            assert "Report saved to" in result.output
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    def test_report_missing_manifest(self) -> None:
        result = runner.invoke(app, ["report", "nonexistent999"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestReplayCommand:
    """Test 'harnessa replay' with mocked ReplayManager."""

    def test_replay_calls_manager(self) -> None:
        mock_manifest = MagicMock()
        mock_manifest.run_id = "replay001"
        mock_manifest.benchmark = "test-bench"
        mock_manifest.scores = []

        with patch("harnessa.replay.ReplayManager") as mock_mgr_cls:
            mock_mgr_cls.return_value.replay.return_value = mock_manifest

            result = runner.invoke(app, ["replay", "original001"])

            assert result.exit_code == 0
            mock_mgr_cls.return_value.replay.assert_called_once()
            assert "original001" in result.output
            assert "replay001" in result.output
