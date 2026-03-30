"""Pydantic models for run telemetry, agent metrics, and quality tracking."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Bug severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugStatus(StrEnum):
    """Bug lifecycle status."""

    OPEN = "open"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"


class DifficultyZone(StrEnum):
    """Difficulty classification for GAN-loop calibration."""

    TOO_EASY = "too_easy"
    IN_ZONE = "in_zone"
    TOO_HARD = "too_hard"
    TRIO_OVERHEAD = "trio_overhead"
    MARGINAL = "marginal"


class ModelInfo(BaseModel):
    """LLM provider and model configuration."""

    model_config = {"strict": True}

    provider: str = Field(description="LLM provider (e.g. openai, anthropic)")
    model_id: str = Field(description="Model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)


class CanonicalResponse(BaseModel):
    """Normalized LiteLLM response for provider-agnostic telemetry."""

    model_config = {"strict": True}

    text: str = Field(description="Response text content")
    stop_reason: str = Field(default="end_turn", description="Why generation stopped")
    model: str = Field(description="Model that produced this response")
    tokens_in: int = Field(ge=0, description="Input token count")
    tokens_out: int = Field(ge=0, description="Output token count")
    cost: float = Field(ge=0.0, description="Estimated cost in USD")
    truncated: bool = Field(default=False, description="Whether the response was truncated")


class AgentMetrics(BaseModel):
    """Per-agent performance and cost metrics."""

    model_config = {"strict": True}

    model_id: str = Field(description="Model identifier used by this agent")
    tokens_in: int = Field(default=0, ge=0)
    tokens_out: int = Field(default=0, ge=0)
    duration_s: float = Field(default=0.0, ge=0.0, description="Wall-clock seconds")
    cost_usd: float = Field(default=0.0, ge=0.0)
    tool_usage: list[str] = Field(default_factory=list, description="Tools invoked by the agent")


class BenchmarkScore(BaseModel):
    """Score for a single evaluation criterion."""

    model_config = {"strict": True}

    criterion: str = Field(description="Criterion name")
    score: float = Field(ge=0.0, le=10.0, description="Score from 0-10")
    justification: str = Field(default="", description="Evaluator's reasoning")


class BugReport(BaseModel):
    """A bug discovered during evaluation."""

    model_config = {"strict": True}

    id: str = Field(description="Unique bug identifier")
    severity: Severity = Field(description="Bug severity")
    description: str = Field(description="What the bug is")
    file: str = Field(default="", description="File where bug occurs")
    line: int = Field(default=0, ge=0, description="Line number")
    status: BugStatus = Field(default=BugStatus.OPEN)


class SprintMetrics(BaseModel):
    """Metrics for a single GAN-loop iteration."""

    model_config = {"strict": True}

    iteration: int = Field(ge=1, description="Iteration number")
    scores: list[BenchmarkScore] = Field(default_factory=list)
    bugs_found: int = Field(default=0, ge=0)
    bugs_fixed: int = Field(default=0, ge=0)
    duration_s: float = Field(default=0.0, ge=0.0)


class QualityTrend(BaseModel):
    """Score evolution across GAN-loop iterations."""

    model_config = {"strict": True}

    criterion: str = Field(description="Criterion name")
    scores: list[float] = Field(default_factory=list, description="Score per iteration")


class DifficultyAnalysis(BaseModel):
    """Classification of benchmark difficulty for GAN calibration."""

    model_config = {"strict": True}

    zone: DifficultyZone = Field(description="Difficulty zone classification")
    avg_score: float = Field(ge=0.0, le=10.0)
    score_variance: float = Field(ge=0.0)
    recommendation: str = Field(default="", description="Suggested adjustment")
    solo_avg: float | None = Field(default=None, description="Solo mode average score")
    trio_avg: float | None = Field(default=None, description="Trio mode average score")


class ContractMetrics(BaseModel):
    """Metrics from the contract negotiation phase."""

    model_config = {"strict": True}

    negotiation_rounds: int = Field(ge=1, le=5)
    approved: bool = True
    features_proposed: int = Field(ge=0)
    criteria_proposed: int = Field(ge=0)
    criteria_added_by_evaluator: int = Field(ge=0)
    duration_s: float = Field(ge=0.0)


class RunManifest(BaseModel):
    """Top-level run metadata and results — the canonical output artifact."""

    model_config = {"strict": True}

    run_id: str = Field(description="Unique run identifier")
    benchmark: str = Field(description="Benchmark that was run")
    mode: str = Field(description="Execution mode (solo/trio)")
    model_info: list[ModelInfo] = Field(default_factory=list)
    agents: list[AgentMetrics] = Field(default_factory=list)
    scores: list[BenchmarkScore] = Field(default_factory=list)
    bugs: list[BugReport] = Field(default_factory=list, description="Bugs discovered during evaluation")
    quality_trends: list[QualityTrend] = Field(
        default_factory=list, description="Score evolution across iterations"
    )
    sprints: list[SprintMetrics] = Field(
        default_factory=list, description="Per-iteration sprint metrics"
    )
    contract_metrics: ContractMetrics | None = Field(
        default=None, description="Contract negotiation metrics (trio mode only)"
    )
    cost_usd: float = Field(default=0.0, ge=0.0)
    duration_s: float = Field(default=0.0, ge=0.0)
    verdict: str = Field(default="", description="Overall PASS/FAIL verdict")
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = Field(default=None)
    replayed_from: str | None = Field(default=None, description="Run ID this was replayed from")
    harness_version: str = Field(default="0.1.0")
