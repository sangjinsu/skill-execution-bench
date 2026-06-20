"""Evaluate real LLM-agent benchmark runs.

Unlike ``run_benchmark`` (which mechanically simulates each mode and always
passes), this module scores the outputs that *real* sub-agents produced when
asked to perform the task using only one mode's SKILL.md.

Each agent run is stored as a JSON file under ``outputs/agent_runs/``:

    {
      "mode": "doc-only",
      "trial": 1,
      "model": "opus",
      "outputs": {"case-001": [...], "case-002": [...], ...}
    }

A missing or malformed output for a case counts as a failure for that case, so
the reliability score reflects what an agent actually achieved from the Skill.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from . import REPO_ROOT
from .evaluators import outputs_match
from .models import load_cases

DEFAULT_RUNS_DIR = REPO_ROOT / "outputs" / "agent_runs"
DEFAULT_DATASET = REPO_ROOT / "datasets" / "tasks.jsonl"
DEFAULT_TRACE = REPO_ROOT / "outputs" / "traces" / "agent-bench.jsonl"

MODE_ORDER = ["doc-only", "inline-code", "python-script", "go-binary"]


@dataclass
class AgentResult:
    mode: str
    trial: int
    model: str
    case_id: str
    passed: bool
    error: str | None

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def load_runs(runs_dir: Path) -> list[dict]:
    """Load all agent-run JSON files from a directory, sorted by filename."""
    if not runs_dir.exists():
        raise FileNotFoundError(f"no agent runs directory: {runs_dir}")
    runs = []
    for path in sorted(runs_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("model", "unknown")
        data.setdefault("outputs", {})
        runs.append(data)
    if not runs:
        raise FileNotFoundError(f"no *.json agent runs found in {runs_dir}")
    return runs


def score_runs(runs: list[dict], expected_by_case: dict) -> list[AgentResult]:
    """Score every (run, case) pair against the expected output."""
    results: list[AgentResult] = []
    for run in runs:
        mode = run.get("mode", "unknown")
        trial = int(run.get("trial", 0))
        model = run.get("model", "unknown")
        produced = run.get("outputs", {})
        for case_id, expected in expected_by_case.items():
            if case_id not in produced:
                results.append(
                    AgentResult(mode, trial, model, case_id, False, "no output produced")
                )
                continue
            actual = produced[case_id]
            if not isinstance(actual, list):
                results.append(
                    AgentResult(mode, trial, model, case_id, False, "output is not a JSON array")
                )
                continue
            passed = outputs_match(actual, expected)
            results.append(
                AgentResult(
                    mode, trial, model, case_id, passed,
                    None if passed else "output did not match expected",
                )
            )
    return results


def write_traces(results: list[AgentResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in results:
            fh.write(r.to_json() + "\n")


def _mode_sort_key(mode: str) -> tuple[int, str]:
    return (MODE_ORDER.index(mode) if mode in MODE_ORDER else len(MODE_ORDER), mode)


def print_report(results: list[AgentResult], case_ids: list[str]) -> None:
    by_mode: dict[str, list[AgentResult]] = defaultdict(list)
    for r in results:
        by_mode[r.mode].append(r)

    print("\nReal LLM-agent Skill-execution benchmark")
    print("=" * 60)
    print(f"{'mode':<16}{'reliability':>14}{'passed':>10}{'total':>10}")
    print("-" * 60)
    for mode in sorted(by_mode, key=_mode_sort_key):
        rows = by_mode[mode]
        passed = sum(1 for r in rows if r.passed)
        total = len(rows)
        pct = (passed / total * 100) if total else 0.0
        print(f"{mode:<16}{pct:>13.1f}%{passed:>10}{total:>10}")
    print("-" * 60)

    # Per-case breakdown: how many trials passed per mode/case.
    print("\nPer-case pass count (passed trials / total trials)")
    header = f"{'case':<12}" + "".join(f"{m:>16}" for m in sorted(by_mode, key=_mode_sort_key))
    print(header)
    print("-" * len(header))
    trials_by_mode = {m: len({r.trial for r in rows}) for m, rows in by_mode.items()}
    for case_id in case_ids:
        line = f"{case_id:<12}"
        for mode in sorted(by_mode, key=_mode_sort_key):
            rows = [r for r in by_mode[mode] if r.case_id == case_id]
            passed = sum(1 for r in rows if r.passed)
            line += f"{f'{passed}/{trials_by_mode[mode]}':>16}"
        print(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score real LLM-agent benchmark runs.")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    cases = load_cases(args.dataset)
    expected_by_case = {c.id: c.expected for c in cases}
    case_ids = [c.id for c in cases]

    runs = load_runs(args.runs_dir)
    results = score_runs(runs, expected_by_case)
    write_traces(results, args.trace)
    print_report(results, case_ids)
    print(f"\nTraces written to {args.trace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
