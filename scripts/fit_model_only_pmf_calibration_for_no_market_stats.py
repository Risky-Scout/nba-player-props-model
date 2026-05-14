#!/usr/bin/env python3
"""Fit lightweight temperature calibration on OOF PMFs for no-market stats (no market data)."""
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

from nba_props_model.calibration.model_only_pmf_calibration import (  # noqa: E402
    apply_model_only_segment_calibration,
)

NO_MARKET_STATS = frozenset({"stl", "blk", "stocks", "pa", "pr", "ra", "pra"})


def _parse_pmf_cell(v) -> dict[int, float] | None:
    if v is None:
        return None
    if isinstance(v, float) and v != v:
        return None
    raw = None
    if isinstance(v, dict):
        raw = v
    else:
        s = str(v)
        if not s.startswith("{"):
            return None
        raw = json.loads(s)
    if not isinstance(raw, dict):
        return None
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


def _nll(d: dict[int, float], y: int) -> float:
    p = max(d.get(int(y), 0.0), 1e-12)
    return float(-math.log(p))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = args.label.strip()

    oof_path = REPO_ROOT / "data" / "oof_pmfs.parquet"
    combo_path = REPO_ROOT / "data" / "oof_combo_pmfs.parquet"
    parts: list[pd.DataFrame] = []
    if oof_path.is_file():
        parts.append(pd.read_parquet(oof_path))
    if combo_path.is_file():
        parts.append(pd.read_parquet(combo_path))
    if not parts:
        print("MISSING_OOF_PARQUET", file=sys.stderr)
        return 2
    df = pd.concat(parts, ignore_index=True)
    df["stat"] = df["stat"].astype(str).str.lower()
    df = df[df["stat"].isin(NO_MARKET_STATS)].copy()
    if df.empty:
        print("NO_ROWS", file=sys.stderr)
        return 1

    pmf_col = "pmf_active" if "pmf_active" in df.columns else "pmf"
    alt_pmf = "pmf" if pmf_col == "pmf_active" and "pmf" in df.columns else None

    segments: dict[str, dict] = {}
    before_rows: list[dict] = []
    roll_rows: list[dict] = []

    for (stat, role), sub in df.groupby(["stat", "role_bucket"], dropna=False):
        sub = sub.copy()
        date_col = None
        for c in ("game_date", "date", "slate_date", "as_of_date"):
            if c in sub.columns:
                date_col = c
                break
        ts = None
        if date_col:
            sub["_d"] = sub[date_col].astype(str).str.slice(0, 10)
            ts = sorted(sub["_d"].dropna().unique().tolist())
        seg_key = f"{stat}|{str(role)}"

        def mean_nll_for_T(rows: pd.DataFrame, tval: float) -> float | None:
            nlls: list[float] = []
            for _, r in rows.iterrows():
                raw = r.get(pmf_col)
                if alt_pmf and (raw is None or (isinstance(raw, float) and raw != raw)):
                    raw = r.get(alt_pmf)
                d0 = _parse_pmf_cell(raw)
                if d0 is None:
                    continue
                d1, _, _ = apply_model_only_segment_calibration(
                    d0, stat=stat, role_bucket=str(role),
                    cal={"segments": {seg_key: {"type": "temperature", "T": tval}}},
                )
                if d1 is None:
                    continue
                try:
                    y = int(r["outcome"])
                except Exception:
                    continue
                nlls.append(_nll(d1, y))
            if len(nlls) < 10:
                return None
            return float(np.mean(nlls))

        if not ts or len(ts) < 4:
            segments[seg_key] = {"type": "identity"}
            roll_rows.append({"segment": seg_key, "reason": "insufficient_date_folds"})
            continue
        cut = max(1, int(len(ts) * 0.75))
        train = sub[sub["_d"].isin(ts[:cut])] if date_col else sub
        val = sub[sub["_d"].isin(ts[cut:])] if date_col else sub.iloc[0:0]

        base_tr = mean_nll_for_T(train, 1.0)
        base_va = mean_nll_for_T(val, 1.0) if len(val) else base_tr
        if base_tr is None:
            segments[seg_key] = {"type": "identity"}
            roll_rows.append({"segment": seg_key, "reason": "too_few_usable_pmfs"})
            continue

        best_t, best_va = 1.0, base_va
        for tval in np.linspace(0.88, 1.12, 13):
            va = mean_nll_for_T(val, float(tval)) if len(val) else mean_nll_for_T(train, float(tval))
            if va is None:
                continue
            if best_va is None or va < best_va:
                best_va = va
                best_t = float(tval)

        tr_new = mean_nll_for_T(train, best_t)
        if tr_new is None or tr_new > base_tr + 1e-4:
            segments[seg_key] = {"type": "identity"}
            roll_rows.append({"segment": seg_key, "reason": "rollback_worse_train_nll", "T_try": best_t})
        elif best_va is not None and base_va is not None and best_va > base_va + 1e-4:
            segments[seg_key] = {"type": "identity"}
            roll_rows.append({"segment": seg_key, "reason": "rollback_worse_val_nll", "T_try": best_t})
        else:
            segments[seg_key] = {"type": "temperature", "T": best_t}

        m_b = mean_nll_for_T(sub, 1.0)
        m_a = mean_nll_for_T(sub, segments[seg_key].get("T", 1.0) if segments[seg_key]["type"] == "temperature" else 1.0)
        before_rows.append(
            {
                "stat": stat,
                "role_bucket": str(role),
                "mean_nll_before": m_b,
                "mean_nll_after": m_a,
                "chosen_T": segments[seg_key].get("T", 1.0),
                "segment_type": segments[seg_key]["type"],
            }
        )

    out_model = {
        "version": 1,
        "label": label,
        "stats": sorted(NO_MARKET_STATS),
        "segments": segments,
        "market_superiority_claim_allowed": False,
        "global_market_superiority_claim_allowed": False,
    }
    model_path = REPO_ROOT / "artifacts" / "models" / "model_only_no_market_pmf_calibration.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(out_model, indent=2) + "\n", encoding="utf-8")

    diag = REPO_ROOT / "artifacts" / "model_diagnostics" / f"model_only_no_market_calibration_{label}"
    diag.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(before_rows).to_csv(diag / "before_after_stat_role.csv", index=False)
    pd.DataFrame(roll_rows).to_csv(diag / "rollback_report.csv", index=False)
    (diag / "summary.json").write_text(json.dumps({"n_segments": len(segments), "model_path": str(model_path)}, indent=2) + "\n")
    print(f"MODEL_ONLY_NO_MARKET_CALIBRATION_FIT_DONE wrote {model_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
