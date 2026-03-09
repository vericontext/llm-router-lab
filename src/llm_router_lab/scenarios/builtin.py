"""Programmatic built-in scenarios for cases too complex for YAML."""

from __future__ import annotations

from typing import Any

from llm_router_lab.types import LLMRequest, Message, Role


def _long_context_scenario() -> dict[str, Any]:
    """Generate a long context scenario with a large input."""
    long_text = "The quick brown fox jumps over the lazy dog. " * 500
    return {
        "name": "long_context_builtin",
        "description": "Programmatically generated long context test",
        "requests": [
            LLMRequest(
                model="gpt-4o",
                messages=[
                    Message(role=Role.USER, content=f"Summarize this text:\n\n{long_text}"),
                ],
                max_tokens=200,
            ),
        ],
    }


def get_builtin_scenarios() -> list[dict[str, Any]]:
    """Return all built-in programmatic scenarios."""
    return [
        _long_context_scenario(),
    ]
