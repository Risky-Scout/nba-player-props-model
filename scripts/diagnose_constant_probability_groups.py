#!/usr/bin/env python3
"""Enumerate OOF fold groups where model over-probability is constant (median-line calibration)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

DOMAIN_FOR_STAT = {
    "pts": 80,
    "reb": 30,
    "ast": 25,
    "tov": 15,
    "stl": 12,
    "blk": 12,
    "stocks": 20,
    "fg3m": 15,
}


def _pad_or_truncate_pmf(pmfs: np.ndarray, target_len: int) -> np.ndarray:
    if pmfs.shape[1] == target_len:
        return pmfs
    if pmfs.shape[1] > target_len:
        out = pmfs[:, :target_len].copy()
        out[:, -1] += pmfs[:, target_len:].sum(axis=1)
        out = out / np.clip(out.sum(axis=1, keepdims=True), 1e-9, None)
        return out
    out = np.zeros((len(pmfs), target_len))
    out[:, : pmfs.shape[1]] = pmfs
    return out


def _cdf_at(pmfs: np.ndarray, x: float) -> np.ndarray:
    cdfs = np.cumsum(pmfs, axis=1)
    cdfs = np.clip(cdfs, 0.0, 1.0)
    if x < 0:
        return np.zeros(len(pmfs))
    k = int(np.floor(x))
    if k >= cdfs.shape[1] - 1:
        return np.ones(len(pmfs))
    return cdfs[:, k]


def _suspected_cause(
    pmfs: np.ndarray,
    over_probs: np.ndarray,
    outcomes: np.ndarray,
    val: float,
) -> str:
    n = len(over_probs)
    if n < 2:
        return "unknown"
    first = pmfs[0]
    if all(np.allclose(first, pmfs[i], atol=1e-8, rtol=0) for i in range(1, n)):
        return "bug_same_pmf_reused"
    u_out = np.unique(outcomes)
    if u_out.size == 1:
        return "true_low_information_baseline"
    if val <= 1e-6 or val >= 1.0 - 1e-6:
        return "line_probability_saturation"
    if np.nanstd(over_probs) < 1e-12:
        return "calibration_map_collapsed"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof-path", type=Path, default=REPO_ROOT / "data" / "oof_pmfs.parquet")
    ap.add_argument("--combo-oof-path", type=Path, default=REPO_ROOT / "data" / "oof_combo_pmfs.parquet")
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    ap.add_argument("--min-chunk", type=int, default=50)
    ap.add_argument("--eps", type=float, default=1e-10)
    args = ap.parse_args()

    rows_out: list[dict] = []
    for label, path, stat_col, role_col, pmf_col in (
        ("base_oof", args.oof_path, "stat", "role_bucket", "pmf_active"),
        ("combo_oof", args.combo_oof_path, "stat", "role_bucket", "pmf"),
    ):
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if pmf_col not in df.columns:
            pmf_col = "pmf"
        if stat_col not in df.columns or pmf_col not in df.columns:
            print(f"SKIP {label}: missing columns", file=sys.stderr)
            continue
        df = df.copy()
        df["game_date"] = df["game_date"].astype(str).str[:10]
        mask = (df["game_date"] >= args.start_date) & (df["game_date"] <= args.end_date)
        df = df.loc[mask]
        if role_col not in df.columns:
            df[role_col] = "unknown"
        for stat in sorted(df[stat_col].astype(str).unique()):
            sub = df[df[stat_col].astype(str) == stat]
            lens = [len(np.asarray(x, dtype=float)) for x in sub[pmf_col].head(500)]
            domain_max = DOMAIN_FOR_STAT.get(stat, (max(lens) - 1) if lens else 20)
            sub = sub.sort_values("game_date")
            sub["fold"] = sub["fold_start"].astype(str) if "fold_start" in sub.columns else "all"
            for fstart in sorted(sub["fold"].unique()):
                chunk = sub[sub["fold"] == fstart]
                if len(chunk) < args.min_chunk:
                    continue
                pmfs = np.stack([np.asarray(p, dtype=np.float64) for p in chunk[pmf_col].values])
                pmfs = _pad_or_truncate_pmf(pmfs, domain_max + 1)
                out = chunk["outcome"].values.astype(int)
                ref_line = float(np.median(out)) + 0.5
                over_probs = 1.0 - _cdf_at(pmfs, ref_line)
                if float(np.std(over_probs)) > args.eps:
                    continue
                val = float(np.mean(over_probs))
                cause = _suspected_cause(pmfs, over_probs, out, val)
                ex = chunk.iloc[0]
                rows_out.append(
                    {
                        "source": label,
                        "stat": stat,
                        "role_bucket": str(ex.get(role_col, "")),
                        "n": len(chunk),
                        "probability_type": "model_over_prob_median_line",
                        "constant_prob_value": val,
                        "source_pmf_column": pmf_col,
                        "model_version": "",
                        "calibration_stage": "oof_fold_chunk",
                        "source_recalibration_stage": "",
                        "ref_line": ref_line,
                        "fold_start": str(ex.get("fold_start", "")),
                        "fold_end": str(ex.get("fold_end", "")),
                        "example_player_id": int(ex["player_id"]) if pd.notna(ex.get("player_id")) else "",
                        "example_game_id": int(ex["game_id"]) if pd.notna(ex.get("game_id")) else "",
                        "example_game_date": str(ex.get("game_date", "")),
                        "suspected_cause": cause,
                    }
                )

    out_csv = REPO_ROOT / "artifacts" / "model_diagnostics" / (
        f"constant_probability_diagnosis_{args.start_date}_{args.end_date}.csv"
    )
    out_md = REPO_ROOT / "artifacts" / "model_diagnostics" / (
        f"constant_probability_diagnosis_{args.start_date}_{args.end_date}.md"
    )
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    if not rows_out:
        print("No constant-probability groups found in range (or OOF files missing).")
        pd.DataFrame().to_csv(out_csv, index=False)
        out_md.write_text("# Constant probability diagnosis\n\nNo groups.\n", encoding="utf-8")
        return 0

    res = pd.DataFrame(rows_out)
    res.to_csv(out_csv, index=False)

    by_stat = res.groupby("stat")["n"].sum().sort_values(ascending=False)
    by_role = res.groupby("role_bucket")["n"].sum().sort_values(ascending=False)
    lines = [
        "# Constant probability diagnosis",
        "",
        f"Window `{args.start_date}` .. `{args.end_date}`",
        "",
        "## Counts by stat",
        by_stat.to_string(),
        "",
        "## Counts by role_bucket",
        by_role.to_string(),
        "",
        f"## Largest group n = {int(res['n'].max())}",
        "",
        res.head(50).to_string(index=False),
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
