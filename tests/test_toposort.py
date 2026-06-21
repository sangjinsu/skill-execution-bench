"""Tests for the dependency topological-sort reference and dataset."""

from __future__ import annotations

import json

import pytest

from harness import REPO_ROOT
from harness.toposort import toposort

TOPO_DATASET = REPO_ROOT / "datasets" / "tasks-toposort.jsonl"


def test_simple_chain():
    recs = [{"id": "3", "deps": ["1", "2"]}, {"id": "1", "deps": []}, {"id": "2", "deps": ["1"]}]
    assert toposort(recs) == ["1", "2", "3"]


def test_reverse_chain_is_descending():
    recs = [{"id": "1", "deps": ["2"]}, {"id": "2", "deps": ["3"]}, {"id": "3", "deps": []}]
    assert toposort(recs) == ["3", "2", "1"]


def test_tie_break_smallest_numeric_id_first():
    # 2 and 10 are both ready at the start; 2 must come first (numeric, not lexicographic).
    recs = [{"id": "10", "deps": []}, {"id": "2", "deps": []}, {"id": "1", "deps": ["2", "10"]}]
    assert toposort(recs) == ["2", "10", "1"]


def test_diamond_respects_dependencies():
    recs = [
        {"id": "1", "deps": []},
        {"id": "2", "deps": ["1"]},
        {"id": "3", "deps": ["1"]},
        {"id": "4", "deps": ["2", "3"]},
    ]
    order = toposort(recs)
    assert order.index("1") < order.index("2") < order.index("4")
    assert order.index("3") < order.index("4")


def test_cycle_raises():
    with pytest.raises(ValueError):
        toposort([{"id": "1", "deps": ["2"]}, {"id": "2", "deps": ["1"]}])


def test_unknown_dependency_raises():
    with pytest.raises(ValueError):
        toposort([{"id": "1", "deps": ["99"]}])


def test_duplicate_id_raises():
    with pytest.raises(ValueError):
        toposort([{"id": "1", "deps": []}, {"id": "1", "deps": []}])


def test_dataset_exists_and_is_nontrivial():
    """Every dataset case's expected order must differ from a plain id sort,
    so 'just sort the ids ascending' cannot accidentally pass."""
    assert TOPO_DATASET.exists()
    lines = [l for l in TOPO_DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 6
    for line in lines:
        case = json.loads(line)
        ids_sorted = sorted((str(r["id"]) for r in case["input"]), key=int)
        assert case["expected"] != ids_sorted, f"{case['id']} is trivially id-sorted"


def test_dataset_expected_matches_reference():
    for line in TOPO_DATASET.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        assert toposort(case["input"]) == case["expected"], case["id"]


def test_output_is_valid_topological_order():
    for line in TOPO_DATASET.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        order = case["expected"]
        pos = {nid: i for i, nid in enumerate(order)}
        for rec in case["input"]:
            for dep in rec.get("deps", []):
                assert pos[str(dep)] < pos[str(rec["id"])], (case["id"], dep, rec["id"])
