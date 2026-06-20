# Skill Execution Benchmark — Report

**Date:** 2026-06-20
**Subject models:** Claude Opus, Claude Haiku
**Task:** Normalize task records (see [`AGENTS.md`](./AGENTS.md))
**Design:** 4 execution modes × 3 trials × 5 cases = **60 graded outputs per model** (120 total)

> Korean version: [`REPORT.ko.md`](./REPORT.ko.md)

## 1. Question

> When an LLM agent uses a Skill, is it more reliable to provide only written
> instructions, inline executable code, a separate Python script, or a separate
> compiled Go binary?

Each mode packages the *same* normalization logic differently. We hold the task
constant and vary only the Skill packaging, then measure how reliably a real
sub-agent produces correct output.

## 2. Method

For every (mode, trial) pair an Opus sub-agent was dispatched with a
fairness-controlled prompt:

- It could read **only** that mode's `skills/<mode>/SKILL.md`.
- Forbidden to read `datasets/tasks.jsonl` (which contains the answers),
  `harness/normalize.py` (the reference implementation), other modes' Skills,
  or prior traces.
- The 5 case **inputs** were inlined in the prompt; expected outputs were never shown.
- Mode-specific execution was enforced:
  - `doc-only` — reason by hand, no code execution allowed.
  - `inline-code` — use the Python block embedded in the SKILL.
  - `python-script` — run `skills/python-script/scripts/transform.py`.
  - `go-binary` — build and run `skills/go-binary/bin/skill-runner`.
- Each agent returned a pure JSON object `{case_id: [...]}`.

Outputs were scored deterministically by `harness/agent_eval.py` against the
dataset's `expected` values (object key order ignored, array order significant).
Any missing or non-array output counts as a failure for that case.

> Note: the mechanical `make bench` always passes by construction (it executes
> the real code path). This report instead measures **real agent behaviour**,
> which is the project's actual goal.

## 3. Results

### 3.1 Reliability (both models)

| Mode | Opus | Haiku |
|------|-----:|------:|
| doc-only | **100%** (15/15) | **100%** (15/15) |
| inline-code | **100%** (15/15) | **100%** (15/15) |
| python-script | **100%** (15/15) | **100%** (15/15) |
| go-binary | **100%** (15/15) | **100%** (15/15) |

**No failures in any model, mode, case, or trial.** Even the weaker model (Haiku)
did not break on doc-only, so the accuracy axis **hit the ceiling**. Each case
targeted a distinct discriminator (status mapping, numeric id ordering, trim, key
order, optional fields) — all handled correctly by both models.

### 3.2 Speed (avg seconds per trial)

| Mode | Opus | Haiku |
|------|-----:|------:|
| doc-only | **11s** | **18s** |
| inline-code | 24s | 34s |
| python-script | 35s | 48s |
| go-binary | 25s | 30s |

### 3.3 Tokens (avg per trial)

| Mode | Opus | Haiku |
|------|------:|------:|
| doc-only | **46,191** | **32,232** |
| inline-code | 47,849 | 34,014 |
| python-script | 48,104 | 33,919 |
| go-binary | 47,118 | 33,201 |

### 3.4 Tool calls (avg per trial)

| Mode | Opus | Haiku |
|------|-----:|------:|
| doc-only | **1** | **1** |
| inline-code | 3 | 4 |
| python-script | 8 | 10 |
| go-binary | 3 | 7 |

## 4. Conclusion

**At this task difficulty, packaging does not separate the modes on accuracy** —
both Opus and Haiku scored 120/120. The real differentiator is **efficiency**:

- **doc-only is the cheapest and fastest** when accuracy holds: pure reasoning,
  one tool call, lowest time and tokens. Running code cost *more* than reasoning
  for this simple, deterministic transform.
- **python-script is the heaviest** — per-case stdin round-trips push it to 8–10
  tool calls and the slowest wall time.
- **go-binary amortizes a one-time build** and then runs fast, beating python-script.
- This flips as an **insurance argument**: once a task gets hard enough that
  doc-only's hand-computation starts to slip, the script/binary modes keep
  accuracy by *just invoking the right tool*. The harder the task, the more the
  external-execution packaging earns its overhead.

## 5. Limitations & next steps

Haiku also hitting the ceiling means **task difficulty is the bottleneck** for
discrimination. To surface packaging differences in accuracy:

- **Harder dataset:** nested structures, large record counts, ambiguous/conflicting
  status labels, adversarial whitespace/unicode — make doc-only break first.
- **More trials:** tighter confidence intervals once variance appears.

The scoring/metrics infrastructure (`harness/agent_eval.py`) and fairness protocol
are reusable as-is for those follow-ups.

## 6. Reproducing

```bash
# 1. Build the Go binary used by the go-binary mode
make build-go

# 2. (Dispatch real sub-agents per mode/trial — orchestrator-driven; see method.)
#    Each run is stored as outputs/agent_runs/<mode>-trial<N>.json

# 3. Score the collected runs
python -m harness.agent_eval
#    -> prints the tables above, writes outputs/traces/agent-bench.jsonl
```

Raw agent outputs (`outputs/agent_runs/`) are git-ignored as non-deterministic;
the numbers in this report are the canonical record of this run.
