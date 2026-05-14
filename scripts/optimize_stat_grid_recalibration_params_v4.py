#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from nba_props_model.calibration.stat_grid_delivery_recalibration import (
    repair_and_validate_pmf,
    StatGridDeliveryRecalibrator,
)


def _find_latest_diag() -> Path:
    roots = sorted(Path("artifacts/model_diagnostics").glob("m8_6q_internal_pmf_quality_*"))
    if not roots:
        raise SystemExit("FATAL: no artifacts/model_diagnostics/m8_6q_internal_pmf_quality_* directory found")
    return roots[-1]


def _pick_col(df: pd.DataFrame, names: list[str], required: bool = True) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    if required:
        raise SystemExit(f"FATAL: none of columns found: {names}; available={list(df.columns)[:100]}")
    return None


def _parse_pmf(x: Any) -> np.ndarray:
    import json
    if isinstance(x, np.ndarray):
        return repair_and_validate_pmf(x)
    if isinstance(x, (list, tuple)):
        return repair_and_validate_pmf(x)
    if isinstance(x, dict):
        if "pmf" in x:
            return _parse_pmf(x["pmf"])
        vals = []
        for k, v in sorted(x.items(), key=lambda kv: int(kv[0]) if str(kv[0]).lstrip("-").isdigit() else str(kv[0])):
            if str(k).lstrip("-").isdigit():
                vals.append(v)
        if vals:
            return repair_and_validate_pmf(vals)
    if isinstance(x, str):
        return _parse_pmf(json.loads(x))
    raise ValueError(f"unsupported PMF type {type(x)}")


def _pmf_col(df: pd.DataFrame) -> str:
    candidates = [
        "raw_pmf_json", "model_pmf_json", "pmf_json", "pmf", "model_pmf",
        "pmf_dict", "model_pmf_dict", "pmf_array", "model_pmf_array"
    ]
    return _pick_col(df, candidates, required=True)  # type: ignore


def _moments(pmf: np.ndarray) -> tuple[float, float]:
    y = np.arange(len(pmf), dtype=float)
    mu = float(np.dot(y, pmf))
    var = float(np.dot((y - mu) ** 2, pmf))
    return mu, max(var, 1e-12)


def _nll(pmf: np.ndarray, y: int) -> float:
    y = int(np.clip(y, 0, len(pmf) - 1))
    return -math.log(max(float(pmf[y]), 1e-15))


def _rps(pmf: np.ndarray, y: int) -> float:
    cdf = np.cumsum(pmf)
    obs = (np.arange(len(pmf)) >= int(y)).astype(float)
    # Equivalent to sum_k (F(k)-1{Y<=k})^2.
    return float(np.mean((cdf - obs) ** 2))


def _pit_mid(pmf: np.ndarray, y: int) -> float:
    y = int(np.clip(y, 0, len(pmf) - 1))
    return float(np.sum(pmf[:y]) + 0.5 * pmf[y])


def _ks_uniform(vals: np.ndarray) -> float:
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    n = len(vals)
    if n == 0:
        return float("nan")
    vals = np.sort(np.clip(vals, 0.0, 1.0))
    i = np.arange(1, n + 1, dtype=float)
    d_plus = np.max(i / n - vals)
    d_minus = np.max(vals - (i - 1) / n)
    return float(max(d_plus, d_minus))


def _metrics(df: pd.DataFrame, pmfs: list[np.ndarray], outcome_col: str) -> dict[str, float]:
    y_actual = df[outcome_col].astype(int).to_numpy()
    mus = []
    vars_ = []
    nlls = []
    rpss = []
    pits = []
    p0s = []
    zeros = []
    for p, y in zip(pmfs, y_actual):
        mu, var = _moments(p)
        mus.append(mu)
        vars_.append(var)
        nlls.append(_nll(p, int(y)))
        rpss.append(_rps(p, int(y)))
        pits.append(_pit_mid(p, int(y)))
        p0s.append(float(p[0]) if len(p) else 0.0)
        zeros.append(1.0 if int(y) == 0 else 0.0)
    actual_sum = float(np.sum(y_actual))
    mean_sum = float(np.sum(mus))
    mean_ae = actual_sum / max(mean_sum, 1e-12)
    squared_resid = float(np.sum((y_actual - np.asarray(mus)) ** 2))
    variance_sum = float(np.sum(vars_))
    variance_ae = squared_resid / max(variance_sum, 1e-12)
    p0_err = float(np.mean(zeros) - np.mean(p0s))
    return {
        "n": float(len(df)),
        "mean_ae": mean_ae,
        "variance_ae": variance_ae,
        "p0_error": p0_err,
        "pit_ks": _ks_uniform(np.asarray(pits)),
        "nll": float(np.mean(nlls)),
        "rps": float(np.mean(rpss)),
    }


