#!/usr/bin/env python3
"""CLI: Run benchmarks against LLM routers."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm_router_lab.report import print_table
from llm_router_lab.runner import run_benchmark, save_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LLM router benchmarks",
    )
    parser.add_argument(
        "--routers",
        nargs="+",
        help="Router names to test (default: all configured)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Canonical model names to test (default: scenario defaults)",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        help="Scenario names to run (default: all)",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat each request (default: 1)",
    )
    parser.add_argument(
        "--save",
        metavar="NAME",
        help="Save results with a label (saved to results/ as JSON)",
    )
    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Skip printing the results table",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    report = await run_benchmark(
        router_names=args.routers,
        model_names=args.models,
        scenario_names=args.scenarios,
        repeat=args.repeat,
    )

    if not args.no_table:
        print_table(report)

    if args.save:
        path = save_report(report, args.save)
        print(f"\nResults saved to: {path}")
    elif report.results:
        path = save_report(report)
        print(f"\nResults saved to: {path}")


if __name__ == "__main__":
    asyncio.run(main())
