"""Tests for RunConfig validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from harnessa.config import RunConfig, RunMode


def test_default_config() -> None:
    """RunConfig with only required field uses sensible defaults."""
    cfg = RunConfig(benchmark="todo-app")
    assert cfg.mode == RunMode.SOLO
    assert cfg.max_iterations == 3
    assert cfg.timeout == 600
    assert len(cfg.run_id) == 12


def test_trio_mode() -> None:
    """RunConfig accepts trio mode."""
    cfg = RunConfig(benchmark="todo-app", mode=RunMode.TRIO)
    assert cfg.mode == RunMode.TRIO


def test_custom_evaluator_models() -> None:
    """RunConfig accepts a custom evaluator model list."""
    cfg = RunConfig(
        benchmark="chat-app",
        evaluator_models=["claude-sonnet-4-20250514", "gpt-4"],
    )
    assert len(cfg.evaluator_models) == 2


def test_invalid_max_iterations() -> None:
    """max_iterations outside 1-20 raises validation error."""
    with pytest.raises(ValidationError):
        RunConfig(benchmark="x", max_iterations=0)
    with pytest.raises(ValidationError):
        RunConfig(benchmark="x", max_iterations=25)


def test_invalid_timeout() -> None:
    """timeout outside 30-7200 raises validation error."""
    with pytest.raises(ValidationError):
        RunConfig(benchmark="x", timeout=10)


def test_criteria_path() -> None:
    """RunConfig accepts a custom criteria path."""
    cfg = RunConfig(benchmark="x", criteria_path=Path("criteria/fullstack.yaml"))
    assert cfg.criteria_path == Path("criteria/fullstack.yaml")
