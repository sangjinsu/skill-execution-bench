"""Tests for the four execution-mode runners.

The doc-only, inline-code, and python-script runners always run. The go-binary
runner requires Go (or a pre-built binary); its tests are skipped with a clear
message when Go is unavailable.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

import pytest

from harness import REPO_ROOT
from harness.models import load_cases
from harness.runners import (
    GO_BINARY,
    PYTHON_SCRIPT,
    DocOnlyRunner,
    GoBinaryRunner,
    InlineCodeRunner,
    PythonScriptRunner,
)

CASES = load_cases(REPO_ROOT / "datasets" / "tasks.jsonl")
GO_AVAILABLE = shutil.which("go") is not None


@pytest.fixture(scope="module")
def go_binary():
    """Build the Go binary once; skip the module's Go tests if unavailable."""
    if GO_BINARY.exists():
        return GO_BINARY
    if not GO_AVAILABLE:
        pytest.skip("Go toolchain not installed and binary not pre-built")
    result = subprocess.run(
        ["go", "build", "-o", str(GO_BINARY),
         "./skills/go-binary/cmd/skill-runner"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"go build failed: {result.stderr}")
    return GO_BINARY


# --- pure / in-process runners -------------------------------------------------

@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_doc_only_runner(case):
    assert DocOnlyRunner().run(case.input) == case.expected


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_inline_code_runner(case):
    assert InlineCodeRunner().run(case.input) == case.expected


def test_inline_runner_extracts_normalize_from_skill():
    # The runner must actually load the function from SKILL.md, not import it.
    runner = InlineCodeRunner()
    assert callable(runner._normalize)


# --- python-script runner ------------------------------------------------------

@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_python_script_runner(case):
    assert PythonScriptRunner().run(case.input) == case.expected


def test_python_script_rejects_invalid_input():
    proc = subprocess.run(
        [sys.executable, str(PYTHON_SCRIPT)],
        input="{not valid json}",
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()


def test_python_script_rejects_non_array():
    proc = subprocess.run(
        [sys.executable, str(PYTHON_SCRIPT)],
        input=json.dumps({"id": "1"}),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


# --- go-binary runner ----------------------------------------------------------

@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_go_binary_runner(case, go_binary):
    assert GoBinaryRunner(go_binary).run(case.input) == case.expected


def test_go_binary_rejects_invalid_input(go_binary):
    proc = subprocess.run(
        [str(go_binary)],
        input="{not valid json}",
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert proc.stderr.strip()


def test_go_binary_rejects_non_array(go_binary):
    proc = subprocess.run(
        [str(go_binary)],
        input=json.dumps({"id": "1"}),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_python_and_go_outputs_are_identical(go_binary):
    """Byte-for-byte parity between the Python script and the Go binary."""
    for case in CASES:
        payload = json.dumps(case.input)
        py = subprocess.run(
            [sys.executable, str(PYTHON_SCRIPT)],
            input=payload, capture_output=True, text=True,
        )
        go = subprocess.run(
            [str(go_binary)],
            input=payload, capture_output=True, text=True,
        )
        assert py.stdout == go.stdout, case.id


# --- missing binary handling ---------------------------------------------------

def test_go_runner_raises_clear_error_when_binary_missing(tmp_path):
    missing = tmp_path / "skill-runner"
    with pytest.raises(FileNotFoundError):
        GoBinaryRunner(missing).run([])
