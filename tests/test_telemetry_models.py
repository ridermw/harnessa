"""Tests for telemetry Pydantic models."""

from datetime import datetime

from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    BugReport,
    BugStatus,
    CanonicalResponse,
    DifficultyAnalysis,
    DifficultyZone,
    ModelInfo,
    QualityTrend,
    RunValidity,
    RunManifest,
    Severity,
    SuiteResult,
    SprintMetrics,
)


def test_model_info() -> None:
    """ModelInfo instantiates with valid data."""
    m = ModelInfo(provider="anthropic", model_id="claude-sonnet-4-20250514", temperature=0.5, max_tokens=8192)
    assert m.provider == "anthropic"
    assert m.temperature == 0.5


def test_canonical_response() -> None:
    """CanonicalResponse captures all required fields."""
    r = CanonicalResponse(
        text="Hello world",
        stop_reason="end_turn",
        model="gpt-4",
        tokens_in=10,
        tokens_out=20,
        cost=0.001,
        truncated=False,
    )
    assert r.text == "Hello world"
    assert r.tokens_in == 10


def test_agent_metrics() -> None:
    """AgentMetrics defaults and field validation."""
    m = AgentMetrics(model_id="gpt-4")
    assert m.tokens_in == 0
    assert m.tool_usage == []


def test_benchmark_score() -> None:
    """BenchmarkScore with criterion and justification."""
    s = BenchmarkScore(criterion="Code Quality", score=8.5, justification="Clean code")
    assert s.score == 8.5


def test_bug_report() -> None:
    """BugReport with all fields."""
    b = BugReport(
        id="bug-001",
        severity=Severity.HIGH,
        description="NullPointerException on login",
        file="src/auth.py",
        line=42,
        status=BugStatus.OPEN,
    )
    assert b.severity == Severity.HIGH


def test_sprint_metrics() -> None:
    """SprintMetrics captures iteration data."""
    s = SprintMetrics(iteration=1, bugs_found=3, bugs_fixed=2, duration_s=120.5)
    assert s.iteration == 1


def test_quality_trend() -> None:
    """QualityTrend tracks score evolution."""
    t = QualityTrend(criterion="Functionality", scores=[5.0, 6.5, 7.0])
    assert len(t.scores) == 3


def test_difficulty_analysis() -> None:
    """DifficultyAnalysis classifies zones."""
    d = DifficultyAnalysis(
        zone=DifficultyZone.IN_ZONE,
        avg_score=6.5,
        score_variance=1.2,
        recommendation="Well calibrated",
    )
    assert d.zone == DifficultyZone.IN_ZONE


def test_run_manifest() -> None:
    """RunManifest captures complete run metadata."""
    m = RunManifest(
        run_id="test-run-001",
        benchmark="todo-app",
        mode="solo",
        model_info=[ModelInfo(provider="openai", model_id="gpt-4", temperature=0.7, max_tokens=4096)],
        agents=[AgentMetrics(model_id="gpt-4", tokens_in=100, tokens_out=200, cost_usd=0.01)],
        scores=[BenchmarkScore(criterion="Functionality", score=7.0, justification="Works well")],
        cost_usd=0.01,
        duration_s=45.0,
        started_at=datetime(2025, 1, 1, 12, 0, 0),
        harness_version="0.1.0",
    )
    assert m.run_id == "test-run-001"
    assert len(m.agents) == 1
    assert m.harness_version == "0.1.0"


def test_suite_result_computes_total_from_pass_fail() -> None:
    """SuiteResult backfills total when omitted."""
    result = SuiteResult(passed=3, failed=2)
    assert result.total == 5


def test_run_manifest_accepts_validity_and_test_evidence() -> None:
    """RunManifest stores shared suite evidence and trust state."""
    manifest = RunManifest(
        run_id="test-run-002",
        benchmark="todo-app",
        mode="solo",
        model_info=[ModelInfo(provider="openai", model_id="gpt-4")],
        scores=[BenchmarkScore(criterion="Functionality", score=7.0, justification="Works well")],
        visible_tests=SuiteResult(
            passed=5,
            failed=1,
            framework="pytest",
            command=["python", "-m", "pytest", "tests"],
            report_path="runs/test/visible-report.xml",
        ),
        eval_tests=SuiteResult(
            passed=3,
            failed=0,
            framework="pytest",
            command=["python", "-m", "pytest", "_eval"],
            report_path="runs/test/eval-report.xml",
        ),
        run_validity=RunValidity.CLEAN,
        cost_usd=0.01,
        duration_s=45.0,
        started_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    assert manifest.run_validity == RunValidity.CLEAN
    assert manifest.visible_tests is not None
    assert manifest.visible_tests.total == 6
    assert manifest.eval_tests is not None
