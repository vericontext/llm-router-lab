"""Cloudflare AI Gateway adapter.

Routes requests through Cloudflare's AI Gateway, which proxies to
upstream providers (e.g., OpenAI) while adding caching, rate-limiting,
and observability.
"""

from __future__ import annotations

import os

from openai import AsyncOpenAI

from llm_router_lab.config import RouterConfig
from llm_router_lab.providers.openai_compat import OpenAICompatProvider


class CloudflareAIGWProvider(OpenAICompatProvider):
    """Adapter for Cloudflare AI Gateway."""

    def __init__(self, config: RouterConfig) -> None:
        super().__init__(config)
        account_id = config.extra.get("account_id", "")
        gateway_id = config.extra.get("gateway_id", "")
        provider_path = config.extra.get("provider_path", "openai")
        base_url = (
            f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/{provider_path}"
        )
        cf_token = os.getenv("CF_AIG_TOKEN", "")
        headers = {}
        if cf_token:
            headers["cf-aig-authorization"] = f"Bearer {cf_token}"
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=config.api_key or "dummy",
            default_headers=headers,
        )
