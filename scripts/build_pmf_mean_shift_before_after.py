#!/usr/bin/env python3
"""Build before/after segment summary for PMF mean-shift repair."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ART = REPO_ROOT / "artifacts" / "model_diagnostics"


def _binary_logloss(p: float, y: float) -> float | None:
    if p is None or y is None or not (p == p) or not (y == y):
        return None
    pp = min(max(float(p), 1e-12), 1.0 - 1e-12)
    yy = float(y)
    return float(-(yy * math.log(pp) + (1.0 - yy) * math.log(1.0 - pp)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label)
    loss_path = ART / f"event_market_loss_rows_{label}.parquet"
    led_path = ART / f"market_superiority_repair_{label}" / "repair_ledger.csv"
    sr_path = ART / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv"
    man_path = REPO_ROOT / "artifacts" / "models" / f"pmf_mean_shift_repair_{label}.json"
    if not loss_path.is_file():
        print(f"FATAL: missing {loss_path}", file=sys.stderr)
        return 2
    loss = pd.read_parquet(loss_path)
    led = pd.read_csv(led_path) if led_path.is_file() else pd.DataFrame()
    sr = pd.read_csv(sr_path) if sr_path.is_file() else pd.DataFrame()
    man = json.loads(man_path.read_text(encoding="utf-8")) if man_path.is_file() else {"segments": {}}
    segs = man.get("segments") or {}

    if "pmf_mean_raw" not in loss.columns:
        print("FATAL: loss rows missing pmf_mean_raw (rebuild with mean-shift path)", file=sys.stderr)
        return 2

    rows = []
    for (st, rb), g in loss.groupby(
        [loss["stat"].astype(str).str.lower(), loss["role_bucket"].astype(str).str.lower()]
    ):
        g2 = g[g["join_status"] == "matched"]
        settled = g2[g2["hit_result"].isin([0, 1])]
        if settled.empty:
            continue
        act = pd.to_numeric(settled["actual"], errors="coerce")
        raw_mu = pd.to_numeric(settled["pmf_mean_raw"], errors="coerce")
        rep_mu = pd.to_numeric(settled["pmf_mean_repaired"], errors="coerce")
        raw_bias = float((raw_mu - act).mean()) if raw_mu.notna().all() else float("nan")
        rep_bias = float((rep_mu - act).mean()) if rep_mu.notna().all() else float("nan")
        rlls = [
            _binary_logloss(float(r["model_prob_over_raw"]), float(r["hit_result"]))
            for _, r in settled.iterrows()
            if r.get("model_prob_over_raw") is not None and r.get("hit_result") is not None
        ]
        rlls = [x for x in rlls if x is not None]
        raw_ll = float(sum(rlls) / len(rlls)) if rlls else float("nan")
        rep_ll = float(settled["model_event_logloss"].mean()) if "model_event_logloss" in settled.columns else float("nan")
        mkt_ll = float(settled["market_event_logloss"].mean()) if "market_event_logloss" in settled.columns else float("nan")
        rbrs = []
        for _, r in settled.iterrows():
            po = r.get("model_prob_over_raw")
            y = r.get("hit_result")
            if po is not None and y is not None and po == po and y == y:
                rbrs.append((float(po) - float(y)) ** 2)
        raw_br = float(sum(rbrs) / len(rbrs)) if rbrs else float("nan")
        mkt_br = float(settled["market_brier"].mean()) if "market_brier" in settled.columns else float("nan")

        sk = f"{st}|{rb}"
        sp = segs.get(sk, {})
        lr = led[(led["stat"].astype(str).str.lower() == st) & (led["role_bucket"].astype(str).str.lower() == rb)]
        lr = lr.iloc[0].to_dict() if len(lr) else {}
        srr = sr[(sr["stat"].astype(str).str.lower() == st) & (sr["role_bucket"].astype(str).str.lower() == rb)]
        srr = srr.iloc[0].to_dict() if len(srr) else {}

        rows.append(
            {
                "stat": st,
                "role_bucket": rb,
                "n": int(len(settled)),
                "raw_mean_bias": raw_bias,
                "repaired_mean_bias": rep_bias,
                "raw_model_logloss": raw_ll,
                "repaired_model_logloss": rep_ll,
                "market_logloss": mkt_ll,
                "raw_model_brier": raw_br,
                "repaired_model_brier": float(srr.get("model_brier_avg", float("nan"))),
                "market_brier": mkt_br,
                "raw_market_superiority_pass": bool(lr.get("market_superiority_pass", False)),
                "repaired_market_superiority_pass": bool(srr.get("market_superiority_pass", False)),
                "raw_calibration_pass": bool(lr.get("calibration_pass", False)),
                "repaired_calibration_pass": bool(srr.get("calibration_pass", False)),
                "raw_model_better_calibrated": bool(lr.get("model_better_calibrated", False)),
                "repaired_model_better_calibrated": bool(srr.get("model_better_calibrated", False)),
                "selected_scope": sp.get("selected_scope"),
                "selected_method": sp.get("selected_method"),
                "rollback_reason": sp.get("rollback_reason") if not sp.get("accepted") else "",
                "claim_status": str(lr.get("claim_status", "")),
            }
        )

    out = pd.DataFrame(rows)
    out_dir = ART / f"pmf_mean_shift_repair_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "before_after.csv"
    out.to_csv(out_path, index=False)
    summ = {
        "segments": int(len(out)),
        "mean_bias_improved": int(
            (
                out["repaired_mean_bias"].notna()
                & out["raw_mean_bias"].notna()
                & (out["repaired_mean_bias"].abs() < out["raw_mean_bias"].abs())
            ).sum()
        ),
        "nll_preserved_or_improved": int(
            (
                out["repaired_model_logloss"].notna()
                & out["raw_model_logloss"].notna()
                & (out["repaired_model_logloss"] <= out["raw_model_logloss"] + 0.001)
            ).sum()
        ),
        "logloss_vs_market_improved": int((out["repaired_model_logloss"] < out["market_logloss"]).sum()),
        "brier_vs_market_improved": int((out["repaired_model_brier"] < out["market_brier"]).sum()),
        "strict_pass_segments_repaired": int(out["repaired_market_superiority_pass"].sum()),
    }
    (out_dir / "before_after_summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    print(json.dumps(summ, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
