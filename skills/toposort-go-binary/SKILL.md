---
id: skill.toposort-go-binary
name: Dependency Topological Sort (Go Binary)
execution_mode: go-binary
version: 0.1.0
---

# Dependency Topological Sort (Go Binary)

## When to use

Use this Skill when you need a topological order of dependency records via a
compiled, standalone binary. Build it once, then run it rather than tracing the
algorithm by hand.

## Inputs

- A JSON array of records on **stdin**, each `{"id": "<integer>", "deps": ["<id>", ...]}`.
- `deps` lists ids that must come before this task (valid DAG, unique integer ids).

## Expected output

- A JSON array of ids on **stdout** (compact), in topological order; ties broken by
  smallest numeric id. Matches the Python script byte-for-byte. Deterministic.
- Exit code `0` on success, non-zero on invalid input or a cycle.

## Procedure

1. Build the binary (standard library only):

   ```bash
   go build -o skills/toposort-go-binary/bin/toposort-runner ./skills/toposort-go-binary/cmd/toposort-runner
   ```

   (or `make build-go`)

2. Run it, piping input JSON to stdin:

   ```bash
   skills/toposort-go-binary/bin/toposort-runner < input.json > output.json
   ```

   ```bash
   echo '[{"id":"3","deps":["1","2"]},{"id":"1","deps":[]},{"id":"2","deps":["1"]}]' \
     | skills/toposort-go-binary/bin/toposort-runner
   # -> ["1","2","3"]
   ```

Build first, then invoke the binary. Do not reimplement the logic by hand.

## Validation

- [ ] `skills/toposort-go-binary/bin/toposort-runner` exists (binary was built).
- [ ] Output parses as a JSON array containing every id exactly once.
- [ ] Every node's dependencies precede it; ties broken by smallest numeric id.
- [ ] Output matches the Python-script output for the same input.
- [ ] A cyclic or malformed input causes a non-zero exit code.
