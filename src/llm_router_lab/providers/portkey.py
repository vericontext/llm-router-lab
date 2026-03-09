"""Portkey AI Gateway adapter.

Uses ``x-portkey-provider`` header to specify the upstream provider
and passes the provider's API key via ``Authorization`` header directly.
No Portkey dashboard integration/virtual-key setup required.
"""

from __future__ import annotations

import os

from openai import AsyncOpenAI

from llm_router_lab.config import RouterConfig
from llm_router_lab.providers.openai_compat import OpenAICompatProvider


class PortkeyProvider(OpenAICompatProvider):
    """Adapter for Portkey AI Gateway."""

    def __init__(self, config: RouterConfig) -> None:
        super().__init__(config)
        portkey_api_key = os.getenv("PORTKEY_API_KEY", "")
        # extra.provider: upstream provider name (e.g. "openai")
        # extra.provider_api_key_env: env var holding the upstream API key
        provider = config.extra.get("provider", "openai")
        provider_key_env = config.extra.get("provider_api_key_env", "OPENAI_API_KEY")
        provider_api_key = os.getenv(provider_key_env, "")
        self._client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=provider_api_key,
            default_headers={
                "x-portkey-api-key": portkey_api_key,
                "x-portkey-provider": provider,
            },
        )
