"""Smoke tests for injury/lineup audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_audit_script_runs():
    script = REPO / "scripts" / "audit_injury_lineup_run_modes.py"
    r = subprocess.run(
        [sys.executable, str(script), "--date", "2026-05-13", "--latest-completed-date", "2026-05-12"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert r.returncode in (0, 2)
    assert "INJURY_LINEUP_RUN_MODE_AUDIT_" in r.stdout
