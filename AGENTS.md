# AGENTS.md

## Project

Project name: `skill-execution-bench`

This repository is a benchmark and testbed for comparing how an LLM coding agent uses a Skill when the executable logic is provided in different forms.

This project is separate from any context-loader or storage-backend benchmark. Do not benchmark SQLite, vector search, manifest loading, or instruction retrieval here. This project focuses only on Skill execution patterns after the Skill has already been selected and loaded.

## Primary Goal

Build a small, repeatable project that compares four Skill execution patterns:

1. **Doc-only Skill**
   - The Skill document contains natural-language instructions only.
   - The LLM must reason from the document and perform the task without reusable embedded code.

2. **Inline-code Skill**
   - The Skill document contains executable code blocks.
   - The LLM may copy, adapt, and execute code from the Skill document.

3. **Python-script Skill**
   - The Skill document explains when and how to use a separate Python script.
   - The reusable implementation lives in a `.py` file under the Skill directory.

4. **Go-binary Skill**
   - The Skill document explains when and how to use a compiled Go binary.
   - The reusable implementation is written in Go and built into a binary before execution.

The benchmark should help evaluate which Skill packaging pattern is most reliable, repeatable, and useful when a real LLM coding agent performs tasks.

## Non-goals

Do not turn this project into a benchmark report generator unless explicitly requested.
Do not compare storage backends such as SQLite, JSON stores, vector databases, or file-system indexing in this project.
Do not build a large agent platform.
Do not require Docker, Kubernetes, cloud services, or external services.
Do not use network calls in the default benchmark path.

## Preferred Tech Stack

Use a simple local-first stack:

- Python 3.11+ for the test harness and evaluators.
- Go 1.22+ for the binary-based Skill implementation.
- Markdown for Skill documents.
- JSONL or JSON for datasets and traces.
- Standard library first. Add dependencies only when they materially simplify the project.

Prefer commands that work on macOS and Linux.

## Repository Structure

Use this structure unless there is a strong reason to change it:

```text
skill-execution-bench/
  AGENTS.md
  README.md
  pyproject.toml
  Makefile

  skills/
    doc-only/
      SKILL.md

    inline-code/
      SKILL.md

    python-script/
      SKILL.md
      scripts/
        transform.py

    go-binary/
      SKILL.md
      cmd/
        skill-runner/
          main.go
      bin/
        .gitkeep

  datasets/
    tasks.jsonl

  harness/
    __init__.py
    models.py
    runners.py
    evaluators.py
    run_benchmark.py

  outputs/
    traces/
      .gitkeep

  tests/
    test_runners.py
    test_evaluators.py
    test_dataset.py
```

## Benchmark Task Design

Use simple deterministic tasks so that differences come from Skill execution style rather than task ambiguity.

Recommended starter task:

```text
Normalize a list of task records.

Input:
- JSON array or JSONL records
- Each record may contain inconsistent casing, whitespace, missing optional fields, or mixed status labels.

Output:
- Normalized JSON array
- Stable key order
- Trimmed strings
- Lowercase status
- Mapped status values
- Deterministic ordering by id
```

Example status mapping:

```text
"todo", "to do", "pending" -> "todo"
"doing", "in progress", "wip" -> "doing"
"done", "complete", "completed" -> "done"
```

This task is intentionally small. The goal is not to test algorithmic difficulty, but to test whether each Skill execution pattern helps the LLM perform the same operation reliably.

## Dataset Format

Use JSONL for benchmark cases:

```jsonl
{"id":"case-001","input":[{"id":" 2 ","title":" Fix Login ","status":"In Progress"},{"id":"1","title":"Write Tests","status":"complete"}],"expected":[{"id":"1","title":"Write Tests","status":"done"},{"id":"2","title":"Fix Login","status":"doing"}]}
```

Each dataset row should include:

- `id`: stable case id.
- `input`: input payload.
- `expected`: expected normalized output.
- Optional `notes`: human-readable notes.

Keep the dataset small at first. Start with 5 to 10 cases.

## Skill Document Rules

Every `SKILL.md` must include:

```markdown
---
id: skill.<name>
name: <Human readable name>
execution_mode: doc-only | inline-code | python-script | go-binary
version: 0.1.0
---

# <Skill Name>

## When to use

## Inputs

## Expected output

## Procedure

## Validation
```

The Skill document is the agent-facing interface. Even when executable code exists in Python or Go, the Skill document must explain when to use it and what output contract to expect.

## Execution Modes

### 1. Doc-only Skill

The doc-only Skill must contain instructions but no reusable implementation code.

Allowed:

- Natural-language rules.
- Examples.
- Validation checklist.

Not allowed:

- Full executable Python implementation.
- Full shell script.
- Full Go implementation.

The LLM should perform the task based on the written procedure.

### 2. Inline-code Skill

The inline-code Skill may contain executable code blocks directly inside `SKILL.md`.

Allowed:

- Python code block.
- Shell command block.
- Small helper function embedded in the document.

The harness should extract or allow the agent to use the inline code in a controlled way.

Make the inline code small and deterministic.

### 3. Python-script Skill

The Python-script Skill must place reusable logic in:

