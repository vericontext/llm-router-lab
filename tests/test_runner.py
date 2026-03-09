"""Tests for scenario loading and runner utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_router_lab.scenarios.loader import load_scenario, load_all_scenarios
from llm_router_lab.runner import PROVIDER_CLASSES

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"


def test_load_basic_completion_scenario():
    scenario = load_scenario(SCENARIOS_DIR / "basic_completion.yaml")
    assert scenario["name"] == "basic_completion"
    assert len(scenario["requests"]) == 3


def test_load_streaming_scenario():
    scenario = load_scenario(SCENARIOS_DIR / "streaming.yaml")
    assert scenario["name"] == "streaming"
    for req in scenario["requests"]:
        assert req.stream is True


def test_load_tool_calling_scenario():
    scenario = load_scenario(SCENARIOS_DIR / "tool_calling.yaml")
    assert scenario["name"] == "tool_calling"
    for req in scenario["requests"]:
        assert req.tools is not None
        assert len(req.tools) > 0


def test_load_all_scenarios():
    scenarios = load_all_scenarios(SCENARIOS_DIR)
    names = [s["name"] for s in scenarios]
    assert "basic_completion" in names
    assert "streaming" in names


def test_provider_classes_registered():
    assert "openrouter" in PROVIDER_CLASSES
    assert "litellm" in PROVIDER_CLASSES
    assert "openai_compat" in PROVIDER_CLASSES
