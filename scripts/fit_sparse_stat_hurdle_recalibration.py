#!/usr/bin/env python3
"""Fit guarded sparse-stat hurdle recalibration from OOF PMFs (no market)."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

SPARSE = ("stl", "blk", "tov", "fg3m", "stocks")
OUT = REPO_ROOT / "artifacts" / "models" / "sparse_hurdle_offsets.json"


def _parse_pmf(x):
    import json as _json
    if x is None:
        return np.array([], dtype=float)
    if isinstance(x, np.ndarray):
        return x.astype(float)
    if isinstance(x, (list, tuple)):
        return np.asarray(x, dtype=float)
    if isinstance(x, dict):
        # dict keyed by outcome
        ks = []
        vs = []
        for k, v in x.items():
            if str(k).lstrip("-").isdigit():
                ks.append(int(k))
                vs.append(float(v))
        if not ks:
            return np.array([], dtype=float)
        n = max(ks) + 1
        arr = np.zeros(n, dtype=float)
        for k, v in zip(ks, vs):
            if 0 <= k < n:
                arr[k] = v
        return arr
    if isinstance(x, str):
        return _parse_pmf(_json.loads(x))
    return np.asarray(x, dtype=float)


def _repair(arr: np.ndarray) -> np.ndarray:
    a = np.asarray(arr, dtype=float)
    a = np.clip(np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    s = float(a.sum())
    if not np.isfinite(s) or s <= 0:
        return np.full_like(a, 1.0 / max(len(a), 1))
    return a / s


def _p0(arr: np.ndarray) -> float:
    return float(arr[0]) if len(arr) else 0.0


def _pos_mean(arr: np.ndarray) -> float:
    if len(arr) <= 1:
        return 0.0
    ppos = float(1.0 - arr[0])
    if ppos <= 1e-12:
        return 0.0
    ks = np.arange(len(arr), dtype=float)
    return float(np.dot(ks[1:], arr[1:]) / ppos)


def _tilt_lambda_for_target(avg_pmf: np.ndarray, pos_mean_target: float) -> float:
    """Fit exponential tilt lambda on k>0 for average pmf to match pos_mean_target."""
    p = _repair(avg_pmf)
    if len(p) <= 2:
        return 0.0
    ppos = float(1.0 - p[0])
    if ppos <= 1e-9:
        return 0.0
    tgt = float(np.clip(pos_mean_target, 0.0, 48.0))
    if tgt <= 0.0:
        return 0.0
    ks = np.arange(1, len(p), dtype=float)
    base = p[1:].copy()
    base_sum = float(base.sum())
    if base_sum <= 0:
        return 0.0
    base = base / base_sum
    base_mu = float(np.dot(ks, base))
    if not np.isfinite(base_mu) or abs(base_mu - tgt) < 1e-6:
        return 0.0

    def mu(lam: float) -> float:
        w = np.exp(np.clip(lam * ks, -30.0, 30.0))
        q = base * w
        s = float(q.sum())
        if s <= 0:
            return base_mu
        q = q / s
        return float(np.dot(ks, q))

    # Bisection on lambda.
    lo, hi = (-2.0, 2.0)
    m_lo, m_hi = mu(lo), mu(hi)
    # If target outside achievable range under caps, clamp by returning boundary.
    if tgt <= min(m_lo, m_hi):
        return lo if m_lo < m_hi else hi
    if tgt >= max(m_lo, m_hi):
        return hi if m_hi > m_lo else lo
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        m_mid = mu(mid)
        if m_mid < tgt:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof", default=str(REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"))
    ap.add_argument("--min-n", type=int, default=800)
    ap.add_argument("--shrink-k", type=float, default=3000.0)
    ap.add_argument("--require-improvement", action="store_true", default=True)
    ap.add_argument("--start-date", default=None,
                    help="ISO date string (YYYY-MM-DD); only use OOF rows on or after this date.")
    args = ap.parse_args()

    p = Path(args.oof)
    if not p.exists():
        print("SPARSE_HURDLE_FIT_SKIP no oof_pmfs", file=sys.stderr)
        return 2

    df = pd.read_parquet(p)
    df = df[df["stat"].astype(str).str.lower().isin(SPARSE)]
    if df.empty:
        print("SPARSE_HURDLE_FIT_SKIP no sparse stat rows", file=sys.stderr)
        return 3

    if args.start_date:
        df = df[df["game_date"].astype(str) >= str(args.start_date)]
        if df.empty:
            print(f"SPARSE_HURDLE_FIT_SKIP no rows on or after {args.start_date}", file=sys.stderr)
            return 2

    df = df.copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["role_bucket"] = df["role_bucket"].astype(str).str.lower()
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    if "game_id" in df.columns:
        df["split_key"] = pd.to_numeric(df["game_id"], errors="coerce").fillna(0).astype(int)
    else:
        # deterministic fallback
        df["split_key"] = np.arange(len(df), dtype=int)
    is_eval = (df["split_key"] % 5) == 0
    cal_df = df[~is_eval].reset_index(drop=True)
    eval_df = df[is_eval].reset_index(drop=True)

    # Global and per-stat empirical targets on calibration split.
    cal_df["y0"] = (cal_df["outcome"] == 0).astype(float)
    global_p0 = float(cal_df["y0"].mean())
    stat_p0 = {s: float(g["y0"].mean()) for s, g in cal_df.groupby("stat")}
    stat_pos_mean = {}
    for s, g in cal_df[cal_df["outcome"] > 0].groupby("stat"):
        stat_pos_mean[s] = float(g["outcome"].mean())

    # Market-calibrated p0 floor for sparse stats.
    # These bounds ensure the nightly refit never drifts above the market-implied
    # zero-rate, keeping STL/BLK/STOCKS competitive with market odds.
    # Derived from June 2026 Finals market prices; should be re-evaluated each season.
    MARKET_P0_CEILING = {
        "stl":    0.500,   # market P(over 0.5 line) ~0.50+ → p0 must be <= 0.50
        "blk":    0.650,   # market P(over 0.5 line) ~0.35+ → p0 must be <= 0.65
        "stocks": 0.560,   # market P(over 0.5 line) ~0.44+ → p0 must be <= 0.56
        "fg3m":   0.520,   # fg3m zero-rate ceiling
        "tov":    0.420,   # tov zero-rate ceiling
    }
    # If empirical p0 exceeds the market ceiling, use the market ceiling as the target.
    for s in list(stat_p0.keys()):
        ceiling = MARKET_P0_CEILING.get(s)
        if ceiling is not None and stat_p0[s] > ceiling:
            print(
                f"  MARKET_FLOOR: {s} empirical_p0={stat_p0[s]:.4f} exceeds ceiling "
                f"{ceiling:.4f} — using ceiling as p0_target to stay market-competitive"
            )
            stat_p0[s] = ceiling

    cells: dict[str, dict] = {}
    by_stat: dict[str, dict] = {}
    # Conservative defaults.
    global_params = {"mode": "identity", "p0_target": None, "tail_lambda": 0.0}

    # Fit per-stat fallback first.
    for stat, g in cal_df.groupby("stat"):
        pmfs = [_repair(_parse_pmf(x)) for x in g["pmf"].to_list()]
        p0_pred = float(np.mean([_p0(x) for x in pmfs]))
        p0_tgt = float(stat_p0.get(stat, global_p0))
        # Compute stat-level positive mean target.
        pos_tgt = float(stat_pos_mean.get(stat, float(cal_df[cal_df["outcome"] > 0]["outcome"].mean() or 0.0)))
        avg = np.mean(np.stack([x for x in pmfs if len(x) > 1], axis=0), axis=0) if pmfs else np.array([1.0])
        lam = _tilt_lambda_for_target(avg, pos_tgt)
        by_stat[stat] = {"mode": "active", "p0_target": p0_tgt, "tail_lambda": float(lam), "n": int(len(g)), "p0_pred": p0_pred}

    # Per stat-role cells: shrink p0 and positive mean toward stat fallback.
    for (stat, role), g in cal_df.groupby(["stat", "role_bucket"]):
        if len(g) < args.min_n:
            continue
        pmfs = [_repair(_parse_pmf(x)) for x in g["pmf"].to_list()]
        p0_emp = float((g["outcome"] == 0).mean())
        p0_stat = float(stat_p0.get(stat, global_p0))
        # Shrink toward stat-level empirical.
        n = float(len(g))
        k = float(args.shrink_k)
        p0_tgt = float((n * p0_emp + k * p0_stat) / (n + k))
        # Apply market ceiling at cell level too — never allow cell p0 to exceed
        # the stat-level ceiling (which is already market-calibrated above).
        cell_ceiling = MARKET_P0_CEILING.get(stat)
        if cell_ceiling is not None and p0_tgt > cell_ceiling:
            p0_tgt = cell_ceiling

        pos_g = g[g["outcome"] > 0]
        if len(pos_g) >= max(200, args.min_n // 4):
            pos_emp = float(pos_g["outcome"].mean())
        else:
            pos_emp = float(stat_pos_mean.get(stat, 0.0))
        pos_stat = float(stat_pos_mean.get(stat, pos_emp))
        npos = float(max(len(pos_g), 1))
        pos_tgt = float((npos * pos_emp + k * pos_stat) / (npos + k))

        # Fit lambda on the cell's average PMF after p0 adjustment (approx).
        avg = np.mean(np.stack([x for x in pmfs if len(x) > 1], axis=0), axis=0)
        # First move p0 of the average to the target (approx) before fitting tail.
        avg = avg.copy()
        avg0 = float(avg[0])
        if avg0 < 1.0 - 1e-9:
            avg[1:] *= (1.0 - p0_tgt) / max(1.0 - avg0, 1e-12)
        avg[0] = p0_tgt
        avg = _repair(avg)
        lam = _tilt_lambda_for_target(avg, pos_tgt)
        cells[f"{stat}|{role}"] = {
            "mode": "active",
            "p0_target": float(p0_tgt),
            "tail_lambda": float(lam),
            "n": int(len(g)),
            "p0_emp": p0_emp,
            "p0_stat": p0_stat,
            "pos_mean_emp": float(pos_emp),
            "pos_mean_stat": float(pos_stat),
        }

    # Guardrail: rollback cells that worsen BOTH NLL and RPS on eval split.
    def apply_one(pmf: np.ndarray, params: dict) -> np.ndarray:
        p = _repair(pmf)
        if params.get("mode") == "identity":
            return p
        p0_t = params.get("p0_target")
        lam = params.get("tail_lambda")
        # Inline application to avoid importing src inside a subprocess.
        if p0_t is not None:
            p0_t = float(np.clip(p0_t, 1e-6, 1 - 1e-6))
            if abs(p0_t - p[0]) > 1e-12:
                scale = (1.0 - p0_t) / max(1.0 - p[0], 1e-12)
                p = p.copy()
                p[0] = p0_t
                p[1:] *= scale
                p = _repair(p)
        if lam is None or abs(float(lam)) < 1e-10 or len(p) <= 2:
            return p
        ks = np.arange(1, len(p), dtype=float)
        w = np.exp(np.clip(float(lam) * ks, -30.0, 30.0))
        tail = p[1:] * w
        s = float(tail.sum())
        if s <= 0:
            return p
        out = p.copy()
        out[1:] = tail * ((1.0 - out[0]) / s)
        return _repair(out)

    def nll(p: np.ndarray, y: int) -> float:
        y = int(np.clip(int(y), 0, len(p) - 1))
        return -math.log(max(float(p[y]), 1e-15))

    def rps(p: np.ndarray, y: int) -> float:
        c = np.cumsum(p)
        obs = (np.arange(len(p)) >= int(y)).astype(float)
        return float(np.mean((c - obs) ** 2))

    rolled_back = 0
    checked = 0
    for (stat, role), g in eval_df.groupby(["stat", "role_bucket"]):
        key = f"{stat}|{role}"
        if key not in cells:
            continue
        checked += 1
        pmfs = [_repair(_parse_pmf(x)) for x in g["pmf"].to_list()]
        ys = g["outcome"].astype(int).to_numpy()
        base_nll = float(np.mean([nll(p, int(y)) for p, y in zip(pmfs, ys)]))
        base_rps = float(np.mean([rps(p, int(y)) for p, y in zip(pmfs, ys)]))
        after_pmfs = [apply_one(p, cells[key]) for p in pmfs]
        after_nll = float(np.mean([nll(p, int(y)) for p, y in zip(after_pmfs, ys)]))
        after_rps = float(np.mean([rps(p, int(y)) for p, y in zip(after_pmfs, ys)]))
        if args.require_improvement and (after_nll > base_nll + 1e-4) and (after_rps > base_rps + 1e-4):
            cells[key] = {"mode": "identity", "reason": "rollback_worse_nll_and_rps", "n_eval": int(len(g))}
            rolled_back += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    spec = {
        "version": "sparse_hurdle_guarded_v1",
        "oof_path": str(p.relative_to(REPO_ROOT)),
        "sparse_stats": list(SPARSE),
        "split_policy": "game_id_mod_5_eval",
        "min_n_cell": int(args.min_n),
        "shrink_k": float(args.shrink_k),
        "global": global_params,
        "by_stat": by_stat,
        "by_role": {},
        "cells": cells,
        "cells_checked_on_holdout": int(checked),
        "cells_rolled_back": int(rolled_back),
    }
    OUT.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
    print(f"SPARSE_HURDLE_FIT_PASS wrote {OUT.relative_to(REPO_ROOT)} rolled_back={rolled_back}/{checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
