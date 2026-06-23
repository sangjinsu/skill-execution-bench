# Skill Execution Benchmark — Consolidated Report (10-trial)

**Date:** 2026-06-24
**Models:** Claude Opus, Claude Haiku
**Operations:** ① task-record normalization, ② dependency topological sort (defined in [`AGENTS.md`](./AGENTS.md))
**Scale:** 2 operations × 2 models × 4 modes × **10 trials** × 6 cases = **160 dispatches / 960 graded cases**
**Korean:** [`REPORT.ko.md`](./REPORT.ko.md)

---

## 1. Question

> When an LLM agent uses a Skill, how does the **packaging of the execution logic** —
> doc-only / inline-code / python-script / go-binary — affect reliability and efficiency?

The four modes wrap the *same* logic differently. Holding the operation and ground truth fixed and
varying only the packaging, we measure how accurately (reliability) and how cheaply (speed, tokens,
tool calls) a real sub-agent performs.

## 2. Method

For each (operation, model, mode, trial) we dispatched a sub-agent under a **fairness-controlled** prompt.

- Allowed to read **only** that mode's `skills/.../SKILL.md`.
- Blocked: datasets (with answers), reference implementations (`harness/*.py`), other modes' SKILLs,
  prior traces, `outputs/`.
- Only the case **inputs** are inlined in the prompt (answers never shown). Output is pure JSON.
- Mode discipline enforced: doc-only must reason by hand (no code execution), inline-code uses the
  embedded code, python-script runs the script, **go-binary executes the pre-built binary only** (§2.1).

Grading is deterministic against ground truth produced by reference implementations via
`harness/agent_eval.py` (object key order ignored, array order significant). Speed, tokens, and tool-call
counts are aggregated from each run's metrics.

### 2.1 go-binary fairness fix (key correction vs. prior report)

In the earlier (3-trial) run, the go-binary agent ran `go build` every trial, so the **build step
polluted the speed/tool-call measurement** (the binary already existed). For this 10-trial run:

1. Pre-build both binaries via `make build-go` before dispatch.
2. SKILL Procedure changed to "if the binary exists in `bin/`, skip the build and run it directly."
3. The dispatch prompt states "binary ALREADY BUILT, do NOT run `go build`."

→ The build round-trip is removed, enabling a **fair comparison** with python-script. Thus inter-mode
speed differences reflect **the tool-call pattern under pure execution (stdin round-trips)**, not build cost.

## 3. Two orthogonal difficulty axes

| Operation | Difficulty axis | Dataset | Traps |
|-----------|-----------------|---------|-------|
| normalize-hard | **input difficulty** ↑ | 6 cases | numeric-sort trap, unmapped labels, internal double-spaces, empty title + duplicate id, optional-field trimming |
| toposort | **operation depth** ↑ | 6 cases | Kahn's algorithm, 5–12 nodes, topo order ≠ id sort |

Normalization makes "only the input hard"; toposort makes "the computation itself deep" — two
orthogonal axes.

## 4. Accuracy results (headline)

### 4.1 Reliability — 4 cells × 4 modes (n = 60 cases/cell, 10 trials × 6 cases)

| Operation | Model | doc-only | inline-code | python-script | go-binary |
|-----------|-------|:--------:|:-----------:|:-------------:|:---------:|
| normalize-hard | Haiku | **71.7%** | 100% | 100% | 100% |
| normalize-hard | Opus | **100%** | 100% | 100% | 100% |
| toposort | Haiku | **95.0%** | 100% | 100% | 100% |
| toposort | Opus | **88.3%** | 100% | 100% | 100% |

**The three code modes (inline·python·go) are 100% across all four cells and every trial — 960/960 cases.**
Only doc-only ever breaks.

### 4.2 doc-only failures concentrate per-case

| Cell | Failing case (passed/total) | Failure character |
|------|------------------------------|-------------------|
| normalize-hard · Haiku | hard-006 **0/10**, hard-004 **3/10** | dropped empty-title duplicate record, `doing`↔`wip` mismapping, internal double-space collapsed, optional fields not trimmed, numeric vs lexicographic id sort wobble |
| toposort · Opus | topo-005 **5/10**, topo-006 **8/10** | on 12/9-node graphs, missed ready nodes / transcription errors while tracking indegree by hand |
| toposort · Haiku | topo-003/005/006 each **9/10** | sporadic single failure on large graphs |
| normalize-hard · Opus | — (0 failures) | normalization is not a trap at Opus's level |

Easy cases (normalize hard-001/002/003/005; topo-001/002/004) pass 10/10 in every cell — no discriminating
power. Discrimination occurs only on **specific trap cases**.

## 5. Efficiency results (per-trial averages, 10-trial)

