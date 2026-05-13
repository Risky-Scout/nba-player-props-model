#!/usr/bin/env python3
"""Fit monotone PIT/CDF calibration maps from OOF PMFs + actual outcomes.

Fits a piecewise-linear monotone map g: [0,1] -> [0,1] so that g(U) is
approximately Uniform(0,1), where U is the mid-PIT value under the raw model.

Maps are fit with fallback hierarchy:
  - stat-role
  - stat
  - role
  - global

Guardrail:
- stat-role maps are rolled back if they worsen BOTH NLL and RPS on a holdout
  split (game_id % 5 == 0).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts" / "models" / "monotone_pmf_cdf_v0.json"


def _parse_pmf(x):
    import json as _json
    if x is None:
        return np.array([], dtype=float)
    if isinstance(x, np.ndarray):
        return x.astype(float)
    if isinstance(x, (list, tuple)):
        return np.asarray(x, dtype=float)
    if isinstance(x, dict):
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


def _repair(p: np.ndarray) -> np.ndarray:
    a = np.asarray(p, dtype=float)
    a = np.clip(np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    s = float(a.sum())
    if not np.isfinite(s) or s <= 0:
        return np.full_like(a, 1.0 / max(len(a), 1))
    return a / s


def _pit_mid(pmf: np.ndarray, y: int) -> float:
    p = _repair(pmf)
    y = int(np.clip(int(y), 0, len(p) - 1))
    return float(np.sum(p[:y]) + 0.5 * p[y])


def _fit_map(u: np.ndarray) -> dict:
    u = np.asarray(u, dtype=float)
    u = u[np.isfinite(u)]
    if len(u) < 10:
        return {"xs": [0.0, 1.0], "ys": [0.0, 1.0], "n_train": int(len(u))}
    u = np.sort(np.clip(u, 0.0, 1.0))
    n = len(u)
    y = (np.arange(1, n + 1, dtype=float)) / float(n + 1)
    xs = np.concatenate([[0.0], u, [1.0]])
    ys = np.concatenate([[0.0], y, [1.0]])
    ys = np.maximum.accumulate(ys)
    return {"xs": [float(x) for x in xs], "ys": [float(t) for t in ys], "n_train": int(n)}


def _apply_map_to_cdf(cdf: np.ndarray, m: dict) -> np.ndarray:
    xs = np.asarray(m["xs"], dtype=float)
    ys = np.asarray(m["ys"], dtype=float)
    out = np.interp(np.clip(cdf, 0.0, 1.0), xs, ys)
    out = np.maximum.accumulate(np.clip(out, 0.0, 1.0))
    out[-1] = 1.0
    return out


def _calibrate_pmf(pmf: np.ndarray, m: dict) -> np.ndarray:
    p = _repair(pmf)
    if len(p) == 0:
        return p
    cdf = np.cumsum(p)
    cdf2 = _apply_map_to_cdf(cdf, m)
    q = np.diff(np.concatenate([[0.0], cdf2]))
    return _repair(q)


def _nll(pmf: np.ndarray, y: int) -> float:
    p = _repair(pmf)
    y = int(np.clip(int(y), 0, len(p) - 1))
    return float(-np.log(max(float(p[y]), 1e-15)))


def _rps(pmf: np.ndarray, y: int) -> float:
    p = _repair(pmf)
    c = np.cumsum(p)
    obs = (np.arange(len(p)) >= int(y)).astype(float)
    return float(np.mean((c - obs) ** 2))


def main() -> int:
    oof_path = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"
    if not oof_path.exists():
        raise SystemExit("FATAL: missing data/oof_stat_pmf_predictions.parquet")
    df = pd.read_parquet(oof_path)
    df = df.dropna(subset=["stat", "role_bucket", "outcome", "pmf"]).copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["role_bucket"] = df["role_bucket"].astype(str).str.lower()
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    df["split_key"] = pd.to_numeric(df.get("game_id"), errors="coerce").fillna(0).astype(int)
    is_eval = (df["split_key"] % 5) == 0
    cal = df[~is_eval].reset_index(drop=True)
    ev = df[is_eval].reset_index(drop=True)

    u_global = np.array(
        [_pit_mid(_parse_pmf(p), int(y)) for p, y in zip(cal["pmf"].to_list(), cal["outcome"].to_list())],
        dtype=float,
    )
    global_map = _fit_map(u_global)

    by_stat = {}
    for stat, g in cal.groupby("stat"):
        u = np.array([_pit_mid(_parse_pmf(p), int(y)) for p, y in zip(g["pmf"].to_list(), g["outcome"].to_list())], dtype=float)
        by_stat[stat] = _fit_map(u)
    by_role = {}
    for role, g in cal.groupby("role_bucket"):
        u = np.array([_pit_mid(_parse_pmf(p), int(y)) for p, y in zip(g["pmf"].to_list(), g["outcome"].to_list())], dtype=float)
        by_role[role] = _fit_map(u)

    stat_role = {}
    rolled_back = []
    min_n = 800
    for (stat, role), g in cal.groupby(["stat", "role_bucket"]):
        if len(g) < min_n:
            continue
        u = np.array([_pit_mid(_parse_pmf(p), int(y)) for p, y in zip(g["pmf"].to_list(), g["outcome"].to_list())], dtype=float)
        m = _fit_map(u)
        gev = ev[(ev["stat"] == stat) & (ev["role_bucket"] == role)]
        # Guard on any non-trivial holdout mass; even small buckets can
        # produce catastrophic tail artifacts if we accept a bad map.
        if len(gev) >= 50:
            pmfs = [_parse_pmf(x) for x in gev["pmf"].to_list()]
            ys = gev["outcome"].to_numpy(dtype=int)
            base_nll = float(np.mean([_nll(p, int(y)) for p, y in zip(pmfs, ys)]))
            base_rps = float(np.mean([_rps(p, int(y)) for p, y in zip(pmfs, ys)]))
            after_pmfs = [_calibrate_pmf(p, m) for p in pmfs]
            after_nll = float(np.mean([_nll(p, int(y)) for p, y in zip(after_pmfs, ys)]))
            after_rps = float(np.mean([_rps(p, int(y)) for p, y in zip(after_pmfs, ys)]))
            if (after_nll > base_nll + 1e-4) and (after_rps > base_rps + 1e-4):
                rolled_back.append(f"{stat}|{role}")
                continue
        stat_role[f"{stat}|{role}"] = m

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "version": "monotone_pit_cdf_v1",
                "fitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "oof_path": str(oof_path.relative_to(REPO_ROOT)),
                "split_policy": "game_id_mod_5_eval",
                "min_n_stat_role": min_n,
                "rolled_back_stat_role": rolled_back,
                "global": global_map,
                "by_stat": by_stat,
                "by_role": by_role,
                "stat_role": stat_role,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(
        f"MONOTONE_CDF_FIT_PASS {OUT.relative_to(REPO_ROOT)} "
        f"rolled_back={len(rolled_back)} kept={len(stat_role)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
