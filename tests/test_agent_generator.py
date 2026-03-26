"""Tests for the GeneratorAgent."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.generator import (
    FEEDBACK_PREAMBLE,
    GENERATOR_SYSTEM_PROMPT,
    GeneratorAgent,
)
from harnessa.telemetry.models import CanonicalResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def work_dir(tmp_path: Path) -> Path:
    d = tmp_path / "work"
    d.mkdir()
    return d


@pytest.fixture()
def agent(work_dir: Path) -> GeneratorAgent:
    return GeneratorAgent(model_id="test-model", work_dir=work_dir)


@pytest.fixture()
def spec_file(tmp_path: Path) -> Path:
    path = tmp_path / "spec.md"
    path.write_text("# Spec\n\nBuild a todo app with CRUD.", encoding="utf-8")
    return path


@pytest.fixture()
def feedback_file(tmp_path: Path) -> Path:
    path = tmp_path / "feedback.md"
    path.write_text(
        "## Feedback\n- Missing error handling in create endpoint\n- No input validation",
        encoding="utf-8",
    )
    return path


def _stub_response(text: str = "# Generated Code\nprint('hello')") -> CanonicalResponse:
    return CanonicalResponse(
        text=text,
        stop_reason="end_turn",
        model="test-model",
        tokens_in=20,
        tokens_out=100,
        cost=0.005,
        truncated=False,
    )


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


class TestGeneratorInstantiation:
    """GeneratorAgent can be created with required arguments."""

    def test_basic_instantiation(self, work_dir: Path) -> None:
        agent = GeneratorAgent(model_id="gpt-4o", work_dir=work_dir)
        assert agent.agent_id == "generator"
        assert agent.model_id == "gpt-4o"

    def test_custom_agent_id(self, work_dir: Path) -> None:
        agent = GeneratorAgent(model_id="gpt-4o", work_dir=work_dir, agent_id="gen-2")
        assert agent.agent_id == "gen-2"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    """The system prompt contains the key instructions from the design."""

    def test_contains_implement_spec(self, agent: GeneratorAgent) -> None:
        prompt = agent.build_system_prompt()
        assert "implement" in prompt.lower()
        assert "spec" in prompt.lower()

    def test_contains_git_commit(self, agent: GeneratorAgent) -> None:
        prompt = agent.build_system_prompt()
        assert "git" in prompt.lower()
        assert "commit" in prompt.lower()

    def test_no_eval_access(self, agent: GeneratorAgent) -> None:
        prompt = agent.build_system_prompt()
        assert "_eval" in prompt
        assert "do not access" in prompt.lower() or "do not" in prompt.lower()

    def test_contains_methodical_instruction(self, agent: GeneratorAgent) -> None:
        prompt = agent.build_system_prompt()
        assert "methodically" in prompt.lower() or "one feature at a time" in prompt.lower()

    def test_contains_self_evaluate(self, agent: GeneratorAgent) -> None:
        prompt = agent.build_system_prompt()
        assert "self-evaluate" in prompt.lower() or "self evaluate" in prompt.lower()


# ---------------------------------------------------------------------------
# Feedback incorporation
# ---------------------------------------------------------------------------


class TestFeedbackIncorporation:
    """Evaluator feedback is incorporated into the prompt when provided."""

    def test_feedback_included_in_prompt(
        self, agent: GeneratorAgent, spec_file: Path, feedback_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=_stub_response()) as mock_call, \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, tmp_path / "gen_work", output_dir, feedback=feedback_file)

        prompt_arg = mock_call.call_args[0][0]
        assert "Evaluator Feedback" in prompt_arg
        assert "Missing error handling" in prompt_arg
        assert "No input validation" in prompt_arg

    def test_no_feedback_when_none(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=_stub_response()) as mock_call, \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, tmp_path / "gen_work", output_dir, feedback=None)

        prompt_arg = mock_call.call_args[0][0]
        assert "Evaluator Feedback" not in prompt_arg

    def test_missing_feedback_file_ignored(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        nonexistent = tmp_path / "nope.md"
        with patch.object(agent, "_call_model", return_value=_stub_response()) as mock_call, \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, tmp_path / "gen_work", output_dir, feedback=nonexistent)

        prompt_arg = mock_call.call_args[0][0]
        assert "Evaluator Feedback" not in prompt_arg


# ---------------------------------------------------------------------------
# Output directory structure
# ---------------------------------------------------------------------------


class TestOutputStructure:
    """run() creates the expected directory layout and files."""

    def test_creates_generator_directory(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=_stub_response()), \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, tmp_path / "gen_work", output_dir)
        assert (output_dir / "generator").is_dir()

    def test_creates_working_directory(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        working = tmp_path / "gen_work"
        with patch.object(agent, "_call_model", return_value=_stub_response()), \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, working, output_dir)
        assert working.is_dir()

    def test_writes_generated_output(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        working = tmp_path / "gen_work"
        with patch.object(agent, "_call_model", return_value=_stub_response("hello code")), \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, working, output_dir)
        output_file = working / "generated_output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "hello code"

    def test_returns_working_dir(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        working = tmp_path / "gen_work"
        with patch.object(agent, "_call_model", return_value=_stub_response()), \
             patch.object(agent, "_git_commit"):
            result = agent.run(spec_file, working, output_dir)
        assert result == working

    def test_writes_status_done(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=_stub_response()), \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, tmp_path / "gen_work", output_dir)
        status_file = agent.work_dir / "generator.status"
        assert status_file.exists()
        assert status_file.read_text() == "done"

    def test_records_metrics(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", return_value=_stub_response()), \
             patch.object(agent, "_git_commit"):
            agent.run(spec_file, tmp_path / "gen_work", output_dir)
        metrics = agent.get_metrics()
        assert metrics.tokens_in == 20
        assert metrics.tokens_out == 100
        assert metrics.cost_usd == pytest.approx(0.005)
        assert metrics.duration_s > 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Errors set status to 'error' and propagate."""

    def test_api_error_writes_error_status(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch.object(agent, "_call_model", side_effect=RuntimeError("API down")):
            with pytest.raises(RuntimeError, match="API down"):
                agent.run(spec_file, tmp_path / "gen_work", output_dir)
        status = (agent.work_dir / "generator.status").read_text()
        assert status == "error"

    def test_missing_spec_raises(
        self, agent: GeneratorAgent, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        missing = tmp_path / "no_spec.md"
        with pytest.raises(FileNotFoundError):
            agent.run(missing, tmp_path / "gen_work", output_dir)


# ---------------------------------------------------------------------------
# execute() interface (BaseAgent contract)
# ---------------------------------------------------------------------------


class TestExecuteInterface:
    """execute() delegates to run() correctly."""

    def test_execute_calls_run(
        self, agent: GeneratorAgent, spec_file: Path, tmp_path: Path
    ) -> None:
        with patch.object(agent, "run", return_value=tmp_path / "gen_work") as mock_run:
            agent.execute(
                spec_path=str(spec_file),
                working_dir=str(tmp_path / "gen_work"),
                output_dir=str(tmp_path / "out"),
            )
            mock_run.assert_called_once()