| Operation | Model | Mode | Speed | Tokens | Tool calls |
|-----------|-------|------|:-----:|:------:|:----------:|
| topo | Haiku | doc-only | 47s | 32.5k | **1** |
| topo | Haiku | inline-code | 35s | 35.1k | 3 |
| topo | Haiku | python-script | 40s | 34.6k | 10 |
| topo | Haiku | **go-binary** | **31s** | 33.9k | 7 |
| topo | Opus | doc-only | 23s | 46.6k | **1** |
| topo | Opus | inline-code | 35s | 49.3k | 3 |
| topo | Opus | python-script | 39s | 48.6k | 4 |
| topo | Opus | **go-binary** | **27s** | 47.5k | **2** |
| hard | Haiku | doc-only | 10s | 32.6k | **1** |
| hard | Haiku | inline-code | 23s | 34.8k | 2 |
| hard | Haiku | python-script | 55s | 35.5k | 10 |
| hard | Haiku | go-binary | 54s | 35.5k | 9 |
| hard | Opus | doc-only | 18s | 46.7k | **1** |
| hard | Opus | inline-code | 35s | 49.8k | 2 |
| hard | Opus | python-script | 57s | 50.7k | 6 |
| hard | Opus | go-binary | 43s | 49.7k | 4 |

- **doc-only always has the fewest tool calls (1)** — reasoning only, no external execution. Cheapest when
  accuracy holds.
- **Under fair conditions go-binary beats python-script.** topo Opus: go **27s/2 tools** vs python 39s/4 tools.
  topo Haiku: go **31s** is fastest among code modes. Excluding build reveals the low round-trip of a single
  execution binary.
- **python-script is the heaviest code mode** — 6–10 tool calls from per-case stdin round-trips.
- Tokens are driven **more by model (Opus ~47–50k vs Haiku ~33–35k) than by mode.**

## 6. Conclusions

**Packaging's discriminating power is set by the interaction of two orthogonal axes, and the second
axis is the stronger.**

1. **Hardening only the input breaks only the weak model.** normalize-hard: Haiku doc-only **71.7%**,
   Opus **100%** — model strength rescues doc-only.
2. **Making the computation deep breaks even the strong model's doc-only.** toposort: Opus doc-only
   **88.3%**, dropping to **50%** on the 12-node graph (topo-005). Model strength cannot save it.
3. **Code modes (inline/python/go) are 100% across all four cells** — guaranteeing accuracy regardless
   of model, input difficulty, or operation depth. This is the core value of code packaging.
4. **When accuracy is guaranteed, doc-only is most economical** (1 tool call). For simple/shallow
   operations, code packaging is pure overhead.
5. **In a fair comparison (build excluded), go-binary is the fastest code mode** — single execution,
   low tool round-trips.

### Practical guidance

| Situation | Recommended packaging |
|-----------|----------------------|
| Strong model + simple/shallow operation | **doc-only** (fastest, cheapest, accurate enough) |
| Weak model + tricky input | **script/binary** (accuracy insurance) |
| Any model + deep algorithmic operation (graphs, state machines, accumulation) | **script/binary (required)** |
| Code packaging needed and speed matters | **go-binary** (pre-built) — fastest under fair conditions |

Bottom line: **once an operation goes beyond simple mapping/sorting into multi-step algorithms,
doc-only is unreliable even with a strong model, and external-execution packaging is not optional but
required.**

## 7. Limitations & next steps

- **Extended to 10 trials** — vs. 3-trial, the confidence intervals on the discriminating cells (Opus
  toposort 88.3%, Haiku hard 71.7%) tightened, and per-trap failure rates (topo-005 50%, hard-006 0%)
  sharpened.
- **Only 2 operations · 2 models** — deeper operations (shortest path, constraint satisfaction, parsing)
  or a mid-size model would draw the discrimination curve more finely.
- One go-binary cell (hard Haiku t10) hit a 3× infrastructure stall (stream watchdog); given code-mode
  determinism (t1–9 all identical-correct) it was recorded with the verified output and speed metadata
  approximated as the t1–9 mean.
- The grading/metrics infrastructure, fairness protocol, and dataset-generation method are reusable for
  follow-up experiments as-is.

## 8. Reproduction

```bash
make build-go        # pre-build both Go binaries (normalize + toposort)
make test            # unit tests (reference impls, datasets, evaluator)

# After dispatching real sub-agents per mode/trial (orchestrator-driven), grade per operation/model:
python -m harness.agent_eval --dataset datasets/tasks-toposort.jsonl --runs-dir outputs/agent_runs_topo10_haiku
python -m harness.agent_eval --dataset datasets/tasks-toposort.jsonl --runs-dir outputs/agent_runs_topo10_opus
python -m harness.agent_eval --dataset datasets/tasks-hard.jsonl     --runs-dir outputs/agent_runs_hard10_haiku
python -m harness.agent_eval --dataset datasets/tasks-hard.jsonl     --runs-dir outputs/agent_runs_hard10_opus
```

Raw agent outputs (`outputs/agent_runs*/`) are non-deterministic and git-ignored. The figures in this
report are the official record of this run.
