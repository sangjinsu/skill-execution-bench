"""Runners that exercise each Skill execution mode.

Each runner implements the common ``SkillRunner`` interface and produces the
normalized output for a given payload *through its mode's mechanism*:

- DocOnlyRunner       -> calls the reference normalizer (simulates the agent
                         performing the doc-only procedure by hand).
- InlineCodeRunner    -> extracts the ``python`` code block from the inline-code
                         SKILL.md and executes it.
- PythonScriptRunner  -> shells out to skills/python-script/scripts/transform.py.
- GoBinaryRunner      -> shells out to the compiled skills/go-binary/bin/skill-runner.

The harness simulates the mechanical execution path; the interface is kept clear
so a real LLM agent could later be asked to use each Skill instead.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from . import REPO_ROOT
from .normalize import normalize as reference_normalize

PYTHON_SCRIPT = REPO_ROOT / "skills" / "python-script" / "scripts" / "transform.py"
INLINE_SKILL = REPO_ROOT / "skills" / "inline-code" / "SKILL.md"
GO_BINARY = REPO_ROOT / "skills" / "go-binary" / "bin" / "skill-runner"

_PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


class SkillRunner:
    """Common interface for all execution modes."""

    name: str = "base"
    execution_mode: str = "base"
    #: True when the runner relies on code/binary outside the harness process.
    used_external_code: bool = False

    def run(self, payload: Any) -> Any:
        raise NotImplementedError


class DocOnlyRunner(SkillRunner):
    name = "doc-only"
    execution_mode = "doc-only"
    used_external_code = False

    def run(self, payload: Any) -> Any:
        # Simulates an agent applying the written procedure by hand.
        return reference_normalize(payload)


class InlineCodeRunner(SkillRunner):
    name = "inline-code"
    execution_mode = "inline-code"
    used_external_code = False

    def __init__(self, skill_path: Path = INLINE_SKILL) -> None:
        self._normalize = self._load_inline_normalize(skill_path)

    @staticmethod
    def _load_inline_normalize(skill_path: Path) -> Callable[[Any], Any]:
        text = skill_path.read_text(encoding="utf-8")
        blocks = _PYTHON_BLOCK.findall(text)
        for block in blocks:
            if "def normalize(" in block:
                namespace: dict[str, Any] = {}
                exec(compile(block, str(skill_path), "exec"), namespace)
                fn = namespace.get("normalize")
                if callable(fn):
                    return fn
        raise ValueError(
            f"no 'normalize' function found in a python code block of {skill_path}"
        )

    def run(self, payload: Any) -> Any:
        return self._normalize(payload)


class PythonScriptRunner(SkillRunner):
    name = "python-script"
    execution_mode = "python-script"
    used_external_code = True

    def __init__(self, script_path: Path = PYTHON_SCRIPT) -> None:
        self.script_path = script_path

    def run(self, payload: Any) -> Any:
        if not self.script_path.exists():
            raise FileNotFoundError(f"script not found: {self.script_path}")
        proc = subprocess.run(
            [sys.executable, str(self.script_path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"transform.py exited with {proc.returncode}: {proc.stderr.strip()}"
            )
        return json.loads(proc.stdout)


class GoBinaryRunner(SkillRunner):
    name = "go-binary"
    execution_mode = "go-binary"
    used_external_code = True

    def __init__(self, binary_path: Path = GO_BINARY) -> None:
        self.binary_path = binary_path

    def run(self, payload: Any) -> Any:
        if not self.binary_path.exists():
            raise FileNotFoundError(
                f"go binary not found: {self.binary_path} (run 'make build-go')"
            )
        proc = subprocess.run(
            [str(self.binary_path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"skill-runner exited with {proc.returncode}: {proc.stderr.strip()}"
            )
        return json.loads(proc.stdout)


def build_runners() -> list[SkillRunner]:
    """Instantiate all runners in a stable order."""
    return [
        DocOnlyRunner(),
        InlineCodeRunner(),
        PythonScriptRunner(),
        GoBinaryRunner(),
    ]
