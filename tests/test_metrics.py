"""Tests for metrics and timing utilities."""

from __future__ import annotations

from llm_router_lab.types import TimingMetrics, TokenUsage, BenchmarkResult, LLMRequest, LLMResponse, Message, Role


def test_timing_latency():
    timing = TimingMetrics(start_time=1.0, end_time=2.5)
    assert timing.latency == pytest.approx(1.5)


def test_timing_ttft_none_by_default():
    timing = TimingMetrics()
    assert timing.ttft is None


def test_token_usage_defaults():
    usage = TokenUsage()
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0


def test_benchmark_result_creation():
    request = LLMRequest(
        model="gpt-4o",
        messages=[Message(role=Role.USER, content="Hello")],
    )
    response = LLMResponse(content="Hi there!")
    timing = TimingMetrics(start_time=1.0, end_time=2.0)

    result = BenchmarkResult(
        router="test",
        model="gpt-4o",
        scenario="basic",
        request=request,
        response=response,
        timing=timing,
    )
    assert result.success is True
    assert result.timing.latency == pytest.approx(1.0)


import pytest
