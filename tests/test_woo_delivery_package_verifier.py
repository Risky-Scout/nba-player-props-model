"""Regression tests for scripts/verify_woo_delivery_package.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify_woo_delivery_package.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_2026_05_04_strict_fails_due_to_no_market_and_no_tov() -> None:
    res = _run(
        "--delivery-date", "2026-05-04", "--mode", "production",
    )
    # The 2026-05-04 fixture has finality blockers for market + tov.
    assert res.returncode == 1, res.stdout + res.stderr
    assert "WOO_DELIVERY_PACKAGE_VERIFICATION_FAILED" in res.stdout
    assert "market_coverage_none" in res.stdout
    assert "missing_stats:tov" in res.stdout


def test_2026_05_04_passes_when_blockers_allowed() -> None:
    res = _run(
        "--delivery-date", "2026-05-04", "--mode", "production",
        "--allow-no-market", "--allow-tov-missing",
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "WOO_DELIVERY_PACKAGE_VERIFICATION_PASS" in res.stdout


def test_missing_directory_fails() -> None:
    res = _run("--delivery-date", "2099-01-01", "--mode", "production")
    assert res.returncode == 1
    assert "WOO_DELIVERY_PACKAGE_VERIFICATION_FAILED" in res.stdout
    assert "missing" in res.stdout
