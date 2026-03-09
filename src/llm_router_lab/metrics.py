"""Latency, cost, and token measurement utilities."""

from __future__ import annotations

import time
from typing import AsyncIterator

from llm_router_lab.providers.base import RouterProvider
from llm_router_lab.types import (
    BenchmarkResult,
    CostMetrics,
    LLMRequest,
    LLMResponse,
    TimingMetrics,
    TokenUsage,
)


async def measure_completion(
    provider: RouterProvider,
    request: LLMRequest,
    scenario_name: str,
) -> BenchmarkResult:
    """Execute a completion request and measure timing/usage metrics."""
    timing = TimingMetrics(start_time=time.perf_counter())

    response = await provider.complete(request)

    timing.end_time = time.perf_counter()

    return BenchmarkResult(
        router=provider.name,
        model=request.model,
        scenario=scenario_name,
        request=request,
        response=response,
        timing=timing,
        success=response.error is None,
    )


async def measure_streaming(
    provider: RouterProvider,
    request: LLMRequest,
    scenario_name: str,
) -> BenchmarkResult:
    """Execute a streaming request and measure TTFT and total latency."""
    timing = TimingMetrics(start_time=time.perf_counter())
    chunks: list[str] = []
    first_chunk = True

    try:
        async for chunk in provider.stream(request):
            if first_chunk:
                timing.ttft = time.perf_counter() - timing.start_time
                first_chunk = False
            chunks.append(chunk)

        timing.end_time = time.perf_counter()
        content = "".join(chunks)

        response = LLMResponse(
            content=content,
            usage=TokenUsage(),
            model=request.model,
        )
        success = True
    except Exception as e:
        timing.end_time = time.perf_counter()
        response = LLMResponse(error=str(e))
        success = False

    return BenchmarkResult(
        router=provider.name,
        model=request.model,
        scenario=scenario_name,
        request=request,
        response=response,
        timing=timing,
        success=success,
    )
