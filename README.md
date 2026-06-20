# skill-execution-bench

A small, local-first benchmark that compares **four Skill execution patterns** for an LLM
coding agent. The benchmark holds the *task* constant (normalize a list of task records) and
varies only how the Skill packages its executable logic:

| Mode | Where the logic lives | How it runs |
|------|-----------------------|-------------|
| `doc-only` | Natural-language instructions only | Agent reasons and performs by hand |
| `inline-code` | A code block inside `SKILL.md` | Agent copies/executes the embedded code |
| `python-script` | A separate `transform.py` | Agent invokes the script (stdin/stdout) |
| `go-binary` | A compiled Go binary | Agent invokes the binary (stdin/stdout) |

The question this project answers:

> When an LLM agent uses a Skill, is it more reliable to provide only written instructions,
> inline executable code, a separate Python script, or a separate compiled Go binary?

See [`AGENTS.md`](./AGENTS.md) for the full specification.

## The task: normalize task records

Each runner takes a JSON array of task records (with inconsistent casing, whitespace, and
status labels) and produces a normalized array. The contract is:

1. Trim all string values.
2. `id` → trimmed string.
3. `status` → trimmed, lowercased, then mapped:
   - `todo, to do, pending` → `todo`
   - `doing, in progress, wip` → `doing`
   - `done, complete, completed` → `done`
   - unknown values keep their lowercased/trimmed form.
4. Other fields → trimmed.
5. Missing optional fields are not added.
6. Stable key order per object: `id`, `title`, `status`, then remaining keys alphabetically.
7. Array sorted by `id` (numeric when all ids are integers, else lexicographic).

All four modes implement this identical contract, so they produce byte-identical compact JSON.

## Layout

```
skills/        doc-only | inline-code | python-script | go-binary  (each has a SKILL.md)
datasets/      tasks.jsonl   (5 deterministic cases)
harness/       runners, evaluator, benchmark driver, reference normalizer
outputs/       traces/       (JSONL benchmark traces)
tests/         unit tests (pytest)
```

## Commands

```bash
make setup       # install pytest (best effort)
make build-go    # build skills/go-binary/bin/skill-runner
make test        # run unit tests (Go tests skip if Go/binary unavailable)
make bench       # run all 4 modes against every case, write traces, print a summary
make clean       # remove the Go binary and generated traces
```

### Quick smoke test

```bash
echo '[{"id":" 2 ","title":" Fix Login ","status":"In Progress"}]' \
  | python3 skills/python-script/scripts/transform.py
# -> [{"id":"2","title":"Fix Login","status":"doing"}]
```

## Requirements

- Python 3.11+
- Go 1.22+ (only for the `go-binary` mode)
- GNU Make

No Docker, no databases, no network access.
