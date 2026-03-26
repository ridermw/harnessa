"""Run configuration for Harnessa orchestration."""

from __future__ import annotations

import uuid
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field


class RunMode(StrEnum):
    """Execution mode for a benchmark run."""

    SOLO = "solo"
    TRIO = "trio"


class RunConfig(BaseModel):
    """Configuration for a single benchmark run.

    Captures everything the orchestrator needs to launch agents,
    route evaluations, and write telemetry.
    """

    model_config = {"strict": True}

    benchmark: str = Field(description="Benchmark identifier to run")
    mode: RunMode = Field(default=RunMode.SOLO, description="Execution mode: solo or trio")
    evaluator_models: list[str] = Field(
        default_factory=lambda: ["claude-sonnet-4-20250514"],
        description="Model IDs for evaluator agents",
    )
    criteria_path: Path = Field(
        default=Path("criteria/backend.yaml"),
        description="Path to the YAML criteria file",
    )
    max_iterations: Annotated[int, Field(ge=1, le=20)] = Field(
        default=3,
        description="Maximum GAN-loop iterations",
    )
    timeout: Annotated[int, Field(ge=30, le=7200)] = Field(
        default=600,
        description="Run timeout in seconds",
    )
    run_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12],
        description="Unique run identifier",
    )
