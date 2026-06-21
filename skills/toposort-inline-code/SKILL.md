---
id: skill.toposort-inline-code
name: Dependency Topological Sort (Inline Code)
execution_mode: inline-code
version: 0.1.0
---

# Dependency Topological Sort (Inline Code)

## When to use

Use this Skill when you need to order tasks so each comes after its dependencies,
and the executable logic is embedded in this document. Copy, adapt, and run the
code block below rather than tracing the algorithm by hand.

## Inputs

- A JSON array of records, each `{"id": "<integer>", "deps": ["<id>", ...]}`.
- `deps` lists ids that must come before this task (valid DAG, unique integer ids).

## Expected output

A list of ids in topological order; when several nodes are ready, the smallest
numeric id comes first. Deterministic.

## Procedure

Use the `toposort` function defined in the following code block. It is
self-contained and deterministic — paste it into your runtime and call
`toposort(records)`.

```python
import heapq


def toposort(records):
    if not isinstance(records, list):
        raise ValueError("input must be a JSON array")

    ids = []
    deps_of = {}
    for record in records:
        if not isinstance(record, dict) or "id" not in record:
            raise ValueError("each record must be an object with an 'id'")
        node = str(record["id"]).strip()
        raw_deps = record.get("deps", []) or []
        deps = [str(d).strip() for d in raw_deps]
        if node in deps_of:
            raise ValueError("duplicate id: " + node)
        ids.append(node)
        deps_of[node] = deps

    node_set = set(ids)
    indegree = {n: 0 for n in ids}
    dependents = {n: [] for n in ids}
    for node in ids:
        for dep in deps_of[node]:
            if dep not in node_set:
                raise ValueError("unknown dependency: " + dep)
            indegree[node] += 1
            dependents[dep].append(node)

    ready = [(int(n), n) for n in ids if indegree[n] == 0]
    heapq.heapify(ready)

    order = []
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
```

To run it end-to-end over stdin:

```python
import json, sys
print(json.dumps(toposort(json.load(sys.stdin)), ensure_ascii=False, separators=(",", ":")))
```

## Validation

- [ ] `toposort` returns a list with every id exactly once.
- [ ] Every node's dependencies precede it.
- [ ] Ties are broken by smallest numeric id.
- [ ] A cyclic graph raises `ValueError`.
