#!/usr/bin/env python3
"""Phase 13AB — verify Derek long-form outcome PMF files.

For every snapshot folder under
``deliveries/<date>/derek_game_snapshots/<game>/<snap_type>/`` that has a
``market_comparison.csv``, this verifier checks:

  - ``outcome_level_probabilities.csv`` exists alongside the parquet sibling
  - the long file has more rows than market_comparison.csv unless every PMF
    has only one support point
  - required identifying columns + ``snapshot_type``, ``row_id``, ``k``,
    ``p_k`` are present
  - ``p_k`` is finite and nonnegative
  - per ``row_id`` PMF sum is within 0.005 of 1.0
  - every original prop has at least one row with ``p_k > 0``
  - no current_live file consists solely of ``k=0`` rows unless the
    underlying PMF is genuinely a single-point mass

Pass: DEREK_OUTCOME_LEVEL_PROBABILITIES_PASS
Fail: DEREK_OUTCOME_LEVEL_PROBABILITIES_FAILED
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PMF_SUM_TOL = 0.005

REQUIRED_COLS = ("snapshot_type", "row_id", "k", "p_k")
ID_COLS = ("player_id", "player_name", "stat", "side", "line",
           "edge_publish_status", "calibration_support_status",
           "contextual_feature_set_id", "lineup_confirmed")


def _is_single_support_pmf(s) -> bool:
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return False
    try:
        d = json.loads(str(s))
    except Exception:
        try:
            d = json.loads(str(s).replace("'", '"'))
        except Exception:
            return False
    nonzero = [v for v in d.values()
               if isinstance(v, (int, float)) and float(v) > 0]
    return len(nonzero) == 1


def _check_one(snap_dir: Path) -> dict:
    market_csv = snap_dir / "market_comparison.csv"
    long_csv = snap_dir / "outcome_level_probabilities.csv"
    long_parquet = snap_dir / "outcome_level_probabilities.parquet"
    if not market_csv.exists():
        return {"path": str(snap_dir.relative_to(REPO_ROOT)),
                "status": "skipped_no_market_comparison"}

    failures: list[str] = []
    if not long_csv.exists():
        failures.append("outcome_level_probabilities.csv missing")
    if not long_parquet.exists():
        failures.append("outcome_level_probabilities.parquet missing")
    if failures:
        return {"path": str(snap_dir.relative_to(REPO_ROOT)),
                "status": "failed", "failures": failures}

    market_df = pd.read_csv(market_csv)
    long_df = pd.read_csv(long_csv)
    n_market = len(market_df)

    # Required columns.
    missing = [c for c in REQUIRED_COLS if c not in long_df.columns]
    if missing:
        failures.append(f"required columns missing: {missing}")
    id_present = [c for c in ID_COLS if c in long_df.columns]
    if not id_present:
        failures.append("no identifying columns from ID_COLS present "
                        f"(checked {ID_COLS!r})")

    if "p_k" in long_df.columns:
        if long_df["p_k"].isna().any():
            failures.append("p_k contains NaN")
        elif (long_df["p_k"] < 0).any():
            failures.append("p_k contains negative values")
        elif not (long_df["p_k"].apply(lambda v: math.isfinite(float(v))).all()):
            failures.append("p_k contains non-finite values")

    # Row count expansion check.
    single_pt_rows = 0
    if "pmf" in market_df.columns:
        single_pt_rows = int(market_df["pmf"].apply(_is_single_support_pmf).sum())
    expected_at_least = n_market - single_pt_rows + max(single_pt_rows, 0)
    # This check enforces "more rows than market_comparison.csv unless every
    # PMF has only one support point".
    if n_market > 0 and single_pt_rows < n_market and len(long_df) <= n_market:
        failures.append(
            f"long file has {len(long_df)} rows but market has {n_market}; "
            f"only {single_pt_rows} of those PMFs are single-point. "
            "Expansion did not occur."
        )

    # Per row_id sum check + nonzero mass check.
    max_err = 0.0
    rows_outside_tol: list[int] = []
    rows_zero_mass: list[int] = []
    only_k0_rows: list[int] = []
    if "row_id" in long_df.columns and "p_k" in long_df.columns:
        sums = long_df.groupby("row_id", sort=False)["p_k"].sum()
        deviations = (sums - 1.0).abs()
        if not deviations.empty:
            max_err = float(deviations.max())
        rows_outside_tol = sums[(sums - 1.0).abs() > PMF_SUM_TOL].index.tolist()
        rows_zero_mass = sums[sums <= 0].index.tolist()
        # Per-row "all-zero except k=0" check — flag rows whose only nonzero
        # mass sits at k=0 and the underlying market PMF actually had support
        # beyond k=0.
        for rid, sub in long_df.groupby("row_id", sort=False):
            nonzero = sub[sub["p_k"] > 0]
            if len(nonzero) == 1 and int(nonzero.iloc[0]["k"]) == 0:
                # Compare against original PMF — only flag if true PMF has
                # multiple support points.
                if rid < n_market and "pmf" in market_df.columns:
                    if not _is_single_support_pmf(market_df.iloc[int(rid)]["pmf"]):
                        only_k0_rows.append(int(rid))
    if rows_outside_tol:
        failures.append(f"rows outside PMF sum tolerance ({PMF_SUM_TOL}): "
                        f"row_ids={rows_outside_tol[:5]}{'...' if len(rows_outside_tol) > 5 else ''} "
                        f"max_err={max_err:.6f}")
    if rows_zero_mass:
        failures.append(f"rows with zero total PMF mass: row_ids={rows_zero_mass[:5]}")
    if only_k0_rows:
        failures.append(f"rows with only k=0 mass while underlying PMF has multi-point "
                        f"support: row_ids={only_k0_rows[:5]}")

    return {
        "path": str(snap_dir.relative_to(REPO_ROOT)),
        "snapshot_type": snap_dir.name,
        "status": "ok" if not failures else "failed",
        "rows_market": n_market,
        "rows_long": int(len(long_df)),
        "single_point_pmfs": single_pt_rows,
        "max_pmf_sum_err": max_err,
        "failures": failures,
    }


def _resolve_snapshot_dirs(delivery_date: str) -> list[Path]:
    base = REPO_ROOT / "deliveries" / delivery_date / "derek_game_snapshots"
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
    args = ap.parse_args(argv)

    dirs = _resolve_snapshot_dirs(args.delivery_date)
    if not dirs:
        print("DEREK_OUTCOME_LEVEL_PROBABILITIES_FAILED  "
              f"reason=no_snapshot_folders  delivery_date={args.delivery_date}",
              file=sys.stderr)
        return 1

    results = [_check_one(d) for d in dirs]
    failures = [r for r in results if r["status"] == "failed"]
    ok = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped_no_market_comparison"]

    for r in results:
        if r["status"] == "ok":
            print(f"  ok: {r['path']}  rows_market={r['rows_market']}  "
                  f"rows_long={r['rows_long']}  "
                  f"single_pt={r['single_point_pmfs']}  "
                  f"max_pmf_sum_err={r['max_pmf_sum_err']:.6f}")
        elif r["status"] == "skipped_no_market_comparison":
            print(f"  skipped: {r['path']} (missed snapshot — no market_comparison.csv)")
        else:
            print(f"  fail: {r['path']}")
            for f in r.get("failures", []):
                print(f"    - {f}")

    if failures:
        print("DEREK_OUTCOME_LEVEL_PROBABILITIES_FAILED  "
              f"delivery_date={args.delivery_date}  failures={len(failures)}  "
              f"ok={len(ok)}  skipped={len(skipped)}", file=sys.stderr)
        return 1

    print("DEREK_OUTCOME_LEVEL_PROBABILITIES_PASS  "
          f"delivery_date={args.delivery_date}  ok={len(ok)}  skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
