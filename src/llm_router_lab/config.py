"""YAML + environment variable configuration loader."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


class RouterConfig(BaseModel):
    """Configuration for a single router provider."""

    name: str
    provider_type: str  # "openrouter", "litellm", "openai_compat"
    base_url: str
    api_key_env: str  # Name of the env var holding the API key
    default_params: dict[str, Any] = Field(default_factory=dict)
    model_map: dict[str, str] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.api_key_env)


class AppConfig(BaseModel):
    """Top-level application configuration."""

    routers: dict[str, RouterConfig] = Field(default_factory=dict)
    models: dict[str, dict[str, str]] = Field(default_factory=dict)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_config(config_dir: Path | None = None) -> AppConfig:
    """Load all configuration from YAML files and environment variables."""
    config_dir = config_dir or CONFIG_DIR

    routers_data = load_yaml(config_dir / "routers.yaml")
    models_data = load_yaml(config_dir / "models.yaml")

    routers: dict[str, RouterConfig] = {}
    for name, cfg in routers_data.get("routers", {}).items():
        model_map = models_data.get("models", {}).get(name, {})
        routers[name] = RouterConfig(name=name, model_map=model_map, **cfg)

    return AppConfig(
        routers=routers,
        models=models_data.get("models", {}),
    )
