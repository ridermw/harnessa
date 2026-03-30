"""Planner agent — expands a short benchmark prompt into a full product spec."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from harnessa.agents.base import BaseAgent
from harnessa.response_adapter import ResponseAdapter
from harnessa.telemetry.models import AgentMetrics, CanonicalResponse

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """\
You are a senior product architect. Your job is to expand a short 1-4 sentence \
product idea into a comprehensive product specification.

Be ambitious about scope — think about what would make this a truly impressive, \
production-quality product. Do NOT hold back.

Focus on:
- Product context and high-level technical design
- User stories that capture real user needs
- A prioritized feature list (P0 / P1 / P2)
- Clear success criteria that are objectively measurable
- Non-functional requirements (performance, security, accessibility)

Do NOT include:
- Implementation details (no code, no file paths, no function signatures)
- Step-by-step build instructions
- Technology choices (the builder agent decides those)

Output format: Markdown with clear headings. Start with a one-paragraph product \
vision, then user stories, feature list, success criteria, and non-functional \
requirements.
"""


class PlannerAgent(BaseAgent):
    """Expands a short benchmark prompt into a full product specification.

    The planner is the first stage of the Planner → Generator → Evaluator
    pipeline. It takes a terse 1-4 sentence prompt and produces a rich
    spec.md that downstream agents use as their north star.
    """

    def __init__(
        self,
        model_id: str,
        work_dir: Path,
        *,
        agent_id: str = "planner",
    ) -> None:
        super().__init__(agent_id=agent_id, model_id=model_id, work_dir=work_dir)
        self._adapter = ResponseAdapter()

    def execute(self, **kwargs: Any) -> None:
        """Execute the planner via keyword arguments (BaseAgent interface)."""
        prompt = kwargs.get("prompt", "")
        output_dir = Path(kwargs.get("output_dir", self.work_dir))
        self.run(prompt, output_dir)

    def run(self, prompt: str, output_dir: Path) -> Path:
        """Expand *prompt* into a product spec and write it to disk.

        Args:
            prompt: The user's 1-4 sentence benchmark description.
            output_dir: Root output directory; spec lands at
                ``{output_dir}/planner/spec.md``.

        Returns:
            Path to the written spec.md file.
        """
        planner_dir = output_dir / "planner"
        planner_dir.mkdir(parents=True, exist_ok=True)
        spec_path = planner_dir / "spec.md"

        self.write_status("running")
        start = time.monotonic()

        try:
            if self.model_id.startswith("copilot/"):
                # Delegation mode: copilot writes the spec directly
                result = self.run_executor(
                    f"Read the task. Expand into a comprehensive spec: problem statement, "
                    f"root cause analysis, proposed approach, acceptance criteria, edge cases. "
                    f"Write the spec to {planner_dir}/spec.md\n\nTask:\n{prompt}",
                    work_dir=output_dir,
                    allow_tools="read, write",
                )
                if not spec_path.exists():
                    # Copilot may have written to stdout instead of file
                    spec_path.parent.mkdir(parents=True, exist_ok=True)
                    spec_path.write_text(result.stdout, encoding="utf-8")
                self._metrics.duration_s = time.monotonic() - start
                self.write_status("done")
                logger.info("[%s] Spec written to %s (copilot delegation)", self.agent_id, spec_path)
                return spec_path
            else:
                # Text mode: existing _call_model() path
                response = self._call_model(prompt)
                self._write_spec(spec_path, response.text)
                self._record_metrics(response, time.monotonic() - start)
                self.write_status("done")
                logger.info("[%s] Spec written to %s", self.agent_id, spec_path)
                return spec_path

        except Exception as exc:
            elapsed = time.monotonic() - start
            self._metrics.duration_s = elapsed
            self.write_status("error")
            logger.error("[%s] Failed: %s", self.agent_id, exc)
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def build_system_prompt(self) -> str:
        """Return the system prompt that instructs the LLM."""
        return PLANNER_SYSTEM_PROMPT

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
                model=self._litellm_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                timeout=120,
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
            elif "ContentFilter" in exc_name or "refusal" in str(exc).lower():
                logger.error("[%s] Content refused by provider", self.agent_id)
            else:
                logger.error("[%s] LLM call failed: %s: %s", self.agent_id, exc_name, exc)
            raise

    @staticmethod
    def _write_spec(path: Path, content: str) -> None:
        """Write spec content atomically (write tmp then rename)."""
        tmp = path.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(path)

    def _record_metrics(self, response: CanonicalResponse, elapsed: float) -> None:
        """Accumulate token / cost metrics from the response."""
        self._metrics.tokens_in += response.tokens_in
        self._metrics.tokens_out += response.tokens_out
        self._metrics.cost_usd += response.cost
        self._metrics.duration_s = elapsed
