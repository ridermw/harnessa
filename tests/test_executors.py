"""Tests for CopilotExecutor, execution dispatch, and fenced-block parser."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.executors import CopilotExecutor, ExecutionResult


# ======================================================================
# ExecutionResult model
# ======================================================================

class TestExecutionResult:
    """Test ExecutionResult Pydantic model."""

    def test_defaults(self) -> None:
        result = ExecutionResult()
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.duration_s == 0.0
        assert result.files_changed == []
        assert result.model == ""
        assert result.success is True

    def test_with_valid_data(self) -> None:
        result = ExecutionResult(
            stdout="done",
            stderr="",
            exit_code=0,
            duration_s=5.2,
            files_changed=["main.py", "utils.py"],
            model="claude-sonnet-4",
            success=True,
        )
        assert result.files_changed == ["main.py", "utils.py"]
        assert result.model == "claude-sonnet-4"

    def test_failure_result(self) -> None:
        result = ExecutionResult(exit_code=1, success=False)
        assert result.success is False
        assert result.exit_code == 1


# ======================================================================
# CopilotExecutor
# ======================================================================

class TestCopilotExecutor:
    """Test CopilotExecutor."""

    def test_copilot_not_found(self, tmp_path: Path) -> None:
        """shutil.which returning None raises RuntimeError."""
        executor = CopilotExecutor(model="claude-sonnet-4")
        with patch("harnessa.agents.executors.shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="copilot CLI not found"):
                executor.execute("do something", tmp_path)

    def test_execute_success(self, tmp_path: Path) -> None:
        """Mock subprocess.run → ExecutionResult with files_changed."""
        executor = CopilotExecutor(model="claude-sonnet-4")

        # Create a file before execution to simulate "existing"
        (tmp_path / "existing.py").write_text("old", encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "All done"
        mock_proc.stderr = ""
        mock_proc.returncode = 0

        def fake_run(cmd, **kwargs):
            # Simulate copilot creating a new file
            (tmp_path / "new_file.py").write_text("print('hello')", encoding="utf-8")
            return mock_proc

        with patch("harnessa.agents.executors.shutil.which", return_value="/usr/bin/copilot"):
            with patch("harnessa.agents.executors.subprocess.run", side_effect=fake_run):
                result = executor.execute("implement feature", tmp_path)

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "All done"
        assert "new_file.py" in result.files_changed
        assert result.model == "claude-sonnet-4"
        assert result.duration_s >= 0.0

    def test_execute_timeout(self, tmp_path: Path) -> None:
        """subprocess.run raising TimeoutExpired → success=False."""
        executor = CopilotExecutor(model="claude-sonnet-4")

        with patch("harnessa.agents.executors.shutil.which", return_value="/usr/bin/copilot"):
            with patch(
                "harnessa.agents.executors.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="copilot", timeout=10, output=b"partial", stderr=b""),
            ):
                result = executor.execute("slow task", tmp_path, timeout=10)

        assert result.success is False
        assert result.exit_code == 124
        assert result.stdout == "partial"

    def test_execute_nonzero_exit(self, tmp_path: Path) -> None:
        """subprocess.run with returncode=1 → success=False."""
        executor = CopilotExecutor(model="claude-sonnet-4")

        mock_proc = MagicMock()
        mock_proc.stdout = "error output"
        mock_proc.stderr = "some error"
        mock_proc.returncode = 1

        with patch("harnessa.agents.executors.shutil.which", return_value="/usr/bin/copilot"):
            with patch("harnessa.agents.executors.subprocess.run", return_value=mock_proc):
                result = executor.execute("bad task", tmp_path)

        assert result.success is False
        assert result.exit_code == 1
        assert result.stderr == "some error"

    def test_file_change_detection(self, tmp_path: Path) -> None:
        """Create files, modify one, detect change via snapshots."""
        executor = CopilotExecutor()

        (tmp_path / "unchanged.txt").write_text("same", encoding="utf-8")
        (tmp_path / "will_change.txt").write_text("before", encoding="utf-8")

        before = executor._snapshot_files(tmp_path)

        (tmp_path / "will_change.txt").write_text("after", encoding="utf-8")
        (tmp_path / "brand_new.txt").write_text("new", encoding="utf-8")

        after = executor._snapshot_files(tmp_path)
        changed = executor._detect_changes(before, after)

        assert "brand_new.txt" in changed
        assert "will_change.txt" in changed
        assert "unchanged.txt" not in changed

    def test_file_deletion_detected(self, tmp_path: Path) -> None:
        """Deleted files appear in changes."""
        executor = CopilotExecutor()

        (tmp_path / "to_delete.txt").write_text("bye", encoding="utf-8")
        before = executor._snapshot_files(tmp_path)

        (tmp_path / "to_delete.txt").unlink()
        after = executor._snapshot_files(tmp_path)
        changed = executor._detect_changes(before, after)

        assert "to_delete.txt" in changed

    def test_prompt_shell_safety(self, tmp_path: Path) -> None:
        """Prompt with special chars is passed as a single argument, not interpolated."""
        executor = CopilotExecutor(model="claude-sonnet-4")

        captured_cmd: list[str] = []

        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_proc.returncode = 0

        def capture_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return mock_proc

        with patch("harnessa.agents.executors.shutil.which", return_value="/usr/bin/copilot"):
            with patch("harnessa.agents.executors.subprocess.run", side_effect=capture_run):
                executor.execute('fix the $HOME "bug" && rm -rf /', tmp_path)

        # Prompt should appear as a single element after -p
        p_index = captured_cmd.index("-p")
        prompt_arg = captured_cmd[p_index + 1]
        assert prompt_arg == 'fix the $HOME "bug" && rm -rf /'

    def test_model_passed_correctly(self, tmp_path: Path) -> None:
        """Verify --model flag in subprocess command."""
        executor = CopilotExecutor(model="gpt-5.4")

        captured_cmd: list[str] = []
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_proc.returncode = 0

        def capture_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return mock_proc

        with patch("harnessa.agents.executors.shutil.which", return_value="/usr/bin/copilot"):
            with patch("harnessa.agents.executors.subprocess.run", side_effect=capture_run):
                executor.execute("task", tmp_path)

        model_index = captured_cmd.index("--model")
        assert captured_cmd[model_index + 1] == "gpt-5.4"

    def test_skip_dirs_in_snapshot(self, tmp_path: Path) -> None:
        """Directories like .git, node_modules, __pycache__ are skipped."""
        executor = CopilotExecutor()

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git data", encoding="utf-8")

        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "dep.js").write_text("module", encoding="utf-8")

        (tmp_path / "real.py").write_text("code", encoding="utf-8")

        snapshot = executor._snapshot_files(tmp_path)
        assert "real.py" in snapshot
        assert ".git/config" not in snapshot
        assert "node_modules/dep.js" not in snapshot


# ======================================================================
# BaseAgent dispatch
# ======================================================================

class TestBaseAgentDispatch:
    """Test run_executor() dispatch in BaseAgent."""

    def test_copilot_prefix_dispatches_to_executor(self, tmp_path: Path) -> None:
        """model_id='copilot/claude-sonnet-4' uses CopilotExecutor."""
        from harnessa.agents.generator import GeneratorAgent

        agent = GeneratorAgent(model_id="copilot/claude-sonnet-4", work_dir=tmp_path)

        mock_result = ExecutionResult(
            stdout="done", exit_code=0, model="claude-sonnet-4", success=True
        )

        with patch("harnessa.agents.base.CopilotExecutor") as MockExecutor:
            instance = MockExecutor.return_value
            instance.execute.return_value = mock_result
            result = agent.run_executor("do task")

        MockExecutor.assert_called_once_with(model="claude-sonnet-4")
        instance.execute.assert_called_once()
        assert result.success is True

    def test_no_prefix_uses_call_llm(self, tmp_path: Path) -> None:
        """model_id='claude-sonnet-4' falls back to call_llm()."""
        from harnessa.agents.generator import GeneratorAgent

        agent = GeneratorAgent(model_id="claude-sonnet-4", work_dir=tmp_path)
        result = agent.run_executor("do task")

        # call_llm returns the stub text
        assert result.success is True
        assert "[stub]" in result.stdout

    def test_model_prefix_stripped(self, tmp_path: Path) -> None:
        """'copilot/gpt-5.4' → CopilotExecutor(model='gpt-5.4')."""
        from harnessa.agents.planner import PlannerAgent

        agent = PlannerAgent(model_id="copilot/gpt-5.4", work_dir=tmp_path)

        mock_result = ExecutionResult(
            stdout="spec", exit_code=0, model="gpt-5.4", success=True
        )

        with patch("harnessa.agents.base.CopilotExecutor") as MockExecutor:
            instance = MockExecutor.return_value
            instance.execute.return_value = mock_result
            agent.run_executor("plan task")

        MockExecutor.assert_called_once_with(model="gpt-5.4")


# ======================================================================
# Generator fenced-block parser
# ======================================================================

class TestGeneratorFencedParser:
    """Test fenced code block parser."""

    def test_single_block(self) -> None:
        from harnessa.agents.generator import GeneratorAgent

        text = "Here is the code:\n```main.py\nprint('hello')\n```\nDone."
        result = GeneratorAgent._parse_fenced_blocks(text)
        assert result == {"main.py": "print('hello')\n"}

    def test_multiple_blocks(self) -> None:
        from harnessa.agents.generator import GeneratorAgent

        text = (
            "```src/app.py\nfrom flask import Flask\napp = Flask(__name__)\n```\n"
            "And the tests:\n"
            "```tests/test_app.py\ndef test_app():\n    pass\n```\n"
        )
        result = GeneratorAgent._parse_fenced_blocks(text)
        assert "src/app.py" in result
        assert "tests/test_app.py" in result
        assert "Flask" in result["src/app.py"]

    def test_no_blocks(self) -> None:
        from harnessa.agents.generator import GeneratorAgent

        text = "Just some plain text with no code blocks."
        result = GeneratorAgent._parse_fenced_blocks(text)
        assert result == {}

    def test_language_only_markers_skipped(self) -> None:
        """```python should not be treated as a file path."""
        from harnessa.agents.generator import GeneratorAgent

        text = "```python\nprint('hello')\n```"
        result = GeneratorAgent._parse_fenced_blocks(text)
        assert result == {}

    def test_path_with_dirs(self) -> None:
        from harnessa.agents.generator import GeneratorAgent

        text = "```src/utils/helper.py\ndef help(): pass\n```"
        result = GeneratorAgent._parse_fenced_blocks(text)
        assert "src/utils/helper.py" in result
        assert "def help(): pass\n" == result["src/utils/helper.py"]

    def test_nested_backticks_in_content(self) -> None:
        """Content containing backticks (not triple) should be preserved."""
        from harnessa.agents.generator import GeneratorAgent

        text = "```readme.md\nUse `pip install` to install.\n```"
        result = GeneratorAgent._parse_fenced_blocks(text)
        assert "readme.md" in result
        assert "`pip install`" in result["readme.md"]


# ======================================================================
# Planner delegation mode
# ======================================================================

class TestPlannerDelegation:
    """Test PlannerAgent delegation mode."""

    def test_planner_copilot_mode_creates_spec(self, tmp_path: Path) -> None:
        """Planner in copilot mode writes spec from executor stdout."""
        from harnessa.agents.planner import PlannerAgent

        agent = PlannerAgent(model_id="copilot/claude-sonnet-4", work_dir=tmp_path)

        mock_result = ExecutionResult(
            stdout="# Spec\nThis is the expanded spec.",
            exit_code=0,
            model="claude-sonnet-4",
            success=True,
        )

        with patch.object(agent, "run_executor", return_value=mock_result):
            spec_path = agent.run("Fix the bug in parser", tmp_path)

        assert spec_path.exists()
        assert "Spec" in spec_path.read_text()

    def test_planner_text_mode_unchanged(self, tmp_path: Path) -> None:
        """Planner without copilot/ prefix uses existing _call_model path."""
        from harnessa.agents.planner import PlannerAgent
        from harnessa.telemetry.models import CanonicalResponse

        agent = PlannerAgent(model_id="claude-sonnet-4", work_dir=tmp_path)

        mock_response = CanonicalResponse(
            text="# Expanded Spec\nFix the parser bug.",
            stop_reason="end_turn",
            model="claude-sonnet-4",
            tokens_in=10,
            tokens_out=50,
            cost=0.001,
            truncated=False,
        )
        with patch.object(agent, "_call_model", return_value=mock_response):
            spec_path = agent.run("Fix the bug", tmp_path)

        assert spec_path.exists()
        assert "Expanded Spec" in spec_path.read_text()


# ======================================================================
# Generator delegation mode
# ======================================================================

class TestGeneratorDelegation:
    """Test GeneratorAgent delegation mode."""

    def test_generator_copilot_mode(self, tmp_path: Path) -> None:
        """Generator in copilot mode uses run_executor."""
        from harnessa.agents.generator import GeneratorAgent

        working_dir = tmp_path / "workspace"
        working_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        spec_path = tmp_path / "spec.md"
        spec_path.write_text("# Spec\nImplement X", encoding="utf-8")

        agent = GeneratorAgent(model_id="copilot/claude-sonnet-4", work_dir=tmp_path)

        mock_result = ExecutionResult(
            stdout="Implemented X",
            exit_code=0,
            model="claude-sonnet-4",
            success=True,
            files_changed=["main.py"],
        )

        with patch.object(agent, "run_executor", return_value=mock_result):
            with patch.object(agent, "_git_commit"):
                result_path = agent.run(spec_path, working_dir, output_dir)

        assert result_path == working_dir
