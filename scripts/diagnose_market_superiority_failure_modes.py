#!/usr/bin/env python3
"""Segment-level diagnosis for strict market-superiority failures vs loss rows."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent


def _as_bool(s) -> bool:
    if isinstance(s, bool):
        return s
    return str(s).strip().lower() in ("1", "true", "t", "yes")


def _dominant_failure(row: pd.Series, loss: pd.DataFrame | None) -> str:
    fr = str(row.get("failure_reason") or "").strip()
    if fr == "model_logloss_not_better":
        dll = row.get("logloss_delta_model_minus_market")
        dbr = row.get("brier_delta_model_minus_market")
        try:
            if dll is not None and float(dll) > 0.02:
                return "model_prob_too_high_or_overconfident_side"
        except Exception:
            pass
        try:
            if dll is not None and float(dll) < -0.02:
                return "model_prob_too_low_or_underconfident_side"
        except Exception:
            pass
        if loss is not None and len(loss) > 0 and "model_mean" in loss.columns and "actual" in loss.columns:
            me = float(loss["model_mean"].mean()) - float(loss["actual"].mean())
            if me > 0.35:
                return "mean_too_high"
            if me < -0.35:
                return "mean_too_low"
            if "model_variance" in loss.columns:
                mv = float(loss["model_variance"].mean())
                av = float(loss["actual"].var())
                if mv < av * 0.65:
                    return "variance_too_narrow"
                if mv > av * 1.4:
                    return "variance_too_wide"
        return "model_logloss_not_better"
    if fr == "insufficient_scored_rows":
        return "insufficient_backtest_sample"
    if "calibration" in fr.lower():
        return "calibration_failure_only"
    if fr:
        return fr
    return "unknown"


def _loss_subset(loss: pd.DataFrame, stat: str, role: str) -> pd.DataFrame:
    m = loss["stat"].astype(str).str.lower() == str(stat).lower()
    if "role_bucket" in loss.columns:
        m &= loss["role_bucket"].astype(str) == str(role)
    if "scoring_blocker" in loss.columns:
        sb = loss["scoring_blocker"]
        m &= sb.isna() | (sb.astype(str).str.len() == 0)
    return loss.loc[m].copy()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="e.g. dates_24c1750e26ad")
    args = ap.parse_args()
    label = str(args.label).strip()
    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"market_superiority_failure_modes_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    sr_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}" / "stat_role_market_superiority.csv"
    loss_path = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    if not sr_path.is_file():
        print(f"FATAL missing {sr_path}", file=sys.stderr)
        return 2
    if not loss_path.is_file():
        print(f"FATAL missing {loss_path}", file=sys.stderr)
        return 2

    sr = pd.read_csv(sr_path)
    loss = pd.read_parquet(loss_path)

    for c in ("market_superiority_eligible", "market_superiority_pass", "calibration_pass"):
        if c in sr.columns:
            sr[c] = sr[c].map(_as_bool)

    eligible = sr["market_superiority_eligible"] if "market_superiority_eligible" in sr.columns else pd.Series(False, index=sr.index)
    failing = sr[eligible & ~sr["market_superiority_pass"]].copy()
    passing = sr[eligible & sr["market_superiority_pass"]].copy()

    ll_col = "event_logloss_delta" if "event_logloss_delta" in loss.columns else None
    if ll_col is None and {"model_event_logloss", "market_event_logloss"} <= set(loss.columns):
        loss["_ll_delta"] = loss["model_event_logloss"] - loss["market_event_logloss"]
        ll_col = "_ll_delta"

    rows_out: list[dict] = []
    worst_parts: list[pd.DataFrame] = []

    for _, r in failing.iterrows():
        stat = str(r.get("stat"))
        role = str(r.get("role_bucket"))
        sub = _loss_subset(loss, stat, role)
        agg: dict = {
            "stat": stat,
            "role_bucket": role,
            "n_segment_report": int(r.get("n_scored") or r.get("n_rows") or 0),
            "n_loss_rows_used": int(len(sub)),
            "model_logloss_avg": r.get("model_logloss_avg"),
            "market_logloss_avg": r.get("market_logloss_avg"),
            "logloss_delta_model_minus_market": r.get("logloss_delta_model_minus_market"),
            "model_brier_avg": r.get("model_brier_avg"),
            "market_brier_avg": r.get("market_brier_avg"),
            "brier_delta_model_minus_market": r.get("brier_delta_model_minus_market"),
            "calibration_pass": r.get("calibration_pass"),
            "model_prob_mean": sub["model_probability_for_side"].mean() if len(sub) and "model_probability_for_side" in sub else None,
            "market_prob_mean": sub["market_probability_for_side"].mean() if len(sub) and "market_probability_for_side" in sub else None,
            "actual_hit_rate": sub["hit_result"].mean() if len(sub) and "hit_result" in sub else None,
            "pmf_mean_mean": sub["model_mean"].mean() if len(sub) and "model_mean" in sub else None,
            "actual_mean": sub["actual"].mean() if len(sub) and "actual" in sub else None,
            "pmf_var_mean": sub["model_variance"].mean() if len(sub) and "model_variance" in sub else None,
            "actual_var": sub["actual"].var() if len(sub) and "actual" in sub else None,
            "line_p25": sub["line"].quantile(0.25) if len(sub) and "line" in sub else None,
            "line_p50": sub["line"].median() if len(sub) and "line" in sub else None,
            "line_p75": sub["line"].quantile(0.75) if len(sub) and "line" in sub else None,
            "n_books": sub["bookmaker_key"].nunique() if len(sub) and "bookmaker_key" in sub else None,
            "n_players": sub["player_id"].nunique() if len(sub) and "player_id" in sub else None,
            "n_dates": sub["date"].nunique() if len(sub) and "date" in sub else None,
            "failure_reason_csv": r.get("failure_reason"),
            "dominant_failure_mode": _dominant_failure(r, sub if len(sub) else None),
        }
        rows_out.append(agg)

        if len(sub) and ll_col and sub[ll_col].notna().any():
            cols = [
                c
                for c in (
                    "date",
                    "game_id",
                    "player_id",
                    "player_name",
                    "stat",
                    "role_bucket",
                    "line",
                    "model_probability_for_side",
                    "market_probability_for_side",
                    "actual",
                    "hit_result",
                    "model_mean",
                    "model_variance",
                    "model_event_logloss",
                    "market_event_logloss",
                )
                if c in sub.columns
            ]
            if ll_col in sub.columns:
                cols.append(ll_col)
            try:
                sub2 = sub.nlargest(30, ll_col)[cols].copy()
            except Exception:
                sub2 = pd.DataFrame()
            if len(sub2):
                sub2["_segment"] = stat + "|" + role
                worst_parts.append(sub2)
    seg_df = pd.DataFrame(rows_out)
    seg_df.to_csv(out_dir / "segment_summary.csv", index=False)

    if worst_parts:
        pd.concat(worst_parts, ignore_index=True).to_csv(out_dir / "worst_rows.csv", index=False)
    else:
        pd.DataFrame().to_csv(out_dir / "worst_rows.csv", index=False)

    if seg_df.empty:
        mode_counts: dict = {}
        by_mode: dict = {}
    else:
        mode_counts = seg_df["dominant_failure_mode"].value_counts().to_dict()
        by_mode = {
            str(k): (v["stat"].astype(str) + "|" + v["role_bucket"].astype(str)).tolist()
            for k, v in seg_df.groupby("dominant_failure_mode")
        }
    root = {
        "label": label,
        "n_failing_eligible_segments": int(len(failing)),
        "dominant_failure_mode_counts": mode_counts,
        "failing_segments_by_mode": by_mode,
    }
    (out_dir / "root_cause_summary.json").write_text(json.dumps(root, indent=2, default=str) + "\n", encoding="utf-8")

    lines = [
        f"# Repair recommendations — {label}",
        "",
        "## Failure mode counts",
        "",
        "```",
        json.dumps(mode_counts, indent=2),
        "```",
        "",
        "## Ranked actions",
        "",
        "1. **Logloss / Brier vs market:** tighten PMF location-scale calibration by stat-role on OOF; rebalance sparse tails for stl/blk.",
        "2. **Mean vs actual:** review minutes → usage mapping and combo joint sampler means for pa/pr/ra/pra roles.",
        "3. **Variance too narrow:** increase simulation variance or hierarchical shrinkage where segment `pmf_var_mean << actual_var`.",
        "4. **Sample instability:** segments with low `n_loss_rows_used` should be excluded from eligibility, not verifier-gated away silently.",
        "",
    ]
    (out_dir / "repair_recommendations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Passing market-superiority rows that still fail global claim (calibration typical)
    pnc = passing.copy()
    if "calibration_pass" in pnc.columns:
        pnc = pnc[pnc["calibration_pass"].eq(False)]

    def _gate_note(row: pd.Series) -> str:
        bits: list[str] = []
        if "calibration_pass" in row.index and not bool(row["calibration_pass"]):
            bits.append("calibration_pass_false")
        for c in ("pit_ks", "model_ece", "mean_error", "variance_error", "p0_error", "model_better_calibrated"):
            if c in row.index and pd.notna(row[c]) and str(row[c]) != "":
                bits.append(f"{c}={row[c]}")
        return "|".join(bits) if bits else "see_strict_and_math_contract_chain"

    if len(pnc):
        pnc["failed_calibration_gates_note"] = pnc.apply(_gate_note, axis=1)
    pnc.to_csv(out_dir / "passing_but_not_claimable.csv", index=False)

    print(f"MARKET_SUPERIORITY_FAILURE_MODES_DIAG wrote {out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
