#!/usr/bin/env python3
"""Guarded line-probability calibration on event-market rows (outcomes only, no market label).

Walk-forward by date: each date is held out; fit on other dates; accept only if every
fold improves logloss and does not worsen Brier vs raw on the held-out fold.

Candidates (per segment, pick first that passes all folds, else none):
  - platt: logit(p') = a + b*logit(p)
  - line_aware: logit(p') = a + b*logit(p) + c*z_line (z from training fold mean/std)
  - isotonic: 1D isotonic regression on raw p (sklearn), serialized as thresholds
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.isotonic import IsotonicRegression

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


def _fit_line_aware(p: np.ndarray, y: np.ndarray, z: np.ndarray) -> tuple[float, float, float]:
    """logit(p') = a + b*logit(p) + c*z."""

    def nll(abc: np.ndarray) -> float:
        a, b, c = float(abc[0]), float(abc[1]), float(abc[2])
        s = a + b * _logit(p) + c * z.astype(float)
        q = 1.0 / (1.0 + np.exp(-np.clip(s, -30, 30)))
        q = np.clip(q, 1e-9, 1.0 - 1e-9)
        return float(-np.mean(y * np.log(q) + (1.0 - y) * np.log(1.0 - q)))

    res = minimize(
        nll,
        x0=np.array([0.0, 1.0, 0.0]),
        method="L-BFGS-B",
        bounds=[(-4.0, 4.0), (0.2, 5.0), (-3.0, 3.0)],
    )
    return float(res.x[0]), float(res.x[1]), float(res.x[2])


def _apply_line_aware(p: np.ndarray, z: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    s = a + b * _logit(p) + c * z.astype(float)
    q = 1.0 / (1.0 + np.exp(-np.clip(s, -30, 30)))
    return np.clip(q, 1e-9, 1.0 - 1e-9)


def _fit_apply_isotonic(p_tr: np.ndarray, y_tr: np.ndarray, p_va: np.ndarray) -> np.ndarray:
    order = np.argsort(p_tr)
    iso = IsotonicRegression(y_min=1e-6, y_max=1.0 - 1e-6, out_of_bounds="clip")
    iso.fit(p_tr[order], y_tr[order])
    return np.clip(iso.predict(p_va), 1e-9, 1.0 - 1e-9), iso


def _iso_to_spec(iso: IsotonicRegression) -> dict:
    return {
        "type": "isotonic",
        "x_thresholds": [float(x) for x in iso.X_thresholds_],
        "y_thresholds": [float(y) for y in iso.y_thresholds_],
    }


def _eval_method_date_folds(
    *,
    sub: pd.DataFrame,
    dates: list[str],
    p_fit_col: str,
    min_rows: int,
    method: str,
) -> tuple[bool, dict | None, list[dict]]:
    """Return (all_folds_ok, spec_for_full_refit, rollback_rows)."""
    roll: list[dict] = []
    dvals = sub["date"].astype(str).to_numpy()
    y_all = pd.to_numeric(sub["hit_result"], errors="coerce").to_numpy()
    p_all = pd.to_numeric(sub[p_fit_col], errors="coerce").to_numpy()
    line_all = pd.to_numeric(sub["line"], errors="coerce").to_numpy() if "line" in sub.columns else None

    if len(dates) < 2:
        m = np.isfinite(p_all) & np.isin(y_all, [0.0, 1.0])
        p0, y0 = p_all[m], y_all[m]
        if len(p0) < min_rows * 2:
            return False, None, [{"reason": "insufficient_rows_single_split"}]
        if method == "platt":
            a, b = _fit_platt(p0, y0)
            raw_ll, raw_br = _metrics(p0, y0)
            new_ll, new_br = _metrics(_apply_platt(p0, a, b), y0)
            if new_ll >= raw_ll or new_br > raw_br + 1e-6:
                return False, None, [{"reason": "single_split_worse", "raw_ll": raw_ll, "new_ll": new_ll}]
            return True, {"type": "platt", "a": a, "b": b}, []
        if method == "line_aware" and line_all is not None and np.nanstd(line_all[m]) > 1e-9:
            mu = float(np.nanmean(line_all[m]))
            sig = float(np.nanstd(line_all[m])) or 1.0
            z0 = (line_all[m] - mu) / sig
            a, b, c = _fit_line_aware(p0, y0, z0)
            raw_ll, raw_br = _metrics(p0, y0)
            new_ll, new_br = _metrics(_apply_line_aware(p0, z0, a, b, c), y0)
            if new_ll >= raw_ll or new_br > raw_br + 1e-6:
                return False, None, [{"reason": "single_split_worse_line"}]
            return True, {"type": "line_aware", "a": a, "b": b, "c": c, "line_mu": mu, "line_std": sig}, []
        if method == "isotonic":
            raw_ll, raw_br = _metrics(p0, y0)
            cal, iso = _fit_apply_isotonic(p0, y0, p0)
            new_ll, new_br = _metrics(cal, y0)
            if new_ll >= raw_ll or new_br > raw_br + 1e-6:
                return False, None, [{"reason": "single_split_worse_iso"}]
            return True, _iso_to_spec(iso), []
        return False, None, [{"reason": "method_not_applicable"}]

    last_spec: dict | None = None
    for held in dates:
        tr = sub[dvals != held]
        va = sub[dvals == held]
        if len(tr) < min_rows or len(va) < min_rows:
            roll.append({"held_date": held, "reason": "small_fold"})
            return False, None, roll
        pt = pd.to_numeric(tr[p_fit_col], errors="coerce").to_numpy()
        yt = pd.to_numeric(tr["hit_result"], errors="coerce").to_numpy()
        mtr = np.isfinite(pt) & np.isin(yt, [0.0, 1.0])
        pt, yt = pt[mtr], yt[mtr]
        if len(pt) < min_rows:
            roll.append({"held_date": held, "reason": "small_train"})
            return False, None, roll

        pv = pd.to_numeric(va[p_fit_col], errors="coerce").to_numpy()
        yv = pd.to_numeric(va["hit_result"], errors="coerce").to_numpy()
        mv = np.isfinite(pv) & np.isin(yv, [0.0, 1.0])
        pv, yv = pv[mv], yv[mv]
        if len(pv) < 5:
            roll.append({"held_date": held, "reason": "small_val"})
            return False, None, roll

        raw_ll, raw_br = _metrics(pv, yv)

        if method == "platt":
            a, b = _fit_platt(pt, yt)
            cal = _apply_platt(pv, a, b)
            spec_fold = {"type": "platt", "a": a, "b": b}
        elif method == "line_aware" and "line" in tr.columns and "line" in va.columns:
            lt = pd.to_numeric(tr["line"], errors="coerce").to_numpy()[mtr]
            lv = pd.to_numeric(va["line"], errors="coerce").to_numpy()[mv]
            mu = float(np.nanmean(lt))
            sig = float(np.nanstd(lt)) or 1.0
            if not np.isfinite(sig) or sig < 1e-9:
                roll.append({"held_date": held, "reason": "line_std_zero"})
                return False, None, roll
            zt = (lt - mu) / sig
            zv = (lv - mu) / sig
            a, b, c = _fit_line_aware(pt, yt, zt)
            cal = _apply_line_aware(pv, zv, a, b, c)
            spec_fold = {"type": "line_aware", "a": a, "b": b, "c": c, "line_mu": mu, "line_std": sig}
        elif method == "isotonic":
            _, iso = _fit_apply_isotonic(pt, yt, pv)
            cal = np.clip(iso.predict(pv), 1e-9, 1.0 - 1e-9)
            spec_fold = _iso_to_spec(iso)
        else:
            return False, None, [{"reason": "unknown_method"}]

        new_ll, new_br = _metrics(cal, yv)
        if new_ll >= raw_ll or new_br > raw_br + 1e-6:
            roll.append(
                {
                    "held_date": held,
                    "raw_ll": raw_ll,
                    "new_ll": new_ll,
                    "raw_br": raw_br,
                    "new_br": new_br,
                    "reason": "rollback_fold_worse",
                    "method": method,
                }
            )
            return False, None, roll
        last_spec = spec_fold

    # Refit final spec on all rows for storage (parameters stable for platt/line; isotonic refit on all)
    m = np.isfinite(p_all) & np.isin(y_all, [0.0, 1.0])
    p0, y0 = p_all[m], y_all[m]
    if method == "platt":
        a, b = _fit_platt(p0, y0)
        return True, {"type": "platt", "a": a, "b": b}, roll
    if method == "line_aware" and line_all is not None:
        mu = float(np.nanmean(line_all[m]))
        sig = float(np.nanstd(line_all[m])) or 1.0
        if sig < 1e-9:
            return False, None, roll
        z0 = (line_all[m] - mu) / sig
        a, b, c = _fit_line_aware(p0, y0, z0)
        return True, {"type": "line_aware", "a": a, "b": b, "c": c, "line_mu": mu, "line_std": sig}, roll
    if method == "isotonic":
        _, iso = _fit_apply_isotonic(p0, y0, p0)
        return True, _iso_to_spec(iso), roll
    return bool(last_spec), last_spec, roll


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--min-rows-per_fold", type=int, default=15)
    args = ap.parse_args()
    label = args.label.strip()

    eml = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    diag = (
        REPO_ROOT
        / "artifacts"
        / "model_diagnostics"
        / f"event_market_superiority_{label}"
        / "segment_failure_diagnosis.csv"
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
    method_order = ["platt", "line_aware", "isotonic"]

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
            cand_rows.append(
                {"stat": stat, "role_bucket": role, "n": int(len(p)), "method": "none", "selected": False}
            )
            continue

        picked: dict | None = None
        picked_method = "none"
        for method in method_order:
            if method == "line_aware" and "line" not in sub.columns:
                continue
            ok, spec, rolls = _eval_method_date_folds(
                sub=sub, dates=dates, p_fit_col=p_fit_col, min_rows=args.min_rows_per_fold, method=method
            )
            for r in rolls:
                roll_rows.append({"stat": stat, "role_bucket": role, **r})
            if ok and spec:
                picked = spec
                picked_method = method
                break

        cand_rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": int(len(p)),
                "method": picked_method,
                "selected": picked is not None,
            }
        )
        if picked:
            selected[f"{stat}|{role}"] = picked

    out_model = REPO_ROOT / "artifacts" / "models" / "guarded_event_calibration.json"
    out_model.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "event_calibration_applied": True,
        "event_calibration_version": "guarded_line_iso_platt_v1",
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
            {
                "n_selected": len(selected),
                "n_rollbacks": len(roll_rows),
                "out_model": str(out_model.relative_to(REPO_ROOT)),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_model} selected={len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
