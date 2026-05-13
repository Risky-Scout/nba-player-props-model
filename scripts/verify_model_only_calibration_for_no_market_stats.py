#!/usr/bin/env python3
"""Internal OOF calibration metrics for stats with no offered market lines (evaluation-only).

Does not set market_superiority_claim_allowed. Writes model_only_calibration_claim_allowed
when per-segment gates pass on OOF rows (no market PMF / no market labels).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]

NO_MARKET_STATS = frozenset({"stl", "blk", "stocks", "pa", "pr", "ra", "pra"})


def _parse_pmf_cell(v) -> dict[int, float] | None:
    if v is None:
        return None
    try:
        if isinstance(v, float) and v != v:
            return None
    except Exception:
        pass
    raw: dict | list | np.ndarray | None = None
    if isinstance(v, dict):
        raw = v
    elif isinstance(v, (list, tuple, np.ndarray)):
        arr = np.asarray(v, dtype=float).ravel()
        if arr.size == 0 or not np.all(np.isfinite(arr)):
            return None
        s = float(arr.sum())
        if s <= 0:
            return None
        raw = {int(i): float(arr[i]) / s for i in range(int(arr.size))}
    else:
        s = str(v)
        if not s.startswith("{"):
            return None
        raw = json.loads(s)
    if raw is None:
        return None
    if isinstance(raw, dict):
        out: dict[int, float] = {}
        for kk, p in raw.items():
            try:
                out[int(kk)] = float(p)
            except Exception:
                continue
        ssum = sum(out.values())
        if ssum <= 0:
            return None
        return {k: float(p) / ssum for k, p in out.items()}
    return None


def _mean_var(d: dict[int, float]) -> tuple[float, float]:
    m = sum(k * p for k, p in d.items())
    m2 = sum(k * k * p for k, p in d.items())
    v = max(m2 - m * m, 0.0)
    return m, v


def _pit_u(d: dict[int, float], y: int) -> float:
    return float(sum(p for k, p in sorted(d.items()) if k <= y))


def _nll(d: dict[int, float], y: int) -> float:
    p = max(d.get(int(y), 0.0), 1e-12)
    return float(-math.log(p))


def _rps(d: dict[int, float], y: int) -> float:
    y = int(y)
    hi = max(max(d.keys()) if d else 0, y, 0)
    tot = 0.0
    for m in range(0, hi + 1):
        f = sum(d.get(k, 0.0) for k in range(0, m + 1))
        h = 1.0 if y <= m else 0.0
        tot += (f - h) ** 2
    return float(tot)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--min-n", type=int, default=50)
    ap.add_argument("--pit-p-min", type=float, default=0.01)
    ap.add_argument("--max-mean-abs-err", type=float, default=0.45)
    args = ap.parse_args()
    label = args.label.strip()

    oof_path = REPO_ROOT / "data" / "oof_pmfs.parquet"
    combo_path = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"
    if not oof_path.is_file():
        print(f"MISSING {oof_path}", file=sys.stderr)
        return 2

    parts: list[pd.DataFrame] = [pd.read_parquet(oof_path)]
    if combo_path.is_file():
        parts.append(pd.read_parquet(combo_path))
    df = pd.concat(parts, ignore_index=True)
    df["stat"] = df["stat"].astype(str).str.lower()
    df = df[df["stat"].isin(NO_MARKET_STATS)].copy()
    if df.empty:
        print("NO_OOF_ROWS_FOR_NO_MARKET_STATS", file=sys.stderr)
        return 1

    pmf_col = "pmf_active" if "pmf_active" in df.columns else "pmf"
    alt_pmf = "pmf" if pmf_col == "pmf_active" and "pmf" in df.columns else None

    rows_out: list[dict] = []
    for (stat, role), sub in df.groupby(["stat", "role_bucket"], dropna=False):
        pit_u: list[float] = []
        pred_mean: list[float] = []
        pred_var: list[float] = []
        p0_pred: list[float] = []
        yv: list[int] = []
        nlls: list[float] = []
        rpss: list[float] = []
        for _, r in sub.iterrows():
            raw = r.get(pmf_col)
            if alt_pmf and (raw is None or (isinstance(raw, float) and raw != raw)):
                raw = r.get(alt_pmf)
            d = _parse_pmf_cell(raw)
            if d is None:
                continue
            try:
                y = int(r["outcome"])
            except Exception:
                continue
            pit_u.append(_pit_u(d, y))
            m, v = _mean_var(d)
            pred_mean.append(m)
            pred_var.append(v)
            p0_pred.append(float(d.get(0, 0.0)))
            yv.append(y)
            nlls.append(_nll(d, y))
            rpss.append(_rps(d, y))
        n = len(yv)
        if n < 5:
            continue
        ya = np.asarray(yv, dtype=float)
        pm = float(np.mean(pred_mean))
        vm = float(np.mean(pred_var))
        mean_err = pm - float(np.mean(ya))
        var_err = vm - float(np.var(ya))
        p0_err = float(np.mean(p0_pred)) - float(np.mean(ya == 0))
        pit_p = float(stats.kstest(np.asarray(pit_u, dtype=float), "uniform").pvalue)
        ks_stat = float(stats.kstest(np.asarray(pit_u, dtype=float), "uniform").statistic)
        m_nll = float(np.mean(nlls))
        m_rps = float(np.mean(rpss))
        gate = (
            n >= args.min_n
            and pit_p >= args.pit_p_min
            and abs(mean_err) <= args.max_mean_abs_err
            and math.isfinite(m_nll)
        )
        rows_out.append(
            {
                "stat": stat,
                "role_bucket": str(role),
                "n": n,
                "pit_ks_statistic": ks_stat,
                "pit_ks_pvalue": pit_p,
                "mean_pred": pm,
                "mean_actual": float(np.mean(ya)),
                "mean_error": mean_err,
                "mean_pred_variance": vm,
                "actual_variance": float(np.var(ya)),
                "variance_error": var_err,
                "mean_p0_pred": float(np.mean(p0_pred)),
                "actual_p0_rate": float(np.mean(ya == 0)),
                "p0_error": p0_err,
                "mean_nll": m_nll,
                "mean_rps": m_rps,
                "gate_pass": gate,
            }
        )

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"model_only_no_market_calibration_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows_out).to_csv(out_dir / "stat_role.csv", index=False)

    sub_elig = [r for r in rows_out if r["n"] >= args.min_n]
    claim = bool(sub_elig) and all(r["gate_pass"] for r in sub_elig)
    summary = {
        "label": label,
        "no_market_stats": sorted(NO_MARKET_STATS),
        "min_n": args.min_n,
        "pit_p_min": args.pit_p_min,
        "max_mean_abs_err": args.max_mean_abs_err,
        "n_segments": len(rows_out),
        "n_segments_meeting_min_n": len(sub_elig),
        "model_only_calibration_claim_allowed": claim,
        "market_superiority_claim_allowed": False,
        "note": "OOF-only internal gates; not comparable to market superiority. "
        "Combines data/oof_pmfs.parquet + data/oof_combo_pmfs.parquet (when present) for combo stats.",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("MODEL_ONLY_NO_MARKET_CALIBRATION_VERIFY_DONE")
    print(json.dumps({"model_only_calibration_claim_allowed": claim}, indent=2))
    return 0 if claim else 1


if __name__ == "__main__":
    raise SystemExit(main())
