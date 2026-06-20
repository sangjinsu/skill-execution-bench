---
id: skill.inline-code
name: Normalize Task Records (Inline Code)
execution_mode: inline-code
version: 0.1.0
---

# Normalize Task Records (Inline Code)

## When to use

Use this Skill when you need to normalize a list of task records and the executable
logic is embedded directly in this document. Copy, adapt, and run the code block below
rather than writing the logic from scratch.

## Inputs

- A JSON array of task records (in memory, or read from stdin).
- Records may have inconsistent casing, whitespace, mixed status labels, and optional fields.

## Expected output

- A normalized list following the shared contract:
  - All string values trimmed.
  - `id` is a trimmed string.
  - `status` is trimmed, lowercased, then mapped (see code).
  - Missing optional fields are not added.
  - Key order per object: `id`, `title`, `status`, then remaining keys alphabetically.
  - Array sorted by `id` (numeric when all ids are integers, else lexicographic).

## Procedure

Use the `normalize` function defined in the following code block. It is self-contained
and deterministic — paste it into your runtime and call `normalize(records)`.

```python
def normalize(records):
    status_map = {
        "todo": "todo", "to do": "todo", "pending": "todo",
        "doing": "doing", "in progress": "doing", "wip": "doing",
        "done": "done", "complete": "done", "completed": "done",
    }
    key_priority = {"id": 0, "title": 1, "status": 2}

    def normalize_status(value):
        if not isinstance(value, str):
            return value
        key = value.strip().lower()
        return status_map.get(key, key)

    def ordered_keys(record):
        return sorted(record.keys(), key=lambda k: (key_priority.get(k, 3), k))

    def is_int(value):
        try:
            int(str(value).strip())
            return True
        except (TypeError, ValueError):
            return False

    if not isinstance(records, list):
        raise ValueError("input must be a JSON array")

    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each record must be a JSON object")
        out = {}
        for key in ordered_keys(record):
            value = record[key]
            if key == "status":
                out[key] = normalize_status(value)
            elif key == "id":
                out[key] = str(value).strip()
            elif isinstance(value, str):
                out[key] = value.strip()
            else:
                out[key] = value
        normalized.append(out)

    if normalized and all(is_int(r.get("id", "")) for r in normalized):
        normalized.sort(key=lambda r: int(str(r.get("id")).strip()))
    else:
        normalized.sort(key=lambda r: str(r.get("id", "")))
    return normalized
```

To run it end-to-end over stdin:

```python
import json, sys
print(json.dumps(normalize(json.load(sys.stdin)), ensure_ascii=False, separators=(",", ":")))
```

## Validation

- [ ] `normalize` returns a list.
- [ ] Every `status` is a mapped canonical value (or an intentionally unmapped label).
- [ ] Records are ordered by `id`.
- [ ] Non-list / non-object input raises `ValueError`.
