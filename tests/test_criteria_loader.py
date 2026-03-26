"""Tests for the criteria loader."""

from pathlib import Path

import pytest

from harnessa.criteria.loader import CriteriaLoader, Criterion, Weight


CRITERIA_DIR = Path(__file__).resolve().parent.parent / "criteria"


def test_load_backend_yaml() -> None:
    """Load backend.yaml and verify all criteria are present."""
    loader = CriteriaLoader()
    criteria = loader.load(CRITERIA_DIR / "backend.yaml")
    names = [c.name for c in criteria]
    assert "Product Depth" in names
    assert "Functionality" in names
    assert "Code Quality" in names
    assert "Test Coverage" in names
    assert len(criteria) == 4


def test_load_fullstack_yaml() -> None:
    """Load fullstack.yaml and verify all criteria are present."""
    loader = CriteriaLoader()
    criteria = loader.load(CRITERIA_DIR / "fullstack.yaml")
    names = [c.name for c in criteria]
    assert "Product Depth" in names
    assert "Visual Design" in names
    assert len(criteria) == 4


def test_criteria_have_few_shot_examples() -> None:
    """Each criterion should have at least one few-shot example."""
    loader = CriteriaLoader()
    criteria = loader.load(CRITERIA_DIR / "backend.yaml")
    for c in criteria:
        assert len(c.few_shot_examples) > 0, f"{c.name} has no few-shot examples"


def test_criteria_weights_are_valid() -> None:
    """All weights must be HIGH, MEDIUM, or LOW."""
    loader = CriteriaLoader()
    criteria = loader.load(CRITERIA_DIR / "backend.yaml")
    for c in criteria:
        assert c.weight in (Weight.HIGH, Weight.MEDIUM, Weight.LOW)


def test_load_missing_file() -> None:
    """Loading a nonexistent file raises FileNotFoundError."""
    loader = CriteriaLoader()
    with pytest.raises(FileNotFoundError):
        loader.load(Path("criteria/nonexistent.yaml"))


def test_validate_empty_list() -> None:
    """Validating an empty criteria list raises ValueError."""
    loader = CriteriaLoader()
    with pytest.raises(ValueError, match="must not be empty"):
        loader.validate([])


def test_validate_duplicate_names() -> None:
    """Validating criteria with duplicate names raises ValueError."""
    loader = CriteriaLoader()
    dupes = [
        Criterion(name="Dup", weight=Weight.HIGH, threshold=5, description="A"),
        Criterion(name="Dup", weight=Weight.MEDIUM, threshold=5, description="B"),
    ]
    with pytest.raises(ValueError, match="Duplicate"):
        loader.validate(dupes)
