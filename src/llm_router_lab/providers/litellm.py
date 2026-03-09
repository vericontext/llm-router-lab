"""LiteLLM proxy adapter.

LiteLLM exposes an OpenAI-compatible API, so this adapter extends the
generic OpenAI-compatible provider with LiteLLM-specific features.
"""

from __future__ import annotations

from llm_router_lab.config import RouterConfig
from llm_router_lab.providers.openai_compat import OpenAICompatProvider


class LiteLLMProvider(OpenAICompatProvider):
    """Adapter for LiteLLM proxy server."""

    def __init__(self, config: RouterConfig) -> None:
        super().__init__(config)
