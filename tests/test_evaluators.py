"""Tests for the deterministic evaluator."""

from __future__ import annotations

from harness.evaluators import evaluate_case, outputs_match
from harness.models import Case
from harness.runners import SkillRunner


class _StubRunner(SkillRunner):
    name = "stub"
    execution_mode = "stub"

    def __init__(self, output=None, exc=None):
        self._output = output
        self._exc = exc

    def run(self, payload):
        if self._exc is not None:
            raise self._exc
        return self._output


def test_outputs_match_is_order_insensitive_for_keys():
    assert outputs_match({"a": 1, "b": 2}, {"b": 2, "a": 1})


def test_outputs_match_is_order_sensitive_for_lists():
    assert not outputs_match([1, 2], [2, 1])


def test_evaluate_case_pass():
    case = Case(id="c1", input=[], expected=[{"id": "1"}])
    runner = _StubRunner(output=[{"id": "1"}])
    row = evaluate_case(runner, case)
    assert row.passed
    assert row.error is None
    assert row.case_id == "c1"
    assert row.runner == "stub"


def test_evaluate_case_mismatch():
    case = Case(id="c1", input=[], expected=[{"id": "1"}])
    runner = _StubRunner(output=[{"id": "2"}])
    row = evaluate_case(runner, case)
    assert not row.passed
    assert row.error == "output did not match expected"


def test_evaluate_case_records_exception():
    case = Case(id="c1", input=[], expected=[])
    runner = _StubRunner(exc=ValueError("boom"))
    row = evaluate_case(runner, case)
    assert not row.passed
    assert "ValueError" in row.error
    assert "boom" in row.error


def test_trace_row_serializes_to_json():
    case = Case(id="c1", input=[], expected=[])
    row = evaluate_case(_StubRunner(output=[]), case)
    text = row.to_json()
    assert '"case_id": "c1"' in text
    assert '"passed": true' in text
