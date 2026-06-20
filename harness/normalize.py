"""Reference implementation of the task-record normalization contract.

This is the canonical Python implementation of the normalization the whole
benchmark is built around. It is intentionally dependency-free and deterministic.

The same contract is duplicated (by design) inside the inline-code SKILL, the
python-script, and the Go binary so that every execution mode can be compared
against the same expected output.
"""

from __future__ import annotations

from typing import Any

# status label -> canonical value
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

# Keys that have a fixed leading order; everything else sorts alphabetically after.
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
    """Normalize a list of task records.

    Raises ValueError on input that is not a list of objects.
    """
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
