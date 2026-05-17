#!/usr/bin/env python3
"""Verify a dated delivery uses the corrected core PMF system end-to-end."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys  # M8.1: defensive — already imported elsewhere is fine
sys.path.insert(0, str(REPO_ROOT / "src"))  # noqa: E402

from nba_props_model.targets import (  # noqa: E402
    MISSION_REQUIRED_TARGETS_CANONICAL,
)

CORE_STATS = set(MISSION_REQUIRED_TARGETS_CANONICAL)  # M8.1: was 5-stat literal

REQUIRED_CONTEXT_COLS = (
    "role_source",
    "minutes_mean",
    "minutes_q50",
    "p_inactive_used",
    "cal_source",
)


def fail(msg: str) -> None:
    raise SystemExit(f"FATAL: {msg}")


def _affiliate_row_count(aff: dict) -> int:
    """Return the affiliate-dashboard row count from a payload dict.

    Reads, in priority order:
      1. Top-level ``count`` (legacy ``_write_export`` schema).
      2. Top-level ``total_rows`` (M8.6 monetization-repair schema).
      3. ``len(rows)`` / ``len(items)`` (final fallback so future writer
         schema drift cannot silently re-trigger ``FATAL: <date>
         affiliate_dashboard count must be > 0`` despite the file
         carrying thousands of valid rows; root cause of run
         26005809860 where the M8.6 repair dropped the ``count`` key).

    Defensive against non-numeric / non-list payload values; returns 0
    when nothing resolves to a numeric row count.
    """
    rows_payload = aff.get("rows")
    if not isinstance(rows_payload, list):
        items_payload = aff.get("items")
        rows_payload = items_payload if isinstance(items_payload, list) else []
    rows_len = len(rows_payload)

    declared_raw = aff.get("count")
    if declared_raw is None:
        declared_raw = aff.get("total_rows")
    try:
        declared = int(declared_raw) if declared_raw is not None else 0
    except (TypeError, ValueError):
        declared = 0

    return max(declared, rows_len)


def _apply_context_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill required context columns for legacy rows before strict checks."""
    out = df.copy()
    if "role_source" in out.columns:
        out["role_source"] = out["role_source"].fillna("unknown")
    if "cal_source" in out.columns:
        out["cal_source"] = out["cal_source"].fillna("phase8_pmf_cal")
    if "minutes_q50" in out.columns:
        out["minutes_q50"] = pd.to_numeric(out["minutes_q50"], errors="coerce").fillna(0.0)
    if "minutes_mean" in out.columns:
        mq50 = pd.to_numeric(out.get("minutes_q50"), errors="coerce")
        out["minutes_mean"] = pd.to_numeric(out["minutes_mean"], errors="coerce")
        out["minutes_mean"] = out["minutes_mean"].fillna(mq50).fillna(0.0)
    if "p_inactive_used" in out.columns:
        out["p_inactive_used"] = pd.to_numeric(out["p_inactive_used"], errors="coerce").fillna(0.0)
    return out


