"""Tests for MarkdownReporter and DifficultyAnalyzer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from harnessa.reporting.difficulty import DifficultyAnalyzer
from harnessa.reporting.markdown import MarkdownReporter
from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    BugReport,
    BugStatus,
    DifficultyZone,
    ModelInfo,
    QualityTrend,
    RunManifest,
    Severity,
)


# ------------------------------------------------------------------
# Fixtures — realistic manifest builders
# ------------------------------------------------------------------

def _make_manifest(
    *,
    run_id: str = "run-001",
    benchmark: str = "small-bugfix-python",
    mode: str = "solo",
    scores: list[BenchmarkScore] | None = None,
    bugs: list[BugReport] | None = None,
    quality_trends: list[QualityTrend] | None = None,
    verdict: str = "PASS",
    cost: float = 0.45,
    duration: float = 120.0,
) -> RunManifest:
    if scores is None:
        scores = [
            BenchmarkScore(criterion="Functionality", score=8.0, justification="All tests pass"),
            BenchmarkScore(criterion="Code Quality", score=7.5, justification="Clean diff"),
            BenchmarkScore(criterion="Regression Safety", score=9.0, justification="No regressions"),
        ]
    return RunManifest(
        run_id=run_id,
        benchmark=benchmark,
        mode=mode,
        model_info=[
            ModelInfo(provider="anthropic", model_id="claude-sonnet-4-20250514", temperature=0.7, max_tokens=8192),
        ],
        agents=[
            AgentMetrics(
                model_id="claude-sonnet-4-20250514",
                tokens_in=5000,
                tokens_out=2000,
                duration_s=60.0,
                cost_usd=0.25,
                tool_usage=["git", "file_write", "shell"],
            ),
            AgentMetrics(
                model_id="claude-sonnet-4-20250514",
                tokens_in=3000,
                tokens_out=1500,
                duration_s=40.0,
                cost_usd=0.20,
                tool_usage=["git", "test_runner"],
            ),
        ],
        scores=scores,
        bugs=bugs or [],
        quality_trends=quality_trends or [],
        verdict=verdict,
        cost_usd=cost,
        duration_s=duration,
        started_at=datetime(2025, 6, 1, 12, 0, 0),
    )


# ------------------------------------------------------------------
# MarkdownReporter — single run
# ------------------------------------------------------------------

class TestMarkdownReporterGenerate:
    """Tests for MarkdownReporter.generate()."""

    def test_generate_creates_file(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest()
        out = tmp_path / "report.md"
        result = reporter.generate(manifest, out)
        assert result == out
        assert out.exists()

    def test_report_contains_run_summary(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Run Summary" in content
        assert "small-bugfix-python" in content
        assert "solo" in content
        assert "claude-sonnet-4-20250514" in content
        assert "$0.4500" in content
        assert "PASS" in content

    def test_report_contains_score_breakdown(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Score Breakdown" in content
        assert "Functionality" in content
        assert "8.0" in content
        assert "✅ PASS" in content

    def test_report_marks_failing_scores(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest(scores=[
            BenchmarkScore(criterion="Quality", score=5.0, justification="Needs work"),
        ])
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "❌ FAIL" in content

    def test_report_contains_cost_breakdown(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Cost Breakdown" in content
        assert "5,000" in content  # tokens_in formatted
        assert "$0.2500" in content

    def test_report_contains_tool_usage(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Tool Usage" in content
        assert "git" in content
        assert "file_write" in content

    def test_report_contains_bugs_section(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest(bugs=[
            BugReport(
                id="bug-1",
                severity=Severity.HIGH,
                description="Null pointer in parser",
                file="src/parser.py",
                line=42,
                status=BugStatus.OPEN,
            ),
        ])
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Bugs Found" in content
        assert "Null pointer in parser" in content
        assert "src/parser.py" in content
        assert "42" in content

    def test_report_omits_bugs_when_none(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest(bugs=[])
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Bugs Found" not in content

    def test_report_contains_quality_trend(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest(quality_trends=[
            QualityTrend(criterion="Functionality", scores=[6.0, 7.5, 8.0]),
            QualityTrend(criterion="Code Quality", scores=[5.0, 6.0, 7.5]),
        ])
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Quality Trend" in content
        assert "Iter 1" in content
        assert "Iter 3" in content

    def test_report_omits_quality_trend_when_empty(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest(quality_trends=[])
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()
        assert "## Quality Trend" not in content

    def test_generate_creates_parent_dirs(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        manifest = _make_manifest()
        out = tmp_path / "nested" / "dir" / "report.md"
        result = reporter.generate(manifest, out)
        assert result.exists()


# ------------------------------------------------------------------
# MarkdownReporter — comparison
# ------------------------------------------------------------------

class TestMarkdownReporterComparison:
    """Tests for MarkdownReporter.generate_comparison()."""

    def test_comparison_creates_file(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        solo = _make_manifest(run_id="solo-001", mode="solo")
        trio = _make_manifest(run_id="trio-001", mode="trio", cost=0.90, duration=200.0)
        out = tmp_path / "comparison.md"
        result = reporter.generate_comparison(solo, trio, out)
        assert result == out
        assert out.exists()

    def test_comparison_contains_summary(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        solo = _make_manifest(mode="solo")
        trio = _make_manifest(
            mode="trio",
            scores=[
                BenchmarkScore(criterion="Functionality", score=9.0, justification="Excellent"),
                BenchmarkScore(criterion="Code Quality", score=8.5, justification="Very clean"),
                BenchmarkScore(criterion="Regression Safety", score=9.5, justification="Perfect"),
            ],
        )
        out = tmp_path / "comparison.md"
        reporter.generate_comparison(solo, trio, out)
        content = out.read_text()
        assert "## Summary Comparison" in content
        assert "Solo" in content
        assert "Trio" in content

    def test_comparison_contains_score_deltas(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        solo = _make_manifest(scores=[
            BenchmarkScore(criterion="Functionality", score=6.0, justification="OK"),
        ])
        trio = _make_manifest(scores=[
            BenchmarkScore(criterion="Functionality", score=9.0, justification="Great"),
        ])
        out = tmp_path / "comparison.md"
        reporter.generate_comparison(solo, trio, out)
        content = out.read_text()
        assert "+3.0" in content

    def test_comparison_contains_cost_comparison(self, tmp_path: Path) -> None:
        reporter = MarkdownReporter()
        solo = _make_manifest(cost=0.30)
        trio = _make_manifest(cost=0.90)
        out = tmp_path / "comparison.md"
        reporter.generate_comparison(solo, trio, out)
        content = out.read_text()
        assert "## Cost Comparison" in content
        assert "$0.3000" in content
        assert "$0.9000" in content


# ------------------------------------------------------------------
# DifficultyAnalyzer
# ------------------------------------------------------------------

class TestDifficultyAnalyzer:
    """Tests for the five difficulty classifications."""

    def _manifest_with_avg(self, avg: float, mode: str = "solo") -> RunManifest:
        """Build a manifest whose score average is exactly *avg*."""
        return _make_manifest(
            mode=mode,
            scores=[BenchmarkScore(criterion="X", score=avg, justification="test")],
        )

    def test_too_easy(self) -> None:
        analyzer = DifficultyAnalyzer()
        solo = self._manifest_with_avg(9.5, mode="solo")
        trio = self._manifest_with_avg(9.5, mode="trio")
        result = analyzer.analyze(solo, trio)
        assert result.zone == DifficultyZone.TOO_EASY
        assert "edge cases" in result.recommendation.lower()

    def test_too_hard(self) -> None:
        analyzer = DifficultyAnalyzer()
        solo = self._manifest_with_avg(3.0, mode="solo")
        trio = self._manifest_with_avg(4.0, mode="trio")
        result = analyzer.analyze(solo, trio)
        assert result.zone == DifficultyZone.TOO_HARD
        assert "simplify" in result.recommendation.lower()

    def test_in_zone(self) -> None:
        analyzer = DifficultyAnalyzer()
        solo = self._manifest_with_avg(6.0, mode="solo")
        trio = self._manifest_with_avg(8.0, mode="trio")  # delta = 2.0 >= 1.5
        result = analyzer.analyze(solo, trio)
        assert result.zone == DifficultyZone.IN_ZONE
        assert "good benchmark" in result.recommendation.lower()

    def test_trio_overhead(self) -> None:
        analyzer = DifficultyAnalyzer()
        solo = self._manifest_with_avg(7.5, mode="solo")
        trio = self._manifest_with_avg(7.0, mode="trio")  # solo > trio
        result = analyzer.analyze(solo, trio)
        assert result.zone == DifficultyZone.TRIO_OVERHEAD
        assert "overhead" in result.recommendation.lower()

    def test_marginal(self) -> None:
        analyzer = DifficultyAnalyzer()
        solo = self._manifest_with_avg(7.0, mode="solo")
        trio = self._manifest_with_avg(7.5, mode="trio")  # delta = 0.5 < 1.5, trio > solo
        result = analyzer.analyze(solo, trio)
        assert result.zone == DifficultyZone.MARGINAL
        assert "statistical significance" in result.recommendation.lower()

    def test_solo_avg_and_trio_avg_populated(self) -> None:
        analyzer = DifficultyAnalyzer()
        solo = self._manifest_with_avg(6.0, mode="solo")
        trio = self._manifest_with_avg(8.0, mode="trio")
        result = analyzer.analyze(solo, trio)
        assert result.solo_avg == 6.0
        assert result.trio_avg == 8.0
        assert result.avg_score == 7.0  # overall avg of [6.0, 8.0]

    def test_analyze_scores_backward_compat(self) -> None:
        """analyze_scores still works for flat score lists."""
        analyzer = DifficultyAnalyzer()
        scores = [BenchmarkScore(criterion="A", score=9.5, justification="")]
        result = analyzer.analyze_scores(scores)
        assert result.zone == DifficultyZone.TOO_EASY
