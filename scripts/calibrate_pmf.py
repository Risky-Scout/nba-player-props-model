"""
Fit the full-PMF CDF calibrators walk-forward out-of-fold.

Per docs/MIGRATION.md §3 step 3:
  * load the full training table via the same loader used by train.py
    (we read the persisted data/training_table.parquet which is written
    at the end of build_training_table so the loader is deterministic)
  * define walk-forward 28-day OOF folds respecting season boundaries
  * for each fold, refit the pipeline models on data strictly before the
    fold start and simulate PMFs on the fold's validation window
  * collect the full OOF (PMF, outcome, date) universe per stat
  * fit per-stat isotonic calibrators via
    calibration.pmf_calibration.fit_all
  * persist pmf_cal_{stat}.pkl artifacts to artifacts/models/
  * print fit diagnostics per stat (PIT moments, KS distance, monotonicity)

Known caveat (documented below and in artifacts/docs/pmf_calibration_run.md):
    training_df's baked-in mp_* feature columns were computed using the
    full-data minutes model, which introduces a small amount of indirect
    leakage when that training_df is sliced per-fold. This implementation
    accepts that leakage and refits the minutes, rate, and hurdle models
    per fold on the feature-sliced data. A strict no-leakage pass would
    require regenerating training_df per fold (~20 min per regen) which
    is not practical for a one-off calibration run.

Reproducible invocation:
    python scripts/calibrate_pmf.py
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nba_props_model.calibration.pmf_calibration import fit_all  # noqa: E402
from nba_props_model.paths import DATA_DIR, MODEL_DIR, REPO_ROOT  # noqa: E402
from nba_props_model.models.minutes import (  # noqa: E402
    MinutesDistribution,
    _compute_rolling_features,
    _coerce_availability,
    minutes_distribution,
    train_state_aware_minutes_model,
    AVAILABILITY_FEATURES,
)
from nba_props_model.models.rate_models import RATE_STATS, train_rate_models  # noqa: E402
from nba_props_model.models.sparse_hurdle import (  # noqa: E402
    SPARSE_STATS, STOCKS_DOMAIN_MAX, stocks_pmf, train_sparse_hurdle,
    DOMAIN_MAX as SPARSE_DOMAIN_MAX,
)
from nba_props_model.models.fg3m_hurdle import FG3MHurdleModel  # noqa: E402
from nba_props_model.models.simulation import DOMAIN_MAX as MAIN_DOMAIN_MAX  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("calibrate_pmf")


# ── configuration ───────────────────────────────────────────────────────────

FOLD_DAYS = 28
MIN_TRAIN_DAYS = 365        # at least one full season of training data
MIN_VAL_ROWS_PER_STAT = 80  # under this we mark the fold insufficient
DOMAIN_MAX_BY_STAT = {
    **{s: MAIN_DOMAIN_MAX[s] for s in RATE_STATS},
    **{s: SPARSE_DOMAIN_MAX[s] for s in SPARSE_STATS},
    "stocks": STOCKS_DOMAIN_MAX,
    "fg3m": 15,
}


# ── NBA season gating ───────────────────────────────────────────────────────


def _season_of(date: pd.Timestamp) -> int:
    """Return NBA season year for a date (year of season start)."""
    y = int(date.year)
    return y if date.month >= 10 else y - 1


def _is_offseason(date: pd.Timestamp) -> bool:
    """NBA regular season roughly Oct 20 to mid-April; playoffs through June.
    We treat July/Aug/Sep as offseason — no useful folds there."""
    return date.month in (7, 8, 9)


def make_walk_forward_folds(
    all_dates: pd.Series,
    fold_days: int = FOLD_DAYS,
    min_train_days: int = MIN_TRAIN_DAYS,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Build (fold_start, fold_end) windows.

    Folds never straddle offseason (July/Aug/Sep). If a proposed fold
    start lies in the offseason, the start is advanced to the next Oct 15.
    """
    sorted_dates = pd.to_datetime(all_dates).sort_values().reset_index(drop=True)
    if sorted_dates.empty:
        return []
    first = sorted_dates.iloc[0]
    last = sorted_dates.iloc[-1]
    fold_start = first + pd.Timedelta(days=min_train_days)
    folds: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    while fold_start <= last:
        if _is_offseason(fold_start):
            # Jump to Oct 15 of the season we're in (or the next one).
            y = fold_start.year
            fold_start = pd.Timestamp(year=y, month=10, day=15)
            continue
        fold_end = fold_start + pd.Timedelta(days=fold_days)
        if fold_end <= last:
            folds.append((fold_start, fold_end))
        fold_start = fold_end
    return folds


# ── artifact-directory rewiring ─────────────────────────────────────────────

_PATCHED_MODULES = (
    "nba_props_model.paths",
    "nba_props_model.models.minutes",
    "nba_props_model.models.rate_models",
    "nba_props_model.models.sparse_hurdle",
    "nba_props_model.calibration.stat_side_platt",
    "nba_props_model.calibration.residual_centering",
)


def _swap_model_dir(new_dir: Path) -> dict[str, Path]:
    """Point every consumer module's MODEL_DIR attribute at `new_dir`.

    Returns a dict of originals for restoration. Also clears the module-
    level caches so fresh fold artifacts are loaded.
    """
    originals: dict[str, Path] = {}
    for modname in _PATCHED_MODULES:
        m = importlib.import_module(modname)
        if hasattr(m, "MODEL_DIR"):
            originals[modname] = m.MODEL_DIR
            m.MODEL_DIR = new_dir
    # Clear caches so the re-loaders find the fresh artifacts.
    from nba_props_model.models import minutes as m_minutes
    from nba_props_model.models import rate_models as m_rate
    from nba_props_model.models import sparse_hurdle as m_hurdle
    m_minutes._STATE_CLF = None
    m_minutes._COND_Q = {}
    m_minutes._STATE_FEATURES = None
    m_minutes._LEGACY_CACHE = {}
    m_minutes._LEGACY_FEATURES = None
    m_rate._RATE_CACHE = {}
    m_hurdle._SPARSE_CACHE = {}
    return originals


