#!/usr/bin/env python3
"""Topologically sort dependency records: read JSON from stdin, write JSON to stdout.

Usage:
    python toposort.py < input.json > output.json

Input:  [{"id": "<int>", "deps": ["<id>", ...]}, ...]   (a valid DAG)
Output: ["<id>", ...] in topological order; when multiple nodes are ready,
        the smallest numeric id is emitted first (deterministic).

Exits non-zero on invalid input or a cycle. No network access, deterministic.
"""

from __future__ import annotations

import heapq
import json
import sys
from typing import Any


def toposort(records: Any) -> list[str]:
    if not isinstance(records, list):
        raise ValueError("input must be a JSON array")

    ids: list[str] = []
    deps_of: dict[str, list[str]] = {}
    for record in records:
        if not isinstance(record, dict) or "id" not in record:
            raise ValueError("each record must be an object with an 'id'")
        node = str(record["id"]).strip()
        raw_deps = record.get("deps", []) or []
        if not isinstance(raw_deps, list):
            raise ValueError("'deps' must be an array")
        deps = [str(d).strip() for d in raw_deps]
        if node in deps_of:
            raise ValueError(f"duplicate id: {node}")
        ids.append(node)
        deps_of[node] = deps

    node_set = set(ids)
    indegree = {n: 0 for n in ids}
    dependents: dict[str, list[str]] = {n: [] for n in ids}
    for node in ids:
        for dep in deps_of[node]:
            if dep not in node_set:
                raise ValueError(f"unknown dependency '{dep}' for node '{node}'")
            indegree[node] += 1
            dependents[dep].append(node)

    ready = [(int(n), n) for n in ids if indegree[n] == 0]
    heapq.heapify(ready)

    order: list[str] = []
    while ready:
        _, node = heapq.heappop(ready)
        order.append(node)
        for child in dependents[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, (int(child), child))

    if len(order) != len(ids):
        raise ValueError("input graph has a cycle")
    return order


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON on stdin: {exc}", file=sys.stderr)
        return 1
    try:
        result = toposort(payload)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
