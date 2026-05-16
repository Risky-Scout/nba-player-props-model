"""Pre-canonical slate universe seed.

The morning-monetization pipeline needs to build the feature snapshot
BEFORE the canonical ``player_prop_pmfs_tonight_MODEL_ONLY.parquet`` is
written, because the canonical MODEL_ONLY is downstream of the stat
grid which itself consumes the feature snapshot. The historical
ordering — feature_snapshot reads canonical MODEL_ONLY as its base
universe — produced a circular dependency on a clean slate
(``SAME_DAY_SOURCE_INPUTS_MISSING``).

The fix is a narrowly scoped, explicit ``pre-canonical slate universe``
seed:

  * Sourced from ``predictions/all_props_<date>.parquet`` (the dated
    prediction output that already carries player_id / game_id /
    slate_date and identity columns).
  * Deduplicated to the ``(player_id, game_id)`` level — exactly the
    slate identity grid that downstream feature population needs.
  * Strict-validated: rows > 0, non-null player_id / game_id, no
    duplicate ``(player_id, game_id)`` rows, ``slate_date`` matches
    the delivery date.
  * Persisted as
    ``data/features/precanonical_slate_universe_<date>_<run_mode>.parquet``
    so it is unmistakably NOT canonical MODEL_ONLY and cannot be
    accidentally consumed by canonical-build callers.

This module deliberately does NOT touch canonical MODEL_ONLY. Canonical
MODEL_ONLY remains built only by ``build_model_only_canonical_from_stat_grid.py``
from the stat-grid output.

Failure markers (raised as RuntimeError so callers can render them
verbatim and the CI step exits non-zero):

  * ``PRECANNONICAL_SLATE_UNIVERSE_MISSING``     — input parquet
    absent or unreadable
  * ``PRECANNONICAL_SLATE_UNIVERSE_EMPTY``       — input present but
    zero rows
  * ``PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING`` — player_id /
    game_id missing or null
  * ``PRECANNONICAL_SLATE_UNIVERSE_DATE_MISMATCH`` — ``slate_date``
    column carries a value other than the requested delivery date
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


class PrecanonicalSlateUniverseError(RuntimeError):
    """Raised on any pre-canonical seed contract violation.

    The ``args[0]`` carries the structured marker line ready for stderr.
    """


REQUIRED_IDENTITY_COLUMNS: tuple[str, ...] = ("player_id", "game_id")

# Columns the downstream feature populators benefit from but are not
# strictly required. We keep whichever subset is actually present in the
# upstream prediction output.
OPTIONAL_IDENTITY_COLUMNS: tuple[str, ...] = (
    "slate_date",
    "player_name",
    "team_id",
    "team_abbr",
    "team",
    "opponent_team_id",
    "opponent_abbr",
    "opponent",
    "is_home",
    "game_start_time_utc",
    "game_start_et",
    "game_date",
)


def predictions_all_props_path(repo_root: Path, date: str) -> Path:
    return repo_root / "predictions" / f"all_props_{date}.parquet"


def precanonical_seed_path(
    repo_root: Path, date: str, run_mode: str
) -> Path:
    return (
        repo_root
        / "data"
        / "features"
        / f"precanonical_slate_universe_{date}_{run_mode}.parquet"
    )


def _read_all_props_parquet(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_MISSING path={path}"
        )
    try:
        return pd.read_parquet(path)
    except Exception as exc:
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_MISSING "
            f"path={path} reason=unreadable exc={type(exc).__name__}:{exc}"
        ) from exc


def build_precanonical_slate_universe(
    all_props_df: pd.DataFrame, delivery_date: str
) -> pd.DataFrame:
    """Strict-build the pre-canonical seed DataFrame.

    Returns a deduplicated ``(player_id, game_id)`` frame carrying the
    identity columns required by the feature snapshot populators. Raises
    :class:`PrecanonicalSlateUniverseError` on any contract violation.
    """
    if all_props_df is None or len(all_props_df) == 0:
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_EMPTY "
            f"delivery_date={delivery_date} rows=0"
        )

    present = set(all_props_df.columns)
    missing = [c for c in REQUIRED_IDENTITY_COLUMNS if c not in present]
    if missing:
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING "
            f"delivery_date={delivery_date} missing={missing} "
            f"present={sorted(present)}"
        )

    # Slate-date integrity: every row that carries slate_date must agree
    # with the delivery date. Missing/blank slate_date is tolerated (we
    # will stamp it on the seed), but mismatched values are fatal — they
    # indicate predict.py ran for a different date.
    if "slate_date" in all_props_df.columns:
        slate_vals = (
            all_props_df["slate_date"].astype("string").str.strip()
        )
        non_blank = slate_vals[slate_vals.notna() & (slate_vals.str.len() > 0)]
        bad = non_blank[non_blank != delivery_date]
        if len(bad) > 0:
            sample = bad.head(5).tolist()
            raise PrecanonicalSlateUniverseError(
                f"PRECANNONICAL_SLATE_UNIVERSE_DATE_MISMATCH "
                f"delivery_date={delivery_date} "
                f"observed_sample={sample} bad_row_count={int(len(bad))}"
            )

    keep_cols = [
        c
        for c in (*REQUIRED_IDENTITY_COLUMNS, *OPTIONAL_IDENTITY_COLUMNS)
        if c in all_props_df.columns
    ]
    seed = all_props_df.loc[:, keep_cols].copy()

    seed = seed.dropna(subset=list(REQUIRED_IDENTITY_COLUMNS))
    if len(seed) == 0:
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING "
            f"delivery_date={delivery_date} "
            f"reason=all_rows_had_null_player_or_game_id"
        )

    seed["player_id"] = pd.to_numeric(seed["player_id"], errors="coerce")
    seed["game_id"] = pd.to_numeric(seed["game_id"], errors="coerce")
    seed = seed.dropna(subset=["player_id", "game_id"])
    if len(seed) == 0:
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING "
            f"delivery_date={delivery_date} "
            f"reason=player_or_game_id_not_numeric"
        )

    seed["player_id"] = seed["player_id"].astype("int64")
    seed["game_id"] = seed["game_id"].astype("int64")

    seed = seed.drop_duplicates(subset=["player_id", "game_id"]).reset_index(drop=True)

    seed["slate_date"] = delivery_date
    if "game_date" not in seed.columns:
        seed["game_date"] = delivery_date
    else:
        seed["game_date"] = seed["game_date"].fillna(delivery_date)

    if len(seed) == 0:
        raise PrecanonicalSlateUniverseError(
            f"PRECANNONICAL_SLATE_UNIVERSE_EMPTY "
            f"delivery_date={delivery_date} rows=0 reason=post_dedup_empty"
        )

    return seed


def materialize_precanonical_slate_universe(
    repo_root: Path,
    *,
    date: str,
    run_mode: str,
    source_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    """Read predictions/all_props_<date>.parquet, build the seed, persist it.

    Returns the path to the written seed parquet. Raises
    :class:`PrecanonicalSlateUniverseError` (with structured marker) on
    any contract violation; callers should surface the exception's
    message verbatim and exit non-zero.
    """
    src = source_path if source_path is not None else predictions_all_props_path(repo_root, date)
    df = _read_all_props_parquet(src)
    seed = build_precanonical_slate_universe(df, date)

    target = out_path if out_path is not None else precanonical_seed_path(repo_root, date, run_mode)
    target.parent.mkdir(parents=True, exist_ok=True)
    seed.to_parquet(target, index=False)
    return target
