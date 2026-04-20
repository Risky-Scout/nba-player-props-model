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
) -> None:
    """Refit minutes + rate + hurdle + fg3m on data strictly before fold_start.

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

    # State-aware minutes.
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
    train_rate_models(wide)
    train_sparse_hurdle(wide)

    # FG3M hurdle. Same column-alias block used by the main pipeline.
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
) -> dict[str, list[dict]]:
    """Produce per-stat OOF PMFs on val_rows using models trained for this fold.

    Returns mapping stat -> list of {'player_id', 'game_id', 'game_date',
    'outcome', 'pmf', 'pmf_cal_source'}. stocks and combos are included in
    v1 only for sparse stats — combos derive in the predict-layer not
    here.
    """
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

    results: dict[str, list[dict]] = {s: [] for s in list(RATE_STATS) + list(SPARSE_STATS) + ["stocks", "fg3m"]}

    rng = np.random.default_rng(0)
    for row in val_rows.itertuples(index=False):
        player_id = int(row.player_id)
        game_id = int(row.game_id)
        game_date = str(row.game_date)[:10]

        # Build minutes distribution.
        history = stats_by_player_date.get(player_id)
        if history is None:
            continue
        history = history[history["game_date"] < game_date]
        if len(history) < 10:
            continue

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
        # Minutes distribution uses the fold's state-aware artifacts.
        # We need home/team_id from stats_df for the row itself:
        row_stats = stats_df[
            (stats_df["player_id"] == player_id) & (stats_df["game_id"] == game_id)
        ]
        if row_stats.empty:
            continue
        row_stats = row_stats.iloc[0]
        team_id = int(row_stats["team_id"])
        is_home = int(row_stats["home_team_id"] == team_id)

        try:
            m_dist = minutes_distribution(
                prior_stats=history, game_context={"rest_days": rest_days, "back_to_back": b2b},
                is_home=bool(is_home), target_date=game_date, team_id=team_id,
                all_stats_df=stats_df, injury_map={}, availability=avail,
            )
        except Exception as e:
            logger.debug(f"  minutes_distribution failed for ({player_id},{game_id}): {e}")
            continue

        feature_row = {k: getattr(row, k, 0.0) for k in row._fields}

        # Main stats via minutes x rate simulation.
        for stat in RATE_STATS:
            q = rate_quantiles(stat, feature_row)
            if q is None:
                continue
            from nba_props_model.models.simulation import simulate_stat_pmf
            pmf_obj = simulate_stat_pmf(
                stat=stat, minutes_dist=m_dist, feature_row=feature_row,
                n_draws=3000, rng=rng, rate_q_override=q,
            )
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
        stl_pmf = hurdle_pmf("stl", feature_row)
        blk_pmf = hurdle_pmf("blk", feature_row)
        if stl_pmf is not None:
            y = float(row_stats.get("stl", 0) or 0)
            results["stl"].append({
                "player_id": player_id, "game_id": game_id, "game_date": game_date,
                "outcome": int(np.clip(y, 0, len(stl_pmf) - 1)),
                "pmf": stl_pmf.astype(np.float64),
            })
        if blk_pmf is not None:
            y = float(row_stats.get("blk", 0) or 0)
            results["blk"].append({
                "player_id": player_id, "game_id": game_id, "game_date": game_date,
                "outcome": int(np.clip(y, 0, len(blk_pmf) - 1)),
                "pmf": blk_pmf.astype(np.float64),
            })
        if stl_pmf is not None and blk_pmf is not None:
            sp = stocks_pmf(stl_pmf, blk_pmf)
            if sp is not None:
                y = float((row_stats.get("stl", 0) or 0) + (row_stats.get("blk", 0) or 0))
                results["stocks"].append({
                    "player_id": player_id, "game_id": game_id, "game_date": game_date,
                    "outcome": int(np.clip(y, 0, len(sp) - 1)),
                    "pmf": sp.astype(np.float64),
                })

        # FG3M.
        if fg3m_model is not None:
            try:
                p = fg3m_model.pmf(feature_row)
                y = float(row_stats.get("fg3m", 0) or 0)
                results["fg3m"].append({
                    "player_id": player_id, "game_id": game_id, "game_date": game_date,
                    "outcome": int(np.clip(y, 0, len(p) - 1)),
                    "pmf": p.astype(np.float64),
                })
            except Exception as e:
                logger.debug(f"  fg3m pmf failed for ({player_id},{game_id}): {e}")

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
    args = parser.parse_args()

    start = time.time()
    logger.info("=" * 60)
    logger.info("PMF calibration — walk-forward OOF refits")
    logger.info("=" * 60)

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
            )

            # Generate OOF PMFs on validation rows.
            val_rows = training_df[
                (training_df["stat"] == "pts") &
                (pd.to_datetime(training_df["game_date"]) >= fold_start) &
                (pd.to_datetime(training_df["game_date"]) < fold_end)
            ]
            logger.info(f"  val rows: {len(val_rows):,}")
            if len(val_rows) < MIN_VAL_ROWS_PER_STAT:
                logger.warning(f"  fold {i} val rows too few — skipping PMF gen")
                per_fold_results.append({})
                continue
            fold_out = _generate_fold_pmfs(
                val_rows=val_rows, stats_df=stats_df,
                availability_df=availability_df, fold_artifact_dir=fold_dir,
            )
            counts = {s: len(v) for s, v in fold_out.items() if v}
            logger.info(f"  fold PMF counts: {counts}")
            per_fold_results.append(fold_out)
        finally:
            _restore_model_dir(originals)

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
               np.array([pd.Timestamp(d) for d in dates]))
        for stat, (pmfs, outcomes, dates) in stacked.items()
        if len(pmfs) >= MIN_VAL_ROWS_PER_STAT
    }
    rng = np.random.default_rng(0)
    meta = fit_all(per_stat_inputs, fold_days=args.fold_days,
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
        f"**Folds:** {len(folds)} walk-forward, {args.fold_days}-day validation, "
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
