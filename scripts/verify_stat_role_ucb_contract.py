#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_loss_rows(label: str) -> pd.DataFrame:
    candidates = [
        REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet",
        REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.csv",
    ]
    for p in candidates:
        if p.exists():
            if p.suffix == ".parquet":
                return pd.read_parquet(p)
            return pd.read_csv(p)
    raise SystemExit(f"Could not find event market loss rows for label/date {label}")


def bootstrap_ucb95(x: np.ndarray, reps: int, seed: int) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan
    mean = float(np.mean(x))
    if len(x) == 1:
        return mean, mean

    rng = np.random.default_rng(seed)
    n = len(x)
    boot = np.empty(reps, dtype=float)

    for j in range(reps):
        idx = rng.integers(0, n, size=n)
        boot[j] = float(np.mean(x[idx]))

    return mean, float(np.quantile(boot, 0.95))


def pick_col(df: pd.DataFrame, names: list[str]) -> str:
    for n in names:
        if n in df.columns:
            return n
    raise SystemExit(f"Missing one of required columns: {names}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--min-n", type=int, default=100)
    ap.add_argument("--tau-logloss", type=float, default=0.0025)
    ap.add_argument("--tau-brier", type=float, default=0.0010)
    ap.add_argument("--bootstrap-reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260512)
    args = ap.parse_args()

    df = read_loss_rows(args.label)

    if "join_status" in df.columns:
        df = df[df["join_status"].astype(str).eq("matched")].copy()

    stat_col = pick_col(df, ["stat", "prop_stat"])
    role_col = "role_bucket" if "role_bucket" in df.columns else None

    model_logloss_col = pick_col(df, ["model_event_logloss", "model_logloss", "model_nll"])
    market_logloss_col = pick_col(df, ["market_event_logloss", "market_logloss", "market_nll"])
    model_brier_col = pick_col(df, ["model_brier", "model_event_brier"])
    market_brier_col = pick_col(df, ["market_brier", "market_event_brier"])

    if role_col is None:
        df["role_bucket"] = "unknown"
        role_col = "role_bucket"

    rows = []
    failures = []

    group_keys = [
        df[stat_col].astype(str).str.lower(),
        df[role_col].fillna("unknown").astype(str),
    ]

    for (stat, role), sub in df.groupby(group_keys, dropna=False):
        s = sub[
            sub[model_logloss_col].notna()
            & sub[market_logloss_col].notna()
            & sub[model_brier_col].notna()
            & sub[market_brier_col].notna()
        ].copy()

        n = int(len(s))

        d_log = (
            pd.to_numeric(s[model_logloss_col], errors="coerce")
            - pd.to_numeric(s[market_logloss_col], errors="coerce")
        ).to_numpy()

        d_brier = (
            pd.to_numeric(s[model_brier_col], errors="coerce")
            - pd.to_numeric(s[market_brier_col], errors="coerce")
        ).to_numpy()

        row_seed = args.seed + len(rows) * 31
        log_mean, log_ucb = bootstrap_ucb95(d_log, args.bootstrap_reps, row_seed)
        brier_mean, brier_ucb = bootstrap_ucb95(d_brier, args.bootstrap_reps, row_seed + 1)

        eligible = n >= args.min_n
        log_pass = bool(log_ucb < -args.tau_logloss) if np.isfinite(log_ucb) else False
        brier_pass = bool(brier_ucb < -args.tau_brier) if np.isfinite(brier_ucb) else False
        gate_pass = bool(eligible and log_pass and brier_pass)

        if not eligible:
            reason = "insufficient_n"
        elif not log_pass:
            reason = "logloss_ucb_not_better"
        elif not brier_pass:
            reason = "brier_ucb_not_better"
        else:
            reason = ""

        row = {
            "label": args.label,
            "stat": stat,
            "role_bucket": role,
            "n": n,
            "eligible": eligible,
            "logloss_delta_mean_model_minus_market": log_mean,
            "logloss_delta_ucb95_model_minus_market": log_ucb,
            "brier_delta_mean_model_minus_market": brier_mean,
            "brier_delta_ucb95_model_minus_market": brier_ucb,
            "tau_logloss": args.tau_logloss,
            "tau_brier": args.tau_brier,
            "gate_pass": gate_pass,
            "failure_reason": reason,
        }

        rows.append(row)

        if eligible and not gate_pass:
            failures.append(row)

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"stat_role_ucb_contract_{args.label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out = pd.DataFrame(rows).sort_values(
        ["eligible", "gate_pass", "stat", "role_bucket"],
        ascending=[False, True, True, True],
    )
    out.to_csv(out_dir / "stat_role_ucb_contract.csv", index=False)

    pd.DataFrame(failures).to_csv(out_dir / "failures.csv", index=False)

    eligible_df = out[out["eligible"] == True]
    summary = {
        "label": args.label,
        "min_n": args.min_n,
        "eligible_cells": int(len(eligible_df)),
        "passed_cells": int(eligible_df["gate_pass"].sum()) if len(eligible_df) else 0,
        "failed_cells": int((~eligible_df["gate_pass"]).sum()) if len(eligible_df) else 0,
        "global_pass": bool(len(eligible_df) > 0 and eligible_df["gate_pass"].all()),
        "tau_logloss": args.tau_logloss,
        "tau_brier": args.tau_brier,
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"wrote {out_dir}")

    if failures:
        print("\nWorst failing cells:")
        fail_df = pd.DataFrame(failures)
        fail_df["badness"] = (
            fail_df["logloss_delta_ucb95_model_minus_market"].clip(lower=0)
            + fail_df["brier_delta_ucb95_model_minus_market"].clip(lower=0)
        )
        cols = [
            "stat",
            "role_bucket",
            "n",
            "failure_reason",
            "logloss_delta_ucb95_model_minus_market",
            "brier_delta_ucb95_model_minus_market",
        ]
        print(fail_df.sort_values("badness", ascending=False)[cols].head(20).to_string(index=False))

    return 0 if summary["global_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
