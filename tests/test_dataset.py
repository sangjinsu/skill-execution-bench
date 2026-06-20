"""Tests for dataset loading and case schema."""

from __future__ import annotations

import json

import pytest

from harness import REPO_ROOT
from harness.models import Case, load_cases

DATASET = REPO_ROOT / "datasets" / "tasks.jsonl"


def test_dataset_file_exists():
    assert DATASET.exists(), f"missing dataset: {DATASET}"


def test_load_cases_returns_at_least_five():
    cases = load_cases(DATASET)
    assert len(cases) >= 5


def test_cases_have_required_fields():
    cases = load_cases(DATASET)
    for case in cases:
        assert isinstance(case.id, str) and case.id
        assert isinstance(case.input, list)
        assert isinstance(case.expected, list)


def test_case_ids_are_unique():
    cases = load_cases(DATASET)
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids))


def test_from_dict_rejects_missing_fields():
    with pytest.raises(ValueError):
        Case.from_dict({"id": "x", "input": []})


def test_load_cases_rejects_invalid_json(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(bad)


def test_expected_matches_reference_normalizer():
    """The dataset's expected output must agree with the reference contract."""
    from harness.normalize import normalize

    for line in DATASET.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        assert normalize(case["input"]) == case["expected"], case["id"]