```text
skills/python-script/scripts/transform.py
```

The script should support stdin/stdout:

```bash
python skills/python-script/scripts/transform.py < input.json > output.json
```

The script must:

- Read JSON from stdin.
- Write JSON to stdout.
- Exit non-zero on invalid input.
- Avoid network access.
- Avoid nondeterminism.

### 4. Go-binary Skill

The Go-binary Skill must place reusable logic in:

```text
skills/go-binary/cmd/skill-runner/main.go
```

Build the binary into:

```text
skills/go-binary/bin/skill-runner
```

Recommended command:

```bash
go build -o skills/go-binary/bin/skill-runner ./skills/go-binary/cmd/skill-runner
```

The binary should support stdin/stdout:

```bash
skills/go-binary/bin/skill-runner < input.json > output.json
```

The binary must:

- Read JSON from stdin.
- Write JSON to stdout.
- Exit non-zero on invalid input.
- Avoid network access.
- Avoid nondeterminism.
- Use only the Go standard library unless there is a clear reason to add dependencies.

## Harness Requirements

The harness should run the same dataset through each execution mode.

Implement a common runner interface similar to:

```python
class SkillRunner:
    name: str
    execution_mode: str

    def run(self, payload: object) -> object:
        ...
```

Recommended runners:

```text
DocOnlyRunner
InlineCodeRunner
PythonScriptRunner
GoBinaryRunner
```

Important distinction:

- The harness may simulate the mechanical execution path.
- The project is ultimately intended for real LLM coding-agent evaluation.
- Keep interfaces clear so that later a real agent can be asked to use each Skill and produce outputs.

## Evaluation

Use strict deterministic evaluation.

A case passes only when actual output exactly matches `expected` after JSON parsing.

Evaluator responsibilities:

- Compare parsed JSON values.
- Report pass/fail per case.
- Record error messages.
- Record execution mode.
- Record whether external code or binary was used.

Do not over-optimize for pretty benchmark reporting. Basic console output and JSONL traces are enough.

## Minimal Trace Format

Store traces under:

```text
outputs/traces/
```

Each trace row may use this shape:

```json
{
  "case_id": "case-001",
  "runner": "python-script",
  "execution_mode": "python-script",
  "passed": true,
  "error": null
}
```

Trace data is for debugging and comparison. Do not build dashboard/reporting features unless requested.

## CLI Commands

Provide simple commands through a Makefile.

Recommended commands:

```bash
make setup
make test
make build-go
make bench
make clean
```

Expected behavior:

```bash
make setup
```

Prepare local Python environment if needed.

```bash
make build-go
```

Build the Go binary.

```bash
make test
```

Run unit tests.

```bash
make bench
```

Run all benchmark cases against all execution modes.

```bash
make clean
```

Remove generated outputs and Go binaries.

## Testing Requirements

Add tests for:

- Dataset loading.
- JSON normalization evaluator.
- Python script execution.
- Go binary build and execution when Go is available.
- Failure handling for invalid input.

Tests should not require a live LLM.

When Go is not installed, Go-specific tests may be skipped with a clear message.

## Coding Guidelines

Keep implementation small and readable.

Prefer simple modules over complex frameworks.

Do not introduce a web server.
Do not introduce a database unless explicitly requested.
Do not add Docker unless explicitly requested.
Do not create generated benchmark reports unless explicitly requested.

Use type hints in Python where helpful.
Use clear error messages.
Keep paths relative to the repository root.

## Safety and Execution Rules

All executable examples must be local-only and deterministic.

Do not execute arbitrary code from untrusted input.
Do not add network access to Skills.
Do not read or write outside the repository except temporary files created by tests.
Do not require secrets or API keys.

## Agent Workflow

When a coding agent works in this repository, follow this order:

1. Read this `AGENTS.md` first.
2. Inspect `README.md` if present.
3. Inspect the relevant `skills/*/SKILL.md` files.
4. Implement the smallest useful scaffold first.
5. Add or update tests with each implementation step.
6. Run `make test`.
7. Build the Go binary with `make build-go` when touching Go code.
8. Run `make bench` after all runners are available.
9. Summarize what changed and which commands were run.

## Recommended Implementation Order

1. Create repository skeleton.
2. Add dataset with 5 deterministic cases.
3. Implement shared normalization logic in test helpers or evaluator only as needed.
4. Implement Python-script Skill.
5. Implement Go-binary Skill.
6. Implement Inline-code Skill.
7. Implement Doc-only Skill baseline.
8. Implement harness runner interface.
9. Add unit tests.
10. Add Makefile commands.
11. Run tests and fix failures.

## Acceptance Criteria

The project is considered minimally complete when:

- All four Skill execution modes exist.
- Each mode has a `SKILL.md`.
- Python-script mode has an executable Python script.
- Go-binary mode has Go source and a build command.
- The harness can run the same dataset against all modes.
- Tests can validate the deterministic output.
- `make test` passes.
- `make bench` runs locally.

## Important Design Principle

This project should answer this question:

```text
When an LLM agent uses a Skill, is it more reliable to provide only written instructions, inline executable code, a separate Python script, or a separate compiled Go binary?
```

Optimize the project for answering that question clearly.
