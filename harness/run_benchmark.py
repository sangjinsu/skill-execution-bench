"""Benchmark driver: run all execution modes against the dataset.

Usage:
    python -m harness.run_benchmark [--dataset PATH] [--trace PATH]

Prints a per-runner pass/fail summary and writes a JSONL trace file.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from . import REPO_ROOT
from .evaluators import evaluate_all
from .models import TraceRow, load_cases
from .runners import build_runners

DEFAULT_DATASET = REPO_ROOT / "datasets" / "tasks.jsonl"
DEFAULT_TRACE = REPO_ROOT / "outputs" / "traces" / "bench.jsonl"


def write_traces(rows: list[TraceRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(row.to_json() + "\n")


def print_summary(rows: list[TraceRow]) -> tuple[int, int]:
    by_runner: dict[str, list[TraceRow]] = defaultdict(list)
    for row in rows:
        by_runner[row.runner].append(row)

    print("\nSkill execution benchmark")
    print("=" * 48)
    print(f"{'mode':<16}{'passed':>10}{'total':>10}")
    print("-" * 48)

    total_passed = 0
    total = 0
    for runner, runner_rows in by_runner.items():
        passed = sum(1 for r in runner_rows if r.passed)
        count = len(runner_rows)
        total_passed += passed
        total += count
        flag = "" if passed == count else "  <-- failures"
        print(f"{runner:<16}{passed:>10}{count:>10}{flag}")

    print("-" * 48)
    print(f"{'ALL':<16}{total_passed:>10}{total:>10}")

    failures = [r for r in rows if not r.passed]
    if failures:
        print("\nFailures:")
        for row in failures:
            print(f"  [{row.runner}] {row.case_id}: {row.error}")
    return total_passed, total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the skill-execution benchmark.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    cases = load_cases(args.dataset)
    runners = build_runners()
    rows = evaluate_all(runners, cases)

    write_traces(rows, args.trace)
    total_passed, total = print_summary(rows)
    print(f"\nTraces written to {args.trace}")

    return 0 if total_passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
