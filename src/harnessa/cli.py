"""Harnessa CLI — Typer-based command interface."""

from __future__ import annotations

import json
import time
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
    max_iterations: Annotated[int, typer.Option("--max-iterations", help="Max GAN-loop iterations")] = 3,
) -> None:
    """Run a benchmark with the specified configuration."""
    if mode not in ("solo", "trio"):
        typer.echo(f"Error: mode must be 'solo' or 'trio', got '{mode}'", err=True)
        raise typer.Exit(code=1)

    models = [m.strip() for m in evaluator_models.split(",")]
    criteria_path = Path(f"criteria/{criteria}.yaml")

    from harnessa.config import RunConfig, RunMode
    from harnessa.orchestrator import Orchestrator
    from harnessa.reporting.markdown import MarkdownReporter

    config = RunConfig(
        benchmark=benchmark,
        mode=RunMode(mode),
        evaluator_models=models,
        criteria_path=criteria_path,
        max_iterations=max_iterations,
    )

    typer.echo(
        f"[harnessa] run benchmark={benchmark} mode={mode} "
        f"evaluators={models} criteria={criteria}"
    )

    orchestrator = Orchestrator(config)
    manifest = orchestrator.start_run()

    # Generate markdown report
    reporter = MarkdownReporter()
    report_path = Path(f"runs/{config.run_id}/report.md")
    reporter.generate(manifest, report_path)

    # Print summary
    avg_score = (
        sum(s.score for s in manifest.scores) / len(manifest.scores)
        if manifest.scores
        else 0.0
    )
    typer.echo(f"\n{'='*50}")
    typer.echo(f"  Benchmark: {manifest.benchmark}")
    typer.echo(f"  Mode:      {manifest.mode}")
    typer.echo(f"  Verdict:   {manifest.verdict}")
    typer.echo(f"  Avg Score: {avg_score:.1f}/10")
    typer.echo(f"  Cost:      ${manifest.cost_usd:.4f}")
    typer.echo(f"  Duration:  {manifest.duration_s:.1f}s")
    typer.echo(f"{'='*50}")
    typer.echo(f"\nFull report: {report_path}")


@app.command()
def replay(
    run_id: Annotated[str, typer.Argument(help="Run ID to replay")],
    evaluator_prompt: Annotated[Optional[Path], typer.Option("--evaluator-prompt", help="Path to custom evaluator prompt")] = None,
) -> None:
    """Replay a previous run with a different evaluator prompt."""
    from harnessa.replay import ReplayManager

    typer.echo(f"[harnessa] replay run_id={run_id}")
    manager = ReplayManager()
    runs_dir = Path("runs")

    new_manifest = manager.replay(
        run_id, runs_dir, evaluator_prompt_override=evaluator_prompt
    )

    typer.echo(f"  Original run:  {run_id}")
    typer.echo(f"  Replay run:    {new_manifest.run_id}")

    orig_manifest_path = runs_dir / run_id / "telemetry" / "run-manifest.json"
    if orig_manifest_path.exists():
        from harnessa.telemetry.models import RunManifest

        original = RunManifest.model_validate_json(
            orig_manifest_path.read_text(encoding="utf-8")
        )
        orig_avg = (
            sum(s.score for s in original.scores) / len(original.scores)
            if original.scores
            else 0.0
        )
        new_avg = (
            sum(s.score for s in new_manifest.scores) / len(new_manifest.scores)
            if new_manifest.scores
            else 0.0
        )
        typer.echo(f"  Original avg:  {orig_avg:.1f}/10")
        typer.echo(f"  Replayed avg:  {new_avg:.1f}/10")
    else:
        typer.echo("  (original manifest not found for comparison)")


@app.command()
def report(
    run_id: Annotated[str, typer.Argument(help="Run ID to generate report for")],
) -> None:
    """Generate a report for a completed run."""
    from harnessa.reporting.markdown import MarkdownReporter
    from harnessa.telemetry.models import RunManifest

    manifest_path = Path(f"runs/{run_id}/telemetry/run-manifest.json")
    if not manifest_path.exists():
        typer.echo(f"Error: manifest not found at {manifest_path}", err=True)
        raise typer.Exit(code=1)

    manifest = RunManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )

    reporter = MarkdownReporter()
    report_path = Path(f"runs/{run_id}/report.md")
    reporter.generate(manifest, report_path)

    report_content = report_path.read_text(encoding="utf-8")
    typer.echo(report_content)
    typer.echo(f"\nReport saved to: {report_path}")


@app.command(name="list")
def list_benchmarks() -> None:
    """List available benchmarks."""
    benchmarks_dir = Path("benchmarks")
    if not benchmarks_dir.exists():
        typer.echo("No benchmarks directory found.")
        return

    typer.echo(f"{'Name':<35} {'Language':<15} {'Description'}")
    typer.echo(f"{'-'*35} {'-'*15} {'-'*50}")

    for entry in sorted(benchmarks_dir.iterdir()):
        if not entry.is_dir():
            continue
        task_md = entry / "TASK.md"
        if not task_md.exists():
            continue

        name = entry.name
        description = task_md.read_text(encoding="utf-8").strip().split("\n")[0]
        language = _detect_language(entry)
        typer.echo(f"{name:<35} {language:<15} {description}")


def _detect_language(benchmark_dir: Path) -> str:
    """Detect the primary language of a benchmark from its files."""
    extensions = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".js": "JavaScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
    }
    counts: dict[str, int] = {}
    for f in benchmark_dir.rglob("*"):
        if f.is_file() and f.suffix in extensions:
            lang = extensions[f.suffix]
            counts[lang] = counts.get(lang, 0) + 1
    if not counts:
        return "Unknown"
    return max(counts, key=counts.get)  # type: ignore[arg-type]


if __name__ == "__main__":
    app()
