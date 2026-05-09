#!/usr/bin/env python3
"""
Milestone 1A: Settled model-vs-market audit aggregator.

Reads per-date settled scoring CSVs produced by score_daily_pmf_delivery_after_game.py:

    deliveries/<date>/after_game_scoring/model_vs_market_scoring.csv

Each row already carries pre-computed model-vs-market fields:
    line, model_p_over, market_no_vig_over_prob, actual_outcome, is_push,
    model_logloss, market_logloss, delta_logloss,
    model_brier, market_brier, delta_brier,
    stat (or target_stat), role_bucket, book

This script does NOT re-parse PMFs. The upstream scorer is the authority on
per-row PMF parsing and over-prob computation. M1A is an aggregation +
breakout layer that mission requires but the upstream scorer does not
produce in detail. PMF math validation itself is repaired in M1B.

Outputs:
    artifacts/audit_model_vs_market_settled/(timestamp)/audit.json
    artifacts/audit_model_vs_market_settled/(timestamp)/audit.md

Interpretation:
    delta_logloss = mean(model_logloss) - mean(market_logloss)
    delta_brier   = mean(model_brier)   - mean(market_brier)
    Negative deltas mean the model beats the market.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES_DIR = REPO_ROOT / "deliveries"
OUT_BASE = REPO_ROOT / "artifacts" / "audit_model_vs_market_settled"

CSV_NAME = "model_vs_market_scoring.csv"
STAT_CANDIDATES = ("target_stat", "stat")


def _resolve_stat_col(df):
    for c in STAT_CANDIDATES:
        if c in df.columns:
            return c
    return None


def _line_bin(line):
    if line is None or not math.isfinite(float(line)):
        return "unknown"
    line = float(line)
    bins = [(0, 2), (2, 5), (5, 10), (10, 15),
            (15, 20), (20, 25), (25, 30), (30, 40), (40, 60)]
    for lo, hi in bins:
        if lo <= line < hi:
            return f"bin_{lo}_{hi}"
    return "bin_60_plus"


def _edge_bucket(model_p, market_p):
    edge = float(model_p) - float(market_p)
    if edge <= -0.05:
        return "below_minus_0.05"
    if edge <= -0.02:
        return "minus_0.05_to_minus_0.02"
    if edge < 0.02:
        return "minus_0.02_to_plus_0.02"
    if edge < 0.05:
        return "plus_0.02_to_plus_0.05"
    return "above_plus_0.05"


def _aggregate(df):
    if df.empty:
        return {
            "n": 0,
            "model_logloss": None, "market_logloss": None, "delta_logloss": None,
            "model_brier": None, "market_brier": None, "delta_brier": None,
            "mean_model_p_over": None, "mean_market_p_over": None,
            "actual_over_rate": None,
        }
    mll = float(df["_mll"].mean())
    xll = float(df["_xll"].mean())
    mbr = float(df["_mbr"].mean())
    xbr = float(df["_xbr"].mean())
    return {
        "n": int(len(df)),
        "model_logloss": mll,
        "market_logloss": xll,
        "delta_logloss": mll - xll,
        "model_brier": mbr,
        "market_brier": xbr,
        "delta_brier": mbr - xbr,
        "mean_model_p_over": float(df["_model_p"].mean()),
        "mean_market_p_over": float(df["_market_p"].mean()),
        "actual_over_rate": float(df["_label"].mean()),
    }


def _breakout(df, by):
    if isinstance(by, str):
        by = [by]
    missing = [c for c in by if c not in df.columns]
    if missing:
        return {"_skipped_missing_columns": missing}
    out = {}
    for key, sub in df.groupby(by, dropna=False):
        if isinstance(key, tuple):
            parts = []
            for k in key:
                if isinstance(k, float) and math.isnan(k):
                    parts.append("NA")
                else:
                    parts.append(str(k))
            key_str = " | ".join(parts)
        else:
            if isinstance(key, float) and math.isnan(key):
                key_str = "NA"
            else:
                key_str = str(key)
        out[key_str] = _aggregate(sub)
    return out


def _scan_dates(deliveries, start, end):
    if not deliveries.exists():
        return []
    out = []
    for child in sorted(deliveries.iterdir()):
        if not child.is_dir():
            continue
        try:
            d = dt.date.fromisoformat(child.name)
        except Exception:
            continue
        if start and d < start:
            continue
        if end and d > end:
            continue
        if (child / "after_game_scoring" / CSV_NAME).exists():
            out.append(child)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", type=str, default=None)
    ap.add_argument("--end-date", type=str, default=None)
    args = ap.parse_args()

    start = dt.date.fromisoformat(args.start_date) if args.start_date else None
    end = dt.date.fromisoformat(args.end_date) if args.end_date else None

    date_dirs = _scan_dates(DELIVERIES_DIR, start, end)
    if not date_dirs:
        print(f"AUDIT_FAILED reason=no_input_csv_found pattern=deliveries/<date>/after_game_scoring/{CSV_NAME}",
              file=sys.stderr)
        return 2

    frames = []
    for dd in date_dirs:
        path = dd / "after_game_scoring" / CSV_NAME
        try:
            df_d = pd.read_csv(path)
        except Exception as e:
            print(f"  WARN: failed to read {path}: {e}", file=sys.stderr)
            continue
        if df_d.empty:
            continue
        df_d["delivery_date"] = dd.name
        frames.append(df_d)

    if not frames:
        print("AUDIT_FAILED reason=no_rows_loaded", file=sys.stderr)
        return 2

    df = pd.concat(frames, ignore_index=True, sort=False)
    rows_raw = int(len(df))
    rows_deduped = 0
    rows_after_dedupe = rows_raw

    stat_col = _resolve_stat_col(df)
    required = ("line", "model_p_over", "market_no_vig_over_prob",
                "actual_outcome", "is_push",
                "model_logloss", "market_logloss",
                "model_brier", "market_brier", "role_bucket")
    missing = [c for c in required if c not in df.columns]
    if stat_col is None:
        missing.append("stat OR target_stat")
    if missing:
        print(f"AUDIT_FAILED reason=missing_required_columns columns={missing}", file=sys.stderr)
        print(f"  available_columns={sorted(df.columns.tolist())}", file=sys.stderr)
        return 2

    line_num = pd.to_numeric(df["line"], errors="coerce")
    actual_num = pd.to_numeric(df["actual_outcome"], errors="coerce")
    model_p_num = pd.to_numeric(df["model_p_over"], errors="coerce")
    market_p_num = pd.to_numeric(df["market_no_vig_over_prob"], errors="coerce")
    mll_num = pd.to_numeric(df["model_logloss"], errors="coerce")
    xll_num = pd.to_numeric(df["market_logloss"], errors="coerce")
    mbr_num = pd.to_numeric(df["model_brier"], errors="coerce")
    xbr_num = pd.to_numeric(df["market_brier"], errors="coerce")

    push_series = df["is_push"]
    if push_series.dtype == object:
        push_bool = push_series.astype(str).str.lower().isin(("true", "1", "yes", "t"))
    else:
        push_bool = push_series.fillna(False).astype(bool)

    rows_filtered_push = int(push_bool.sum())
    rows_filtered_null_line = int(df["line"].isna().sum())
    rows_filtered_null_market_prob = int(df["market_no_vig_over_prob"].isna().sum())
    rows_filtered_null_actual_outcome = int(df["actual_outcome"].isna().sum())
    rows_filtered_null_model_prob = int(df["model_p_over"].isna().sum())

    bad_market = df["market_no_vig_over_prob"].notna() & (
        market_p_num.isna() | ~market_p_num.between(0.0, 1.0)
    )
    bad_model = df["model_p_over"].notna() & (
        model_p_num.isna() | ~model_p_num.between(0.0, 1.0)
    )
    rows_filtered_bad_probability = int((bad_market | bad_model).sum())

    keep_mask = (
        (~push_bool)
        & line_num.notna()
        & actual_num.notna()
        & model_p_num.between(0.0, 1.0)
        & market_p_num.between(0.0, 1.0)
        & mll_num.notna()
        & xll_num.notna()
        & mbr_num.notna()
        & xbr_num.notna()
    )

    df_kept = df.loc[keep_mask].copy()
    df_kept["_line"] = line_num[keep_mask].values
    df_kept["_actual"] = actual_num[keep_mask].values
    df_kept["_model_p"] = model_p_num[keep_mask].values
    df_kept["_market_p"] = market_p_num[keep_mask].values
    df_kept["_mll"] = mll_num[keep_mask].values
    df_kept["_xll"] = xll_num[keep_mask].values
    df_kept["_mbr"] = mbr_num[keep_mask].values
    df_kept["_xbr"] = xbr_num[keep_mask].values

    rows_after_filter = int(len(df_kept))

    if rows_after_filter == 0:
        print("AUDIT_FAILED reason=no_rows_scoreable", file=sys.stderr)
        print(f"  rows_raw={rows_raw}", file=sys.stderr)
        print(f"  rows_filtered_push={rows_filtered_push}", file=sys.stderr)
        print(f"  rows_filtered_null_line={rows_filtered_null_line}", file=sys.stderr)
        print(f"  rows_filtered_null_market_prob={rows_filtered_null_market_prob}", file=sys.stderr)
        print(f"  rows_filtered_null_actual_outcome={rows_filtered_null_actual_outcome}", file=sys.stderr)
        print(f"  rows_filtered_null_model_prob={rows_filtered_null_model_prob}", file=sys.stderr)
        print(f"  rows_filtered_bad_probability={rows_filtered_bad_probability}", file=sys.stderr)
        return 3

    df_kept["_label"] = (df_kept["_actual"] > df_kept["_line"]).astype(int)
    df_kept["line_bin"] = df_kept["_line"].map(_line_bin)
    df_kept["edge_bucket"] = [
        _edge_bucket(mp, xp)
        for mp, xp in zip(df_kept["_model_p"].tolist(), df_kept["_market_p"].tolist())
    ]
    if stat_col != "stat":
        df_kept["stat"] = df_kept[stat_col]

    rows_scored = int(len(df_kept))
    overall = _aggregate(df_kept)

    breakouts = {
        "by_date": _breakout(df_kept, "delivery_date"),
        "by_stat": _breakout(df_kept, "stat"),
        "by_role_bucket": _breakout(df_kept, "role_bucket"),
        "by_stat_role_bucket": _breakout(df_kept, ["stat", "role_bucket"]),
        "by_line_bin": _breakout(df_kept, "line_bin"),
        "by_edge_bucket": _breakout(df_kept, "edge_bucket"),
    }
    if "book" in df_kept.columns:
        breakouts["by_book"] = _breakout(df_kept, "book")

    accounting = {
        "rows_raw": rows_raw,
        "rows_after_filter": rows_after_filter,
        "rows_after_dedupe": rows_after_dedupe,
        "rows_scored": rows_scored,
        "rows_filtered_push": rows_filtered_push,
        "rows_filtered_null_line": rows_filtered_null_line,
        "rows_filtered_null_market_prob": rows_filtered_null_market_prob,
        "rows_filtered_null_actual_outcome": rows_filtered_null_actual_outcome,
        "rows_filtered_null_model_prob": rows_filtered_null_model_prob,
        "rows_filtered_bad_probability": rows_filtered_bad_probability,
        "rows_deduped": rows_deduped,
        "rows_filtered_null_pmf": 0,
        "rows_filtered_bad_pmf": 0,
    }

    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_dir = OUT_BASE / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "source": f"deliveries/<date>/after_game_scoring/{CSV_NAME}",
        "stat_column_used": stat_col,
        "pmf_parse_mode": "not_reparsed_csv_uses_upstream_model_p_over",
        "design_note": (
            "M1A aggregates canonical settled model_vs_market_scoring.csv; "
            "PMF parsing and pmf_valid repair are handled in M1B."
        ),
        "delivery_dates_scanned": [d.name for d in date_dirs],
        "row_accounting": accounting,
        "overall": overall,
        "breakouts": breakouts,
        "interpretation": {
            "delta_logloss": "model - market; negative means model beats market",
            "delta_brier": "model - market; negative means model beats market",
        },
    }
    (out_dir / "audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    md = []
    md.append(f"# Settled model-vs-market audit: {timestamp}")
    md.append("")
    md.append(f"Source: deliveries/<date>/after_game_scoring/{CSV_NAME}")
    md.append(f"Stat column: {stat_col}")
    md.append(f"PMF parse mode: not_reparsed_csv_uses_upstream_model_p_over")
    md.append("")
    md.append("Design note: M1A aggregates canonical settled model_vs_market_scoring.csv;")
    md.append("PMF parsing and pmf_valid repair are handled in M1B.")
    md.append("")
    md.append("## Row accounting")
    md.append("")
    for k, v in accounting.items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append(f"## Overall (n = {overall['n']})")
    md.append("")
    md.append(f"- model_logloss:    {overall['model_logloss']:.6f}")
    md.append(f"- market_logloss:   {overall['market_logloss']:.6f}")
    md.append(f"- delta_logloss:    {overall['delta_logloss']:+.6f}  (negative = model beats market)")
    md.append(f"- model_brier:      {overall['model_brier']:.6f}")
    md.append(f"- market_brier:     {overall['market_brier']:.6f}")
    md.append(f"- delta_brier:      {overall['delta_brier']:+.6f}  (negative = model beats market)")
    md.append(f"- mean_model_p_over:  {overall['mean_model_p_over']:.6f}")
    md.append(f"- mean_market_p_over: {overall['mean_market_p_over']:.6f}")
    md.append(f"- actual_over_rate:   {overall['actual_over_rate']:.6f}")
    md.append("")
    for label, table in breakouts.items():
        md.append(f"## {label}")
        md.append("")
        md.append("| key | n | delta_logloss | delta_brier | mean_model_p_over | mean_market_p_over | actual_over_rate |")
        md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        items = [(k, v) for k, v in table.items() if isinstance(v, dict) and "n" in v]
        items.sort(key=lambda kv: -(kv[1].get("n") or 0))
        for k, v in items:
            n = v.get("n")
            dl = v.get("delta_logloss")
            db = v.get("delta_brier")
            mm = v.get("mean_model_p_over")
            xx = v.get("mean_market_p_over")
            ar = v.get("actual_over_rate")
            dl_s = f"{dl:+.4f}" if dl is not None else "NA"
            db_s = f"{db:+.4f}" if db is not None else "NA"
            mm_s = f"{mm:.4f}" if mm is not None else "NA"
            xx_s = f"{xx:.4f}" if xx is not None else "NA"
            ar_s = f"{ar:.4f}" if ar is not None else "NA"
            md.append(f"| {k} | {n} | {dl_s} | {db_s} | {mm_s} | {xx_s} | {ar_s} |")
        md.append("")
    (out_dir / "audit.md").write_text("\n".join(md), encoding="utf-8")

    print("SETTLED_MODEL_VS_MARKET_AUDIT_PASS")
    print(f"  output_dir: {out_dir.relative_to(REPO_ROOT)}")
    for k, v in accounting.items():
        print(f"  {k}: {v}")
    print(f"  model_logloss:      {overall['model_logloss']:.6f}")
    print(f"  market_logloss:     {overall['market_logloss']:.6f}")
    print(f"  delta_logloss:      {overall['delta_logloss']:+.6f}")
    print(f"  model_brier:        {overall['model_brier']:.6f}")
    print(f"  market_brier:       {overall['market_brier']:.6f}")
    print(f"  delta_brier:        {overall['delta_brier']:+.6f}")
    print(f"  mean_model_p_over:  {overall['mean_model_p_over']:.6f}")
    print(f"  mean_market_p_over: {overall['mean_market_p_over']:.6f}")
    print(f"  actual_over_rate:   {overall['actual_over_rate']:.6f}")
    for label, table in breakouts.items():
        items = [(k, v) for k, v in table.items() if isinstance(v, dict) and "n" in v]
        items.sort(key=lambda kv: -(kv[1].get("n") or 0))
        print(f"  --- {label} (top by n) ---")
        for k, v in items[:8]:
            n = v.get("n")
            dl = v.get("delta_logloss")
            db = v.get("delta_brier")
            print(f"    {k}: n={n}  dlog={dl:+.4f}  dbri={db:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
