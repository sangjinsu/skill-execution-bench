# skill-execution-bench

**English** | [한국어](./README.ko.md)

A small, local-first benchmark that compares **four Skill execution patterns** for an LLM
coding agent. The benchmark holds the *task* constant (normalize a list of task records) and
varies only how the Skill packages its executable logic:

| Mode | Where the logic lives | How it runs |
|------|-----------------------|-------------|
| [`doc-only`](./skills/doc-only/SKILL.md) | Natural-language instructions only | Agent reasons and performs by hand |
| [`inline-code`](./skills/inline-code/SKILL.md) | A code block inside `SKILL.md` | Agent copies/executes the embedded code |
| [`python-script`](./skills/python-script/SKILL.md) | A separate [`transform.py`](./skills/python-script/scripts/transform.py) | Agent invokes the script (stdin/stdout) |
| [`go-binary`](./skills/go-binary/SKILL.md) | A compiled Go binary | Agent invokes the binary (stdin/stdout) |

The question this project answers:

> When an LLM agent uses a Skill, is it more reliable to provide only written instructions,
> inline executable code, a separate Python script, or a separate compiled Go binary?

See [`AGENTS.md`](./AGENTS.md) for the full specification and [`REPORT.md`](./REPORT.md) for results.

## Results at a glance

Real sub-agents, 10 trials each. **The three code modes (inline/python/go) score 100%
everywhere; only `doc-only` breaks.** How it breaks reveals two axes: input difficulty
sinks the weak model (Haiku normalize-hard **71.7%**), and operation depth sinks even the
strong one (Opus toposort **88.3%**).

[Jump to full results ↓](#real-agent-benchmark-results-summary) | [`REPORT.md`](./REPORT.md) | [한국어 리포트](./REPORT.ko.md)

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

## Real-agent benchmark results (summary)

Unlike `make bench` (a mechanical simulation that always passes), the real-agent
benchmark dispatches sub-agents that see only each mode's `SKILL.md` and grades
their output. See [`REPORT.md`](./REPORT.md) for the full tables and method.

**10-trial run:** 2 operations × 2 models × 4 modes × **10 trials** × 6 cases =
**160 dispatches / 960 graded cases**.

**The three code modes (inline/python/go) are 100% across all four cells and every
trial: 960/960. Only doc-only ever breaks.**

| Operation | Model | doc-only | inline / python / go |
|-----------|-------|:--------:|:--------------------:|
| normalize-hard | Haiku | **71.7%** | 100% |
| normalize-hard | Opus | **100%** | 100% |
| toposort | Haiku | **95.0%** | 100% |
| toposort | Opus | **88.3%** | 100% |

**Two orthogonal discrimination axes emerge:**

- The **input-difficulty** trap (normalize-hard) breaks *only the weak model*:
  Haiku 71.7% vs Opus 100%. Failures concentrate on hard-006 (empty title +
  duplicate id + internal double-space) **0/10** and hard-004 (optional-field
  trimming) **3/10**.
- The **operation-depth** trap (toposort) breaks *even the strong model*: Opus
  doc-only **88.3%**, dropping to **50% (5/10)** on the 12-node graph (topo-005).
  Model strength cannot save it.

So the strongest discrimination axis is the **algorithmic depth of the operation**,
not input difficulty. Once an operation goes beyond simple mapping/sorting into a
multi-step algorithm, script/binary packaging is a requirement, not a preference.

**Efficiency (10-trial averages):** doc-only always has the fewest tool calls (1),
making it cheapest, but only when accuracy holds. **In a fair comparison (binary
pre-built, build excluded), go-binary is the fastest code mode.** Toposort Opus:
go 27s (2 tool calls) vs python 39s (4); toposort Haiku: go 31s is fastest among
code modes. python-script is heaviest (6 to 10 tool calls from per-case stdin
round-trips). See [`REPORT.md`](./REPORT.md) for full tables.

## Requirements

- Python 3.11+
- Go 1.22+ (only for the `go-binary` mode)
- GNU Make

No Docker, no databases, no network access.
