#!/usr/bin/env python3
"""Verify a dated delivery uses the corrected core PMF system end-to-end."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_STATS = {"pts", "reb", "ast", "fg3m", "tov"}

REQUIRED_CONTEXT_COLS = (
    "role_source",
    "minutes_mean",
    "minutes_q50",
    "p_inactive_used",
    "cal_source",
)


def fail(msg: str) -> None:
    raise SystemExit(f"FATAL: {msg}")


def verify_date(date: str, skip_derek_snapshots: bool = False) -> None:
    delivery = REPO_ROOT / "deliveries" / date
    wide_path = delivery / "wizard_of_odds" / "full_pmfs_wide.parquet"
    if not wide_path.exists():
        fail(f"missing WoO full_pmfs_wide: {wide_path}")

    wide = pd.read_parquet(wide_path)
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

    public_pmf = REPO_ROOT / "public_export" / "wizard_of_odds" / date / "pmf_research.json"
    public_aff = REPO_ROOT / "public_export" / "wizard_of_odds" / date / "affiliate_dashboard.json"
    if not public_pmf.exists():
        fail(f"{date} missing public PMF export: {public_pmf}")
    if not public_aff.exists():
        fail(f"{date} missing affiliate dashboard: {public_aff}")

    pmf = json.loads(public_pmf.read_text())
    aff = json.loads(public_aff.read_text())

    expected_source = f"deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet"
    if pmf.get("source") != expected_source:
        fail(f"{date} public PMF source mismatch: {pmf.get('source')} != {expected_source}")

    public_stats = set()
    for player in pmf.get("players", []):
        public_stats.update(str(s).lower() for s in player.get("stats", {}).keys())
    if public_stats != CORE_STATS:
        fail(f"{date} bad public PMF stats: {sorted(public_stats)}")

    if int(aff.get("count") or 0) <= 0:
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

    print(f"CORRECTED_PMF_DELIVERY_VERIFY_PASS date={date} rows={len(wide)} affiliate_count={aff.get('count')} derek_snapshots={len(manifests)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument(
        "--skip-derek-snapshots",
        action="store_true",
        help="WoO/FTP-only verification: do not require Derek per-game snapshot manifests",
    )
    args = ap.parse_args()
    verify_date(args.date, skip_derek_snapshots=args.skip_derek_snapshots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
