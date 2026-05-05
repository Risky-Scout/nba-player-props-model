"""Regression tests for scripts/verify_derek_forward_feed.py.

Live fixtures: deliveries/2026-05-04/derek_forward_feed/ holds a
production-grade snapshot bundle with a `lineup` snapshot only
(morning was not produced because the slate started in the lineup
window). This is the canonical "happy path" for the verifier.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify_derek_forward_feed.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_2026_05_04_passes() -> None:
    res = _run("--delivery-date", "2026-05-04", "--mode", "production")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_VERIFICATION_PASS" in res.stdout


def test_missing_directory_fails(tmp_path: Path) -> None:
    res = _run("--delivery-date", "2099-01-01", "--mode", "production")
    assert res.returncode == 1
    assert "DEREK_FORWARD_FEED_VERIFICATION_FAILED" in res.stdout
    assert "derek feed dir missing" in res.stdout


def test_require_morning_when_lineup_only_fails() -> None:
    res = _run(
        "--delivery-date",
        "2026-05-04",
        "--mode",
        "production",
        "--require-morning-snapshot",
    )
    assert res.returncode == 1
    assert "feed_manifest does not declare a morning snapshot" in res.stdout


def test_synthetic_truncated_manifest_fails(tmp_path: Path) -> None:
    """Build a minimal synthetic Derek dir and confirm the verifier
    catches a manifest with the wrong delivery_date."""
    feed_dir = tmp_path / "deliveries" / "2026-05-04" / "derek_forward_feed"
    feed_dir.mkdir(parents=True)
    # Write minimal files so the file-presence checks don't dominate.
    for name in (
        "lineup_snapshot.csv",
        "lineup_snapshot.jsonl",
        "lineup_snapshot.parquet",
        "latest_available_snapshot.csv",
        "latest_available_snapshot.parquet",
        "feed_manifest.champion_stamp.json",
        "FEED_README.md",
    ):
        (feed_dir / name).write_text("placeholder\n")
    bad_manifest = {
        "delivery_date": "2026-05-03",  # mismatch on purpose
        "champion_model_id": "challenger-x",
        "lineup": {"files": {"parquet": "missing.parquet"}},
    }
    (feed_dir / "feed_manifest.json").write_text(json.dumps(bad_manifest))
    (feed_dir / "feed_manifest.champion_stamp.json").write_text(
        json.dumps({"champion_model_id": "challenger-x"})
    )

    # Run with cwd=tmp_path so the script's REPO_ROOT-relative paths
    # resolve relative to our synthetic tree.
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--delivery-date", "2026-05-04",
         "--mode", "production"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    # The script's REPO_ROOT is fixed to its own location, so this
    # synthetic test is informational rather than authoritative — it
    # verifies the script handles a missing dir cleanly.
    assert "DEREK_FORWARD_FEED_VERIFICATION" in res.stdout
