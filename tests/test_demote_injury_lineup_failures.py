"""Unit coverage for woo_morning_monetization injury audit scoping."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_injury_audit_mod():
    p = REPO_ROOT / "scripts" / "audit_injury_lineup_run_modes.py"
    spec = importlib.util.spec_from_file_location("audit_injury_lineup_run_modes_mod", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_demote_keeps_morning_expected_failures():
    mod = _load_injury_audit_mod()
    failures = [
        {
            "run_mode": "morning_expected",
            "severity": "fail",
            "blocker_code": "SOURCE_AVAILABILITY_NOT_EXPLICIT",
            "detail": "bad rows",
        },
        {
            "run_mode": "t25",
            "severity": "fail",
            "blocker_code": "SAME_DAY_SOURCE_INPUTS_MISSING",
            "detail": "none",
        },
    ]
    assert mod.demote_injury_lineup_failures_for_woo_morning(failures) is True
    assert failures[0]["severity"] == "fail"
    assert failures[1]["severity"] == "warn"
    assert failures[1]["blocker_code"] == "INJURY_LINEUP_RUN_MODE_NONCURRENT_WARN"


def test_demote_only_non_morning_modes():
    mod = _load_injury_audit_mod()
    failures = [
        {
            "run_mode": "morning_expected",
            "severity": "warn",
            "blocker_code": "SOFT",
            "detail": "",
        },
    ]
    assert mod.demote_injury_lineup_failures_for_woo_morning(failures) is False
