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
    load_stat_grid_delivery_recalibrator,
    repair_and_validate_pmf,
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
    return _pick_col(df, ["raw_pmf_json", "model_pmf_json", "pmf_json", "pmf", "model_pmf", "pmf_dict", "model_pmf_dict"])  # type: ignore


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
    return float(max(np.max(i / n - vals), np.max(vals - (i - 1) / n)))


def _metrics(df: pd.DataFrame, pmfs: list[np.ndarray], outcome_col: str) -> dict[str, float | bool]:
    ys = df[outcome_col].astype(int).to_numpy()
    mus, vars_, nlls, rpss, pits, p0s, zeros = [], [], [], [], [], [], []
    for p, y in zip(pmfs, ys):
        p = repair_and_validate_pmf(p)
        mu, var = _moments(p)
        mus.append(mu)
        vars_.append(var)
        nlls.append(_nll(p, int(y)))
        rpss.append(_rps(p, int(y)))
        pits.append(_pit_mid(p, int(y)))
        p0s.append(float(p[0]))
        zeros.append(1.0 if int(y) == 0 else 0.0)
    mean_ae = float(np.sum(ys) / max(np.sum(mus), 1e-12))
    variance_ae = float(np.sum((ys - np.asarray(mus)) ** 2) / max(np.sum(vars_), 1e-12))
    p0_err = float(np.mean(zeros) - np.mean(p0s))
    pit_ks = _ks_uniform(np.asarray(pits))
    mean_pass = abs(mean_ae - 1.0) <= 0.02
    variance_pass = 0.90 <= variance_ae <= 1.10
    p0_pass = abs(p0_err) <= 0.03
    pit_pass = pit_ks <= 0.08
    return {
        "n": float(len(df)),
        "mean_ae": mean_ae,
        "variance_ae": variance_ae,
        "p0_error": p0_err,
        "pit_ks": pit_ks,
        "nll": float(np.mean(nlls)),
        "rps": float(np.mean(rpss)),
        "mean_pass": bool(mean_pass),
        "variance_pass": bool(variance_pass),
        "p0_pass": bool(p0_pass),
        "pit_pass": bool(pit_pass),
        "internal_pass": bool(mean_pass and variance_pass and p0_pass and pit_pass),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag-dir", default=None)
    ap.add_argument("--model-dir", default=None)
    ap.add_argument("--min-supported-n", type=int, default=1000)
    args = ap.parse_args()

    diag = Path(args.diag_dir) if args.diag_dir else _find_latest_diag()
    model_dir = Path(args.model_dir or os.environ.get("STAT_GRID_RECALIBRATION_MODEL_DIR", "_stat_grid_delivery_calibration_optimizer/artifacts/models"))
    recal = load_stat_grid_delivery_recalibrator(model_dir)

    row_path = diag / "row_level_internal_pmf_scores.parquet"
    if not row_path.exists():
        row_path = diag / "row_level_internal_pmf_scores.csv"
    if not row_path.exists():
        raise SystemExit(f"FATAL: missing row_level_internal_pmf_scores in {diag}")
    df = pd.read_parquet(row_path) if row_path.suffix == ".parquet" else pd.read_csv(row_path)

    stat_col = _pick_col(df, ["stat", "prop_type"])
    role_col = _pick_col(df, ["role_bucket", "role"])
    outcome_col = _pick_col(df, ["actual", "outcome", "y", "actual_value", "result"])
    pmf_col = _pmf_col(df)

    work = df[[stat_col, role_col, outcome_col, pmf_col]].dropna().copy()
    work[stat_col] = work[stat_col].astype(str).str.lower()
    work[role_col] = work[role_col].astype(str).str.lower()
    work[outcome_col] = work[outcome_col].astype(int)

    rows = []
    before_fail = after_fail = supported = 0
    nll_improved = rps_improved = 0
    before_aggs = []
    after_aggs = []

    for (stat, role), sub in work.groupby([stat_col, role_col], dropna=False):
        if len(sub) < args.min_supported_n:
            continue
        supported += 1
        pmfs_before = [_parse_pmf(x) for x in sub[pmf_col].to_list()]
        pmfs_after = [recal.apply(p, stat=stat, role_bucket=role)[0] for p in pmfs_before]
        b = _metrics(sub, pmfs_before, outcome_col)
        a = _metrics(sub, pmfs_after, outcome_col)
        before_fail += 0 if b["internal_pass"] else 1
        after_fail += 0 if a["internal_pass"] else 1
        nll_improved += 1 if float(a["nll"]) < float(b["nll"]) else 0
        rps_improved += 1 if float(a["rps"]) < float(b["rps"]) else 0
        before_aggs.append(b)
        after_aggs.append(a)
        rows.append({
            "stat": stat, "role_bucket": role, "n": len(sub),
            **{f"before_{k}": v for k, v in b.items()},
            **{f"after_{k}": v for k, v in a.items()},
            "mean_ae_abs_error_delta": abs(float(a["mean_ae"]) - 1.0) - abs(float(b["mean_ae"]) - 1.0),
            "variance_ae_abs_error_delta": abs(float(a["variance_ae"]) - 1.0) - abs(float(b["variance_ae"]) - 1.0),
            "p0_abs_error_delta": abs(float(a["p0_error"])) - abs(float(b["p0_error"])),
            "pit_ks_delta": float(a["pit_ks"]) - float(b["pit_ks"]),
            "nll_delta": float(a["nll"]) - float(b["nll"]),
            "rps_delta": float(a["rps"]) - float(b["rps"]),
        })

    out_dir = Path("_stat_grid_delivery_calibration_optimizer/verification") / ("before_after_oof_" + pd.Timestamp.utcnow().strftime("%Y%m%dT%H%M%SZ"))
    out_dir.mkdir(parents=True, exist_ok=True)
    comp = pd.DataFrame(rows).sort_values(["after_internal_pass", "pit_ks_delta", "nll_delta"], ascending=[True, False, False]) if rows else pd.DataFrame()
    comp.to_csv(out_dir / "before_after_stat_role_comparison.csv", index=False)
    try:
        comp.to_parquet(out_dir / "before_after_stat_role_comparison.parquet", index=False)
    except Exception:
        pass

    def avg(metric: str, items: list[dict[str, Any]], transform=lambda x: x):
        if not items:
            return None
        return float(np.mean([transform(float(x[metric])) for x in items]))

    summary = {
        "out_dir": str(out_dir.resolve()),
        "n_rows_before": int(len(work)),
        "n_rows_after": int(len(work)),
        "supported_cells_before": supported,
        "failed_supported_stat_role_cells_before": before_fail,
        "failed_supported_stat_role_cells_after": after_fail,
        "failed_cell_reduction": before_fail - after_fail,
        "mean_ae_abs_error_avg_before": avg("mean_ae", before_aggs, lambda x: abs(x - 1.0)),
        "mean_ae_abs_error_avg_after": avg("mean_ae", after_aggs, lambda x: abs(x - 1.0)),
        "variance_ae_abs_error_avg_before": avg("variance_ae", before_aggs, lambda x: abs(x - 1.0)),
        "variance_ae_abs_error_avg_after": avg("variance_ae", after_aggs, lambda x: abs(x - 1.0)),
        "p0_abs_error_avg_before": avg("p0_error", before_aggs, abs),
        "p0_abs_error_avg_after": avg("p0_error", after_aggs, abs),
        "pit_ks_avg_before": avg("pit_ks", before_aggs),
        "pit_ks_avg_after": avg("pit_ks", after_aggs),
        "n_cells_nll_improved": nll_improved,
        "n_cells_rps_improved": rps_improved,
        "market_pmf_used": False,
        "market_superiority_claim_allowed": False,
    }
    (out_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2))
    report_lines = ["# Before/After OOF Recalibration Verification", "", "```json", json.dumps(summary, indent=2), "```", ""]
    if not comp.empty:
        report_lines += ["## Worst after cells / regressions", "", comp.head(25).to_string(index=False)]
    (out_dir / "BEFORE_AFTER_OOF_VERIFICATION_REPORT.md").write_text("\n".join(report_lines))
    print(json.dumps(summary, indent=2))
    print(f"REPORT={out_dir / 'BEFORE_AFTER_OOF_VERIFICATION_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
