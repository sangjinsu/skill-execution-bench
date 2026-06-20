"""Tests for the real-agent benchmark evaluator (synthetic runs, no live LLM)."""

from __future__ import annotations

import json

from harness.agent_eval import load_runs, score_runs, write_traces

EXPECTED = {
    "case-001": [{"id": "1", "title": "A", "status": "todo"}],
    "case-002": [{"id": "2", "title": "B", "status": "done"}],
}


def _run(mode, trial, outputs):
    return {"mode": mode, "trial": trial, "model": "test", "outputs": outputs}


def test_all_correct_is_full_reliability():
    runs = [_run("python-script", 1, EXPECTED)]
    results = score_runs(runs, EXPECTED)
    assert all(r.passed for r in results)
    assert len(results) == 2


def test_partial_correct():
    outputs = {
        "case-001": EXPECTED["case-001"],
        "case-002": [{"id": "2", "title": "B", "status": "doing"}],  # wrong status
    }
    results = score_runs([_run("doc-only", 1, outputs)], EXPECTED)
    passed = {r.case_id: r.passed for r in results}
    assert passed["case-001"] is True
    assert passed["case-002"] is False


def test_missing_output_counts_as_failure():
    results = score_runs([_run("doc-only", 1, {"case-001": EXPECTED["case-001"]})], EXPECTED)
    by_case = {r.case_id: r for r in results}
    assert by_case["case-002"].passed is False
    assert by_case["case-002"].error == "no output produced"


def test_non_array_output_counts_as_failure():
    results = score_runs([_run("doc-only", 1, {"case-001": {"not": "a list"}, "case-002": EXPECTED["case-002"]})], EXPECTED)
    by_case = {r.case_id: r for r in results}
    assert by_case["case-001"].passed is False
    assert "not a JSON array" in by_case["case-001"].error


def test_key_order_does_not_affect_pass():
    reordered = {"case-001": [{"status": "todo", "title": "A", "id": "1"}]}
    results = score_runs([_run("inline-code", 1, reordered)], {"case-001": EXPECTED["case-001"]})
    assert results[0].passed is True


def test_load_runs_reads_directory(tmp_path):
    (tmp_path / "doc-only-trial1.json").write_text(
        json.dumps(_run("doc-only", 1, EXPECTED)), encoding="utf-8"
    )
    (tmp_path / "go-binary-trial1.json").write_text(
        json.dumps(_run("go-binary", 1, EXPECTED)), encoding="utf-8"
    )
    runs = load_runs(tmp_path)
    assert len(runs) == 2
    assert {r["mode"] for r in runs} == {"doc-only", "go-binary"}


def test_write_traces_roundtrip(tmp_path):
    results = score_runs([_run("doc-only", 1, EXPECTED)], EXPECTED)
    trace = tmp_path / "agent-bench.jsonl"
    write_traces(results, trace)
    lines = [json.loads(l) for l in trace.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert all("passed" in row for row in lines)
