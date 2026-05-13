#!/usr/bin/env python3
"""Build segment-level before/after event probability metrics from loss rows."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ART = REPO_ROOT / "artifacts" / "model_diagnostics"


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(p, 1e-12, 1.0 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def _ece(p: np.ndarray, y: np.ndarray, n_bins: int = 10) -> float:
    if len(p) < n_bins:
        return float("nan")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi if hi < 1.0 else p <= 1.0)
        n = int(m.sum())
        if n == 0:
            continue
        conf = float(p[m].mean())
        acc = float(y[m].mean())
        ece += (n / len(p)) * abs(acc - conf)
    return float(ece)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument(
        "--ledger",
        default=None,
        help="Optional repair_ledger.csv for claim_status / calibration flags.",
    )
    args = ap.parse_args()
    label = str(args.label)
    pq = ART / f"event_market_loss_rows_{label}.parquet"
    if not pq.is_file():
        raise SystemExit(f"FATAL: missing {pq}")
    df = pd.read_parquet(pq)
    need = ("hit_result", "model_prob_over_raw", "model_prob_over_active", "market_prob_over_no_vig")
    for c in need:
        if c not in df.columns:
            raise SystemExit(f"FATAL: missing column {c} in loss rows (rebuild with patched builder)")
    m = df["hit_result"].isin([0, 1]) & df["model_prob_over_raw"].notna() & df["model_prob_over_active"].notna()
    d = df.loc[m].copy()

    rows_out: list[dict] = []
    for (stat, role), g in d.groupby(["stat", "role_bucket"]):
        yi = g["hit_result"].astype(float).to_numpy()
        pri = g["model_prob_over_raw"].astype(float).to_numpy()
        pai = g["model_prob_over_active"].astype(float).to_numpy()
        mki = g["market_prob_over_no_vig"].astype(float).to_numpy()
        rows_out.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": int(len(g)),
                "raw_model_logloss": _logloss(pri, yi),
                "repaired_model_logloss": _logloss(pai, yi),
                "market_logloss": _logloss(mki, yi),
                "raw_model_brier": _brier(pri, yi),
                "repaired_model_brier": _brier(pai, yi),
                "market_brier": _brier(mki, yi),
                "raw_ece": _ece(pri, yi),
                "repaired_ece": _ece(pai, yi),
                "raw_calibration_pass": math.nan,
                "repaired_calibration_pass": math.nan,
                "raw_market_superiority_pass": math.nan,
                "repaired_market_superiority_pass": math.nan,
                "raw_model_better_calibrated": math.nan,
                "repaired_model_better_calibrated": math.nan,
                "selected_scope": "",
                "selected_method": "",
                "rollback_reason": "",
            }
        )

    out = pd.DataFrame(rows_out)
    selp = ART / f"market_superiority_repair_{label}" / "probability_scale_selected_calibrators.csv"
    if selp.is_file():
        sel = pd.read_csv(selp)
        if not sel.empty and {"stat", "role_bucket", "selected_scope", "selected_method"}.issubset(
            set(sel.columns)
        ):
            rr_col = sel["rollback_reason"] if "rollback_reason" in sel.columns else pd.Series([""] * len(sel))
            sel2 = sel[["stat", "role_bucket", "selected_scope", "selected_method"]].copy()
            sel2["rollback_reason_scale"] = rr_col
            out = out.drop(columns=["selected_scope", "selected_method", "rollback_reason"], errors="ignore")
            out = out.merge(sel2, on=["stat", "role_bucket"], how="left")
            out = out.rename(columns={"rollback_reason_scale": "rollback_reason"})
    if args.ledger:
        lp = Path(args.ledger)
        if not lp.is_file():
            lp = REPO_ROOT / lp
        if lp.is_file():
            led = pd.read_csv(lp)
            cols = [
                c
                for c in (
                    "stat",
                    "role_bucket",
                    "calibration_pass",
                    "market_superiority_pass",
                    "model_better_calibrated",
                    "claim_status",
                )
                if c in led.columns
            ]
            out = out.merge(led[cols], on=["stat", "role_bucket"], how="left")
            ren = {}
            if "calibration_pass" in out.columns:
                ren["calibration_pass"] = "repaired_calibration_pass"
            if "market_superiority_pass" in out.columns:
                ren["market_superiority_pass"] = "repaired_market_superiority_pass"
            if "model_better_calibrated" in out.columns:
                ren["model_better_calibrated"] = "repaired_model_better_calibrated"
            out = out.rename(columns=ren)

    out_dir = ART / f"market_superiority_repair_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    outp = out_dir / "event_probability_before_after.csv"
    out.to_csv(outp, index=False)
    print(f"Wrote {outp.relative_to(REPO_ROOT)} rows={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
