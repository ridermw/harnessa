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


def test_run_prints_not_implemented() -> None:
    """'run' command with valid args prints not-yet-implemented."""
    result = runner.invoke(app, ["run", "todo-app"])
    assert result.exit_code == 0
    assert "Not yet implemented" in result.output


def test_run_invalid_mode() -> None:
    """'run' with invalid mode exits with error."""
    result = runner.invoke(app, ["run", "todo-app", "--mode", "invalid"])
    assert result.exit_code == 1


def test_replay_help() -> None:
    """'replay' subcommand --help shows run-id argument."""
    result = runner.invoke(app, ["replay", "--help"])
    assert result.exit_code == 0
    assert "run" in result.output.lower()


def test_report_prints_not_implemented() -> None:
    """'report' command prints not-yet-implemented."""
    result = runner.invoke(app, ["report", "abc123"])
    assert result.exit_code == 0
    assert "Not yet implemented" in result.output


def test_list_prints_not_implemented() -> None:
    """'list' command prints not-yet-implemented."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Not yet implemented" in result.output
