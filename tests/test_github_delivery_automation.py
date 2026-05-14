"""Smoke tests for GitHub delivery automation audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_audit_script_runs():
    script = REPO / "scripts" / "audit_github_delivery_automation.py"
    r = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert r.returncode in (0, 2)
    assert "GITHUB_DELIVERY_AUTOMATION_AUDIT_" in r.stdout