def _restore_model_dir(originals: dict[str, Path]) -> None:
    for modname, original in originals.items():
        m = importlib.import_module(modname)
        m.MODEL_DIR = original
    # Invalidate caches after restoration so subsequent calls see the
    # full-data artifacts.
    from nba_props_model.models import minutes as m_minutes
    from nba_props_model.models import rate_models as m_rate
    from nba_props_model.models import sparse_hurdle as m_hurdle
    m_minutes._STATE_CLF = None
    m_minutes._COND_Q = {}
    m_minutes._STATE_FEATURES = None
    m_minutes._LEGACY_CACHE = {}
    m_minutes._LEGACY_FEATURES = None
    m_rate._RATE_CACHE = {}
    m_hurdle._SPARSE_CACHE = {}


# ── per-fold refits ─────────────────────────────────────────────────────────


def _refit_models_for_fold(
    fold_start: pd.Timestamp,
    stats_df: pd.DataFrame,
    availability_df: pd.DataFrame,
    training_df: pd.DataFrame,
    fold_artifact_dir: Path,
    allowed_stats: set[str] | None = None,
) -> None:
    """Refit minutes + rate + hurdle + fg3m on data strictly before fold_start.

    `allowed_stats` restricts which per-stat trainers run. The minutes model
    always trains because every downstream stat PMF depends on it. None
    means "train the full family" (unchanged legacy behavior).

    Writes the trained artifacts to fold_artifact_dir. Caller is
    responsible for having swapped MODEL_DIR to fold_artifact_dir before
    invoking this.
    """
    fold_artifact_dir.mkdir(parents=True, exist_ok=True)

    train_stats = stats_df[pd.to_datetime(stats_df["game_date"]) < fold_start]
    train_avail = availability_df[pd.to_datetime(availability_df["game_date"]) < fold_start]
    train_training = training_df[pd.to_datetime(training_df["game_date"]) < fold_start]

    logger.info(
        f"  refit train stats rows={len(train_stats):,}  "
        f"training_df rows={len(train_training):,}"
    )

    # State-aware minutes (always trained — needed by every downstream stat).
    train_state_aware_minutes_model(train_stats, availability_df=train_avail)

    # Build wide view for rate + sparse hurdle.
    raw_cols = ["player_id", "game_id", "min",
                "pts", "reb", "ast", "turnover", "stl", "blk"]
    pts_slice = train_training[train_training["stat"] == "pts"].drop(columns=["actual"])
    overlap = [c for c in raw_cols if c not in ("player_id", "game_id")
               and c in pts_slice.columns]
    if overlap:
        pts_slice = pts_slice.drop(columns=overlap)
    wide = pts_slice.merge(
        train_stats[raw_cols], on=["player_id", "game_id"], how="left",
    )

    # Rate models — subset when allowed_stats is given.
    from nba_props_model.models.rate_models import RATE_STATS
    rate_subset = (
        tuple(s for s in RATE_STATS if s in allowed_stats)
        if allowed_stats is not None else RATE_STATS
    )
    if rate_subset:
        train_rate_models(wide, stats=rate_subset)
    else:
        logger.info("  rate models: none in allowed_stats, skipping")

    # Sparse hurdle (stl / blk) — subset when allowed_stats is given.
    from nba_props_model.models.sparse_hurdle import SPARSE_STATS
    sparse_subset = (
        tuple(s for s in SPARSE_STATS if s in allowed_stats)
        if allowed_stats is not None else SPARSE_STATS
    )
    if sparse_subset:
        train_sparse_hurdle(wide, stats=sparse_subset)
    else:
        logger.info("  sparse hurdle (stl/blk): skipped (not in allowed_stats)")

    # FG3M hurdle. Same column-alias block used by the main pipeline.
    if allowed_stats is not None and "fg3m" not in allowed_stats:
        logger.info("  fg3m hurdle: skipped (not in allowed_stats)")
    else:
        fg3m_df = train_training[train_training["stat"] == "fg3m"].copy()
        if len(fg3m_df) > 500:
            for src, dst, mul in [
                ("per_min_fg3a_last10", "mean_fg3a_last10", "mp_mean_last10"),
                ("per_min_fg3a_last10", "mean_fg3a_last5",  "mp_mean_last10"),
                ("per_min_fg3a_last10", "season_mean_fg3a", "mp_mean_season"),
                ("per_min_fg3a_last10", "ewma10_fg3a",      "mp_ewma_10"),
            ]:
                if dst not in fg3m_df.columns and src in fg3m_df.columns:
                    fg3m_df[dst] = fg3m_df[src] * fg3m_df.get(mul, 36).fillna(36)
            if "zero_pct_fg3a" not in fg3m_df.columns and "fg3m_p_zero_last10" in fg3m_df.columns:
                fg3m_df["zero_pct_fg3a"] = fg3m_df["fg3m_p_zero_last10"]
            if "trend_fg3a" not in fg3m_df.columns and "fg3a_attempt_trend" in fg3m_df.columns:
                fg3m_df["trend_fg3a"] = fg3m_df["fg3a_attempt_trend"]
            if "per_min_fg3a_season" not in fg3m_df.columns and "per_min_fg3a_last10" in fg3m_df.columns:
                fg3m_df["per_min_fg3a_season"] = fg3m_df["per_min_fg3a_last10"]
            fg3m_hurdle = FG3MHurdleModel()
            fg3m_hurdle.fit(fg3m_df)
            fg3m_hurdle.save(str(fold_artifact_dir / "fg3m_hurdle.pkl"))
        else:
            logger.warning("  fg3m hurdle: insufficient rows, skipping")


# ── per-fold OOF PMF generation ─────────────────────────────────────────────


