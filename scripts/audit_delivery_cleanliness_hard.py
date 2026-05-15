#!/usr/bin/env python3
"""Hard delivery cleanliness audit.

Rules:
- required fields may not be silently blank;
- blanks are allowed only with explicit status + unavailable reason;
- market probabilities must be finite and within [0, 1];
- if both market over/under probabilities exist, they must sum to ~1.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date as dt_date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.delivery.delivery_contract import (  # noqa: E402
    explicit_status_tokens,
    infer_run_mode_for_delivery_date,
    delivery_file_specs,
)


def _iter_dates(start: str, end: str) -> list[str]:
    d0 = dt_date.fromisoformat(start)
    d1 = dt_date.fromisoformat(end)
    out: list[str] = []
    cur = d0
    while cur <= d1:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _blank_mask(series: pd.Series) -> pd.Series:
    if series.dtype == object:
        return series.isna() | (series.astype(str).str.strip() == "")
    return series.isna()


def _any_reason_present(df: pd.DataFrame, reason_cols: list[str]) -> pd.Series:
    if not reason_cols:
        return pd.Series(False, index=df.index)
    out = pd.Series(False, index=df.index)
    for c in reason_cols:
        out = out | (~_blank_mask(df[c]))
    return out


def _any_explicit_status(df: pd.DataFrame, status_cols: list[str]) -> pd.Series:
    tokens = explicit_status_tokens()
    if not status_cols:
        return pd.Series(False, index=df.index)
    out = pd.Series(False, index=df.index)
    for c in status_cols:
        vals = df[c].astype(str).str.lower().str.strip()
        out = out | vals.isin(tokens)
    return out


def _market_unavailable_mask(df: pd.DataFrame, status_cols: list[str]) -> pd.Series:
    bad = {"no_offered_market", "not_available_yet", "source_unavailable"}
    if not status_cols:
        return pd.Series(False, index=df.index)
    out = pd.Series(False, index=df.index)
    for c in status_cols:
        vals = df[c].astype(str).str.lower().str.strip()
        out = out | vals.isin(bad)
    return out


def _load_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    return pd.DataFrame()


def _audit_file(path: Path, required_cols: tuple[str, ...], run_mode: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file() or path.suffix not in {".parquet", ".csv"}:
        return rows

    try:
        df = _load_table(path)
    except Exception as exc:
        rows.append(
            {
                "relative_path": str(path.relative_to(REPO_ROOT)),
                "run_mode": run_mode,
                "code": "read_failed",
                "count": 1,
                "detail": str(exc),
            }
        )
        return rows
    if df.empty:
        return rows

    cols_lower = {str(c).lower(): c for c in df.columns}
    req_present = [cols_lower[c.lower()] for c in required_cols if c.lower() in cols_lower]
    req_missing = [c for c in required_cols if c.lower() not in cols_lower]
    if req_missing:
        rows.append(
            {
                "relative_path": str(path.relative_to(REPO_ROOT)),
                "run_mode": run_mode,
                "code": "missing_required_columns",
                "count": len(req_missing),
                "detail": "|".join(req_missing),
            }
        )
        return rows

    status_cols = [c for c in df.columns if "status" in str(c).lower()]
    market_status_cols = [c for c in status_cols if "market" in str(c).lower()]
    reason_cols = [c for c in df.columns if "reason" in str(c).lower()]
    reason_ok = _any_reason_present(df, reason_cols)
    status_ok = _any_explicit_status(df, status_cols)
    market_status_ok = _any_explicit_status(df, market_status_cols)

    market_coverage_col = next(
        (c for c in df.columns if str(c).lower() == "market_coverage_status"),
        None,
    )
    covered_mask = pd.Series(True, index=df.index)
    if market_coverage_col is not None:
        covered_vals = df[market_coverage_col].astype(str).str.lower().str.strip()
        covered_mask = covered_vals.isin({"covered", "ok", "available"})

    for c in req_present:
        c_low = str(c).lower()
        is_market_sensitive = (
            "market" in c_low
            or c_low in {"book", "edge", "fair_over_odds_american", "fair_under_odds_american", "model_p_over"}
        )
        base_required = pd.Series(True, index=df.index)
        if is_market_sensitive:
            base_required = covered_mask
        bad = base_required & _blank_mask(df[c]) & ~(reason_ok & status_ok)
        n_bad = int(bad.sum())
        if n_bad > 0:
            rows.append(
                {
                    "relative_path": str(path.relative_to(REPO_ROOT)),
                    "run_mode": run_mode,
                    "code": "silent_blank_required",
                    "count": n_bad,
                    "detail": str(c),
                }
            )

    market_prob_cols = [
        c
        for c in df.columns
        if "market_prob" in str(c).lower() and "status" not in str(c).lower()
    ]
    for c in market_prob_cols:
        vals = pd.to_numeric(df[c], errors="coerce")
        present = vals.notna()
        out_of_range = present & ((vals < -1e-9) | (vals > 1.0 + 1e-9) | ~np.isfinite(vals))
        n_bad = int(out_of_range.sum())
        if n_bad > 0:
            rows.append(
                {
                    "relative_path": str(path.relative_to(REPO_ROOT)),
                    "run_mode": run_mode,
                    "code": "market_probability_out_of_range",
                    "count": n_bad,
                    "detail": str(c),
                }
            )

    over_col = next((c for c in market_prob_cols if "over" in str(c).lower()), None)
    under_col = next((c for c in market_prob_cols if "under" in str(c).lower()), None)
    if over_col and under_col:
        po = pd.to_numeric(df[over_col], errors="coerce")
        pu = pd.to_numeric(df[under_col], errors="coerce")
        both = po.notna() & pu.notna()
        bad_sum = both & ((po + pu - 1.0).abs() > 1e-3)
        n_bad_sum = int(bad_sum.sum())
        if n_bad_sum > 0:
            rows.append(
                {
                    "relative_path": str(path.relative_to(REPO_ROOT)),
                    "run_mode": run_mode,
                    "code": "market_probabilities_not_sum_to_one",
                    "count": n_bad_sum,
                    "detail": f"{over_col}|{under_col}",
                }
            )

    unavailable = _market_unavailable_mask(df, market_status_cols)
    if unavailable.any():
        line_col = next((c for c in df.columns if str(c).lower() == "line"), None)
        for c in market_prob_cols + ([line_col] if line_col else []):
            if c is None:
                continue
            non_null = ~_blank_mask(df[c])
            n_bad = int((unavailable & non_null).sum())
            if n_bad > 0:
                rows.append(
                    {
                        "relative_path": str(path.relative_to(REPO_ROOT)),
                        "run_mode": run_mode,
                        "code": "market_values_present_while_unavailable",
                        "count": n_bad,
                        "detail": str(c),
                    }
                )

    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    ap.add_argument("--out-dir", default="artifacts/model_diagnostics/delivery_cleanliness_hard")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    violations: list[dict[str, Any]] = []
    for d in _iter_dates(args.start_date, args.end_date):
        root = REPO_ROOT / "deliveries" / d
        if not root.is_dir():
            violations.append(
                {
                    "relative_path": f"deliveries/{d}",
                    "run_mode": "missing",
                    "code": "missing_delivery_date_folder",
                    "count": 1,
                    "detail": "",
                }
            )
            continue
        run_mode = infer_run_mode_for_delivery_date(REPO_ROOT, d).value
        for spec in delivery_file_specs():
            path = root / spec.relative_path
            violations.extend(_audit_file(path, spec.required_columns, run_mode))

    vdf = pd.DataFrame(violations)
    vpath = out_dir / "violations.csv"
    vdf.to_csv(vpath, index=False)
    fail = not vdf.empty

    summary = {
        "start_date": args.start_date,
        "end_date": args.end_date,
        "pass_all": not fail,
        "violation_count": int(len(vdf)),
        "violation_codes": sorted(vdf["code"].astype(str).unique().tolist()) if not vdf.empty else [],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    marker = "DELIVERY_CLEANLINESS_HARD_PASS" if not fail else "DELIVERY_CLEANLINESS_HARD_FAIL"
    print(marker)
    print(f"  wrote: {out_dir.relative_to(REPO_ROOT)}")
    return 0 if not fail else 2


if __name__ == "__main__":
    raise SystemExit(main())
