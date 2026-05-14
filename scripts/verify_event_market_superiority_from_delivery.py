#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def _pick(df, names, required=True):
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    if required:
        raise SystemExit(f"FATAL missing one of {names}; columns={list(df.columns)}")
    return None


def _safe_prob(x):
    return np.clip(pd.to_numeric(x, errors="coerce").astype(float), 1e-6, 1 - 1e-6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--input", default=None)
    ap.add_argument("--min-supported-n", type=int, default=30)
    args = ap.parse_args()

    path = Path(args.input) if args.input else Path(f"deliveries/{args.date}/after_game_scoring/model_vs_market_scoring.parquet")
    if not path.exists():
        alt = Path(f"deliveries/{args.date}/wizard_of_odds/market_comparison.parquet")
        raise SystemExit(f"FATAL: no settled scoring file found at {path}. Need after-game scoring. Existing market_comparison ({alt}) is not enough because it lacks actual outcomes.")

    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)

    stat_col = _pick(df, ["stat", "stat_type"])
    role_col = _pick(df, ["role_bucket", "role"], required=False)
    ctx_col = _pick(df, ["prediction_context", "snapshot_type", "snapshot"], required=False)
    actual_over_col = _pick(df, ["actual_over", "over_result", "hit_over", "event_over_result"])
    model_p_col = _pick(df, ["final_model_prob_over", "calibrated_model_prob_over", "model_prob_over", "p_over"])
    market_p_col = _pick(df, ["market_prob_over_no_vig", "market_no_vig_over_prob", "no_vig_over_prob"])

    df = df.copy()
    df["_model_p"] = _safe_prob(df[model_p_col])
    df["_market_p"] = _safe_prob(df[market_p_col])
    df["_actual"] = pd.to_numeric(df[actual_over_col], errors="coerce").astype(float)
    df = df[df["_actual"].isin([0.0, 1.0])].copy()

    df["_model_brier"] = (df["_model_p"] - df["_actual"]) ** 2
    df["_market_brier"] = (df["_market_p"] - df["_actual"]) ** 2
    df["_model_ll"] = -(df["_actual"] * np.log(df["_model_p"]) + (1 - df["_actual"]) * np.log(1 - df["_model_p"]))
    df["_market_ll"] = -(df["_actual"] * np.log(df["_market_p"]) + (1 - df["_actual"]) * np.log(1 - df["_market_p"]))
    df["_brier_delta"] = df["_model_brier"] - df["_market_brier"]
    df["_ll_delta"] = df["_model_ll"] - df["_market_ll"]

    if role_col is None:
        df["_role"] = "unknown"
        role_col = "_role"
    if ctx_col is None:
        df["_context"] = "unknown"
        ctx_col = "_context"

    groups = [
        [stat_col],
        [role_col],
        [stat_col, role_col],
        [stat_col, role_col, ctx_col],
    ]
    rows = []
    for gcols in groups:
        for key, sub in df.groupby(gcols, dropna=False):
            if len(sub) < args.min_supported_n:
                continue
            if not isinstance(key, tuple):
                key = (key,)
            rec = {col: val for col, val in zip(gcols, key)}
            model_cal = float((sub["_actual"] - sub["_model_p"]).mean())
            market_cal = float((sub["_actual"] - sub["_market_p"]).mean())
            rec.update({
                "grouping": "|".join(gcols),
                "n": len(sub),
                "model_event_logloss": float(sub["_model_ll"].mean()),
                "market_event_logloss": float(sub["_market_ll"].mean()),
                "event_logloss_delta": float(sub["_ll_delta"].mean()),
                "event_logloss_delta_se": float(sub["_ll_delta"].std(ddof=1) / math.sqrt(len(sub))) if len(sub) > 1 else float("nan"),
                "model_brier": float(sub["_model_brier"].mean()),
                "market_brier": float(sub["_market_brier"].mean()),
                "brier_delta": float(sub["_brier_delta"].mean()),
                "brier_delta_se": float(sub["_brier_delta"].std(ddof=1) / math.sqrt(len(sub))) if len(sub) > 1 else float("nan"),
                "model_cal_error": model_cal,
                "market_cal_error": market_cal,
                "model_abs_cal_error": abs(model_cal),
                "market_abs_cal_error": abs(market_cal),
                "logloss_pass": float(sub["_ll_delta"].mean()) < 0,
                "brier_pass": float(sub["_brier_delta"].mean()) < 0,
                "calibration_pass": abs(model_cal) < abs(market_cal),
            })
            rec["market_superiority_pass"] = bool(rec["logloss_pass"] and rec["brier_pass"] and rec["calibration_pass"])
            rows.append(rec)

    out_dir = Path(f"_stat_grid_delivery_calibration_optimizer/verification/event_market_{args.date}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "event_market_benchmark_by_group.csv", index=False)
    failed = out[(out.get("market_superiority_pass") == False)] if not out.empty else out
    failed.to_csv(out_dir / "failed_supported_event_market_groups.csv", index=False)
    report = {
        "date": args.date,
        "input": str(path),
        "n_rows": int(len(df)),
        "n_supported_groups": int(len(out)),
        "n_failed_supported_groups": int(len(failed)),
        "market_pmf_used": False,
        "market_superiority_claim_allowed": bool(len(out) > 0 and len(failed) == 0),
        "out_dir": str(out_dir.resolve()),
    }
    (out_dir / "event_market_gate_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
