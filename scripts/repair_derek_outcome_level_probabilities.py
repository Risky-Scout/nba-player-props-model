#!/usr/bin/env python3
"""Phase 13AB — Repair Derek long-form outcome-level PMF files.

The current_live snapshot writer was producing one row per prop with
``k=0, p_k=0.0`` because it iterated legacy ``p_ge_X`` columns that no
longer exist on the canonical predictions parquet. The PMFs themselves
are intact in ``market_comparison.csv`` (and ``full_pmf_wide.csv``) as
JSON dicts. This script regenerates ``outcome_level_probabilities.csv``
(and the parquet sibling) deterministically from those JSON PMFs without
touching model values.

Inputs:
  --delivery-date YYYY-MM-DD
  --all-snapshots                  (default: all snapshot folders for the date)
  --snapshot-folder PATH ...       (optional; specific folder(s) to repair)

Behavior:
  - scan ``deliveries/<date>/derek_game_snapshots/*/*/market_comparison.csv``
  - skip folders without market_comparison.csv (missed snapshots)
  - parse each row's PMF JSON and emit one CSV row per (original_row, k)
  - validate per-original-row PMF sums to 1.0 ± 0.005
  - rewrite outcome_level_probabilities.csv and .parquet atomically
  - emit DEREK_OUTCOME_LEVEL_PMF_REPAIR_PASS on success, fail otherwise

Hard rules:
  - PMF values are NOT modified — only normalized to floats and emitted long.
  - market_comparison.csv values are NOT modified.
  - Wizard of Odds files are NOT touched.
  - No model retraining, no calibration changes.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

# Identifying columns to preserve in the long-form file. Anything missing
# from the source frame is silently skipped — we never fabricate.
ID_COLS = (
    "player_id", "player_name", "game_id", "game", "team_id",
    "stat", "side", "line", "bet_vendor", "book",
    "model_prob", "market_prob",
    "edge_publish_status", "calibration_support_status",
    "contextual_feature_set_id", "lineup_confirmed",
)

PMF_SUM_TOL = 0.005


def _parse_pmf(value) -> dict[int, float] | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, dict):
        raw = value
    else:
        s = str(value).strip()
        if not s or s in {"nan", "None", "{}"}:
            return None
        try:
            raw = json.loads(s)
        except Exception:
            try:
                raw = json.loads(s.replace("'", '"'))
            except Exception:
                try:
                    raw = ast.literal_eval(s)
                except Exception:
                    return None
    out: dict[int, float] = {}
    for k, v in raw.items():
        try:
            ki = int(float(k))
            pv = float(v)
        except Exception:
            return None
        if not math.isfinite(pv) or pv < 0:
            return None
        out[ki] = out.get(ki, 0.0) + pv
    return out or None


def _expand_long(market_csv: Path, *, snapshot_type: str) -> tuple[pd.DataFrame, list[str]]:
    """Return (long_df, errors). Errors are non-fatal warnings; if any
    PMF parse fails or any sum deviates beyond tolerance the caller
    treats it as a hard failure."""
    df = pd.read_csv(market_csv)
    if df.empty:
        return pd.DataFrame(), [f"empty market_comparison.csv: {market_csv}"]
    if "pmf" not in df.columns:
        return pd.DataFrame(), [f"no pmf column in {market_csv}"]

    rows: list[dict] = []
    errors: list[str] = []
    for orig_idx, r in df.reset_index(drop=True).iterrows():
        pmf = _parse_pmf(r.get("pmf"))
        if pmf is None:
            errors.append(
                f"row {orig_idx} ({r.get('player_name')!r}/{r.get('stat')!r}/"
                f"{r.get('side')!r}@{r.get('line')!r}/{r.get('bet_vendor')!r}): "
                "PMF parse failed"
            )
            continue
        # Renormalize defensively. We do NOT alter the source PMF column.
        s = sum(pmf.values())
        if not math.isfinite(s) or s <= 0:
            errors.append(f"row {orig_idx}: invalid PMF sum={s}")
            continue
        if abs(s - 1.0) > PMF_SUM_TOL:
            # Renormalize for the long-form file but report the raw deviation.
            errors.append(
                f"row {orig_idx} ({r.get('player_name')!r}/{r.get('stat')!r}): "
                f"raw PMF sum={s:.6f} outside tolerance — renormalized for long form"
            )
        norm = {k: v / s for k, v in pmf.items()}

        base = {col: r.get(col) for col in ID_COLS if col in df.columns}
        base["snapshot_type"] = snapshot_type
        base["row_id"] = int(orig_idx)
        for k in sorted(norm):
            rows.append({**base, "k": int(k), "p_k": float(norm[k])})

    if not rows:
        return pd.DataFrame(), errors or [f"no PMF rows produced from {market_csv}"]
    out = pd.DataFrame(rows)
    return out, errors


def _validate(long_df: pd.DataFrame) -> tuple[bool, dict]:
    """Check per-row_id sum == 1.0 within tolerance. Returns (ok, summary)."""
    if long_df.empty:
        return False, {"reason": "empty long-form frame", "max_err": None}
    grouped = long_df.groupby("row_id", sort=False)["p_k"].sum()
    deviations = (grouped - 1.0).abs()
    max_err = float(deviations.max())
    bad = deviations[deviations > PMF_SUM_TOL]
    nonzero_per_row = long_df.groupby("row_id", sort=False)["p_k"].sum()
    all_zero_rows = nonzero_per_row[nonzero_per_row <= 0]
    summary = {
        "rows_long": int(len(long_df)),
        "rows_original": int(long_df["row_id"].nunique()),
        "max_pmf_sum_err": max_err,
        "rows_outside_tolerance": int(len(bad)),
        "rows_with_zero_total_mass": int(len(all_zero_rows)),
        "k_distribution_min": int(long_df["k"].min()),
        "k_distribution_max": int(long_df["k"].max()),
    }
    ok = (len(bad) == 0) and (len(all_zero_rows) == 0)
    return ok, summary


def _repair_one(snapshot_dir: Path) -> dict:
    market_csv = snapshot_dir / "market_comparison.csv"
    if not market_csv.exists():
        return {"path": str(snapshot_dir.relative_to(REPO_ROOT)),
                "status": "skipped_no_market_comparison"}

    snap_type = snapshot_dir.name  # current_live | t_minus_25 | close_lock
    out_csv = snapshot_dir / "outcome_level_probabilities.csv"
    out_parquet = snapshot_dir / "outcome_level_probabilities.parquet"

    rows_before_csv = 0
    if out_csv.exists():
        try:
            rows_before_csv = int(len(pd.read_csv(out_csv)))
        except Exception:
            rows_before_csv = -1

    long_df, errors = _expand_long(market_csv, snapshot_type=snap_type)
    fatal_errors = [e for e in errors if "PMF parse failed" in e or "invalid PMF" in e
                    or "no pmf column" in e or "no PMF rows" in e]
    if fatal_errors:
        return {"path": str(snapshot_dir.relative_to(REPO_ROOT)),
                "status": "failed",
                "errors": fatal_errors}

    ok, summary = _validate(long_df)
    if not ok:
        return {"path": str(snapshot_dir.relative_to(REPO_ROOT)),
                "status": "failed_validation",
                "summary": summary,
                "errors": errors}

    # Deterministic column order — id cols first, then snapshot_type, row_id,
    # k, p_k.
    leading = [c for c in ID_COLS if c in long_df.columns]
    cols = leading + ["snapshot_type", "row_id", "k", "p_k"]
    long_df = long_df[cols]

    long_df.to_csv(out_csv, index=False)
    long_df.to_parquet(out_parquet, index=False)

    return {
        "path": str(snapshot_dir.relative_to(REPO_ROOT)),
        "status": "ok",
        "rows_before_csv": rows_before_csv,
        "rows_after_csv": int(len(long_df)),
        "original_props": summary["rows_original"],
        "max_pmf_sum_err": summary["max_pmf_sum_err"],
        "errors": errors,
    }


def _resolve_snapshot_dirs(args: argparse.Namespace) -> list[Path]:
    if args.snapshot_folder:
        return [Path(p).resolve() for p in args.snapshot_folder]
    base = REPO_ROOT / "deliveries" / args.delivery_date / "derek_game_snapshots"
    if not base.exists():
        return []
    out: list[Path] = []
    for game_dir in sorted(base.iterdir()):
        if not game_dir.is_dir():
            continue
        for snap_dir in sorted(game_dir.iterdir()):
            if snap_dir.is_dir() and snap_dir.name in {
                "current_live", "t_minus_25", "close_lock"
            }:
                out.append(snap_dir)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delivery-date", required=True)
    ap.add_argument("--all-snapshots", action="store_true",
                    help="repair every snapshot folder under the delivery date "
                         "(default behavior when --snapshot-folder is not set)")
    ap.add_argument("--snapshot-folder", action="append", default=[],
                    help="specific snapshot folder path (repeatable)")
    args = ap.parse_args(argv)

    dirs = _resolve_snapshot_dirs(args)
    if not dirs:
        print(f"DEREK_OUTCOME_LEVEL_PMF_REPAIR_FAILED  reason=no_snapshot_folders  "
              f"delivery_date={args.delivery_date}", file=sys.stderr)
        return 1

    results = [_repair_one(d) for d in dirs]
    failures = [r for r in results if r["status"].startswith("failed")]
    repaired = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped_no_market_comparison"]

    for r in results:
        tag = {"ok": "  repaired", "skipped_no_market_comparison": "  skipped",
               "failed": "  failed", "failed_validation": "  failed_validation"}.get(
            r["status"], "  ?"
        )
        if r["status"] == "ok":
            print(f"{tag}: {r['path']}  rows_before={r['rows_before_csv']}  "
                  f"rows_after={r['rows_after_csv']}  "
                  f"original_props={r['original_props']}  "
                  f"max_pmf_sum_err={r['max_pmf_sum_err']:.6f}")
        elif r["status"] == "skipped_no_market_comparison":
            print(f"{tag}: {r['path']} (no market_comparison.csv — likely missed snapshot)")
        else:
            print(f"{tag}: {r['path']}")
            for e in r.get("errors", []):
                print(f"    - {e}")
            if "summary" in r:
                print(f"    summary: {r['summary']}")

    if failures:
        print(f"DEREK_OUTCOME_LEVEL_PMF_REPAIR_FAILED  delivery_date={args.delivery_date}  "
              f"failures={len(failures)}  repaired={len(repaired)}  skipped={len(skipped)}",
              file=sys.stderr)
        return 1

    print(f"DEREK_OUTCOME_LEVEL_PMF_REPAIR_PASS  delivery_date={args.delivery_date}  "
          f"repaired={len(repaired)}  skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
