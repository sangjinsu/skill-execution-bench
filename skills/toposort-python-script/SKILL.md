---
id: skill.toposort-python-script
name: Dependency Topological Sort (Python Script)
execution_mode: python-script
version: 0.1.0
---

# Dependency Topological Sort (Python Script)

## When to use

Use this Skill when you need a topological order of dependency records and a
reusable Python script is the preferred execution path. Run the bundled script
rather than re-deriving the algorithm.

## Inputs

- A JSON array of records on **stdin**, each `{"id": "<integer>", "deps": ["<id>", ...]}`.
- `deps` lists ids that must come before this task (valid DAG, unique integer ids).

## Expected output

- A JSON array of ids on **stdout** (compact), in topological order; ties broken by
  smallest numeric id. Deterministic.
- Exit code `0` on success, non-zero on invalid input or a cycle.

## Procedure

Run the bundled script, piping the input JSON to stdin and capturing stdout:

```bash
python skills/toposort-python-script/scripts/toposort.py < input.json > output.json
```

```bash
echo '[{"id":"3","deps":["1","2"]},{"id":"1","deps":[]},{"id":"2","deps":["1"]}]' \
  | python skills/toposort-python-script/scripts/toposort.py
# -> ["1","2","3"]
```

Do not reimplement the algorithm inline — invoke the script so behavior stays
consistent and testable.

## Validation

- [ ] Output parses as a JSON array containing every id exactly once.
- [ ] Every node's dependencies precede it in the output.
- [ ] Ties are broken by smallest numeric id.
- [ ] A cyclic or malformed input causes a non-zero exit code.
