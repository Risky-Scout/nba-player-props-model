"""Run 25956230745 surfaced the M8.6 morning completeness + OddsAPI/BDL
coverage step hard-failing on a forced morning delivery because the
backtest inventory CSV is a training-time artifact that does NOT yet
contain today's slate. The verifier must skip-not-fail in single-date
mode when the inventory is missing or doesn't include the date, but
must still hard-fail in range mode (historical backfill audits)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "verify_oddsapi_bdl_full_prop_coverage",
    REPO / "scripts" / "verify_oddsapi_bdl_full_prop_coverage.py",
)


def _load_module():
    mod = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(mod)
    return mod


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "verify_oddsapi_bdl_full_prop_coverage.py"), *args],
        capture_output=True,
        text=True,
    )


def test_missing_inventory_with_date_skips_not_fails(tmp_path):
    """The exact regression from run 25956230745."""
    missing = tmp_path / "no_such_inventory.csv"
    proc = _run(["--date", "2026-05-15", "--dates-file", str(missing)])
    assert proc.returncode == 0, proc.stderr
    assert "ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_SKIPPED" in proc.stdout
    assert "reason=MISSING_INVENTORY" in proc.stdout


def test_missing_inventory_without_date_still_hard_fails(tmp_path):
    """Range/no-date callers (the historical backfill audit) must keep
    the strict failure so an actually-broken inventory is surfaced."""
    missing = tmp_path / "no_such_inventory.csv"
    proc = _run(["--dates-file", str(missing)])
    assert proc.returncode == 2
    assert "MISSING_INVENTORY" in proc.stderr


def test_date_not_in_inventory_skips_not_fails(tmp_path):
    inv = tmp_path / "inv.csv"
    pd.DataFrame(
        [
            {"date": "2026-04-01", "eligible_for_event_market_backtest": True},
            {"date": "2026-04-02", "eligible_for_event_market_backtest": True},
        ]
    ).to_csv(inv, index=False)
    proc = _run(["--date", "2026-05-15", "--dates-file", str(inv)])
    assert proc.returncode == 0, proc.stderr
    assert "ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_SKIPPED" in proc.stdout
    assert "reason=DATE_NOT_IN_INVENTORY" in proc.stdout


def test_range_with_empty_match_still_hard_fails(tmp_path):
    inv = tmp_path / "inv.csv"
    pd.DataFrame(
        [
            {"date": "2026-04-01", "eligible_for_event_market_backtest": True},
        ]
    ).to_csv(inv, index=False)
    proc = _run(
        [
            "--start-date",
            "2027-01-01",
            "--end-date",
            "2027-01-31",
            "--dates-file",
            str(inv),
        ]
    )
    assert proc.returncode == 1
    assert "ODDSAPI_BDL_FULL_PROP_COVERAGE_AUDIT_FAIL" in proc.stderr
