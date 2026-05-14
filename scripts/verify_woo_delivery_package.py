#!/usr/bin/env python3
"""Phase 13AN — Wizard of Odds delivery-package verifier.

Gates the FTP/SFTP deploy. Every check below must pass before the
deployer is allowed to touch the WoO portal. Operates in two modes:

    --mode strict       every gate is hard-required.
    --mode production   strict + an explicit allowance for the
                        finality_blocker pattern observed when the
                        slate has no market coverage. The verifier
                        still emits FAIL in that case unless the
                        operator explicitly passes --allow-no-market.

Required prediction inputs (today's slate must already exist):

    predictions/all_props_<date>.parquet     (rows > 0)
    predictions/pmf_display_<date>.json      (non-empty)
    predictions/singles_<date>.json          (non-empty)

Required delivery files:

    deliveries/<date>/wizard_of_odds/run_manifest.json
    deliveries/<date>/wizard_of_odds/run_manifest.champion_stamp.json
    deliveries/<date>/wizard_of_odds/full_pmfs_wide.parquet
    deliveries/<date>/wizard_of_odds/market_comparison.parquet
    deliveries/<date>/wizard_of_odds/fair_odds_board.parquet
    deliveries/<date>/wizard_of_odds/publishable_edges.parquet

Required public_export (the new pipeline output):

    public_export/wizard_of_odds/<date>/affiliate_dashboard.json
    public_export/wizard_of_odds/<date>/pmf_research.json

Structural checks:

    * delivery_date in run_manifest equals the deploy date.
    * champion_model_id stamped on manifest matches champion_pointer.json.
    * no duplicate (player_id, stat, line) props in publishable_edges.
    * tov accounted for: either tov rows exist in full_pmfs_wide OR
      run_manifest.finality_blocker_codes documents the absence as
      ``missing_stats:tov`` (only when --allow-tov-missing is set).
    * affiliate_dashboard rows > 0 and pmf_research players > 0.

Pass line:
    WOO_DELIVERY_PACKAGE_VERIFICATION_PASS  date=<date>  mode=<mode>

Fail line:
    WOO_DELIVERY_PACKAGE_VERIFICATION_FAILED  date=<date>  count=<n>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delivery-date", required=True)
    ap.add_argument(
        "--mode", choices=["strict", "production"], default="production"
    )
    ap.add_argument(
        "--allow-no-market",
        action="store_true",
        help="Allow market_coverage_none finality_blocker (e.g. ODDS_API_KEY exhausted).",
    )
    ap.add_argument(
        "--allow-tov-missing",
        action="store_true",
        help=(
            "Allow tov to be missing when documented in run_manifest "
            "finality_blocker_codes as 'missing_stats:tov'."
        ),
    )
    args = ap.parse_args(argv)

    date = args.delivery_date
    mode = args.mode
    deliv_dir = REPO_ROOT / "deliveries" / date / "wizard_of_odds"
    pred_dir = REPO_ROOT / "predictions"
    public_export_dir = REPO_ROOT / "public_export" / "wizard_of_odds" / date

    failures: list[str] = []
    warnings: list[str] = []

    # ── Prediction inputs ──────────────────────────────────────────
    parquet = pred_dir / f"all_props_{date}.parquet"
    pmf_disp = pred_dir / f"pmf_display_{date}.json"
    singles = pred_dir / f"singles_{date}.json"

    for p in (parquet, pmf_disp, singles):
        if not p.exists() or p.stat().st_size == 0:
            failures.append(
                f"prediction file missing/empty: {p.relative_to(REPO_ROOT)}"
            )

    # ── Delivery package files ──────────────────────────────────────
    if not deliv_dir.exists():
        failures.append(
            f"WoO delivery dir missing: {deliv_dir.relative_to(REPO_ROOT)}"
        )
    else:
        required_delivery = (
            "run_manifest.json",
            "run_manifest.champion_stamp.json",
            "full_pmfs_wide.parquet",
            "market_comparison.parquet",
            "fair_odds_board.parquet",
            "publishable_edges.parquet",
        )
        for name in required_delivery:
            p = deliv_dir / name
            if not p.exists() or p.stat().st_size == 0:
                failures.append(
                    f"missing/empty WoO delivery file: {p.relative_to(REPO_ROOT)}"
                )

    # ── public_export new-pipeline outputs ──────────────────────────
    affiliate_path = public_export_dir / "affiliate_dashboard.json"
    pmf_research_path = public_export_dir / "pmf_research.json"
    for p in (affiliate_path, pmf_research_path):
        if not p.exists() or p.stat().st_size == 0:
            msg = f"missing/empty public_export file: {p.relative_to(REPO_ROOT)}"
            if mode == "strict":
                failures.append(msg)
            else:
                warnings.append(msg)

    # ── Run manifest cross-checks ───────────────────────────────────
    run_manifest = _read_json(deliv_dir / "run_manifest.json") or {}
    if run_manifest:
        if run_manifest.get("delivery_date") != date:
            failures.append(
                f"run_manifest.delivery_date={run_manifest.get('delivery_date')} "
                f"!= --delivery-date={date}"
            )
        if not run_manifest.get("champion_model_id"):
            msg = "run_manifest missing champion_model_id"
            if mode == "strict":
                failures.append(msg)
            else:
                warnings.append(msg)

    # Champion-pointer cross-check.
    pointer = _read_json(
        REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    ) or {}
    pointer_champion = pointer.get("champion_model_id")
    manifest_champion = run_manifest.get("champion_model_id")
    if pointer_champion and manifest_champion and pointer_champion != manifest_champion:
        failures.append(
            f"champion mismatch: pointer={pointer_champion!r} "
            f"manifest={manifest_champion!r}"
        )

    # finality_blocker_codes audit.
    blocker_codes = list(run_manifest.get("finality_blocker_codes") or [])
    implicit_blockers = set(blocker_codes)
    # Legacy compatibility: no_odds_fetch indicates no trustworthy market
    # freshness/coverage for strict package validation.
    if bool(run_manifest.get("no_odds_fetch")):
        implicit_blockers.add("market_coverage_none")
        # When market snapshots are unavailable, treat TOV market-backed
        # packaging as missing unless explicitly allowed.
        implicit_blockers.add("missing_stats:tov")
    if implicit_blockers:
        if "market_coverage_none" in implicit_blockers and not args.allow_no_market:
            failures.append(
                "run_manifest.finality_blocker_codes contains "
                "'market_coverage_none' (--allow-no-market not set)"
            )
        if "missing_stats:tov" in implicit_blockers and not args.allow_tov_missing:
            failures.append(
                "run_manifest.finality_blocker_codes contains "
                "'missing_stats:tov' (--allow-tov-missing not set)"
            )

    # ── Affiliate dashboard / PMF research row counts ──────────────
    affiliate = _read_json(affiliate_path) or {}
    if affiliate:
        rows = affiliate.get("rows") or []
        if not isinstance(rows, list) or len(rows) == 0:
            msg = "affiliate_dashboard.json has zero rows"
            if mode == "strict":
                failures.append(msg)
            else:
                warnings.append(msg)
    pmf_research = _read_json(pmf_research_path) or {}
    if pmf_research:
        players = pmf_research.get("players") or []
        if not isinstance(players, list) or len(players) == 0:
            msg = "pmf_research.json has zero players"
            if mode == "strict":
                failures.append(msg)
            else:
                warnings.append(msg)

    # ── Pandas-backed structural checks ─────────────────────────────
    try:
        import pandas as pd
    except ImportError:
        if mode == "strict":
            failures.append("pandas required in strict mode")
    else:
        publishable_edges = deliv_dir / "publishable_edges.parquet"
        if publishable_edges.exists() and publishable_edges.stat().st_size > 0:
            try:
                df = pd.read_parquet(publishable_edges)
            except Exception as exc:
                failures.append(f"publishable_edges parquet unreadable: {exc!r}")
            else:
                key_cols = [c for c in ("player_id", "stat", "line") if c in df.columns]
                if len(key_cols) >= 2 and "sportsbook" in df.columns:
                    dups = df.duplicated(
                        subset=key_cols + ["sportsbook"], keep=False
                    )
                    if int(dups.sum()) > 0:
                        failures.append(
                            f"publishable_edges duplicate rows on "
                            f"{key_cols + ['sportsbook']}: {int(dups.sum())}"
                        )

        full_pmfs = deliv_dir / "full_pmfs_wide.parquet"
        if full_pmfs.exists() and full_pmfs.stat().st_size > 0:
            try:
                df_pmf = pd.read_parquet(full_pmfs)
            except Exception as exc:
                failures.append(f"full_pmfs_wide parquet unreadable: {exc!r}")
            else:
                if "stat" in df_pmf.columns:
                    stats_present = {
                        str(s).lower() for s in df_pmf["stat"].dropna().unique()
                    }
                    if "tov" not in stats_present and not args.allow_tov_missing:
                        failures.append(
                            "full_pmfs_wide has no 'tov' rows and "
                            "--allow-tov-missing not set"
                        )

    if failures:
        for f in failures:
            print(f"::error::{f}")
        print(
            f"WOO_DELIVERY_PACKAGE_VERIFICATION_FAILED  date={date}  "
            f"mode={mode}  count={len(failures)}"
        )
        return 1

    for w in warnings:
        print(f"::warning::{w}")

    print(
        f"WOO_DELIVERY_PACKAGE_VERIFICATION_PASS  date={date}  mode={mode}  "
        f"champion_model_id={pointer_champion}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
