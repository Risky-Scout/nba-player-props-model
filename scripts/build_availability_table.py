"""Build the as-of player availability table used for training and eval.

Produces data/player_availability_asof.parquet with one row per
(player_id, game_date, team_id) for every game in
data/player_game_stats.parquet.

Runtime on full history: a few minutes single-threaded.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd  # noqa: E402

from nba_props_model.features.availability_asof import (  # noqa: E402
    AvailabilityBuilder,
)
from nba_props_model.paths import DATA_DIR  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_availability_table")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start-date", default=None,
        help="ISO start date (inclusive). Default: earliest game in stats.",
    )
    parser.add_argument(
        "--end-date", default=None,
        help="ISO end date (inclusive). Default: latest game in stats.",
    )
    parser.add_argument(
        "--slate-date",
        default=None,
        help=(
            "When set: rebuild availability only for this calendar date "
            "(YYYY-MM-DD), merge into existing --out, preserving all other "
            "dates. Mutually exclusive with --start-date/--end-date. "
            "Intended for daily PMF delivery preflight."
        ),
    )
    parser.add_argument(
        "--out", default=str(DATA_DIR / "player_availability_asof.parquet"),
        help="Output parquet path.",
    )
    args = parser.parse_args()

    if args.slate_date and (args.start_date or args.end_date):
        parser.error("--slate-date may not be combined with --start-date/--end-date")

    t0 = time.time()
    logger.info("Loading source parquet files...")
    builder = AvailabilityBuilder.from_data_dir()
    logger.info(
        f"  injury_reports rows: {len(builder.injury_reports):,}"
        f"  | game_stats rows: {len(builder.game_stats):,}"
    )

    pairs = builder.game_stats[["player_id", "team_id", "game_date"]].drop_duplicates()
    pairs = pairs.copy()
    pairs["_game_date_norm"] = (
        pd.to_datetime(pairs["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    )
    if args.slate_date:
        pairs = pairs[pairs["_game_date_norm"] == args.slate_date]
        if pairs.empty:
            logger.warning(
                "No game_stats rows for slate_date=%s — leaving %s unchanged.",
                args.slate_date,
                args.out,
            )
            return
    else:
        if args.start_date:
            pairs = pairs[pairs["_game_date_norm"] >= args.start_date]
        if args.end_date:
            pairs = pairs[pairs["_game_date_norm"] <= args.end_date]
    pairs_use = pairs[["player_id", "team_id", "game_date"]].drop_duplicates()
    logger.info(f"Building features for {len(pairs_use):,} (player, team, date) rows...")

    feats = builder.features_for(pairs_use)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.slate_date and out_path.exists():
        old = pd.read_parquet(out_path)
        old_norm = pd.to_datetime(old["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        old_kept = old.loc[old_norm != args.slate_date].copy()
        merged = pd.concat([old_kept, feats], ignore_index=True)
        merged.to_parquet(out_path, index=False)
        slice_mask = (
            pd.to_datetime(merged["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
            == args.slate_date
        )
        _log_coverage(merged.loc[slice_mask])
        dt = time.time() - t0
        logger.info(
            f"Merged slate {args.slate_date!r}: {len(feats):,} new rows, "
            f"{len(merged):,} total -> {out_path}  ({dt:.1f}s)"
        )
    elif out_path.exists() and (args.start_date or args.end_date):
        old = pd.read_parquet(out_path)
        old_norm = pd.to_datetime(old["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        start_filter = args.start_date or "0000-01-01"
        end_filter = args.end_date or "9999-12-31"
        old_kept = old.loc[~((old_norm >= start_filter) & (old_norm <= end_filter))].copy()
        merged = pd.concat([old_kept, feats], ignore_index=True)
        merged.to_parquet(out_path, index=False)
        dt = time.time() - t0
        logger.info(
            f"Merged range {start_filter} \u2192 {end_filter}: "
            f"{len(feats):,} new rows, {len(merged):,} total -> {out_path}  ({dt:.1f}s)"
        )
        _log_coverage(feats)
    else:
        feats.to_parquet(out_path, index=False)
        dt = time.time() - t0
        logger.info(f"Wrote {len(feats):,} rows -> {out_path}  ({dt:.1f}s)")
        _log_coverage(feats)


def _log_coverage(feats: pd.DataFrame) -> None:
    by_conf = feats["availability_confidence"].value_counts(dropna=False)
    total = len(feats)
    logger.info("Confidence tier coverage:")
    for tier in ("HIGH", "MEDIUM", "LOW"):
        n = int(by_conf.get(tier, 0))
        logger.info(f"  {tier:6s}  {n:>8,}  ({n/total:.1%})")

    by_status = feats["availability_status"].value_counts(dropna=False)
    logger.info("Status distribution:")
    for status, n in by_status.items():
        logger.info(f"  {status:12s}  {int(n):>8,}")


if __name__ == "__main__":
    main()