# Cumulative wall-clock accumulators for the OOF PMF hot path. Printed
# unconditionally at the end of every _generate_fold_pmfs call so every
# Phase 8 run emits hotspot data — no debug flag required. Named row-loop
# keys sum to "row_total" within a small residual ("unattributed_row_
# overhead"). Meta keys (_generate_fold_pmfs_total, parquet_write,
# row_total) are excluded from the residual calculation.
_PMF_GEN_TIMES: dict = {}
_PMF_GEN_COUNTS: dict = {}
_PMF_GEN_META_KEYS = frozenset({"_generate_fold_pmfs_total", "parquet_write", "row_total"})


def _reset_pmf_gen_timers() -> None:
    _PMF_GEN_TIMES.clear()
    _PMF_GEN_COUNTS.clear()


def _pmf_timer_add(key: str, seconds: float, count: int = 1) -> None:
    _PMF_GEN_TIMES[key] = _PMF_GEN_TIMES.get(key, 0.0) + seconds
    _PMF_GEN_COUNTS[key] = _PMF_GEN_COUNTS.get(key, 0) + count


def _log_pmf_gen_summary(val_row_count: int, fold_index: int | None) -> None:
    total = _PMF_GEN_TIMES.get("_generate_fold_pmfs_total", 0.0)
    row_total = _PMF_GEN_TIMES.get("row_total", 0.0)
    n_rows = _PMF_GEN_COUNTS.get("row_total", 0)
    tag = f"fold={fold_index}" if fold_index is not None else "fold=?"
    logger.info("=" * 60)
    logger.info(f"PMF GEN TIMING [{tag}] val_rows={val_row_count}  rows_processed={n_rows}")
    logger.info("=" * 60)
    logger.info(f"  {'_generate_fold_pmfs_total':32s} {total:8.2f}s")
    if val_row_count > 0:
        logger.info(f"  avg per input val row          {1000.0*total/val_row_count:8.2f}ms")
    # Row-loop timers, sorted descending by cumulative wall-clock.
    named_items = sorted(
        ((k, v) for k, v in _PMF_GEN_TIMES.items() if k not in _PMF_GEN_META_KEYS),
        key=lambda kv: kv[1], reverse=True,
    )
    for k, v in named_items:
        n = _PMF_GEN_COUNTS.get(k, 0)
        pct = 100.0 * v / max(row_total, 1e-9)
        avg_ms = 1000.0 * v / max(n, 1) if n else 0.0
        logger.info(f"  {k:32s} {v:8.2f}s  ({pct:5.1f}%)  n={n:>7d}  avg={avg_ms:7.2f}ms")
    logger.info(
        f"  {'row_total':32s} {row_total:8.2f}s  "
        f"n={n_rows:>7d}  avg={1000.0*row_total/max(n_rows,1):7.2f}ms"
    )
    # Unattributed residual: row_total - sum(named row-loop timers).
    summed = sum(v for k, v in _PMF_GEN_TIMES.items() if k not in _PMF_GEN_META_KEYS)
    unattributed = max(row_total - summed, 0.0)
    pct_u = 100.0 * unattributed / max(row_total, 1e-9)
    avg_u_ms = 1000.0 * unattributed / max(n_rows, 1) if n_rows else 0.0
    logger.info(
        f"  {'unattributed_row_overhead':32s} {unattributed:8.2f}s  "
        f"({pct_u:5.1f}%)  n={n_rows:>7d}  avg={avg_u_ms:7.2f}ms"
    )
    # Parquet-write timing lives outside the row loop; print separately.
    pq = _PMF_GEN_TIMES.get("parquet_write")
    if pq is not None:
        logger.info(f"  {'parquet_write (post-loop)':32s} {pq:8.2f}s")


def _load_fg3m_if_present(model_dir: Path) -> FG3MHurdleModel | None:
    p = model_dir / "fg3m_hurdle.pkl"
    if not p.exists():
        return None
    try:
        return FG3MHurdleModel.load(str(p))
    except Exception as e:
        logger.warning(f"  fg3m load failed: {e}")
        return None


