"""Report generation: comparison tables, CSV, and markdown output."""

from __future__ import annotations

import csv
import io
import json
import statistics
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from llm_router_lab.types import BenchmarkReport, BenchmarkResult


def _aggregate_results(
    results: list[BenchmarkResult],
) -> list[dict[str, Any]]:
    """Aggregate results by (router, model, scenario)."""
    groups: dict[tuple[str, str, str], list[BenchmarkResult]] = {}
    for r in results:
        key = (r.router, r.model, r.scenario)
        groups.setdefault(key, []).append(r)

    rows = []
    for (router, model, scenario), group in sorted(groups.items()):
        latencies = [r.timing.latency for r in group]
        ttfts = [r.timing.ttft for r in group if r.timing.ttft is not None]
        successes = sum(1 for r in group if r.success)

        if len(latencies) >= 2:
            qs = statistics.quantiles(latencies, n=100)
            p50 = qs[49]
            p95 = qs[94]
            p99 = qs[98]
        else:
            p50 = p95 = p99 = latencies[0] if latencies else 0.0

        rows.append({
            "router": router,
            "model": model,
            "scenario": scenario,
            "count": len(group),
            "success_rate": successes / len(group),
            "avg_latency": sum(latencies) / len(latencies),
            "p50_latency": p50,
            "p95_latency": p95,
            "p99_latency": p99,
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "avg_ttft": sum(ttfts) / len(ttfts) if ttfts else None,
            "avg_prompt_tokens": sum(r.response.usage.prompt_tokens for r in group) / len(group),
            "avg_completion_tokens": sum(r.response.usage.completion_tokens for r in group) / len(group),
        })

    return rows


def print_table(report: BenchmarkReport) -> None:
    """Print a rich comparison table to the console."""
    console = Console()
    rows = _aggregate_results(report.results)

    table = Table(title="Benchmark Results", show_lines=True)
    table.add_column("Router", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Scenario", style="yellow")
    table.add_column("Count", justify="right")
    table.add_column("Success", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("p50", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("p99", justify="right")
    table.add_column("TTFT", justify="right")
    table.add_column("Prompt Tok", justify="right")
    table.add_column("Compl Tok", justify="right")

    for row in rows:
        ttft_str = f"{row['avg_ttft']:.3f}s" if row["avg_ttft"] is not None else "-"
        table.add_row(
            row["router"],
            row["model"],
            row["scenario"],
            str(row["count"]),
            f"{row['success_rate']:.0%}",
            f"{row['avg_latency']:.3f}s",
            f"{row['p50_latency']:.3f}s",
            f"{row['p95_latency']:.3f}s",
            f"{row['p99_latency']:.3f}s",
            ttft_str,
            f"{row['avg_prompt_tokens']:.0f}",
            f"{row['avg_completion_tokens']:.0f}",
        )

    console.print(table)


def to_csv(report: BenchmarkReport) -> str:
    """Generate a CSV string from benchmark results."""
    rows = _aggregate_results(report.results)
    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def to_markdown(report: BenchmarkReport) -> str:
    """Generate a markdown table from benchmark results."""
    rows = _aggregate_results(report.results)
    if not rows:
        return "No results."

    headers = ["Router", "Model", "Scenario", "Count", "Success", "Avg Latency", "p50", "p95", "p99", "TTFT"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in rows:
        ttft = f"{row['avg_ttft']:.3f}s" if row["avg_ttft"] is not None else "-"
        lines.append(
            f"| {row['router']} | {row['model']} | {row['scenario']} "
            f"| {row['count']} | {row['success_rate']:.0%} "
            f"| {row['avg_latency']:.3f}s "
            f"| {row['p50_latency']:.3f}s | {row['p95_latency']:.3f}s | {row['p99_latency']:.3f}s "
            f"| {ttft} |"
        )

    return "\n".join(lines)


def load_report(path: Path) -> BenchmarkReport:
    """Load a benchmark report from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return BenchmarkReport(**data)