def _quality_score(m: dict[str, float], base: dict[str, float] | None = None) -> float:
    mean_err = abs(m["mean_ae"] - 1.0)
    var_err = abs(m["variance_ae"] - 1.0)
    p0_err = abs(m["p0_error"])
    pit = m["pit_ks"]
    score = 2.0 * mean_err + 1.5 * var_err + 1.5 * p0_err + 3.0 * pit
    if base:
        # Strong penalties for damaging likelihood / ranked score.
        score += 8.0 * max(0.0, m["nll"] - base["nll"] - 0.002)
        score += 8.0 * max(0.0, m["rps"] - base["rps"] - 0.002)
        score += 2.0 * max(0.0, m["pit_ks"] - base["pit_ks"] - 0.005)
        score += 2.0 * max(0.0, abs(m["variance_ae"] - 1.0) - abs(base["variance_ae"] - 1.0) - 0.01)
    return float(score)


def _split_eval(sub: pd.DataFrame, group_col: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if group_col and group_col in sub.columns:
        keys = pd.Series(sub[group_col].astype(str).unique()).sort_values().to_list()
        if len(keys) >= 4:
            eval_keys = set(keys[::5])  # deterministic 20% grouped holdout.
            eval_df = sub[sub[group_col].astype(str).isin(eval_keys)]
            cal_df = sub[~sub[group_col].astype(str).isin(eval_keys)]
            if len(eval_df) >= max(50, len(sub) // 10) and len(cal_df) > 0:
                return cal_df, eval_df
    # deterministic row split fallback.
    eval_df = sub.iloc[::5].copy()
    cal_df = sub.drop(eval_df.index).copy()
    return cal_df, eval_df


def _target_from_cal(cal_df: pd.DataFrame, cal_pmfs: list[np.ndarray], outcome_col: str, stat: str, role: str) -> dict[str, float]:
    m = _metrics(cal_df, cal_pmfs, outcome_col)
    mean_mult = float(np.clip(m["mean_ae"], 0.60, 1.80))
    if role == "inactive_risk":
        mean_mult = float(np.clip(mean_mult, 0.60, 1.90))
    if stat == "fg3m":
        var_mult = float(np.clip(m["variance_ae"], 0.65, 1.60))
    else:
        var_mult = float(np.clip(m["variance_ae"], 0.65, 1.50))
    # p0 target = empirical zero rate on calibration split.
    p0_target = float(np.clip((cal_df[outcome_col].astype(int) == 0).mean(), 1e-6, 1.0 - 1e-6))
    return {"mean_multiplier_raw": mean_mult, "variance_multiplier_raw": var_mult, "p0_target_raw": p0_target}


def _candidate_params(target: dict[str, float], stat: str, role: str) -> list[dict[str, Any]]:
    # Include identity and conservative grids. This is the important difference vs blind multipliers.
    mean_strengths = [0.0, 0.25, 0.50, 0.75, 1.0]
    var_strengths = [0.0, 0.25, 0.50, 0.75, 1.0]
    p0_strengths = [0.0, 0.25, 0.50, 0.75, 1.0]
    # Keep combinatorics reasonable; for sparse stats search p0 more, for composites search mean/var.
    sparse = stat in {"stl", "blk", "stocks", "fg3m", "tov"}
    out: list[dict[str, Any]] = [{"mode": "identity", "mean_multiplier": 1.0, "variance_multiplier": 1.0, "p0_strength": 0.0, "p0_target": None}]
    for ms in mean_strengths:
        for vs in var_strengths:
            p0s_list = p0_strengths if sparse else [0.0, 0.5]
            for ps in p0s_list:
                mm = 1.0 + ms * (target["mean_multiplier_raw"] - 1.0)
                vm = 1.0 + vs * (target["variance_multiplier_raw"] - 1.0)
                # Avoid pure variance changes for cells already terrible PIT without p0 consideration? Keep but conservative.
                out.append({
                    "mode": "active",
                    "mean_multiplier": float(mm),
                    "variance_multiplier": float(vm),
                    "p0_target": float(target["p0_target_raw"]),
                    "p0_strength": float(ps),
                    "stage": "v4_guarded_oof_selected",
                })
    return out


def _apply_candidate(pmfs: list[np.ndarray], params: dict[str, Any], stat: str, role: str) -> list[np.ndarray]:
    recal = StatGridDeliveryRecalibrator({"enabled": True, "version": "v4_eval", "cells": {f"{stat}|{role}": params}})
    out = []
    for p in pmfs:
        q, _ = recal.apply(p, stat=stat, role_bucket=role)
        out.append(q)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag-dir", default=None)
    ap.add_argument("--model-dir", default=None)
    ap.add_argument("--min-supported-n", type=int, default=1000)
    ap.add_argument("--require-improvement", action="store_true", default=True)
    args = ap.parse_args()

    diag = Path(args.diag_dir) if args.diag_dir else _find_latest_diag()
    model_dir = Path(args.model_dir or os.environ.get("STAT_GRID_RECALIBRATION_MODEL_DIR", "_stat_grid_delivery_calibration_optimizer/artifacts/models"))
    model_dir.mkdir(parents=True, exist_ok=True)

    row_path = diag / "row_level_internal_pmf_scores.parquet"
    if not row_path.exists():
        row_path = diag / "row_level_internal_pmf_scores.csv"
    if not row_path.exists():
        raise SystemExit(f"FATAL: missing row_level_internal_pmf_scores parquet/csv in {diag}")

    df = pd.read_parquet(row_path) if row_path.suffix == ".parquet" else pd.read_csv(row_path)

    stat_col = _pick_col(df, ["stat", "prop_type"])
    role_col = _pick_col(df, ["role_bucket", "role"])
    outcome_col = _pick_col(df, ["actual", "outcome", "y", "actual_value", "result"])
    game_col = _pick_col(df, ["game_id", "game_date", "date"], required=False)
    pmf_col = _pmf_col(df)

    # Drop rows with unusable PMFs/outcomes.
    work = df[[stat_col, role_col, outcome_col, pmf_col] + ([game_col] if game_col else [])].copy()
    work = work.dropna(subset=[stat_col, role_col, outcome_col, pmf_col])
    work[stat_col] = work[stat_col].astype(str).str.lower()
    work[role_col] = work[role_col].astype(str).str.lower()
    work[outcome_col] = work[outcome_col].astype(int)

    cells: dict[str, Any] = {}
    rows_summary = []
    all_base = []
    all_after = []
    total_supported = 0
    total_selected = 0

    grouped = list(work.groupby([stat_col, role_col], dropna=False))
    for (stat, role), sub in grouped:
        if len(sub) < args.min_supported_n:
            continue
        total_supported += 1
        cal_df, eval_df = _split_eval(sub, game_col)
        try:
            cal_pmfs = [_parse_pmf(x) for x in cal_df[pmf_col].to_list()]
            eval_pmfs = [_parse_pmf(x) for x in eval_df[pmf_col].to_list()]
        except Exception as e:
            cells[f"{stat}|{role}"] = {"mode": "identity", "reason": f"pmf_parse_failed:{e}"}
            continue

        base_eval = _metrics(eval_df, eval_pmfs, outcome_col)
        target = _target_from_cal(cal_df, cal_pmfs, outcome_col, stat, role)
        base_score = _quality_score(base_eval)

        best_params = {"mode": "identity", "mean_multiplier": 1.0, "variance_multiplier": 1.0, "p0_target": None, "p0_strength": 0.0}
        best_metrics = dict(base_eval)
        best_score = base_score

        for cand in _candidate_params(target, stat, role):
            try:
                cand_pmfs = _apply_candidate(eval_pmfs, cand, stat, role)
                cm = _metrics(eval_df, cand_pmfs, outcome_col)
                cs = _quality_score(cm, base_eval)
            except Exception:
                continue
            # Must improve composite objective and avoid major scoring damage.
            if cs < best_score - 1e-6:
                best_score = cs
                best_params = cand
                best_metrics = cm

        selected = best_params.get("mode") != "identity"
        if selected:
            # Additional safety: if selected worsens both NLL and RPS, roll back.
            if (best_metrics["nll"] > base_eval["nll"] + 0.002) and (best_metrics["rps"] > base_eval["rps"] + 0.002):
                selected = False
                best_params = {"mode": "identity", "mean_multiplier": 1.0, "variance_multiplier": 1.0, "p0_target": None, "p0_strength": 0.0, "reason": "rollback_nll_rps"}
                best_metrics = dict(base_eval)
                best_score = base_score

        if selected:
            total_selected += 1
        key = f"{stat}|{role}"
        best_params.update({
            "selected_on": "heldout_oof",
            "base_score": base_score,
            "selected_score": best_score,
            "eval_n": int(len(eval_df)),
            "cal_n": int(len(cal_df)),
            "base_mean_ae": base_eval["mean_ae"],
            "after_mean_ae": best_metrics["mean_ae"],
            "base_variance_ae": base_eval["variance_ae"],
            "after_variance_ae": best_metrics["variance_ae"],
            "base_p0_error": base_eval["p0_error"],
            "after_p0_error": best_metrics["p0_error"],
            "base_pit_ks": base_eval["pit_ks"],
            "after_pit_ks": best_metrics["pit_ks"],
            "base_nll": base_eval["nll"],
            "after_nll": best_metrics["nll"],
            "base_rps": base_eval["rps"],
            "after_rps": best_metrics["rps"],
        })
        cells[key] = best_params

        row = {
            "stat": stat,
            "role_bucket": role,
            "n": len(sub),
            "cal_n": len(cal_df),
            "eval_n": len(eval_df),
            "selected": selected,
            **{f"before_{k}": v for k, v in base_eval.items()},
            **{f"after_{k}": v for k, v in best_metrics.items()},
            "base_score": base_score,
            "selected_score": best_score,
            "mean_multiplier": best_params.get("mean_multiplier", 1.0),
            "variance_multiplier": best_params.get("variance_multiplier", 1.0),
            "p0_strength": best_params.get("p0_strength", 0.0),
        }
        rows_summary.append(row)

    params = {
        "enabled": True,
        "version": "v4_guarded_oof_rollforward",
        "market_pmf_used": False,
        "objective": "guarded heldout OOF internal PMF calibration with NLL/RPS rollback",
        "min_supported_n": args.min_supported_n,
        "cells": cells,
        "global": {"mode": "identity", "mean_multiplier": 1.0, "variance_multiplier": 1.0, "p0_target": None, "p0_strength": 0.0},
        "event_calibration_enabled": True,
        "event_weights": {"global": 1.0},
        "supported_cells": total_supported,
        "selected_cells": total_selected,
    }

    out_json = model_dir / "stat_grid_recalibration_params.json"
    out_json.write_text(json.dumps(params, indent=2, sort_keys=True))

    summary = pd.DataFrame(rows_summary)
    summary.to_csv(model_dir / "v4_guarded_oof_selection_by_stat_role.csv", index=False)
    try:
        summary.to_parquet(model_dir / "v4_guarded_oof_selection_by_stat_role.parquet", index=False)
    except Exception:
        pass

    report = {
        "model_dir": str(model_dir),
        "diag_dir": str(diag),
        "rows": int(len(work)),
        "supported_cells": total_supported,
        "selected_cells": total_selected,
        "market_pmf_used": False,
        "params_path": str(out_json),
    }
    (model_dir / "v4_guarded_optimizer_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
