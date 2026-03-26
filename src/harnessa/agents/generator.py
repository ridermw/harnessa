"""Generator agent — implements a spec by writing code to a working directory."""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from harnessa.agents.base import BaseAgent
from harnessa.response_adapter import ResponseAdapter
from harnessa.telemetry.models import AgentMetrics, CanonicalResponse

logger = logging.getLogger(__name__)

GENERATOR_SYSTEM_PROMPT = """\
You are an expert software engineer. Your job is to implement a product \
specification faithfully and completely.

## Core principles
- Implement the spec faithfully — every feature described must be present.
- Work methodically, one feature at a time. Do not skip steps.
- Use git to commit your work in logical chunks (one commit per feature or \
logical unit of work).
- Self-evaluate before handing off: re-read the spec and verify each \
requirement is met.
- Write clean, production-quality code with proper error handling.

## Constraints
- Do NOT access or look for any _eval/ directory, test fixtures, or \
evaluation criteria. You must implement based solely on the spec.
- Do NOT attempt to find, read, or reverse-engineer evaluation tests.
- Focus only on the product specification provided.

## Output
Write all code files to the working directory. Commit each logical chunk \
with a clear commit message describing what was implemented.
"""

FEEDBACK_PREAMBLE = """\

## Evaluator Feedback (from previous iteration)
The evaluator reviewed your previous implementation and provided the \
following feedback. Address each point:

{feedback}
"""


class GeneratorAgent(BaseAgent):
    """Implements a product spec by writing code to a working directory.

    The generator is the second stage of the Planner → Generator → Evaluator
    pipeline. It reads a spec produced by the planner and writes working code.
    """

    def __init__(
        self,
        model_id: str,
        work_dir: Path,
        *,
        agent_id: str = "generator",
    ) -> None:
        super().__init__(agent_id=agent_id, model_id=model_id, work_dir=work_dir)
        self._adapter = ResponseAdapter()

    def execute(self, **kwargs: Any) -> None:
        """Execute the generator via keyword arguments (BaseAgent interface)."""
        spec_path = Path(kwargs["spec_path"])
        working_dir = Path(kwargs.get("working_dir", self.work_dir))
        output_dir = Path(kwargs.get("output_dir", self.work_dir))
        feedback = Path(kwargs["feedback"]) if kwargs.get("feedback") else None
        self.run(spec_path, working_dir, output_dir, feedback=feedback)

    def run(
        self,
        spec_path: Path,
        working_dir: Path,
        output_dir: Path,
        feedback: Path | None = None,
    ) -> Path:
        """Implement the spec and write code to *working_dir*.

        Args:
            spec_path: Path to the product specification (spec.md).
            working_dir: Directory where generated code is written.
            output_dir: Root output directory for artifacts.
            feedback: Optional path to evaluator feedback from a prior
                iteration; incorporated into the prompt when provided.

        Returns:
            Path to the working directory containing generated code.
        """
        generator_dir = output_dir / "generator"
        generator_dir.mkdir(parents=True, exist_ok=True)
        working_dir.mkdir(parents=True, exist_ok=True)

        self.write_status("running")
        start = time.monotonic()

        try:
            spec_content = spec_path.read_text(encoding="utf-8")
            feedback_content = self._read_feedback(feedback)

            user_prompt = self._build_user_prompt(spec_content, feedback_content)
            response = self._call_model(user_prompt)

            self._write_code(working_dir, response.text)
            self._git_commit(working_dir)

            elapsed = time.monotonic() - start
            self._record_metrics(response, elapsed)
            self.write_status("done")
            logger.info("[%s] Code written to %s", self.agent_id, working_dir)
            return working_dir

        except Exception as exc:
            elapsed = time.monotonic() - start
            self._metrics.duration_s = elapsed
            self.write_status("error")
            logger.error("[%s] Failed: %s", self.agent_id, exc)
            raise

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def build_system_prompt(self) -> str:
        """Return the system prompt that instructs the LLM."""
        return GENERATOR_SYSTEM_PROMPT

    def _read_feedback(self, feedback_path: Path | None) -> str | None:
        """Read evaluator feedback if the path is provided and exists."""
        if feedback_path is None:
            return None
        if not feedback_path.exists():
            logger.warning("[%s] Feedback file not found: %s", self.agent_id, feedback_path)
            return None
        return feedback_path.read_text(encoding="utf-8")

    def _build_user_prompt(self, spec: str, feedback: str | None) -> str:
        """Combine the spec and optional feedback into the user prompt."""
        prompt = f"## Product Specification\n\n{spec}"
        if feedback:
            prompt += FEEDBACK_PREAMBLE.format(feedback=feedback)
        return prompt

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    def _call_model(self, user_prompt: str) -> CanonicalResponse:
        """Call LiteLLM via the ResponseAdapter, with error handling.

        Falls back to the BaseAgent stub when LiteLLM is unavailable.
        """
        try:
            import litellm  # noqa: F811
        except ImportError:
            logger.warning("[%s] litellm not installed — using stub", self.agent_id)
            return self.call_llm(user_prompt)

        system_prompt = self.build_system_prompt()

        try:
            raw = litellm.completion(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=8192,
                timeout=180,
            )
            raw_dict = raw.model_dump() if hasattr(raw, "model_dump") else dict(raw)
            response = self._adapter.normalize(raw_dict)

            if response.truncated:
                logger.warning("[%s] Response was truncated", self.agent_id)

            return response

        except Exception as exc:
            exc_name = type(exc).__name__
            if "RateLimitError" in exc_name:
                logger.error("[%s] Rate limited by provider", self.agent_id)
            elif "Timeout" in exc_name or "TimeoutError" in exc_name:
                logger.error("[%s] API call timed out", self.agent_id)
            else:
                logger.error("[%s] LLM call failed: %s: %s", self.agent_id, exc_name, exc)
            raise

    # ------------------------------------------------------------------
    # Code output
    # ------------------------------------------------------------------

    def _write_code(self, working_dir: Path, content: str) -> None:
        """Write the LLM response to the working directory.

        The content is written to a single output file. In a full
        implementation this would parse the response and write multiple
        files; for now, we write the raw response.
        """
        output_file = working_dir / "generated_output.txt"
        tmp = output_file.with_suffix(".txt.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(output_file)

    def _git_commit(self, working_dir: Path) -> None:
        """Stage and commit all changes in *working_dir*."""
        try:
            # Initialize repo if needed
            git_dir = working_dir / ".git"
            if not git_dir.exists():
                subprocess.run(
                    ["git", "init"],
                    cwd=str(working_dir),
                    capture_output=True,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.email", "generator@harnessa.dev"],
                    cwd=str(working_dir),
                    capture_output=True,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Harnessa Generator"],
                    cwd=str(working_dir),
                    capture_output=True,
                    check=True,
                )

            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(working_dir),
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"[{self.agent_id}] Implement spec"],
                cwd=str(working_dir),
                capture_output=True,
                check=False,  # No error if nothing to commit
            )
            logger.info("[%s] Git commit created", self.agent_id)
        except FileNotFoundError:
            logger.warning("[%s] git not available — skipping commit", self.agent_id)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _record_metrics(self, response: CanonicalResponse, elapsed: float) -> None:
        """Accumulate token / cost metrics from the response."""
        self._metrics.tokens_in += response.tokens_in
        self._metrics.tokens_out += response.tokens_out
        self._metrics.cost_usd += response.cost
        self._metrics.duration_s = elapsed
