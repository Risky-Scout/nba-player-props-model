#!/usr/bin/env python3
"""Audit M8.7 market-superiority repair pipeline (thresholds + active scoring)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _must_contain(path: Path, needle: str, desc: str) -> None:
    t = path.read_text(encoding="utf-8")
    if needle not in t:
        raise SystemExit(f"FATAL: {desc}: missing {needle!r} in {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="dates_24c1750e26ad")
    ap.add_argument("--dates-file", default="artifacts/model_diagnostics/event_market_backtest_date_inventory.csv")
    ap.add_argument(
        "--event-manifest",
        default="artifacts/models/event_neutral_probability_scale_repair_dates_24c1750e26ad.json",
    )
    ap.add_argument(
        "--mean-manifest",
        default="artifacts/models/pmf_mean_shift_repair_dates_24c1750e26ad.json",
    )
    args = ap.parse_args()

    sr_rep = REPO_ROOT / "scripts" / "build_stat_role_market_superiority_report.py"
    math_v = REPO_ROOT / "scripts" / "verify_market_superiority_math_contract.py"
    strict_v = REPO_ROOT / "scripts" / "verify_market_superiority_by_stat_role_contract.py"
    fit_ms = REPO_ROOT / "scripts" / "fit_pmf_mean_shift_repair.py"
    fit_ev = REPO_ROOT / "scripts" / "fit_event_neutral_probability_scale_repair.py"

    _must_contain(sr_rep, "DEFAULT_MIN_SCORED = 100", "stat_role_report_min_scored")
    _must_contain(math_v, "bootstrap_reps", "math_contract_bootstrap_param")
    _must_contain(strict_v, "eligible", "strict_contract_eligible_logic")

    for fp, desc in (
        (fit_ms, "fit_pmf_mean_shift_repair"),
        (fit_ev, "fit_event_neutral_probability_scale_repair"),
    ):
        t = fp.read_text(encoding="utf-8")
        for needle, lab in (
            ('"uses_market_probability_as_label": False', "market_not_label"),
            ('"uses_market_probability_as_feature": False', "market_not_feature"),
            ('"fold_key": "game_date"', "oof_fold_game_date"),
        ):
            if needle not in t:
                raise SystemExit(f"FATAL: {desc}: missing {lab} sentinel {needle!r}")

    fit_t = fit_ms.read_text(encoding="utf-8").lower()
    if "no_vig" in fit_t:
        print("FATAL: market odds token in fit_pmf_mean_shift_repair.py", file=sys.stderr)
        return 2

    vrf = REPO_ROOT / "scripts" / "verify_repair_active_scoring_contract.py"
    cmd = [
        sys.executable,
        str(vrf),
        "--label",
        args.label,
        "--dates-file",
        str(REPO_ROOT / args.dates_file),
        "--event-prob-calibration-manifest",
        str(REPO_ROOT / args.event_manifest),
        "--pmf-mean-shift-manifest",
        str(REPO_ROOT / args.mean_manifest),
    ]
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or "")
        if r.stdout:
            sys.stderr.write(r.stdout)
        print("FATAL: active scoring contract subprocess failed", file=sys.stderr)
        return r.returncode
    if "REPAIR_ACTIVE_SCORING_CONTRACT_PASS" not in (r.stdout or ""):
        print("FATAL: active contract did not emit pass token", file=sys.stderr)
        return 2
    print(r.stdout.strip())

    print("MARKET_SUPERIORITY_REPAIR_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
