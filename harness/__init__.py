"""Test harness for the skill-execution benchmark.

Runs the same dataset through each Skill execution mode (doc-only, inline-code,
python-script, go-binary) and evaluates the output deterministically.
"""

from __future__ import annotations

from pathlib import Path

# Repository root, derived from this file's location (harness/ is at the root).
REPO_ROOT = Path(__file__).resolve().parent.parent
