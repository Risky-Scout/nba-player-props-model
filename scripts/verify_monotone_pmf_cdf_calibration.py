#!/usr/bin/env python3
import json
import math
import sys
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


def _apply_map_to_cdf(cdf: np.ndarray, m: dict) -> np.ndarray:
    xs = np.asarray(m.get("xs", [0.0, 1.0]), dtype=float)
    ys = np.asarray(m.get("ys", [0.0, 1.0]), dtype=float)
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
    return float(-math.log(max(float(p[y]), 1e-15)))


def _rps(pmf: np.ndarray, y: int) -> float:
    p = _repair(pmf)
    c = np.cumsum(p)
    obs = (np.arange(len(p)) >= int(y)).astype(float)
    return float(np.mean((c - obs) ** 2))


def main() -> int:
    if not OUT.exists():
        print("MONOTONE_VERIFY_FAIL", file=sys.stderr)
        return 1
    spec = json.loads(OUT.read_text(encoding="utf-8"))
    if spec.get("version") != "monotone_pit_cdf_v1":
        print(f"MONOTONE_VERIFY_FAIL unexpected_version={spec.get('version')}", file=sys.stderr)
        return 2
    oof_path = REPO_ROOT / "data" / "oof_stat_pmf_predictions.parquet"
    if not oof_path.exists():
        print("MONOTONE_VERIFY_FAIL missing oof_stat_pmf_predictions.parquet", file=sys.stderr)
        return 2

    df = pd.read_parquet(oof_path)
    df = df.dropna(subset=["stat", "role_bucket", "outcome", "pmf"]).copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["role_bucket"] = df["role_bucket"].astype(str).str.lower()
    df["outcome"] = pd.to_numeric(df["outcome"], errors="coerce").fillna(0).astype(int)
    df["split_key"] = pd.to_numeric(df.get("game_id"), errors="coerce").fillna(0).astype(int)
    ev = df[(df["split_key"] % 5) == 0].reset_index(drop=True)
    if ev.empty:
        print("MONOTONE_VERIFY_FAIL empty_eval_split", file=sys.stderr)
        return 2

    stat_role = spec.get("stat_role", {})
    by_stat = spec.get("by_stat", {})
    by_role = spec.get("by_role", {})
    global_map = spec.get("global", {"xs": [0.0, 1.0], "ys": [0.0, 1.0]})

    def pick(stat: str, role: str) -> dict:
        key = f"{stat}|{role}"
        if key in stat_role:
            return stat_role[key]
        if stat in by_stat:
            return by_stat[stat]
        if role in by_role:
            return by_role[role]
        return global_map

    bad = []
    rows = []
    for (stat, role), g in ev.groupby(["stat", "role_bucket"]):
        pmfs = [_parse_pmf(x) for x in g["pmf"].to_list()]
        ys = g["outcome"].to_numpy(dtype=int)
        m = pick(stat, role)
        after = [_calibrate_pmf(p, m) for p in pmfs]
        # validity checks
        for a in after[:20]:
            if (a < -1e-9).any() or not np.isfinite(a).all() or abs(float(a.sum()) - 1.0) > 1e-6:
                print("MONOTONE_VERIFY_FAIL invalid_pmf_after", file=sys.stderr)
                return 1
        nll_b = float(np.mean([_nll(p, int(y)) for p, y in zip(pmfs, ys)]))
        rps_b = float(np.mean([_rps(p, int(y)) for p, y in zip(pmfs, ys)]))
        nll_a = float(np.mean([_nll(p, int(y)) for p, y in zip(after, ys)]))
        rps_a = float(np.mean([_rps(p, int(y)) for p, y in zip(after, ys)]))
        rows.append(
            {
                "stat": stat,
                "role_bucket": role,
                "n": int(len(g)),
                "nll_before": nll_b,
                "nll_after": nll_a,
                "rps_before": rps_b,
                "rps_after": rps_a,
                "nll_delta": nll_a - nll_b,
                "rps_delta": rps_a - rps_b,
                "used_map": "stat_role" if f"{stat}|{role}" in stat_role else ("stat" if stat in by_stat else ("role" if role in by_role else "global")),
            }
        )
        if f"{stat}|{role}" in stat_role and (nll_a > nll_b + 1e-4) and (rps_a > rps_b + 1e-4):
            bad.append(f"{stat}|{role}")

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / "monotone_cdf_verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(["nll_delta", "rps_delta"], ascending=False).to_csv(out_dir / "before_after_cells.csv", index=False)

    if bad:
        print(f"MONOTONE_VERIFY_FAIL worsened_stat_role_cells={bad[:20]} (n={len(bad)})", file=sys.stderr)
        return 1

    print(f"MONOTONE_PMF_CDF_VERIFY_PASS eval_rows={len(ev)} cells={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
