"""Fail-fast pre-training data alignment verifier.

Checks that every data source the training pipeline relies on is aligned
to the declared AS_OF_DATE before training or Phase 8 calibration runs.

Checks performed:
  1. player_game_stats max(game_date) == AS_OF_DATE (within tolerance)
  2. player_availability_asof max(game_date <= AS_OF_DATE) == AS_OF_DATE (within tolerance)
  3. [--check-training-table] training_table max(game_date) == AS_OF_DATE
  4. availability player-game coverage >= 95%
  5. [--check-training-table] training_table has all required stats:
     pts, reb, ast, fg3m, stl, blk, tov

Exit codes:
  0 — all checks passed
  1 — one or more checks failed (details printed to stdout)

Do NOT call this script with || true. It is a hard gate.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

DATA_DIR = ROOT / "data"

REQUIRED_STATS = ["pts", "reb", "ast", "fg3m", "stl", "blk", "tov"]

# A gap of 1–2 days between max(game_date) and as_of_date is acceptable on
# rest days or days with no NBA games.  A gap of 3+ days is a hard failure.
MAX_ACCEPTABLE_GAP_DAYS = 2


# ── Helpers ────────────────────────────────────────────────────────────────────


def _read_max_date(path: Path, col: str = "game_date") -> str | None:
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path, columns=[col])
        if df.empty:
            return None
        return df[col].astype(str).str[:10].max()
    except Exception as exc:
        raise RuntimeError(f"Failed to read {path}: {exc}") from exc


def _read_max_date_filtered(
    path: Path, ceiling: str, col: str = "game_date"
) -> str | None:
    """Return max(game_date) for rows where game_date <= ceiling."""
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path, columns=[col])
        if df.empty:
            return None
        df = df[df[col].astype(str).str[:10] <= ceiling]
        return df[col].astype(str).str[:10].max() if not df.empty else None
    except Exception as exc:
        raise RuntimeError(f"Failed to read {path}: {exc}") from exc


def _date_gap(actual_max: str, expected: str) -> int:
    """Return (expected - actual_max).days.  Positive = actual is behind."""
    try:
        return (_date.fromisoformat(expected) - _date.fromisoformat(actual_max)).days
    except ValueError:
        return 9999


def _check_max_date(
    label: str,
    actual_max: str | None,
    expected: str,
    errors: list[str],
) -> None:
    if actual_max is None:
        errors.append(f"{label}: no data found (file empty or missing)")
        return
    if actual_max > expected:
        errors.append(
            f"{label}: max game_date ({actual_max}) is ABOVE as_of_date "
            f"({expected}) — future data leak detected"
        )
        return
    gap = _date_gap(actual_max, expected)
    if gap > MAX_ACCEPTABLE_GAP_DAYS:
        errors.append(
            f"{label}: max game_date ({actual_max}) is {gap} days BELOW "
            f"as_of_date ({expected}) — source data appears incomplete. "
            f"Run the BDL backfill script and retry."
        )
    elif gap > 0:
        print(
            f"  WARN {label}: max game_date ({actual_max}) is {gap} day(s) "
            f"before as_of_date ({expected}) — possible rest day or no-game day."
        )
    else:
        print(f"  OK   {label}: max game_date ({actual_max}) == {expected}")


# ── Individual checks ──────────────────────────────────────────────────────────


def check_player_game_stats(as_of_date: str, errors: list[str]) -> None:
    path = DATA_DIR / "player_game_stats.parquet"
    if not path.exists():
        errors.append(f"player_game_stats: file not found at {path}")
        return
    actual = _read_max_date(path)
    _check_max_date("player_game_stats", actual, as_of_date, errors)


def check_player_availability(as_of_date: str, errors: list[str]) -> None:
    path = DATA_DIR / "player_availability_asof.parquet"
    if not path.exists():
        errors.append(f"player_availability_asof: file not found at {path}")
        return
    # The availability parquet is built through delivery_date (which can be
    # one day ahead of as_of_date). Filter to <= as_of_date before checking.
    actual = _read_max_date_filtered(path, ceiling=as_of_date)
    _check_max_date("player_availability_asof (filtered ≤ as_of_date)", actual, as_of_date, errors)


def check_availability_coverage(as_of_date: str, errors: list[str]) -> None:
    avail_path = DATA_DIR / "player_availability_asof.parquet"
    stats_path = DATA_DIR / "player_game_stats.parquet"
    if not avail_path.exists() or not stats_path.exists():
        return  # missing-file errors already reported above
    try:
        avail_df = pd.read_parquet(avail_path, columns=["player_id", "game_date"])
        avail_df = avail_df[
            avail_df["game_date"].astype(str).str[:10] <= as_of_date
        ]
        stats_df = pd.read_parquet(stats_path, columns=["player_id", "game_date"])
        stats_df = stats_df[
            stats_df["game_date"].astype(str).str[:10] <= as_of_date
        ]
        if stats_df.empty:
            return
        avail_keys = set(
            zip(
                avail_df["player_id"].astype(int),
                avail_df["game_date"].astype(str).str[:10],
            )
        )
        stats_keys = set(
            zip(
                stats_df["player_id"].astype(int),
                stats_df["game_date"].astype(str).str[:10],
            )
        )
        matched = len(avail_keys & stats_keys)
        total = len(stats_keys)
        coverage = matched / total if total else 0.0
        if coverage < 0.95:
            errors.append(
                f"availability player-game coverage {coverage:.1%} < 95% threshold "
                f"({matched:,}/{total:,} player-games matched)"
            )
        else:
            print(
                f"  OK   availability coverage: {coverage:.1%} "
                f"({matched:,}/{total:,} player-games)"
            )
    except Exception as exc:
        errors.append(f"availability coverage check error: {exc}")


def check_training_table_max_date(as_of_date: str, errors: list[str]) -> None:
    path = DATA_DIR / "training_table.parquet"
    if not path.exists():
        errors.append(
            "training_table: file not found — run "
            "python3 scripts/train.py --build-table-only --as-of-date <date> first"
        )
        return
    actual = _read_max_date(path)
    _check_max_date("training_table", actual, as_of_date, errors)


def check_training_table_stats(errors: list[str]) -> None:
    path = DATA_DIR / "training_table.parquet"
    if not path.exists():
        return  # already reported above
    try:
        df = pd.read_parquet(path, columns=["stat"])
        present = set(df["stat"].dropna().unique())
        missing = [s for s in REQUIRED_STATS if s not in present]
        if missing:
            errors.append(
                f"training_table missing required stats: {missing} "
                f"(present: {sorted(present)})"
            )
        else:
            print(
                f"  OK   training_table stats: "
                f"{sorted(present & set(REQUIRED_STATS))}"
            )
    except Exception as exc:
        errors.append(f"training_table stats check error: {exc}")


# ── Entry point ────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--as-of-date",
        required=True,
        metavar="YYYY-MM-DD",
        help="Expected max game_date for all training source files.",
    )
    p.add_argument(
        "--check-training-table",
        action="store_true",
        help=(
            "Also verify training_table.parquet max date and required stats. "
            "Pass this flag after the table has been built."
        ),
    )
    args = p.parse_args()
    as_of_date = args.as_of_date

    print(
        f"verify_training_data_alignment: as_of_date={as_of_date} "
        f"check_training_table={args.check_training_table}"
    )

    errors: list[str] = []

    check_player_game_stats(as_of_date, errors)
    check_player_availability(as_of_date, errors)
    check_availability_coverage(as_of_date, errors)

    if args.check_training_table:
        check_training_table_max_date(as_of_date, errors)
        check_training_table_stats(errors)

    if errors:
        print(f"\nFAIL: {len(errors)} alignment error(s) for as_of_date={as_of_date}:")
        for err in errors:
            print(f"  ERROR: {err}")
        sys.exit(1)

    print(
        f"\nPASS: all data alignment checks passed for as_of_date={as_of_date}"
    )


if __name__ == "__main__":
    main()
