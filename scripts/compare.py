#!/usr/bin/env python3
"""CLI: Compare benchmark results from saved JSON files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm_router_lab.report import load_report, print_table, to_csv, to_markdown
from llm_router_lab.types import BenchmarkReport


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare benchmark results",
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Benchmark result JSON files to compare",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv", "markdown"],
        default="table",
        help="Output format (default: table)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Merge all results into a single report
    merged = BenchmarkReport()
    for path in args.files:
        report = load_report(path)
        merged.results.extend(report.results)

    if args.format == "table":
        print_table(merged)
    elif args.format == "csv":
        print(to_csv(merged))
    elif args.format == "markdown":
        print(to_markdown(merged))


if __name__ == "__main__":
    main()
