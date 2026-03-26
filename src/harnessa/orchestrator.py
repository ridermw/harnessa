"""Orchestrator — manages the full pipeline lifecycle for a benchmark run."""

from __future__ import annotations

import logging
import os
import resource
import signal
import subprocess
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Any

from harnessa.config import RunConfig, RunMode

logger = logging.getLogger(__name__)

# Port allocation: bench N gets ports 8001+((N-1)*10) through 8001+((N-1)*10)+9
_PORT_BLOCK_SIZE = 10
_PORT_BASE = 8001


class RunStatus(StrEnum):
    """Status values written to the .status file."""

    RUNNING = "running"
    ERROR = "error"
    DONE = "done"


class Orchestrator:
    """Manages the pipeline lifecycle for a single benchmark run.

    Responsibilities:
    - Launch agent subprocesses with resource limits
    - Manage the solo/trio execution modes
    - Write .status files for polling
    - Perform atomic file writes
    - Allocate ports per benchmark
    - Handle graceful shutdown on Ctrl+C
    """

    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self._child_pids: list[int] = []
        self._original_sigint: signal.Handlers | None = None
        self._run_dir = Path(f"runs/{config.run_id}")

    def start_run(self) -> None:
        """Start the benchmark run according to the configured mode."""
        logger.info("Starting run %s (benchmark=%s, mode=%s)",
                     self.config.run_id, self.config.benchmark, self.config.mode)

        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._install_signal_handler()
        self._write_status(RunStatus.RUNNING)

        try:
            match self.config.mode:
                case RunMode.SOLO:
                    self._run_solo_mode()
                case RunMode.TRIO:
                    self._run_trio_mode()

            self._write_status(RunStatus.DONE)
            logger.info("Run %s completed", self.config.run_id)
        except Exception:
            self._write_status(RunStatus.ERROR)
            logger.exception("Run %s failed", self.config.run_id)
            raise
        finally:
            self._restore_signal_handler()

    def _run_solo_mode(self) -> None:
        """Execute a single-agent run (one builder, one evaluator)."""
        logger.info("[stub] Would launch solo mode: 1 builder + 1 evaluator")
        # Phase 2: launch builder subprocess, then evaluator

    def _run_trio_mode(self) -> None:
        """Execute a trio run (builder + attacker + evaluator GAN loop)."""
        logger.info("[stub] Would launch trio mode: builder + attacker + evaluator")
        # Phase 2: launch all three agents in the GAN loop

    def _launch_agent(
        self,
        agent_type: str,
        *,
        port: int,
        env: dict[str, str] | None = None,
    ) -> subprocess.Popen[bytes]:
        """Launch an agent subprocess with resource limits.

        Args:
            agent_type: The type of agent to launch (builder/attacker/evaluator).
            port: The port to assign to this agent.
            env: Additional environment variables for the subprocess.
        """
        logger.info("[stub] Would launch %s agent on port %d", agent_type, port)

        merged_env = {**os.environ, **(env or {}), "HARNESSA_PORT": str(port)}

        def _set_limits() -> None:
            """Set resource limits for the child process (memory cap)."""
            # 2 GB memory limit
            mem_limit = 2 * 1024 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))

        proc = subprocess.Popen(
            ["echo", f"[stub] {agent_type} agent placeholder"],
            env=merged_env,
            preexec_fn=_set_limits,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._child_pids.append(proc.pid)
        return proc

    def allocate_port(self, bench_index: int, offset: int = 0) -> int:
        """Allocate a port for a benchmark agent.

        Ports are assigned in blocks of 10:
        bench 1 → 8001-8010, bench 2 → 8011-8020, etc.
        """
        return _PORT_BASE + ((bench_index - 1) * _PORT_BLOCK_SIZE) + offset

    def _write_status(self, status: RunStatus) -> None:
        """Write run status atomically (write-to-temp + rename + .done marker)."""
        status_file = self._run_dir / ".status"
        self._atomic_write(status_file, status.value)
        if status in (RunStatus.DONE, RunStatus.ERROR):
            done_marker = self._run_dir / ".done"
            done_marker.touch()

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Write content atomically: write to temp file, then rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.rename(path)

    def _install_signal_handler(self) -> None:
        """Install Ctrl+C handler for graceful shutdown."""
        self._original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _restore_signal_handler(self) -> None:
        """Restore the original SIGINT handler."""
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """Gracefully shut down child processes on Ctrl+C."""
        logger.warning("Ctrl+C received — shutting down child processes")
        for pid in self._child_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info("Sent SIGTERM to PID %d", pid)
            except ProcessLookupError:
                pass
        self._write_status(RunStatus.ERROR)
        raise KeyboardInterrupt