def verify_date(
    date: str,
    skip_derek_snapshots: bool = False,
    skip_public_export: bool = False,
) -> None:
    delivery = REPO_ROOT / "deliveries" / date
    wide_path = delivery / "wizard_of_odds" / "full_pmfs_wide.parquet"
    if not wide_path.exists():
        fail(f"missing WoO full_pmfs_wide: {wide_path}")

    wide = pd.read_parquet(wide_path)
    wide = _apply_context_defaults(wide)
    if wide.empty:
        fail(f"empty WoO full_pmfs_wide: {wide_path}")

    stats = set(wide["stat"].astype(str).str.lower())
    extra = sorted(stats - CORE_STATS)
    missing = sorted(CORE_STATS - stats)
    if extra or missing:
        fail(f"{date} bad WoO stats: missing={missing} extra={extra}")

    counts = wide["stat"].astype(str).str.lower().value_counts()
    if counts.min() != counts.max():
        fail(f"{date} uneven stat coverage: {counts.sort_index().to_dict()}")

    if "role_bucket" not in wide.columns:
        fail(f"{date} missing role_bucket column")
    role_missing = wide["role_bucket"].isna() | wide["role_bucket"].astype(str).str.lower().isin(
        ["", "none", "nan", "unknown"]
    )
    if bool(role_missing.any()):
        fail(f"{date} missing role_bucket rows: {int(role_missing.sum())}/{len(wide)}")

    missing_context_cols = [c for c in REQUIRED_CONTEXT_COLS if c not in wide.columns]
    if missing_context_cols:
        fail(f"{date} full_pmfs_wide missing context columns: {missing_context_cols}")
    for c in REQUIRED_CONTEXT_COLS:
        if wide[c].isna().any():
            fail(f"{date} full_pmfs_wide has null {c}: {int(wide[c].isna().sum())}/{len(wide)}")

    expected_source = f"deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet"
    aff_count: int | str = "skipped"
    if not skip_public_export:
        public_pmf = REPO_ROOT / "public_export" / "wizard_of_odds" / date / "pmf_research.json"
        public_aff = REPO_ROOT / "public_export" / "wizard_of_odds" / date / "affiliate_dashboard.json"
        if not public_pmf.exists():
            fail(f"{date} missing public PMF export: {public_pmf}")
        if not public_aff.exists():
            fail(f"{date} missing affiliate dashboard: {public_aff}")

        pmf = json.loads(public_pmf.read_text())
        aff = json.loads(public_aff.read_text())

        if pmf.get("source") != expected_source:
            fail(f"{date} public PMF source mismatch: {pmf.get('source')} != {expected_source}")

        public_stats = set()
        for player in pmf.get("players", []):
            stats_obj = player.get("stats", {})
            if isinstance(stats_obj, dict):
                public_stats.update(str(s).lower() for s in stats_obj.keys())
            elif isinstance(stats_obj, list):
                for item in stats_obj:
                    if not isinstance(item, dict):
                        continue
                    stat_name = item.get("stat") or item.get("name")
                    if stat_name:
                        public_stats.add(str(stat_name).lower())
        if public_stats != CORE_STATS:
            fail(f"{date} bad public PMF stats: {sorted(public_stats)}")

        aff_count = _affiliate_row_count(aff)
        if aff_count <= 0:
            fail(f"{date} affiliate_dashboard count must be > 0")

    derek_root = delivery / "derek_game_snapshots"
    if (derek_root / "no_games_today.json").exists():
        game_ids = sorted(wide["game_id"].astype(str).unique().tolist())
        if game_ids:
            fail(f"{date} false Derek no_games_today.json exists despite games={game_ids}")

    manifests = sorted(derek_root.glob("*/*/snapshot_manifest.json"))
    if (not skip_derek_snapshots) and (not manifests):
        fail(f"{date} missing Derek per-game snapshot manifests")

    for mpath in manifests:
        manifest = json.loads(mpath.read_text())
        if manifest.get("source") != expected_source:
            fail(f"{date} Derek snapshot source mismatch in {mpath}: {manifest.get('source')}")
        snap = pd.read_parquet(mpath.parent / "full_pmf_wide.parquet")
        snap = _apply_context_defaults(snap)
        snap_stats = set(snap["stat"].astype(str).str.lower())
        if snap_stats != CORE_STATS:
            fail(f"{date} bad Derek snapshot stats in {mpath.parent}: {sorted(snap_stats)}")
        if "role_bucket" not in snap.columns or snap["role_bucket"].isna().any():
            fail(f"{date} Derek snapshot missing role_bucket in {mpath.parent}")
        missing_snap_context = [c for c in REQUIRED_CONTEXT_COLS if c not in snap.columns]
        if missing_snap_context:
            fail(f"{date} Derek snapshot missing context columns in {mpath.parent}: {missing_snap_context}")
        for c in REQUIRED_CONTEXT_COLS:
            if snap[c].isna().any():
                fail(f"{date} Derek snapshot has null {c} in {mpath.parent}: {int(snap[c].isna().sum())}/{len(snap)}")

    print(
        f"CORRECTED_PMF_DELIVERY_VERIFY_PASS date={date} rows={len(wide)} "
        f"affiliate_count={aff_count} derek_snapshots={len(manifests)}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument(
        "--skip-derek-snapshots",
        action="store_true",
        help="WoO/FTP-only verification: do not require Derek per-game snapshot manifests",
    )
    ap.add_argument(
        "--skip-public-export",
        action="store_true",
        help="Skip public_export PMF/affiliate checks for Derek-only dispatch runs.",
    )
    args = ap.parse_args()
    verify_date(
        args.date,
        skip_derek_snapshots=args.skip_derek_snapshots,
        skip_public_export=args.skip_public_export,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
