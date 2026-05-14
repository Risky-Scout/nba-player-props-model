#!/usr/bin/env python3
"""M8.6 — summarize stat-role market-superiority failures for remediation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    date = args.date

    sup_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{date}"
    csv_path = sup_dir / "stat_role_market_superiority.csv"
    eml_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{date}.parquet"
    out_dir = sup_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    diagnoses: list[dict] = []
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        fail = df[df["market_superiority_pass"] == False]
        for _, r in fail.iterrows():
            diagnoses.append({
                "stat": r.get("stat"),
                "role_bucket": r.get("role_bucket"),
                "primary_failure_reason": r.get("failure_reason") or "unknown",
                "secondary_failure_reasons": [],
                "exact_metric_gap": {
                    "brier_delta_model_minus_market": r.get("brier_delta_model_minus_market"),
                    "logloss_delta_model_minus_market": r.get("logloss_delta_model_minus_market"),
                },
                "recommended_fix": "Improve OOF join (player_id alignment), refresh availability, or extend OOF rows for combos (RA).",
                "required_script_or_module_to_patch": "scripts/build_event_market_loss_rows.py",
            })

    join_rate = None
    if eml_path.exists():
        em = pd.read_parquet(eml_path)
        if len(em) and "join_status" in em.columns:
            join_rate = float((em["join_status"] == "matched").mean())

    payload = {
        "date": date,
        "n_failed_segments": len(diagnoses),
        "event_market_join_rate": join_rate,
        "failures": diagnoses,
    }
    (out_dir / "failure_diagnosis.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# Market superiority failure diagnosis — {date}",
        "",
        f"- Event-market join rate (matched / all): {join_rate}",
        f"- Failed stat-role segments: {len(diagnoses)}",
        "",
    ]
    for d in diagnoses[:200]:
        lines.append(
            f"## {d['stat']} / {d['role_bucket']}\n"
            f"- **Primary:** {d['primary_failure_reason']}\n"
            f"- **Gap:** {d['exact_metric_gap']}\n"
            f"- **Fix:** {d['recommended_fix']}\n"
        )
    (out_dir / "failure_diagnosis.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"MARKET_SUPERIORITY_FAILURE_DIAGNOSIS_PASS out={out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