def _generate_fold_pmfs(
    val_rows: pd.DataFrame,
    stats_df: pd.DataFrame,
    availability_df: pd.DataFrame,
    fold_artifact_dir: Path,
    allowed_stats: set[str] | None = None,
    fold_index: int | None = None,
    pmf_draws: int = 300,
) -> dict[str, list[dict]]:
    """Produce per-stat OOF PMFs on val_rows using models trained for this fold.

    Returns mapping stat -> list of {'player_id', 'game_id', 'game_date',
    'outcome', 'pmf', 'pmf_cal_source'}. stocks and combos are included in
    v1 only for sparse stats — combos derive in the predict-layer not
    here.

    Emits an unconditional PMF GEN TIMING summary at completion. See the
    module-level _PMF_GEN_TIMES / _PMF_GEN_COUNTS accumulators.
    """
    _reset_pmf_gen_timers()
    _t_total_start = time.perf_counter()
    from nba_props_model.models.rate_models import rate_quantiles
    from nba_props_model.models.sparse_hurdle import hurdle_pmf

    fg3m_model = _load_fg3m_if_present(fold_artifact_dir)
    avail_lookup: dict[tuple[int, str], dict] = {}
    for r in availability_df.itertuples(index=False):
        avail_lookup[(int(r.player_id), str(r.game_date))] = {
            c: getattr(r, c, None) for c in AVAILABILITY_FEATURES
        }

    stats_by_player_date: dict[int, pd.DataFrame] = {
        pid: g.sort_values("game_date").reset_index(drop=True)
        for pid, g in stats_df.groupby("player_id")
    }

    # Per-row stat lookup — one O(1) dict hit per val row instead of an
    # O(N) boolean scan of stats_df. Holds the first box-score row for
    # each (player_id, game_id) pair; the previous boolean filter also
    # consumed `.iloc[0]`, so semantics are preserved. Values are stored
    # as dicts so downstream .get(col, default) calls behave identically.
    row_stats_lookup: dict[tuple[int, int], dict] = {}
    row_stats_dup_count = 0
    for _r in stats_df.itertuples(index=False):
        _key = (int(_r.player_id), int(_r.game_id))
        if _key in row_stats_lookup:
            row_stats_dup_count += 1
            continue
        row_stats_lookup[_key] = _r._asdict()
    logger.info(
        f"row_stats_lookup built: {len(row_stats_lookup):,} unique (player_id, "
        f"game_id) keys; duplicate_key_count={row_stats_dup_count:,}"
    )
    # Sanity: confirm itertuples._asdict() preserved stats_df column names
    # intact (and did not rename any columns to _0, _1, ... because they
    # weren't valid Python identifiers). Log the key list of the first
    # entry so any silent renames surface before the loop starts.
    if row_stats_lookup:
        _sample_key = next(iter(row_stats_lookup))
        _sample_keys = list(row_stats_lookup[_sample_key].keys())
        logger.info(
            f"row_stats_lookup sanity: sample_key={_sample_key}, "
            f"keys={_sample_keys}"
        )

    # Pre-sorted date vectors per player for O(log N) history slicing —
    # replaces the per-row boolean filter `history["game_date"] < date`.
    # Each stats_by_player_date frame is already sort_values("game_date")
    # + reset_index(drop=True), so a searchsorted on the "game_date"
    # column yields the same cutoff as the prior boolean filter (strict
    # < comparison on 10-char ISO strings is monotone).
    history_date_vec: dict[int, np.ndarray] = {
        pid: df["game_date"].astype(str).str.slice(0, 10).to_numpy()
        for pid, df in stats_by_player_date.items()
    }

    results: dict[str, list[dict]] = {s: [] for s in list(RATE_STATS) + list(SPARSE_STATS) + ["stocks", "fg3m"]}

    rng = np.random.default_rng(0)
    for row in val_rows.itertuples(index=False):
        _row_t0 = time.perf_counter()
        try:
            player_id = int(row.player_id)
            game_id = int(row.game_id)
            game_date = str(row.game_date)[:10]

            # history + usable-length guard — timed as history_filter on
            # every exit path (nested try/finally captures both continues).
            _hf_t0 = time.perf_counter()
            try:
                history_full = stats_by_player_date.get(player_id)
                if history_full is None:
                    continue
                date_vec = history_date_vec.get(player_id)
                # searchsorted side='left' returns the first index whose
                # date >= game_date; rows before it satisfy the old
                # strict `< game_date` filter.
                cutoff = int(np.searchsorted(date_vec, game_date, side="left"))
                if cutoff < 10:
                    continue
                history = history_full.iloc[:cutoff]
            finally:
                _pmf_timer_add("history_filter", time.perf_counter() - _hf_t0)

            # Context: recover is_home, rest_days, back_to_back from stats_df.
            # (stats_df has home_team_id / team_id which lets us infer is_home;
            # rest_days is the gap since the previous played game.)
            prev_games = history.tail(1)
            rest_days = 2
            if len(prev_games):
                prev_date = pd.to_datetime(prev_games.iloc[-1]["game_date"])
                rest_days = int((pd.to_datetime(game_date) - prev_date).days)
            b2b = 1 if rest_days == 1 else 0

            avail = avail_lookup.get((player_id, game_date))
            # O(1) pre-indexed lookup — replaces the O(|stats_df|) boolean
            # filter + .iloc[0]. Semantics preserved: same (player_id,
            # game_id) row, same field set. Missing key maps to the old
            # early-continue on row_stats.empty.
            row_stats = row_stats_lookup.get((player_id, game_id))
            if row_stats is None:
                continue
            team_id = int(row_stats["team_id"])
            is_home = int(row_stats["home_team_id"] == team_id)

            try:
                _t = time.perf_counter()
                m_dist = minutes_distribution(
                    prior_stats=history, game_context={"rest_days": rest_days, "back_to_back": b2b},
                    is_home=bool(is_home), target_date=game_date, team_id=team_id,
                    all_stats_df=stats_df, injury_map={}, availability=avail,
                )
                _pmf_timer_add("minutes_distribution_build", time.perf_counter() - _t)
            except Exception as e:
                logger.debug(f"  minutes_distribution failed for ({player_id},{game_id}): {e}")
                continue

            _fr_t0 = time.perf_counter()
            feature_row = {k: getattr(row, k, 0.0) for k in row._fields}
            _pmf_timer_add("feature_row_build", time.perf_counter() - _fr_t0)

            def _allowed(stat: str) -> bool:
                return allowed_stats is None or stat in allowed_stats

            # Main stats via minutes x rate simulation.
            for stat in RATE_STATS:
                if not _allowed(stat):
                    continue
                _t = time.perf_counter()
                q = rate_quantiles(stat, feature_row)
                _pmf_timer_add(f"rate_quantiles.{stat}", time.perf_counter() - _t)
                if q is None:
                    continue
                from nba_props_model.models.simulation import simulate_stat_pmf
                _t = time.perf_counter()
                pmf_obj = simulate_stat_pmf(
                    stat=stat, minutes_dist=m_dist, feature_row=feature_row,
                    n_draws=pmf_draws, rng=rng, rate_q_override=q,
                )
                _pmf_timer_add(f"simulate_stat_pmf.{stat}", time.perf_counter() - _t)
                if pmf_obj is None:
                    continue
                # outcome_int
                outcome_col = "turnover" if stat == "tov" else stat
                y = float(row_stats.get(outcome_col, 0) or 0)
                results[stat].append({
                    "player_id": player_id, "game_id": game_id, "game_date": game_date,
                    "outcome": int(np.clip(y, 0, len(pmf_obj.pmf) - 1)),
                    "pmf": pmf_obj.pmf.astype(np.float64),
                })

            # Sparse stats.
            need_stl = _allowed("stl") or _allowed("stocks")
            need_blk = _allowed("blk") or _allowed("stocks")
            if need_stl:
                _t = time.perf_counter()
                stl_pmf = hurdle_pmf("stl", feature_row)
                _pmf_timer_add("hurdle_pmf.stl", time.perf_counter() - _t)
            else:
                stl_pmf = None

            if need_blk:
                _t = time.perf_counter()
                blk_pmf = hurdle_pmf("blk", feature_row)
                _pmf_timer_add("hurdle_pmf.blk", time.perf_counter() - _t)
            else:
                blk_pmf = None
            if _allowed("stl") and stl_pmf is not None:
                y = float(row_stats.get("stl", 0) or 0)
                results["stl"].append({
                    "player_id": player_id, "game_id": game_id, "game_date": game_date,
                    "outcome": int(np.clip(y, 0, len(stl_pmf) - 1)),
                    "pmf": stl_pmf.astype(np.float64),
                })
            if _allowed("blk") and blk_pmf is not None:
                y = float(row_stats.get("blk", 0) or 0)
                results["blk"].append({
                    "player_id": player_id, "game_id": game_id, "game_date": game_date,
                    "outcome": int(np.clip(y, 0, len(blk_pmf) - 1)),
                    "pmf": blk_pmf.astype(np.float64),
                })
            if _allowed("stocks") and stl_pmf is not None and blk_pmf is not None:
                _t = time.perf_counter()
                sp = stocks_pmf(stl_pmf, blk_pmf)
                _pmf_timer_add("stocks_pmf", time.perf_counter() - _t)
                if sp is not None:
                    y = float((row_stats.get("stl", 0) or 0) + (row_stats.get("blk", 0) or 0))
                    results["stocks"].append({
                        "player_id": player_id, "game_id": game_id, "game_date": game_date,
                        "outcome": int(np.clip(y, 0, len(sp) - 1)),
                        "pmf": sp.astype(np.float64),
                    })

            # FG3M.
            if _allowed("fg3m") and fg3m_model is not None:
                try:
                    _t = time.perf_counter()
                    p = fg3m_model.pmf(feature_row)
                    _pmf_timer_add("fg3m_model_pmf", time.perf_counter() - _t)
                    y = float(row_stats.get("fg3m", 0) or 0)
                    results["fg3m"].append({
                        "player_id": player_id, "game_id": game_id, "game_date": game_date,
                        "outcome": int(np.clip(y, 0, len(p) - 1)),
                        "pmf": p.astype(np.float64),
                    })
                except Exception as e:
                    logger.debug(f"  fg3m pmf failed for ({player_id},{game_id}): {e}")
        finally:
            _pmf_timer_add("row_total", time.perf_counter() - _row_t0)
            # Per-25-row throughput ping — narrow-grained visibility for
            # the first minutes of a fold before the 500-row PARTIAL
            # SNAPSHOT fires.
            processed = _PMF_GEN_COUNTS.get("row_total", 0)
            if processed > 0 and processed % 25 == 0:
                elapsed = time.perf_counter() - _t_total_start
                rate = processed / elapsed if elapsed > 0 else 0
                logger.info(
                    f"  PMF gen progress: {processed} rows in {elapsed:.1f}s "
                    f"({rate:.2f} rows/sec, {1000.0*elapsed/processed:.1f} ms/row)"
                )
            # Periodic partial snapshot — protects against mid-run
            # timeouts by flushing hotspot timings to the log before the
            # fold finishes. Keyed on the actual row-processed count,
            # not on per-stat result list lengths (which skew under
            # _allowed() gating).
            processed_rows = _PMF_GEN_COUNTS.get("row_total", 0)
            if processed_rows > 0 and processed_rows % 500 == 0:
                _PMF_GEN_TIMES["_generate_fold_pmfs_total"] = (
                    time.perf_counter() - _t_total_start
                )
                logger.info("PMF GEN TIMING PARTIAL SNAPSHOT")
                _log_pmf_gen_summary(
                    val_row_count=processed_rows, fold_index=fold_index,
                )

    _PMF_GEN_TIMES["_generate_fold_pmfs_total"] = time.perf_counter() - _t_total_start
    _log_pmf_gen_summary(val_row_count=len(val_rows), fold_index=fold_index)
    return results


