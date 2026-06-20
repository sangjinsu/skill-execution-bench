"""Data models for the benchmark: dataset cases and trace rows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Case:
    """A single benchmark case loaded from the dataset."""

    id: str
    input: Any
    expected: Any
    notes: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Case":
        missing = [k for k in ("id", "input", "expected") if k not in data]
        if missing:
            raise ValueError(f"case is missing required fields: {missing}")
        return Case(
            id=data["id"],
            input=data["input"],
            expected=data["expected"],
            notes=data.get("notes"),
        )


@dataclass
class TraceRow:
    """One result row: how a runner did on a single case."""

    case_id: str
    runner: str
    execution_mode: str
    passed: bool
    error: str | None = None
    used_external_code: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def load_cases(path: str | Path) -> list[Case]:
    """Load cases from a JSONL dataset file."""
    cases: list[Case] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            cases.append(Case.from_dict(data))
    if not cases:
        raise ValueError(f"no cases found in {path}")
    return cases
