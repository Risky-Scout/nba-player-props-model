#!/usr/bin/env python3
"""Prove placeholder Odds API CLI args exit before network or file writes."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "oddsapi_nba_props.py"), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    rc, out = _run(
        [
            "historical-lock-day",
            "--target-date",
            "YYYY-MM-DD",
            "--dry-run",
            "--max-events",
            "1",
        ]
    )
    if rc != 2 or "ODDSAPI_INVALID_DATE_ARGUMENT" not in out:
        print("VERIFY_FAIL historical-lock-day placeholder date", file=sys.stderr)
        print(out, file=sys.stderr)
        return 1

    rc2, out2 = _run(
        [
            "historical-events",
            "--snapshot-time-utc",
            "YYYY-MM-DDTHH:MM:SSZ",
            "--dry-run",
        ]
    )
    if rc2 != 2 or "ODDSAPI_INVALID_TIMESTAMP_ARGUMENT" not in out2:
        print("VERIFY_FAIL historical-events placeholder timestamp", file=sys.stderr)
        print(out2, file=sys.stderr)
        return 1

    print("ODDSAPI_PLACEHOLDER_DATE_GUARD_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
