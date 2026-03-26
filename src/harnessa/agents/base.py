"""Base agent — abstract class defining the shared agent lifecycle."""

from __future__ import annotations

import abc
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from harnessa.telemetry.models import AgentMetrics, CanonicalResponse

logger = logging.getLogger(__name__)


class BaseAgent(abc.ABC):
    """Abstract base class for all Harnessa agents.

    Provides shared lifecycle methods: launching subprocesses, calling
    LiteLLM (stubbed), writing status files, and handling errors.
    Subclasses implement the agent-specific logic in `execute()`.
    """

    def __init__(self, agent_id: str, model_id: str, work_dir: Path) -> None:
        self.agent_id = agent_id
        self.model_id = model_id
        self.work_dir = work_dir
        self._process: subprocess.Popen[bytes] | None = None
        self._metrics = AgentMetrics(model_id=model_id)

    @abc.abstractmethod
    def execute(self, **kwargs: Any) -> None:
        """Execute the agent's primary task. Implemented by subclasses."""
        ...

    def launch_subprocess(self, cmd: list[str], env: dict[str, str] | None = None) -> subprocess.Popen[bytes]:
        """Launch a subprocess for this agent.

        Args:
            cmd: Command and arguments to run.
            env: Additional environment variables.

        Returns:
            The subprocess handle.
        """
        merged_env = {**os.environ, **(env or {})}
        logger.info("[%s] Launching subprocess: %s", self.agent_id, " ".join(cmd))
        self._process = subprocess.Popen(
            cmd,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.work_dir),
        )
        return self._process

    def call_llm(self, prompt: str) -> CanonicalResponse:
        """Call LiteLLM and return a normalized response.

        Stubbed for Phase 1 — returns a placeholder response.
        """
        logger.info("[%s] [stub] Would call LLM (%s) with prompt length=%d",
                     self.agent_id, self.model_id, len(prompt))
        return CanonicalResponse(
            text="[stub] LLM response placeholder",
            stop_reason="end_turn",
            model=self.model_id,
            tokens_in=0,
            tokens_out=0,
            cost=0.0,
            truncated=False,
        )

    def write_status(self, status: str) -> None:
        """Write agent status to a .status file for orchestrator polling."""
        status_file = self.work_dir / f"{self.agent_id}.status"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = status_file.with_suffix(".status.tmp")
        tmp.write_text(status, encoding="utf-8")
        tmp.rename(status_file)

    def get_metrics(self) -> AgentMetrics:
        """Return accumulated metrics for this agent."""
        return self._metrics

    def cleanup(self) -> None:
        """Clean up subprocess resources."""
        if self._process is not None:
            self._process.terminate()
            self._process.wait(timeout=5)
            logger.info("[%s] Subprocess terminated", self.agent_id)
