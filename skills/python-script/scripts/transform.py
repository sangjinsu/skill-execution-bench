#!/usr/bin/env python3
"""Normalize task records: read JSON from stdin, write normalized JSON to stdout.

Usage:
    python transform.py < input.json > output.json

Exits non-zero on invalid input. No network access, fully deterministic.
"""

from __future__ import annotations

import json
import sys
from typing import Any

STATUS_MAP: dict[str, str] = {
    "todo": "todo",
    "to do": "todo",
    "pending": "todo",
    "doing": "doing",
    "in progress": "doing",
    "wip": "doing",
    "done": "done",
    "complete": "done",
    "completed": "done",
}

_KEY_PRIORITY = {"id": 0, "title": 1, "status": 2}


def _normalize_status(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    key = value.strip().lower()
    return STATUS_MAP.get(key, key)


def _ordered_keys(record: dict[str, Any]) -> list[str]:
    return sorted(record.keys(), key=lambda k: (_KEY_PRIORITY.get(k, 3), k))


def _is_int(value: Any) -> bool:
    try:
        int(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False


def normalize(records: Any) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError("input must be a JSON array")
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each record must be a JSON object")
        out: dict[str, Any] = {}
        for key in _ordered_keys(record):
            value = record[key]
            if key == "status":
                out[key] = _normalize_status(value)
            elif key == "id":
                out[key] = str(value).strip()
            elif isinstance(value, str):
                out[key] = value.strip()
            else:
                out[key] = value
        normalized.append(out)
    if normalized and all(_is_int(r.get("id", "")) for r in normalized):
        normalized.sort(key=lambda r: int(str(r.get("id")).strip()))
    else:
        normalized.sort(key=lambda r: str(r.get("id", "")))
    return normalized


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON on stdin: {exc}", file=sys.stderr)
        return 1
    try:
        result = normalize(payload)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
