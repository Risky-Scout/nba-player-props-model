#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "artifacts" / "models" / "sparse_hurdle_offsets.json"

SPARSE = ("stl", "blk", "tov", "fg3m", "stocks")


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


def _repair(a: np.ndarray) -> np.ndarray:
    x = np.asarray(a, dtype=float)
    x = np.clip(np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    s = float(x.sum())
    if not np.isfinite(s) or s <= 0:
        return np.full_like(x, 1.0 / max(len(x), 1))
    return x / s


def _nll(p: np.ndarray, y: int) -> float:
    y = int(np.clip(int(y), 0, len(p) - 1))
    return -math.log(max(float(p[y]), 1e-15))


def _rps(p: np.ndarray, y: int) -> float:
    c = np.cumsum(p)
    obs = (np.arange(len(p)) >= int(y)).astype(float)
    return float(np.mean((c - obs) ** 2))


def _pit_mid(p: np.ndarray, y: int) -> float:
    y = int(np.clip(int(y), 0, len(p) - 1))
    return float(np.sum(p[:y]) + 0.5 * p[y])


def _ks_uniform(vals: np.ndarray) -> float:
    v = np.asarray(vals, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return float("nan")
    v = np.sort(np.clip(v, 0.0, 1.0))
    n = float(len(v))
    i = np.arange(1, len(v) + 1, dtype=float)
    return float(max(np.max(i / n - v), np.max(v - (i - 1) / n)))


def _pos_mean(p: np.ndarray) -> float:
    if len(p) <= 1:
        return 0.0
    ppos = float(1.0 - p[0])
    if ppos <= 1e-12:
        return 0.0
    ks = np.arange(len(p), dtype=float)
    return float(np.dot(ks[1:], p[1:]) / ppos)


def _apply_one(pmf: np.ndarray, params: dict) -> np.ndarray:
    p = _repair(pmf)
    if params.get("mode") == "identity":
        return p
    p0_t = params.get("p0_target")
    lam = params.get("tail_lambda")
    if p0_t is not None:
        p0_t = float(np.clip(float(p0_t), 1e-6, 1 - 1e-6))
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


def main() -> int:
    if not OUT.exists():
        print("SPARSE_HURDLE_VERIFY_FAIL missing offsets", file=sys.stderr)
        return 1
    spec = json.loads(OUT.read_text())
    if "cells" not in spec or "by_stat" not in spec:
        print("SPARSE_HURDLE_VERIFY_FAIL missing keys", file=sys.stderr)
        return 2
    oof_path = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"
    if not oof_path.exists():
        print("SPARSE_HURDLE_VERIFY_FAIL missing data/oof_stat_pmf_predictions.parquet", file=sys.stderr)
        return 2

    df = pd.read_parquet(oof_path)
    df = df[df["stat"].astype(str).str.lower().isin(SPARSE)].copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["role_bucket"] = df["role_bucket"].astype(str).str.lower()
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    df["split_key"] = pd.to_numeric(df.get("game_id"), errors="coerce").fillna(0).astype(int)
    eval_df = df[(df["split_key"] % 5) == 0].reset_index(drop=True)
    if eval_df.empty:
        print("SPARSE_HURDLE_VERIFY_FAIL empty_eval_split", file=sys.stderr)
        return 2

    def params_for(stat: str, role: str) -> dict:
        key = f"{stat}|{role}"
        if key in spec.get("cells", {}):
            return dict(spec["cells"][key])
        if stat in spec.get("by_stat", {}):
            return dict(spec["by_stat"][stat])
        return dict(spec.get("global", {"mode": "identity"}))

    # Compute per-cell before/after metrics + enforce no worsening.
    bad = []
    rows = []
    for (stat, role), g in eval_df.groupby(["stat", "role_bucket"]):
        key = f"{stat}|{role}"
        params = params_for(stat, role)
        pmfs = [_repair(_parse_pmf(x)) for x in g["pmf"].to_list()]
        ys = g["outcome"].astype(int).to_numpy()
        p0_pred_b = np.mean([p[0] for p in pmfs])
        p0_pred_a = np.mean([_apply_one(p, params)[0] for p in pmfs])
        y0 = np.mean(ys == 0)
        pos_mean_b = float(np.mean([_pos_mean(p) for p in pmfs]))
        pos_mean_a = float(np.mean([_pos_mean(_apply_one(p, params)) for p in pmfs]))
        nll_b = float(np.mean([_nll(p, int(y)) for p, y in zip(pmfs, ys)]))
        rps_b = float(np.mean([_rps(p, int(y)) for p, y in zip(pmfs, ys)]))
        after_pmfs = [_apply_one(p, params) for p in pmfs]
        nll_a = float(np.mean([_nll(p, int(y)) for p, y in zip(after_pmfs, ys)]))
        rps_a = float(np.mean([_rps(p, int(y)) for p, y in zip(after_pmfs, ys)]))
        pit_b = _ks_uniform(np.array([_pit_mid(p, int(y)) for p, y in zip(pmfs, ys)]))
        pit_a = _ks_uniform(np.array([_pit_mid(p, int(y)) for p, y in zip(after_pmfs, ys)]))
        rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": int(len(g)),
                "p0_error_before": float(y0 - p0_pred_b),
                "p0_error_after": float(y0 - p0_pred_a),
                "positive_mean_before": pos_mean_b,
                "positive_mean_after": pos_mean_a,
                "nll_before": nll_b,
                "nll_after": nll_a,
                "rps_before": rps_b,
                "rps_after": rps_a,
                "pit_ks_before": float(pit_b),
                "pit_ks_after": float(pit_a),
                "nll_delta": nll_a - nll_b,
                "rps_delta": rps_a - rps_b,
                "mode": str(params.get("mode", "unknown")),
            }
        )
        if params.get("mode") != "identity" and (nll_a > nll_b + 1e-4) and (rps_a > rps_b + 1e-4):
            bad.append(key)

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / "sparse_hurdle_verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(["nll_delta", "rps_delta"], ascending=False).to_csv(out_dir / "before_after_sparse_cells.csv", index=False)

    if bad:
        print(f"SPARSE_HURDLE_VERIFY_FAIL worsened_cells={bad[:20]} (n={len(bad)})", file=sys.stderr)
        return 1

    print(f"SPARSE_HURDLE_VERIFY_PASS eval_rows={len(eval_df)} cells={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
