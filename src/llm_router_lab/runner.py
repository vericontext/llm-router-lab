"""Async benchmark runner."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from llm_router_lab.config import AppConfig, RouterConfig, load_config
from llm_router_lab.metrics import measure_completion, measure_streaming
from llm_router_lab.providers.base import RouterProvider
from llm_router_lab.providers.cloudflare_ai_gw import CloudflareAIGWProvider
from llm_router_lab.providers.litellm import LiteLLMProvider
from llm_router_lab.providers.openai_compat import OpenAICompatProvider
from llm_router_lab.providers.openrouter import OpenRouterProvider
from llm_router_lab.providers.portkey import PortkeyProvider
from llm_router_lab.scenarios.loader import load_scenario
from llm_router_lab.types import BenchmarkReport, BenchmarkResult, LLMRequest

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "scenarios"

PROVIDER_CLASSES: dict[str, type[RouterProvider]] = {
    "openrouter": OpenRouterProvider,
    "litellm": LiteLLMProvider,
    "openai_compat": OpenAICompatProvider,
    "portkey": PortkeyProvider,
    "cloudflare_ai_gw": CloudflareAIGWProvider,
}


def create_provider(config: RouterConfig) -> RouterProvider:
    """Instantiate a provider from its config."""
    cls = PROVIDER_CLASSES.get(config.provider_type)
    if cls is None:
        raise ValueError(f"Unknown provider type: {config.provider_type}")
    return cls(config)


async def run_single(
    provider: RouterProvider,
    request: LLMRequest,
    scenario_name: str,
) -> BenchmarkResult:
    """Run a single request against a provider."""
    if request.stream:
        return await measure_streaming(provider, request, scenario_name)
    return await measure_completion(provider, request, scenario_name)


async def run_benchmark(
    router_names: list[str] | None = None,
    model_names: list[str] | None = None,
    scenario_names: list[str] | None = None,
    config: AppConfig | None = None,
    repeat: int = 1,
) -> BenchmarkReport:
    """Run benchmarks across specified routers, models, and scenarios.

    Args:
        router_names: Routers to test (None = all configured).
        model_names: Canonical model names (None = use scenario defaults).
        scenario_names: Scenario file stems (None = all in scenarios/).
        config: App config (None = load from default config dir).
        repeat: Number of times to repeat each request.

    Returns:
        BenchmarkReport with all results.
    """
    config = config or load_config()
    console = Console()
    report = BenchmarkReport(
        metadata={
            "routers": router_names,
            "models": model_names,
            "scenarios": scenario_names,
            "started_at": datetime.now().isoformat(),
        }
    )

    # Determine which routers to use
    routers_to_test = router_names or list(config.routers.keys())

    # Load scenarios
    if scenario_names:
        scenarios = []
        for name in scenario_names:
            path = SCENARIOS_DIR / f"{name}.yaml"
            if path.exists():
                scenarios.append(load_scenario(path))
            else:
                console.print(f"[yellow]Warning: scenario '{name}' not found[/yellow]")
    else:
        from llm_router_lab.scenarios.loader import load_all_scenarios
        scenarios = load_all_scenarios()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for router_name in routers_to_test:
            router_config = config.routers.get(router_name)
            if not router_config:
                console.print(f"[yellow]Warning: router '{router_name}' not configured[/yellow]")
                continue

            provider = create_provider(router_config)
            try:
                for scenario in scenarios:
                    for request in scenario["requests"]:
                        # Override model if specified
                        models = model_names or [request.model]
                        for model in models:
                            req = request.model_copy(update={"model": model})
                            for i in range(repeat):
                                repeat_tag = f" [{i+1}/{repeat}]" if repeat > 1 else ""
                                task_desc = f"{router_name} / {model} / {scenario['name']}{repeat_tag}"
                                task = progress.add_task(task_desc, total=None)

                                result = await run_single(provider, req, scenario["name"])
                                report.results.append(result)

                                status = "[green]OK" if result.success else f"[red]FAIL: {result.response.error}"
                                latency = result.timing.latency
                                progress.update(task, description=f"{task_desc} → {status} ({latency:.2f}s)")
                                progress.stop_task(task)

                                if repeat > 1 and i < repeat - 1:
                                    await asyncio.sleep(0.5)
            finally:
                await provider.close()

    report.metadata["finished_at"] = datetime.now().isoformat()
    return report


def save_report(report: BenchmarkReport, name: str | None = None) -> Path:
    """Save a benchmark report to the results directory as JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.json" if name else f"benchmark_{timestamp}.json"
    path = RESULTS_DIR / filename

    with open(path, "w") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, default=str)

    return path
