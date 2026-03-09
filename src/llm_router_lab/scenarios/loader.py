"""YAML scenario loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llm_router_lab.types import LLMRequest, Message, Role, ToolDefinition

SCENARIOS_DIR = Path(__file__).resolve().parents[3] / "scenarios"


def _parse_messages(raw_messages: list[dict[str, Any]]) -> list[Message]:
    """Convert raw YAML message dicts to Message objects."""
    return [
        Message(role=Role(m["role"]), content=m["content"])
        for m in raw_messages
    ]


def _parse_scenario_to_requests(data: dict[str, Any]) -> list[LLMRequest]:
    """Parse a scenario YAML dict into a list of LLMRequest objects."""
    requests: list[LLMRequest] = []
    defaults = data.get("defaults", {})

    for case in data.get("cases", []):
        messages = _parse_messages(case["messages"])

        tools = None
        if "tools" in case:
            tools = [ToolDefinition(**t) for t in case["tools"]]

        req = LLMRequest(
            model=case.get("model", defaults.get("model", "gpt-4o")),
            messages=messages,
            temperature=case.get("temperature", defaults.get("temperature", 0.7)),
            max_tokens=case.get("max_tokens", defaults.get("max_tokens")),
            stream=case.get("stream", defaults.get("stream", False)),
            tools=tools,
        )
        requests.append(req)

    return requests


def load_scenario(path: Path | str) -> dict[str, Any]:
    """Load a single scenario file and return parsed data.

    Returns a dict with keys: name, description, requests.
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)

    return {
        "name": data.get("name", path.stem),
        "description": data.get("description", ""),
        "requests": _parse_scenario_to_requests(data),
    }


def load_all_scenarios(
    scenarios_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load all YAML scenario files from the scenarios directory."""
    scenarios_dir = scenarios_dir or SCENARIOS_DIR
    scenarios = []
    for path in sorted(scenarios_dir.glob("*.yaml")):
        scenarios.append(load_scenario(path))
    return scenarios
