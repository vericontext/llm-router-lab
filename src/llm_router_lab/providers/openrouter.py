"""OpenRouter-specific adapter.

Extends the OpenAI-compatible adapter with OpenRouter-specific headers
and response parsing (e.g., cost information from x-openrouter headers).
"""

from __future__ import annotations

from typing import AsyncIterator

from openai import AsyncOpenAI

from llm_router_lab.config import RouterConfig
from llm_router_lab.providers.openai_compat import OpenAICompatProvider
from llm_router_lab.types import LLMRequest, LLMResponse


class OpenRouterProvider(OpenAICompatProvider):
    """Adapter for OpenRouter with provider-specific enhancements."""

    def __init__(self, config: RouterConfig) -> None:
        super().__init__(config)
        # Recreate client with OpenRouter-specific headers
        self._client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key or "dummy",
            default_headers={
                "HTTP-Referer": "https://github.com/llm-router-lab",
                "X-Title": "LLM Router Lab",
            },
        )
