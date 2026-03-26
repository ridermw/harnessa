"""Criteria loader — parse and validate YAML evaluation criteria files."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Weight(StrEnum):
    """Criterion weight levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FewShotExample(BaseModel):
    """A few-shot example for calibrating evaluator scoring."""

    model_config = {"strict": True}

    input: str = Field(description="Example input or scenario")
    score: int = Field(ge=1, le=10, description="Expected score")
    justification: str = Field(description="Why this score is appropriate")


class Criterion(BaseModel):
    """A single evaluation criterion with weight, threshold, and examples."""

    model_config = {"strict": True}

    name: str = Field(description="Criterion name")
    weight: Weight = Field(description="Importance level: HIGH, MEDIUM, or LOW")
    threshold: int = Field(ge=1, le=10, description="Minimum passing score")
    description: str = Field(description="What this criterion measures")
    few_shot_examples: list[FewShotExample] = Field(
        default_factory=list,
        description="Calibration examples for evaluators",
    )


class CriteriaLoader:
    """Load and validate YAML criteria files into typed Pydantic models.

    Usage:
        loader = CriteriaLoader()
        criteria = loader.load(Path("criteria/backend.yaml"))
        loader.validate(criteria)
    """

    def load(self, path: Path) -> list[Criterion]:
        """Load criteria from a YAML file.

        Args:
            path: Path to the YAML criteria file.

        Returns:
            A list of validated Criterion models.

        Raises:
            FileNotFoundError: If the criteria file doesn't exist.
            ValueError: If the YAML structure is invalid.
        """
        if not path.exists():
            raise FileNotFoundError(f"Criteria file not found: {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "criteria" not in raw:
            raise ValueError(f"Invalid criteria file: expected top-level 'criteria' key in {path}")

        # strict=False allows YAML string→enum coercion while models stay strict by default
        criteria = [Criterion.model_validate(item, strict=False) for item in raw["criteria"]]
        self.validate(criteria)
        return criteria

    def validate(self, criteria: list[Criterion]) -> None:
        """Validate a list of criteria for completeness.

        Raises:
            ValueError: If criteria list is empty or has duplicate names.
        """
        if not criteria:
            raise ValueError("Criteria list must not be empty")

        names = [c.name for c in criteria]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate criterion names: {names}")
