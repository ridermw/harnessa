"""Harnessa CLI — Typer-based command interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

app = typer.Typer(
    name="harnessa",
    help="GAN-inspired multi-agent harness for LLM evaluation.",
    no_args_is_help=True,
)


@app.command()
def run(
    benchmark: Annotated[str, typer.Argument(help="Benchmark identifier to run")],
    mode: Annotated[str, typer.Option(help="Execution mode")] = "solo",
    evaluator_models: Annotated[str, typer.Option("--evaluator-models", help="Comma-separated evaluator model IDs")] = "claude-sonnet-4-20250514",
    criteria: Annotated[str, typer.Option(help="Criteria preset name (e.g. backend, fullstack)")] = "backend",
) -> None:
    """Run a benchmark with the specified configuration."""
    if mode not in ("solo", "trio"):
        typer.echo(f"Error: mode must be 'solo' or 'trio', got '{mode}'", err=True)
        raise typer.Exit(code=1)

    models = [m.strip() for m in evaluator_models.split(",")]
    typer.echo(
        f"[harnessa] run benchmark={benchmark} mode={mode} "
        f"evaluators={models} criteria={criteria}"
    )
    typer.echo("Not yet implemented")


@app.command()
def replay(
    run_id: Annotated[str, typer.Argument(help="Run ID to replay")],
    evaluator_prompt: Annotated[Optional[Path], typer.Option("--evaluator-prompt", help="Path to custom evaluator prompt")] = None,
) -> None:
    """Replay a previous run with a different evaluator prompt."""
    typer.echo(f"[harnessa] replay run_id={run_id} evaluator_prompt={evaluator_prompt}")
    typer.echo("Not yet implemented")


@app.command()
def report(
    run_id: Annotated[str, typer.Argument(help="Run ID to generate report for")],
) -> None:
    """Generate a report for a completed run."""
    typer.echo(f"[harnessa] report run_id={run_id}")
    typer.echo("Not yet implemented")


@app.command(name="list")
def list_benchmarks() -> None:
    """List available benchmarks."""
    typer.echo("[harnessa] Available benchmarks:")
    typer.echo("Not yet implemented")


if __name__ == "__main__":
    app()
