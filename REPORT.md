# Skill Execution Benchmark — Report

**Date:** 2026-06-20
**Subject model:** Claude Opus (`opus`)
**Task:** Normalize task records (see [`AGENTS.md`](./AGENTS.md))
**Design:** 4 execution modes × 3 trials × 5 cases = **60 graded outputs**

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

### Reliability by mode

| Mode | Reliability | Passed / Total |
|------|------------:|---------------:|
| doc-only | **100.0%** | 15 / 15 |
| inline-code | **100.0%** | 15 / 15 |
| python-script | **100.0%** | 15 / 15 |
| go-binary | **100.0%** | 15 / 15 |

### Per-case pass count (passed trials / total trials)

| Case | doc-only | inline-code | python-script | go-binary |
|------|:--------:|:-----------:|:-------------:|:---------:|
| case-001 | 3/3 | 3/3 | 3/3 | 3/3 |
| case-002 | 3/3 | 3/3 | 3/3 | 3/3 |
| case-003 | 3/3 | 3/3 | 3/3 | 3/3 |
| case-004 | 3/3 | 3/3 | 3/3 | 3/3 |
| case-005 | 3/3 | 3/3 | 3/3 | 3/3 |

**No failures in any mode, case, or trial.**

Each case targeted a distinct normalization rule, all handled correctly:

| Case | Discriminator tested |
|------|----------------------|
| case-001 | trim + status mapping + id ordering |
| case-002 | status label variants (`WIP`, `to do`, `pending`) |
| case-003 | whitespace trim + case preservation in title |
| case-004 | numeric id ordering (10 sorts after 2, not before) |
| case-005 | optional field preserved, key order `id,title,status,…` |

## 4. Conclusion

**At Opus capability, Skill packaging does not affect execution reliability.**
The doc-only mode — reasoning entirely by hand with no code — matched the
script- and binary-backed modes perfectly across all 60 outputs. Opus correctly
handled every discriminator: numeric sorting, status mapping, trimming, key
ordering, and optional-field preservation.

In other words, for a task of this difficulty the result **hit the ceiling** for
all four modes; the benchmark cannot distinguish them at this model tier.

## 5. Limitations & next steps

To surface the differences this project is designed to measure, raise difficulty
until doc-only breaks first:

- **Weaker model (e.g. Haiku):** likely degrades doc-only (manual reasoning)
  before the script/binary modes, which only require correct invocation.
- **Harder dataset:** nested structures, large record counts, ambiguous status
  labels, adversarial whitespace/unicode.
- **More trials:** tighter reliability estimates once variance appears.

The scoring infrastructure (`harness/agent_eval.py`) and fairness protocol are
reusable as-is for those follow-ups.

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
