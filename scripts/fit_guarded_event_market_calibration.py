#!/usr/bin/env python3
"""Fit Platt scaling on model line probabilities using outcomes only (no market label).

Walk-forward by date within the loss-row parquet: each date is held out once;
Platt parameters (a,b) are fit on other dates only, evaluated on held-out date.
A segment is selected only if every held-out fold improves logloss and does not
worsen Brier vs raw on that fold.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

REPO_ROOT = Path(__file__).resolve().parents[1]


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p.astype(float), 1e-9, 1.0 - 1e-9)
    return np.log(p / (1.0 - p))


def _metrics(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    p = np.clip(p.astype(float), 1e-9, 1.0 - 1e-9)
    ll = float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))
    br = float(np.mean((p - y) ** 2))
    return ll, br


def _fit_platt(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return (a, b) for logit(p') = a + b*logit(p)."""

    def nll(ab: np.ndarray) -> float:
        a, b = float(ab[0]), float(ab[1])
        z = a + b * _logit(p)
        q = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        q = np.clip(q, 1e-9, 1.0 - 1e-9)
        return float(-np.mean(y * np.log(q) + (1.0 - y) * np.log(1.0 - q)))

    res = minimize(nll, x0=np.array([0.0, 1.0]), method="L-BFGS-B", bounds=[(-4.0, 4.0), (0.2, 5.0)])
    return float(res.x[0]), float(res.x[1])


def _apply_platt(p: np.ndarray, a: float, b: float) -> np.ndarray:
    z = a + b * _logit(p)
    q = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
    return np.clip(q, 1e-9, 1.0 - 1e-9)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--min-rows-per_fold", type=int, default=15)
    args = ap.parse_args()
    label = args.label.strip()

    eml = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    diag = (
        REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}" / "segment_failure_diagnosis.csv"
    )
    if not eml.is_file():
        print(f"MISSING {eml}", file=sys.stderr)
        return 2

    combo = pd.read_parquet(eml)
    p_fit_col = (
        "model_prob_over_pre_event_calibration"
        if "model_prob_over_pre_event_calibration" in combo.columns
        else "model_probability_for_side"
    )
    targets: list[tuple[str, str]] = []
    if diag.is_file():
        df = pd.read_csv(diag)
        df = df[df.get("precise_failure_reason", "") == "model_logloss_not_better"]
        for _, r in df.iterrows():
            targets.append((str(r["stat"]).lower(), str(r["role_bucket"])))
    if not targets:
        for (s, rb), _cnt in combo.groupby(["stat", "role_bucket"]).size().items():
            targets.append((str(s).lower(), str(rb)))
            if len(targets) >= 12:
                break

    cand_rows: list[dict] = []
    selected: dict = {}
    roll_rows: list[dict] = []

    dates = sorted(combo["date"].astype(str).unique()) if "date" in combo.columns else []

    for stat, role in targets:
        sub = combo[
            (combo["stat"].astype(str).str.lower() == stat)
            & (combo["role_bucket"].astype(str) == role)
            & (combo["join_status"] == "matched")
            & (combo["settled"] == True)
        ].copy()
        p = pd.to_numeric(sub[p_fit_col], errors="coerce")
        y = pd.to_numeric(sub["hit_result"], errors="coerce")
        mask = p.notna() & y.notna() & y.isin([0.0, 1.0])
        sub = sub.loc[mask]
        p = p[mask].to_numpy(dtype=float)
        y = y[mask].to_numpy(dtype=float)
        if len(sub) < 2 * args.min_rows_per_fold or not dates:
            roll_rows.append(
                {"stat": stat, "role_bucket": role, "reason": "insufficient_rows_or_no_dates"}
            )
            continue
        dvals = sub["date"].astype(str).to_numpy()
        ok_folds = True
        a_b = (0.0, 1.0)
        if len(dates) >= 2:
            for held in dates:
                tr = sub[dvals != held]
                va = sub[dvals == held]
                if len(tr) < args.min_rows_per_fold or len(va) < args.min_rows_per_fold:
                    ok_folds = False
                    roll_rows.append({"stat": stat, "role_bucket": role, "reason": f"small_fold_{held}"})
                    break
                pt = pd.to_numeric(tr[p_fit_col], errors="coerce").to_numpy()
                yt = pd.to_numeric(tr["hit_result"], errors="coerce").to_numpy()
                mtr = pt == pt
                pt, yt = pt[mtr], yt[mtr]
                yt = yt[np.isin(yt, [0, 1])]
                pt = pt[: len(yt)]
                if len(pt) < args.min_rows_per_fold:
                    ok_folds = False
                    break
                a, b = _fit_platt(pt, yt)
                pv = pd.to_numeric(va[p_fit_col], errors="coerce").to_numpy()
                yv = pd.to_numeric(va["hit_result"], errors="coerce").to_numpy()
                mv = np.isfinite(pv) & np.isin(yv, [0, 1])
                pv, yv = pv[mv], yv[mv]
                if len(pv) < 5:
                    ok_folds = False
                    break
                raw_ll, raw_br = _metrics(pv, yv)
                cal = _apply_platt(pv, a, b)
                new_ll, new_br = _metrics(cal, yv)
                if new_ll >= raw_ll or new_br > raw_br + 1e-6:
                    ok_folds = False
                    roll_rows.append(
                        {
                            "stat": stat,
                            "role_bucket": role,
                            "held_date": held,
                            "raw_ll": raw_ll,
                            "new_ll": new_ll,
                            "raw_br": raw_br,
                            "new_br": new_br,
                            "reason": "rollback_fold_worse",
                        }
                    )
                    break
                a_b = (a, b)
        else:
            a, b = _fit_platt(p, y)
            raw_ll, raw_br = _metrics(p, y)
            new_ll, new_br = _metrics(_apply_platt(p, a, b), y)
            if new_ll >= raw_ll or new_br > raw_br + 1e-6:
                ok_folds = False
                roll_rows.append({"stat": stat, "role_bucket": role, "reason": "single_split_worse"})
            a_b = (a, b)

        cand_rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": int(len(p)),
                "type": "platt",
                "a": a_b[0],
                "b": a_b[1],
                "selected": bool(ok_folds),
            }
        )
        if ok_folds:
            key = f"{stat}|{role}"
            selected[key] = {"type": "platt", "a": a_b[0], "b": a_b[1]}

    out_model = REPO_ROOT / "artifacts" / "models" / "guarded_event_calibration.json"
    out_model.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "event_calibration_applied": True,
        "event_calibration_version": "guarded_platt_v1",
        "event_calibration_stage": "oof_date_holdout_one_fold_per_date",
        "event_calibration_source": "guarded_oof_actuals_only",
        "market_pmf_used": False,
        "market_prob_used_as_training_label": False,
        "segments": selected,
    }
    out_model.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    diag_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"guarded_event_calibration_{label}"
    diag_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cand_rows).to_csv(diag_dir / "candidate_results.csv", index=False)
    rows_sel = [{"segment": k, "spec_json": json.dumps(v)} for k, v in selected.items()]
    pd.DataFrame(rows_sel).to_csv(diag_dir / "selected_calibrators.csv", index=False)
    pd.DataFrame(roll_rows).to_csv(diag_dir / "rollback_report.csv", index=False)
    (diag_dir / "summary.json").write_text(
        json.dumps(
            {"n_selected": len(selected), "n_rollbacks": len(roll_rows), "out_model": str(out_model.relative_to(REPO_ROOT))},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_model} selected={len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
