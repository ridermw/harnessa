"""Execution backends for Harnessa agents.

CopilotExecutor delegates tasks to GitHub Copilot CLI (copilot -p).
In delegation mode, copilot edits files directly — it doesn't return
code as text. The executor checks the filesystem for results.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Directories to skip when snapshotting the filesystem
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "venv"}


class ExecutionResult(BaseModel):
    """Result of a delegated execution via copilot -p."""

    model_config = {"strict": True}

    stdout: str = Field(default="", description="copilot's text output")
    stderr: str = Field(default="", description="error output if any")
    exit_code: int = Field(default=0, description="copilot process exit code")
    duration_s: float = Field(default=0.0, ge=0.0, description="wall-clock seconds")
    files_changed: list[str] = Field(default_factory=list, description="files modified by copilot")
    model: str = Field(default="", description="model used (from --model flag)")
    success: bool = Field(default=True, description="True if exit_code == 0")


class CopilotExecutor:
    """Executes tasks by delegating to copilot -p.

    Unlike LiteLLM (which returns text), CopilotExecutor delegates the
    entire task to a Copilot CLI session that can read files, edit code,
    run shell commands, and commit changes directly.
    """

    def __init__(self, model: str = "claude-sonnet-4") -> None:
        self.model = model

    def execute(
        self,
        prompt: str,
        work_dir: Path,
        allow_tools: str = "write, shell(*), read",
        timeout: int = 600,
        allow_all_paths: bool = False,
    ) -> ExecutionResult:
        """Delegate a task to copilot -p.

        Args:
            prompt: The task description.
            work_dir: Directory where copilot should work.
            allow_tools: Comma-separated tool permissions.
            timeout: Max seconds to wait.
            allow_all_paths: When True, allow edits outside work_dir.

        Returns:
            ExecutionResult with stdout, files_changed, etc.
        """
        copilot_bin = shutil.which("copilot")
        if copilot_bin is None:
            raise RuntimeError(
                "copilot CLI not found. Install: "
                "https://docs.github.com/en/copilot/how-tos/copilot-cli"
            )

        before = self._snapshot_files(work_dir)

        cmd = [
            copilot_bin,
            "-p", prompt,
            "-s",
            "--no-ask-user",
            "--model", self.model,
            f"--allow-tool={allow_tools}",
        ]
        if allow_all_paths:
            cmd.append("--allow-all-paths")

        logger.info("[copilot-executor] Running copilot -p in %s (model=%s)", work_dir, self.model)
        start = time.monotonic()

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.monotonic() - start

            after = self._snapshot_files(work_dir)
            changed = self._detect_changes(before, after)

            return ExecutionResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                duration_s=round(elapsed, 2),
                files_changed=changed,
                model=self.model,
                success=proc.returncode == 0,
            )

        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - start
            logger.error("[copilot-executor] Timed out after %ds", timeout)
            return ExecutionResult(
                stdout=exc.stdout or "" if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace"),
                stderr=exc.stderr or "" if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(errors="replace"),
                exit_code=124,
                duration_s=round(elapsed, 2),
                files_changed=[],
                model=self.model,
                success=False,
            )

    def _snapshot_files(self, work_dir: Path) -> dict[str, float]:
        """Snapshot all file mtimes in work_dir for change detection."""
        snapshot: dict[str, float] = {}
        if not work_dir.exists():
            return snapshot
        for path in work_dir.rglob("*"):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                try:
                    rel = str(path.relative_to(work_dir))
                    snapshot[rel] = path.stat().st_mtime
                except (OSError, ValueError):
                    continue
        return snapshot

    def _detect_changes(self, before: dict[str, float], after: dict[str, float]) -> list[str]:
        """Compare snapshots to find changed/new/deleted files."""
        changed: list[str] = []

        # New or modified files
        for path, mtime in after.items():
            if path not in before or before[path] != mtime:
                changed.append(path)

        # Deleted files
        for path in before:
            if path not in after:
                changed.append(path)

        return sorted(changed)
