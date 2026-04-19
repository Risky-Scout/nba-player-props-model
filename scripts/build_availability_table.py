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
        "--out", default=str(DATA_DIR / "player_availability_asof.parquet"),
        help="Output parquet path.",
    )
    args = parser.parse_args()

    t0 = time.time()
    logger.info("Loading source parquet files...")
    builder = AvailabilityBuilder.from_data_dir()
    logger.info(
        f"  injury_reports rows: {len(builder.injury_reports):,}"
        f"  | game_stats rows: {len(builder.game_stats):,}"
    )

    pairs = builder.game_stats[["player_id", "team_id", "game_date"]].drop_duplicates()
    if args.start_date:
        pairs = pairs[pairs["game_date"] >= args.start_date]
    if args.end_date:
        pairs = pairs[pairs["game_date"] <= args.end_date]
    logger.info(f"Building features for {len(pairs):,} (player, team, date) rows...")

    feats = builder.features_for(pairs)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
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
