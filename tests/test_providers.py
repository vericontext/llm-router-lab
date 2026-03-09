"""Tests for provider adapters."""

from __future__ import annotations

import pytest

from llm_router_lab.config import RouterConfig
from llm_router_lab.providers.openai_compat import OpenAICompatProvider
from llm_router_lab.providers.openrouter import OpenRouterProvider
from llm_router_lab.providers.litellm import LiteLLMProvider
from llm_router_lab.providers.portkey import PortkeyProvider
from llm_router_lab.providers.cloudflare_ai_gw import CloudflareAIGWProvider


def _make_config(**overrides) -> RouterConfig:
    defaults = {
        "name": "test",
        "provider_type": "openai_compat",
        "base_url": "http://localhost:8000/v1",
        "api_key_env": "TEST_API_KEY",
    }
    defaults.update(overrides)
    return RouterConfig(**defaults)


def test_openai_compat_provider_creation():
    config = _make_config()
    provider = OpenAICompatProvider(config)
    assert provider.name == "test"


def test_openrouter_provider_creation():
    config = _make_config(provider_type="openrouter", base_url="https://openrouter.ai/api/v1")
    provider = OpenRouterProvider(config)
    assert provider.name == "test"


def test_litellm_provider_creation():
    config = _make_config(provider_type="litellm")
    provider = LiteLLMProvider(config)
    assert provider.name == "test"


def test_portkey_provider_creation():
    config = _make_config(
        provider_type="portkey",
        base_url="https://api.portkey.ai/v1",
    )
    provider = PortkeyProvider(config)
    assert provider.name == "test"


def test_cloudflare_ai_gw_provider_creation():
    config = _make_config(
        provider_type="cloudflare_ai_gw",
        base_url="https://gateway.ai.cloudflare.com",
        extra={"account_id": "test_account", "gateway_id": "test_gw"},
    )
    provider = CloudflareAIGWProvider(config)
    assert provider.name == "test"



def test_model_resolution():
    config = _make_config(model_map={"gpt-4o": "openai/gpt-4o"})
    provider = OpenAICompatProvider(config)
    assert provider.resolve_model("gpt-4o") == "openai/gpt-4o"
    assert provider.resolve_model("unknown-model") == "unknown-model"
