"""Shared Pydantic models for requests, responses, and metrics."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    role: Role
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class ToolDefinition(BaseModel):
    type: str = "function"
    function: dict[str, Any]


class LLMRequest(BaseModel):
    """Normalized request sent to any router provider."""

    model: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    tools: list[ToolDefinition] | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Normalized response from any router provider."""

    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class TimingMetrics(BaseModel):
    """Timing measurements for a single request."""

    start_time: float = 0.0
    end_time: float = 0.0
    ttft: float | None = None  # Time to first token (streaming)

    @property
    def latency(self) -> float:
        return self.end_time - self.start_time


class CostMetrics(BaseModel):
    """Cost information for a single request."""

    input_cost: float | None = None
    output_cost: float | None = None
    total_cost: float | None = None


class BenchmarkResult(BaseModel):
    """Result of a single benchmark run."""

    router: str
    model: str
    scenario: str
    request: LLMRequest
    response: LLMResponse
    timing: TimingMetrics
    cost: CostMetrics = Field(default_factory=CostMetrics)
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True


class BenchmarkReport(BaseModel):
    """Aggregate report across multiple benchmark runs."""

    results: list[BenchmarkResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
