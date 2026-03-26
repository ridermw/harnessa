"""Tests for the Harnessa CLI."""

from typer.testing import CliRunner

from harnessa.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    """CLI --help exits cleanly and shows the app description."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "GAN-inspired" in result.output


def test_run_help() -> None:
    """'run' subcommand --help shows benchmark argument."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "benchmark" in result.output.lower()


def test_run_prints_benchmark_name() -> None:
    """'run' command with valid args prints benchmark name."""
    from unittest.mock import MagicMock, patch

    mock_manifest = MagicMock()
    mock_manifest.benchmark = "todo-app"
    mock_manifest.mode = "solo"
    mock_manifest.verdict = "PASS"
    mock_manifest.cost_usd = 0.0
    mock_manifest.duration_s = 0.0
    mock_manifest.scores = []
    mock_manifest.run_id = "test123"

    with patch("harnessa.orchestrator.Orchestrator") as mock_orch_cls, \
         patch("harnessa.reporting.markdown.MarkdownReporter") as mock_reporter_cls:
        mock_orch_cls.return_value.start_run.return_value = mock_manifest
        result = runner.invoke(app, ["run", "todo-app"])
        assert result.exit_code == 0
        assert "todo-app" in result.output


def test_run_invalid_mode() -> None:
    """'run' with invalid mode exits with error."""
    result = runner.invoke(app, ["run", "todo-app", "--mode", "invalid"])
    assert result.exit_code == 1


def test_replay_help() -> None:
    """'replay' subcommand --help shows run-id argument."""
    result = runner.invoke(app, ["replay", "--help"])
    assert result.exit_code == 0
    assert "run" in result.output.lower()


def test_report_requires_manifest() -> None:
    """'report' command exits with error when manifest not found."""
    result = runner.invoke(app, ["report", "nonexistent123"])
    assert result.exit_code == 1


def test_list_shows_benchmarks() -> None:
    """'list' command shows benchmarks from benchmarks/ directory."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "small-bugfix-python" in result.output