# ── OOF aggregator + calibration ────────────────────────────────────────────


def _pad_pmf(pmf: np.ndarray, target_len: int) -> np.ndarray:
    if len(pmf) == target_len:
        return pmf
    if len(pmf) > target_len:
        out = pmf[:target_len].copy()
        out[-1] += float(pmf[target_len:].sum())
        return out / max(out.sum(), 1e-9)
    out = np.zeros(target_len)
    out[:len(pmf)] = pmf
    return out


def stack_per_stat(
    per_fold_results: list[dict[str, list[dict]]],
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Concatenate per-fold results into (pmfs, outcomes, dates) arrays."""
    stacked: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    all_stats = set()
    for fold_res in per_fold_results:
        all_stats.update(fold_res.keys())
    for stat in sorted(all_stats):
        rows: list[dict] = []
        for fold_res in per_fold_results:
            rows.extend(fold_res.get(stat, []))
        if not rows:
            continue
        target_len = DOMAIN_MAX_BY_STAT[stat] + 1
        pmfs = np.stack([_pad_pmf(r["pmf"], target_len) for r in rows], axis=0)
        outcomes = np.array([r["outcome"] for r in rows], dtype=int)
        dates = np.array([r["game_date"] for r in rows])
        stacked[stat] = (pmfs, outcomes, dates)
    return stacked


# ── main orchestration ─────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fold-days", type=int, default=FOLD_DAYS,
        help=f"Days per validation fold (default {FOLD_DAYS}).",
    )
    parser.add_argument(
        "--max-folds", type=int, default=999,
        help="Upper bound on number of folds to run. Default: no limit.",
    )
    parser.add_argument(
        "--temp-root", default=None,
        help="Root of the per-fold temp directories. Default: system temp.",
    )
    parser.add_argument(
        "--core-props-only", action="store_true",
        help=(
            "Restrict calibration to core props (PTS, REB, AST, FG3M, TOV). "
            "Skips STL, BLK, STOCKS. CI runtime optimization."
        ),
    )
    parser.add_argument(
        "--val-rows-limit", type=int, default=None,
        help=(
            "Profiling-only: cap the number of validation rows scored per "
            "fold to this integer (deterministic .head(N), no sampling). "
            "Used to measure PMF-gen throughput without running a full "
            "fold. Downstream metrics under this flag are diagnostic only."
        ),
    )
    parser.add_argument(
        "--pmf-draws", type=int, default=3000,
        help=(
            "Monte Carlo sample count for simulate_stat_pmf during Phase 8 "
            "OOF generation. Default 3000. Lower values reduce runtime "
            "but increase calibration noise, especially for bench/rotation "
            "PMFs where each missing draw has high relative weight. "
            "Production prediction (predict.py) is unaffected — it pins "
            "n_draws=4000 at its own call site."
        ),
    )
    # Single-fold / aggregate modes — used to parallelize Phase 8 across a
    # GitHub Actions matrix. A single job runs --fold-index N with
    # --emit-fold-oof + --skip-final-fit to emit that fold's OOF parquet
    # only; an --aggregate-mode job stacks every fold_*.parquet in
    # --aggregate-oofs and fits the final per-stat PMF calibrators.
    parser.add_argument(
        "--fold-index", type=int, default=None,
        help="1-based fold index to run (single-fold mode). Incompatible "
             "with --aggregate-mode.",
    )
    parser.add_argument(
        "--emit-fold-oof", default=None,
        help="Path to write the fold's OOF PMF parquet. Required when "
             "--fold-index is set.",
    )
    parser.add_argument(
        "--skip-final-fit", action="store_true",
        help="Skip final pmf_cal_*.pkl + pmf_calibration_run.md writeout. "
             "Used in single-fold mode so only the aggregate job fits "
             "the final calibrators.",
    )
    parser.add_argument(
        "--aggregate-mode", action="store_true",
        help="Read fold OOF parquets from --aggregate-oofs, stack them, "
             "and fit the final PMF calibrators. Skips all per-fold "
             "refit work.",
    )
    parser.add_argument(
        "--aggregate-oofs", default=None,
        help="Directory of fold_*.parquet files to stack in aggregate mode.",
    )
    args = parser.parse_args()
    if args.fold_index is not None and args.emit_fold_oof is None:
        parser.error("--fold-index requires --emit-fold-oof")
    if args.aggregate_mode and not args.aggregate_oofs:
        parser.error("--aggregate-mode requires --aggregate-oofs")
    if args.aggregate_mode and args.fold_index is not None:
        parser.error("--aggregate-mode is incompatible with --fold-index")
    logger.info(
        "CLI args: fold_index=%s max_folds=%s core_props_only=%s val_rows_limit=%s aggregate_mode=%s",
        args.fold_index, args.max_folds, args.core_props_only,
        args.val_rows_limit, args.aggregate_mode,
    )
    logger.info("CLI args: pmf_draws=%d", args.pmf_draws)
    core_only_allowed = {"pts", "reb", "ast", "fg3m", "tov"} if args.core_props_only else None

    start = time.time()
    logger.info("=" * 60)
    logger.info("PMF calibration — walk-forward OOF refits")
    logger.info("=" * 60)

    if args.val_rows_limit is not None:
        logger.warning(
            "PROFILE MODE: val_rows_limit active (%d); downstream metrics "
            "are diagnostic only and must not be used for ship/quality claims.",
            args.val_rows_limit,
        )

    # ── Aggregate mode: read fold OOFs and fit final calibrators ────────
    if args.aggregate_mode:
        agg_dir = Path(args.aggregate_oofs)
        oof_paths = sorted(agg_dir.glob("fold_*.parquet"))
        if not oof_paths:
            logger.error(f"No fold_*.parquet in {agg_dir}")
            sys.exit(1)
        frames = [pd.read_parquet(p) for p in oof_paths]
        oof_df_agg = pd.concat(frames, ignore_index=True)
        logger.info(
            f"Aggregate mode: loaded {len(oof_paths)} fold files "
            f"({len(oof_df_agg):,} rows total)"
        )
        # Reconstruct per_fold_results + fold_bounds from the stacked
        # OOF frame so _fit_final_calibrators_and_emit_report consumes
        # the same shape as the full-run path.
        agg_per_fold_results: list[dict[str, list[dict]]] = []
        agg_fold_bounds: list[tuple[pd.Timestamp, pd.Timestamp]] = []
        fold_group_keys = sorted(
            oof_df_agg[["fold_start", "fold_end"]].drop_duplicates().itertuples(index=False, name=None),
            key=lambda fp: fp[0],
        )
        for fs_str, fe_str in fold_group_keys:
            fstart = pd.Timestamp(fs_str) if fs_str else pd.NaT
            fend = pd.Timestamp(fe_str) if fe_str else pd.NaT
            agg_fold_bounds.append((fstart, fend))
            sub = oof_df_agg[
                (oof_df_agg["fold_start"] == fs_str) &
                (oof_df_agg["fold_end"] == fe_str)
            ]
            fold_res: dict[str, list[dict]] = {}
            for stat_name, sub_stat in sub.groupby("stat"):
                fold_res[str(stat_name)] = [
                    {
                        "player_id": int(r.player_id),
                        "game_id": int(r.game_id),
                        "game_date": str(r.game_date),
                        "outcome": int(r.outcome),
                        "pmf": np.asarray(r.pmf),
                    }
                    for r in sub_stat.itertuples(index=False)
                ]
            agg_per_fold_results.append(fold_res)
        agg_backup = MODEL_DIR.parent / "archive" / (
            "aggregate_only_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        )
        _fit_final_calibrators_and_emit_report(
            per_fold_results=agg_per_fold_results,
            fold_bounds=agg_fold_bounds,
            folds=agg_fold_bounds,
            full_data_backup=agg_backup,
            start=start,
            fold_days=args.fold_days,
        )
        return

    stats_df = pd.read_parquet(DATA_DIR / "player_game_stats.parquet")
    stats_df["game_date"] = stats_df["game_date"].astype(str).str[:10]
    availability_df = pd.read_parquet(DATA_DIR / "player_availability_asof.parquet")
    availability_df["game_date"] = availability_df["game_date"].astype(str).str[:10]
    training_df = pd.read_parquet(DATA_DIR / "training_table.parquet")
    training_df["game_date"] = training_df["game_date"].astype(str).str[:10]
    logger.info(
        f"Loaded: stats={len(stats_df):,}  avail={len(availability_df):,}  "
        f"training={len(training_df):,}"
    )

    all_dates = pd.to_datetime(stats_df["game_date"])
    folds = make_walk_forward_folds(
        all_dates, fold_days=args.fold_days, min_train_days=MIN_TRAIN_DAYS,
    )
    if args.max_folds < len(folds):
        folds = folds[-args.max_folds:]
    logger.info(f"Built {len(folds)} walk-forward folds")
    for i, (fs, fe) in enumerate(folds, 1):
        logger.info(f"  fold {i:>2}: {fs.date()} -> {fe.date()}")

    # ── Single-fold mode: run just the requested fold ──────────────────
    if args.fold_index is not None:
        if not (1 <= args.fold_index <= len(folds)):
            logger.error(
                f"--fold-index {args.fold_index} out of range [1, {len(folds)}]"
            )
            sys.exit(1)
        selected = folds[args.fold_index - 1]
        folds = [selected]
        logger.info(
            f"Single-fold mode: running fold {args.fold_index} "
            f"({selected[0].date()} -> {selected[1].date()})"
        )

    # Back up existing production artifacts before any dir-swap churn.
    full_data_backup = MODEL_DIR.parent / "archive" / (
        "pre_calibrate_pmf_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    )
    full_data_backup.mkdir(parents=True, exist_ok=True)
    for f in MODEL_DIR.iterdir():
        if f.is_file():
            shutil.copy2(f, full_data_backup / f.name)
    logger.info(f"Production artifacts backed up to {full_data_backup}")

    temp_root = Path(args.temp_root) if args.temp_root else Path(tempfile.mkdtemp(prefix="pmf_cal_"))
    logger.info(f"Per-fold artifact temp root: {temp_root}")

    per_fold_results: list[dict[str, list[dict]]] = []
    fold_bounds: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for i, (fs, fe) in enumerate(folds, 1):
        fold_start = fs
        fold_end = fe
        fold_dir = temp_root / f"fold_{i:02d}_{fold_start.date()}"
        fold_bounds.append((fold_start, fold_end))
        logger.info(f"---- fold {i}/{len(folds)} [{fold_start.date()} -> {fold_end.date()}]")

        originals = _swap_model_dir(fold_dir)
        try:
            # Refit all relevant models on train-only data.
            _refit_models_for_fold(
                fold_start=fold_start, stats_df=stats_df,
                availability_df=availability_df, training_df=training_df,
                fold_artifact_dir=fold_dir,
                allowed_stats=core_only_allowed,
            )

            # Generate OOF PMFs on validation rows.
            val_rows = training_df[
                (training_df["stat"] == "pts") &
                (pd.to_datetime(training_df["game_date"]) >= fold_start) &
                (pd.to_datetime(training_df["game_date"]) < fold_end)
            ]
            if args.val_rows_limit is not None and len(val_rows) > args.val_rows_limit:
                val_rows = val_rows.head(args.val_rows_limit).reset_index(drop=True)
                logger.info(
                    f"--val-rows-limit={args.val_rows_limit} applied; "
                    f"val_rows reduced to {len(val_rows):,}"
                )
            logger.info(f"  val rows: {len(val_rows):,}")
            if len(val_rows) < MIN_VAL_ROWS_PER_STAT:
                logger.warning(f"  fold {i} val rows too few — skipping PMF gen")
                per_fold_results.append({})
                continue
            fold_out = _generate_fold_pmfs(
                val_rows=val_rows, stats_df=stats_df,
                availability_df=availability_df, fold_artifact_dir=fold_dir,
                allowed_stats=core_only_allowed,
                fold_index=i,
                pmf_draws=args.pmf_draws,
            )
            counts = {s: len(v) for s, v in fold_out.items() if v}
            logger.info(f"  fold PMF counts: {counts}")
            per_fold_results.append(fold_out)
        finally:
            _restore_model_dir(originals)

    # ── Single-fold mode: emit fold OOF parquet and exit ────────────────
    # Each fold's OOF rows are materialized into the same schema the
    # aggregate path reads, then written to --emit-fold-oof. The final
    # calibrator fit is deferred to a later --aggregate-mode invocation.
    if args.fold_index is not None:
        fold_oof_rows: list[dict] = []
        for fold_idx, fold_res in enumerate(per_fold_results):
            fstart, fend = (fold_bounds[fold_idx] if fold_idx < len(fold_bounds)
                            else (pd.NaT, pd.NaT))
            for stat, rows in fold_res.items():
                for r in rows:
                    fold_oof_rows.append({
                        "stat": stat,
                        "player_id": r["player_id"],
                        "game_id": r["game_id"],
                        "game_date": r["game_date"],
                        "outcome": r["outcome"],
                        "pmf": r["pmf"],
                        "fold_start": str(fstart.date()) if pd.notna(fstart) else "",
                        "fold_end": str(fend.date()) if pd.notna(fend) else "",
                    })
        fold_oof_df = pd.DataFrame(fold_oof_rows)
        fold_out_path = Path(args.emit_fold_oof)
        fold_out_path.parent.mkdir(parents=True, exist_ok=True)
        _t_pq = time.perf_counter()
        fold_oof_df.to_parquet(fold_out_path, index=False)
        _pmf_timer_add("parquet_write", time.perf_counter() - _t_pq)
        logger.info(
            f"Fold {args.fold_index} OOF written to {fold_out_path} "
            f"({len(fold_oof_df):,} rows) in {_PMF_GEN_TIMES['parquet_write']:.2f}s"
        )
        if args.skip_final_fit:
            logger.info("--skip-final-fit: exiting without final calibrator fit")
            return

    _fit_final_calibrators_and_emit_report(
        per_fold_results=per_fold_results,
        fold_bounds=fold_bounds,
        folds=folds,
        full_data_backup=full_data_backup,
        start=start,
        fold_days=args.fold_days,
    )


def _fit_final_calibrators_and_emit_report(
    per_fold_results: list[dict[str, list[dict]]],
    fold_bounds: list[tuple[pd.Timestamp, pd.Timestamp]],
    folds: list[tuple[pd.Timestamp, pd.Timestamp]],
    full_data_backup: Path,
    start: float,
    fold_days: int,
) -> None:
    # Persist the full OOF universe before any further processing so
    # scripts/run_diagnostics.py has a deterministic input to read.
    oof_rows: list[dict] = []
    for fold_idx, fold_res in enumerate(per_fold_results):
        fstart, fend = (fold_bounds[fold_idx] if fold_idx < len(fold_bounds)
                        else (pd.NaT, pd.NaT))
        for stat, rows in fold_res.items():
            for r in rows:
                oof_rows.append({
                    "stat": stat,
                    "player_id": r["player_id"],
                    "game_id": r["game_id"],
                    "game_date": r["game_date"],
                    "outcome": r["outcome"],
                    "pmf": r["pmf"],
                    "fold_start": str(fstart.date()) if pd.notna(fstart) else "",
                    "fold_end": str(fend.date()) if pd.notna(fend) else "",
                })
    oof_df = pd.DataFrame(oof_rows)
    oof_path = DATA_DIR / "oof_pmfs.parquet"
    oof_df.to_parquet(oof_path, index=False)
    logger.info(f"OOF PMF universe persisted to {oof_path} ({len(oof_df):,} rows)")

    # Aggregate across folds and fit per-stat calibrators.
    stacked = stack_per_stat(per_fold_results)
    logger.info("OOF aggregation:")
    for stat, (pmfs, outcomes, dates) in stacked.items():
        logger.info(f"  {stat}: n={len(pmfs):,}  domain={pmfs.shape[1]}")

    # Fit calibrators. We run fit_all per-stat and capture its meta log.
    if not stacked:
        logger.error("No OOF data collected; aborting before calibrator fit.")
        sys.exit(1)

    per_stat_inputs = {
        stat: (pmfs.astype(np.float64), outcomes.astype(int),
               np.array([pd.Timestamp(str(d)) for d in dates]))
        for stat, (pmfs, outcomes, dates) in stacked.items()
        if len(pmfs) >= MIN_VAL_ROWS_PER_STAT
    }
    rng = np.random.default_rng(0)
    meta = fit_all(per_stat_inputs, fold_days=fold_days,
                   min_train_days=MIN_TRAIN_DAYS, rng=rng)

    logger.info("=" * 60)
    logger.info("Per-stat calibration results")
    logger.info("=" * 60)
    report_rows: list[dict] = []
    for stat, stat_meta in meta.get("stats", {}).items():
        fitted = stat_meta.get("fitted", False)
        if fitted:
            logger.info(
                f"  {stat:>6s}  n_train={stat_meta.get('n_train',0):>6,}  "
                f"PIT raw mean={stat_meta.get('pit_mean_raw',float('nan')):.3f}  "
                f"std={stat_meta.get('pit_std_raw',float('nan')):.3f}  -> "
                f"cal mean={stat_meta.get('pit_mean_cal',float('nan')):.3f}  "
                f"std={stat_meta.get('pit_std_cal',float('nan')):.3f}"
            )
        else:
            logger.info(f"  {stat:>6s}  NOT FITTED ({stat_meta.get('reason','unknown')})")
        report_rows.append({"stat": stat, **stat_meta})

    # Dropped stats (insufficient data).
    insufficient = [
        stat for stat, (pmfs, _, _) in stacked.items()
        if len(pmfs) < MIN_VAL_ROWS_PER_STAT
    ]
    for stat in insufficient:
        logger.warning(
            f"  {stat:>6s}  SKIPPED — only {len(stacked[stat][0])} OOF rows "
            f"(< {MIN_VAL_ROWS_PER_STAT})"
        )

    # Persist a top-level run report.
    run_report = REPO_ROOT / "artifacts" / "docs" / "pmf_calibration_run.md"
    run_report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PMF calibration run",
        "",
        f"**Run at:** {datetime.utcnow().isoformat()}Z",
        f"**Folds:** {len(folds)} walk-forward, {fold_days}-day validation, "
        f"{MIN_TRAIN_DAYS}-day minimum training window.",
        f"**Production artifact backup:** `{full_data_backup}`",
        "",
        "## Per-stat result",
        "",
        "| Stat | N OOF rows | Calibrator fitted | PIT raw mean/std | PIT cal mean/std |",
        "|---|---:|---|---|---|",
    ]
    for stat in sorted(stacked.keys()):
        (pmfs, _, _) = stacked[stat]
        stat_meta = meta.get("stats", {}).get(stat, {"fitted": False, "reason": "insufficient"})
        if stat_meta.get("fitted"):
            lines.append(
                f"| {stat} | {len(pmfs):,} | yes | "
                f"{stat_meta.get('pit_mean_raw',float('nan')):.3f} / {stat_meta.get('pit_std_raw',float('nan')):.3f} | "
                f"{stat_meta.get('pit_mean_cal',float('nan')):.3f} / {stat_meta.get('pit_std_cal',float('nan')):.3f} |"
            )
        else:
            lines.append(
                f"| {stat} | {len(pmfs):,} | no ({stat_meta.get('reason','unknown')}) | - | - |"
            )
    lines.append("")
    lines.append("## Known caveat")
    lines.append("")
    lines.append(
        "training_df's baked-in mp_* feature columns were computed with the "
        "full-data minutes model. When per-fold models are refit on data "
        "sliced by date from that training_df, those baked-in columns carry "
        "a small indirect leakage. The validation outcomes themselves are "
        "never seen by the fold's models, so the primary OOF guarantee "
        "holds; the effective calibration is slightly optimistic. "
        "A strict-regen walk-forward would require rebuilding training_df "
        "per fold (~20 min each); this run does not pay that cost."
    )
    run_report.write_text("\n".join(lines))
    logger.info(f"Wrote {run_report}")

    elapsed = time.time() - start
    logger.info(f"Done in {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()
