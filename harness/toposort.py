"""Reference implementation of the dependency topological-sort operation.

This is the canonical, deterministic implementation the topological-sort
benchmark is built around. Like the normalization reference, it is duplicated
(by design) in the inline-code SKILL, the python-script, and the Go binary so
every execution mode can be compared against the same expected output.

Contract:
- Input: a JSON array of records, each ``{"id": <int-string>, "deps": [<id>, ...]}``.
  Ids are unique integer strings; deps reference existing nodes (a valid DAG).
- Output: a list of ids in topological order. When several nodes are ready at
  once, the one with the smallest numeric id is emitted first (Kahn + min-heap),
  making the order fully deterministic.
- A cycle (or an unresolvable graph) raises ValueError.
"""

from __future__ import annotations

import heapq
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
    indegree: dict[str, int] = {n: 0 for n in ids}
    dependents: dict[str, list[str]] = {n: [] for n in ids}
    for node in ids:
        for dep in deps_of[node]:
            if dep not in node_set:
                raise ValueError(f"unknown dependency '{dep}' for node '{node}'")
            indegree[node] += 1
            dependents[dep].append(node)

    def key(node: str) -> int:
        return int(node)

    ready: list[tuple[int, str]] = [(key(n), n) for n in ids if indegree[n] == 0]
    heapq.heapify(ready)

    order: list[str] = []
    while ready:
        _, node = heapq.heappop(ready)
        order.append(node)
        for child in dependents[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, (key(child), child))

    if len(order) != len(ids):
        raise ValueError("input graph has a cycle")
    return order
