#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

import pandas as pd


def prev_day(slate_date: str) -> str:
    return (pd.Timestamp(slate_date).date() - timedelta(days=1)).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser("verify_sgp_bundle_asof_contract")
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--expected-cutoff-date", default=None)
    args = ap.parse_args()

    expected = args.expected_cutoff_date or prev_day(args.date)
    root = Path(args.repo_root) / "deliveries" / args.date / "sgp_engine" / "slate_state_bundle_v1"
    manifest_path = root / "bundle_manifest.json"
    dq_path = root / "data_quality_report.json"
    if not manifest_path.exists():
        raise SystemExit(f"FAIL: missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    dq = json.loads(dq_path.read_text()) if dq_path.exists() else {}

    trained = manifest.get("trained_through_date") or manifest.get("asof_contract", {}).get("trained_through_date")
    calibrated = manifest.get("calibrated_through_date") or manifest.get("asof_contract", {}).get("calibrated_through_date")

    checks = {
        "expected_cutoff_date": expected,
        "trained_through_date": trained,
        "calibrated_through_date": calibrated,
        "trained_matches_expected": trained == expected,
        "calibrated_matches_expected": calibrated == expected,
        "bundle_status": manifest.get("bundle_status"),
        "quality_status": dq.get("status"),
        "asof_contract": manifest.get("asof_contract", {}),
    }
    print(json.dumps(checks, indent=2, sort_keys=True))

    if trained != expected or calibrated != expected:
        raise SystemExit("FAIL: SGP bundle as-of contract failed.")
    if manifest.get("bundle_status") != "PASS":
        raise SystemExit("FAIL: bundle_status is not PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
