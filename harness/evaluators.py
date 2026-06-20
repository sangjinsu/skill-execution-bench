"""Strict deterministic evaluation of runner output against expected values."""

from __future__ import annotations

from typing import Any

from .models import Case, TraceRow
from .runners import SkillRunner


def outputs_match(actual: Any, expected: Any) -> bool:
    """Deep structural equality of two already-parsed JSON values.

    Object key order does not matter (dict comparison is order-independent),
    but list order does — which is exactly the contract we want.
    """
    return actual == expected


def evaluate_case(runner: SkillRunner, case: Case) -> TraceRow:
    """Run a single case through a runner and compare to the expected output."""
    try:
        actual = runner.run(case.input)
    except Exception as exc:  # noqa: BLE001 - record any failure as a trace row
        return TraceRow(
            case_id=case.id,
            runner=runner.name,
            execution_mode=runner.execution_mode,
            passed=False,
            error=f"{type(exc).__name__}: {exc}",
            used_external_code=runner.used_external_code,
        )

    passed = outputs_match(actual, case.expected)
    error = None if passed else "output did not match expected"
    return TraceRow(
        case_id=case.id,
        runner=runner.name,
        execution_mode=runner.execution_mode,
        passed=passed,
        error=error,
        used_external_code=runner.used_external_code,
    )


def evaluate_all(
    runners: list[SkillRunner], cases: list[Case]
) -> list[TraceRow]:
    """Evaluate every runner against every case."""
    rows: list[TraceRow] = []
    for runner in runners:
        for case in cases:
            rows.append(evaluate_case(runner, case))
    return rows
