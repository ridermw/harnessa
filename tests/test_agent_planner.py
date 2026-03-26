"""Tests for the PlannerAgent."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.planner import PLANNER_SYSTEM_PROMPT, PlannerAgent
from harnessa.telemetry.models import CanonicalResponse


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


class TestPlannerInstantiation:
    """PlannerAgent can be created with required arguments."""

    def test_basic_instantiation(self, tmp_path: Path) -> None:
        agent = PlannerAgent(model_id="gpt-4o", work_dir=tmp_path)
        assert agent.agent_id == "planner"
        assert agent.model_id == "gpt-4o"

    def test_custom_agent_id(self, tmp_path: Path) -> None:
        agent = PlannerAgent(model_id="gpt-4o", work_dir=tmp_path, agent_id="planner-2")
        assert agent.agent_id == "planner-2"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    """The system prompt contains the key instructions from the design."""

    def test_contains_ambitious_scope(self, tmp_path: Path) -> None:
        agent = PlannerAgent(model_id="m", work_dir=tmp_path)
        prompt = agent.build_system_prompt()
        assert "ambitious" in prompt.lower()

    def test_contains_user_stories(self, tmp_path: Path) -> None:
        prompt = PlannerAgent(model_id="m", work_dir=tmp_path).build_system_prompt()
        assert "user stories" in prompt.lower()

    def test_contains_feature_list(self, tmp_path: Path) -> None:
        prompt = PlannerAgent(model_id="m", work_dir=tmp_path).build_system_prompt()
        assert "feature list" in prompt.lower()

    def test_contains_success_criteria(self, tmp_path: Path) -> None:
        prompt = PlannerAgent(model_id="m", work_dir=tmp_path).build_system_prompt()
        assert "success criteria" in prompt.lower()

    def test_no_implementation_details(self, tmp_path: Path) -> None:
        prompt = PlannerAgent(model_id="m", work_dir=tmp_path).build_system_prompt()
        assert "do not include" in prompt.lower() or "do not" in prompt.lower()
        assert "implementation detail" in prompt.lower()

    def test_focuses_on_product_context(self, tmp_path: Path) -> None:
        prompt = PlannerAgent(model_id="m", work_dir=tmp_path).build_system_prompt()
        assert "product context" in prompt.lower()

    def test_focuses_on_high_level_design(self, tmp_path: Path) -> None:
        prompt = PlannerAgent(model_id="m", work_dir=tmp_path).build_system_prompt()
        assert "high-level technical design" in prompt.lower()


# ---------------------------------------------------------------------------
# run() — output structure
# ---------------------------------------------------------------------------


class TestRunOutputStructure:
    """run() creates the expected directory layout and files."""

    def _make_agent(self, tmp_path: Path) -> PlannerAgent:
        agent = PlannerAgent(model_id="test-model", work_dir=tmp_path)
        return agent

    def _stub_response(self) -> CanonicalResponse:
        return CanonicalResponse(
            text="# Product Spec\n\nThis is a test spec.",
            stop_reason="end_turn",
            model="test-model",
            tokens_in=10,
            tokens_out=50,
            cost=0.001,
            truncated=False,
        )

    def test_creates_planner_directory(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path)
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=self._stub_response()):
            agent.run("Build a todo app", output_dir)
        assert (output_dir / "planner").is_dir()

    def test_creates_spec_md(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path)
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=self._stub_response()):
            result = agent.run("Build a todo app", output_dir)
        assert result == output_dir / "planner" / "spec.md"
        assert result.read_text() == "# Product Spec\n\nThis is a test spec."

    def test_writes_status_done(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path)
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=self._stub_response()):
            agent.run("Build a todo app", output_dir)
        status_file = tmp_path / "planner.status"
        assert status_file.exists()
        assert status_file.read_text() == "done"

    def test_records_metrics(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path)
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=self._stub_response()):
            agent.run("Build a todo app", output_dir)
        metrics = agent.get_metrics()
        assert metrics.tokens_in == 10
        assert metrics.tokens_out == 50
        assert metrics.cost_usd == pytest.approx(0.001)
        assert metrics.duration_s > 0

    def test_run_returns_path(self, tmp_path: Path) -> None:
        agent = self._make_agent(tmp_path)
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=self._stub_response()):
            result = agent.run("Build a todo app", output_dir)
        assert isinstance(result, Path)
        assert result.name == "spec.md"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Errors set status to 'error' and propagate."""

    def test_litellm_not_available_uses_stub(self, tmp_path: Path) -> None:
        """When litellm is not importable, falls back to BaseAgent.call_llm stub."""
        agent = PlannerAgent(model_id="test-model", work_dir=tmp_path)
        output_dir = tmp_path / "output"

        with patch.dict("sys.modules", {"litellm": None}):
            result = agent.run("Build a chat app", output_dir)

        assert result.exists()
        # Stub text from BaseAgent.call_llm
        assert "stub" in result.read_text().lower()
        status = (tmp_path / "planner.status").read_text()
        assert status == "done"

    def test_api_error_writes_error_status(self, tmp_path: Path) -> None:
        agent = PlannerAgent(model_id="test-model", work_dir=tmp_path)
        output_dir = tmp_path / "output"

        with patch.object(agent, "_call_model", side_effect=RuntimeError("API down")):
            with pytest.raises(RuntimeError, match="API down"):
                agent.run("Build something", output_dir)

        status = (tmp_path / "planner.status").read_text()
        assert status == "error"

    def test_timeout_error_writes_error_status(self, tmp_path: Path) -> None:
        agent = PlannerAgent(model_id="test-model", work_dir=tmp_path)
        output_dir = tmp_path / "output"

        with patch.object(agent, "_call_model", side_effect=TimeoutError("timed out")):
            with pytest.raises(TimeoutError):
                agent.run("Build something", output_dir)

        status = (tmp_path / "planner.status").read_text()
        assert status == "error"

    def test_truncated_response_still_succeeds(self, tmp_path: Path) -> None:
        """A truncated response is written; status is still 'done'."""
        agent = PlannerAgent(model_id="test-model", work_dir=tmp_path)
        output_dir = tmp_path / "output"

        truncated = CanonicalResponse(
            text="# Partial spec...",
            stop_reason="length",
            model="test-model",
            tokens_in=10,
            tokens_out=4096,
            cost=0.01,
            truncated=True,
        )
        with patch.object(agent, "_call_model", return_value=truncated):
            result = agent.run("Build a todo app", output_dir)

        assert result.read_text() == "# Partial spec..."
        assert (tmp_path / "planner.status").read_text() == "done"


# ---------------------------------------------------------------------------
# execute() interface (BaseAgent contract)
# ---------------------------------------------------------------------------


class TestExecuteInterface:
    """execute() delegates to run() correctly."""

    def test_execute_calls_run(self, tmp_path: Path) -> None:
        agent = PlannerAgent(model_id="m", work_dir=tmp_path)
        with patch.object(agent, "run", return_value=tmp_path / "spec.md") as mock_run:
            agent.execute(prompt="Build X", output_dir=str(tmp_path / "out"))
            mock_run.assert_called_once_with("Build X", tmp_path / "out")
