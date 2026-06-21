---
id: skill.toposort-doc-only
name: Dependency Topological Sort (Doc Only)
execution_mode: doc-only
version: 0.1.0
---

# Dependency Topological Sort (Doc Only)

## When to use

Use this Skill when you need to order tasks so that every task comes after all of
its dependencies, and only written instructions are available. There is no reusable
code here — reason through the algorithm below and produce the order by hand.

## Inputs

- A JSON array of records, each `{"id": "<integer>", "deps": ["<id>", ...]}`.
- `deps` lists the ids that must come **before** this task (empty if none).
- Ids are unique integers; every dependency refers to an existing node (valid DAG,
  no cycles).

## Expected output

A JSON array of ids in a valid topological order. Output compact JSON (no spaces),
e.g. `["5","4","3","2","1"]`.

> Note: the topological order is usually **not** the same as sorting ids
> ascending. You must follow the dependencies.

## Procedure (Kahn's algorithm)

1. **Compute indegree** for every node = the number of its dependencies (length of
   its `deps` list).
2. **Ready set** = all nodes whose indegree is 0 (no remaining dependencies).
3. **Repeat until every node is placed:**
   a. Among the nodes currently in the ready set, pick the one with the
      **smallest numeric id** (e.g. `2` before `10`).
   b. Append that id to the output order and remove it from the ready set.
   c. For every node that listed the just-placed id in its `deps`, decrease its
      indegree by 1. If a node's indegree reaches 0, add it to the ready set.
4. The output is the sequence of ids in the order they were placed.

Track the indegrees and the ready set carefully as they change at each step — the
choice of "smallest ready id" is re-evaluated every iteration, not once.

### Worked example

Input:

```json
[{"id":"3","deps":["1","2"]},{"id":"1","deps":[]},{"id":"2","deps":["1"]}]
```

- indegree: 1→0, 2→1, 3→2. Ready = {1}.
- Place 1. Now 2's indegree → 0. Ready = {2}.
- Place 2. Now 3's indegree → 0. Ready = {3}.
- Place 3.

Output: `["1","2","3"]`

## Validation

- [ ] The result is a JSON array containing every input id exactly once.
- [ ] For every record, all of its `deps` appear **before** it in the output.
- [ ] Whenever multiple nodes were ready at the same time, the smaller numeric id
      comes first.
- [ ] The order is not assumed to be ascending id order — it follows dependencies.
