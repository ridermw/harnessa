"""Response adapter — normalizes LiteLLM responses to CanonicalResponse."""

from __future__ import annotations

import logging
from typing import Any

from harnessa.telemetry.models import CanonicalResponse

logger = logging.getLogger(__name__)


class ResponseAdapter:
    """Normalizes raw LiteLLM completion responses into CanonicalResponse.

    Handles differences between providers (OpenAI, Anthropic, etc.)
    and extracts a consistent set of fields for telemetry.
    """

    def normalize(self, raw_response: dict[str, Any]) -> CanonicalResponse:
        """Convert a raw LiteLLM response dict to a CanonicalResponse.

        Args:
            raw_response: The raw response from litellm.completion().

        Returns:
            A normalized CanonicalResponse.
        """
        logger.debug("Normalizing response from model=%s", raw_response.get("model", "unknown"))

        choices = raw_response.get("choices", [])
        text = ""
        stop_reason = "unknown"
        if choices:
            message = choices[0].get("message", {})
            text = message.get("content", "")
            stop_reason = choices[0].get("finish_reason", "unknown")

        usage = raw_response.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)

        model = raw_response.get("model", "unknown")

        # LiteLLM provides cost via response headers or _hidden_params
        cost = raw_response.get("_cost", 0.0)

        truncated = stop_reason == "length"

        return CanonicalResponse(
            text=text,
            stop_reason=stop_reason,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            truncated=truncated,
        )
