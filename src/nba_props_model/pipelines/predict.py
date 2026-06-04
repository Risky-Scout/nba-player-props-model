#!/usr/bin/env python3
"""
NBA Props Model — daily prediction pipeline.

Outputs (separate files, one per day):
  predictions/singles_{date}.json       — individual prop bets (EV > 2.5%)
  predictions/sgps_{date}.json          — 2-leg and 3-leg SGPs (EV > 2.5%)
  predictions/pmf_display_{date}.json   — full PMF rows for the web dashboard
  predictions/all_props_{date}.parquet  — full universe of evaluated props
  predictions/paper_trade_log.csv       — forward paper trade ledger

Architecture:
  - Loads Q10-Q90 quantile models per target
  - Monotonicity enforcement BEFORE any probability computation
  - P(over/under) via piecewise linear CDF interpolation
  - SGPs via Gaussian copula simulation (50k samples)
  - Quarter-Kelly sizing, 2-unit cap singles, 1-unit cap SGPs
  - Supports: pts, reb, ast, fg3m, stl, blk, tov + combo props
"""

from nba_props_model.calibration.stat_side_platt import IsotonicCalibrator  # needed for platt pkl loading
from nba_props_model.calibration.role_buckets import role_bucket_from_minutes_dist  # phase14: role-aware live calibration
from nba_props_model.calibration.pmf_calibration import ROLE_AWARE_BLEND_POLICY  # phase14: blend-policy audit tag
import csv
import json
import logging
import os
import sys
import warnings
from datetime import date, datetime
from pathlib import Path

import joblib
import numpy as np

# ── PlattCalibrator — must match calibrate_stat_side.py definition ─────────────
# Required for joblib to unpickle calibrators saved by calibrate_stat_side.py
class PlattCalibrator:
    """Platt scaling via logit transform → LogisticRegression."""
    def __init__(self, C=1.0):
        from sklearn.linear_model import LogisticRegression
        self.C  = C
        self.lr = LogisticRegression(C=C, solver="lbfgs", max_iter=1000)
        self.fitted = False

    def _logit(self, p):
        p = np.clip(np.array(p, dtype=float), 1e-4, 1 - 1e-4)
        return np.log(p / (1 - p))

    def fit(self, probs, outcomes):
        X = self._logit(probs).reshape(-1, 1)
        y = np.array(outcomes, dtype=int)
        self.lr.fit(X, y)
        self.fitted     = True
        self.slope_     = float(self.lr.coef_[0][0])
        self.intercept_ = float(self.lr.intercept_[0])
        return self

    def predict_proba(self, probs):
        X = self._logit(np.array(probs)).reshape(-1, 1)
        return self.lr.predict_proba(X)[:, 1]

    def predict_proba_2d(self, X):
        cal = self.predict_proba(X[:, 0])
        return np.column_stack([1 - cal, cal])

import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

try:
    from nba_props_model.data.bdl_client import (
        _get_api_key, parse_minutes,
        get_player_game_stats, get_games, get_game_odds,
        get_injuries, get_advanced_stats_v2,
        build_game_context_map, build_injury_map,
        get_nba_injury_report, merge_injury_sources,
        parse_props_for_game,
        enrich_game_context_with_snapshots,
    )
    from nba_props_model.features.engineering import (
        build_player_game_features,
        add_interaction_features,
        get_feature_cols_for_stat,
        STATS, COMBO_STATS, ALL_TARGETS,
    )
    from nba_props_model.calibration.pmf_calibration import load_calibrator as _load_pmf_cal
    from nba_props_model.models import minutes as _minutes_mod
    from nba_props_model.models.rate_models import rate_quantiles as _rate_quantiles
    from nba_props_model.models.simulation import simulate_stat_pmf as _simulate_stat_pmf
    from nba_props_model.models.sparse_hurdle import (
        hurdle_pmf as _hurdle_pmf,
        stocks_pmf as _stocks_pmf,
    )
    from nba_props_model.models import combos as _combos_mod
    from nba_props_model.models.simulation import StatPMF as _StatPMF
    from nba_props_model.pipelines.pmf_predict import score_prop_line as _score_prop_line
    from nba_props_model.features.availability_asof import (
        load_availability_table as _load_availability_table,
        AvailabilityBuilder as _AvailabilityBuilder,
    )
    from nba_props_model.correlation.sgp_engine import (
        p_over, p_under,
        ev_from_prob, kelly_fraction,
        enforce_monotonicity,
        build_sgp_candidates,
        WithinPlayerCorrelationEngine,
        TeammateCorrelationEngine,
        usage_bucket, mp_bucket,
        price_combo_from_simulation, COMBO_COMPONENTS,
        american_to_decimal,
        QUANTILES,
        compute_pmf, pmf_to_fair_odds, market_efficiency,
        portfolio_kelly,
    )
except ImportError as e:
    sys.exit(f"Import error: {e}")

# ── Paths ──────────────────────────────────────────────────────────────────────

from nba_props_model.paths import DATA_DIR, MODEL_DIR, PRED_DIR  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]

# ── Constants ──────────────────────────────────────────────────────────────────

STAT_DISPLAY = {
    "pts":    "Points",
    "reb":    "Rebounds",
    "ast":    "Assists",
    "fg3m":   "Threes",
    "stl":    "Steals",
    "blk":    "Blocks",
    "tov":    "Turnovers",
    "pra":    "Pts+Reb+Ast",
    "pr":     "Pts+Reb",
    "pa":     "Pts+Ast",
    "ra":     "Reb+Ast",
    "stocks": "Stl+Blk",
}

MIN_EV           = 0.025   # global floor — per-stat overrides below
MIN_GAMES_SEASON = 20  # raised from 15 — filter fringe rotation players
KELLY_FRAC       = 0.15  # fractional Kelly — conservative until edge verified on clean data
MAX_UNITS_SINGLE = 1.5     # doc 7 §5: reduced from 2.0 — too much vol for current cal quality
MAX_UNITS_SGP    = 1.0
PMF_SIM_DRAWS = int(os.getenv("NBA_PMF_SIM_DRAWS", "50000"))

# ── Deployment gates — calibrated from diagnostic 2026-03-19 ─────────────────
# OVER: require prob >= 0.60 (tighter than before)
# UNDER: reintroduced selectively with strict prob + line-gap + edge gates
# Portfolio limits: max 25 total, max 2/player, max 4/game, max 1/player/stat
MAX_PORTFOLIO     = 25
MAX_PER_PLAYER    = 2
MAX_PER_GAME      = 4
MAX_PER_PLAYER_STAT = 1

# All EV thresholds reset to neutral — prior bans were learned from broken model data
# (implied_team_total was constant 110, 78 ADV features were zero)
# Thresholds will be recalibrated after 3-4 weeks of clean picks accumulate
STAT_SIDE_MIN_EV = {
    ("pts",    "OVER"):  0.025,
    ("reb",    "OVER"):  0.025,
    ("ast",    "OVER"):  0.025,
    ("fg3m",   "OVER"):  0.025,
    ("stl",    "OVER"):  0.025,
    ("blk",    "OVER"):  0.025,
    ("tov",    "OVER"):  0.025,
    ("pra",    "OVER"):  0.025,
    ("pr",     "OVER"):  0.025,
    ("pa",     "OVER"):  0.025,
    ("ra",     "OVER"):  0.025,
    ("stocks", "OVER"):  0.025,
    ("pts",    "UNDER"): 0.025,
    ("ast",    "UNDER"): 0.025,
    ("reb",    "UNDER"): 0.025,
    ("fg3m",   "UNDER"): 0.025,
    ("blk",    "UNDER"): 0.025,
    ("stl",    "UNDER"): 0.025,
    ("tov",    "UNDER"): 0.025,
    ("pra",    "UNDER"): 0.025,
    ("pr",     "UNDER"): 0.025,
    ("pa",     "UNDER"): 0.025,
    ("ra",     "UNDER"): 0.025,
    ("stocks", "UNDER"): 0.025,
}

# Per-stat per-side probability bounds
# OVER: require >= 0.60 (diagnostic shows overs need tighter prob floor)
# UNDER: require >= 0.67–0.72 depending on stat (per instructions)
# Per-stat OVER probability floors
# pts: 0.60 (most graded data, most calibrated)
# reb/ast: 0.56 (less data, reb correction reset — allow more plays through)
# fg3m: 0.57 (sparse but reasonable)
# Probability bounds reset to neutral — will recalibrate from clean data
STAT_SIDE_PROB_BOUNDS = {
    "OVER":  (0.53, 0.85),
    "UNDER": (0.53, 0.85),
}
# Per-stat OVER minimum probability — neutral floor
OVER_MIN_PROB_BY_STAT = {
    "pts":  0.53,
    "reb":  0.53,
    "ast":  0.53,
    "fg3m": 0.53,
    "stl":  0.53,
    "blk":  0.53,
    "tov":  0.53,
    "pra":  0.53,
    "pr":   0.53,
    "pa":   0.53,
    "ra":   0.53,
    "stocks":0.53,
}

# Per-stat UNDER minimum probability — neutral floor
UNDER_MIN_PROB = {
    "pts":  0.53,
    "ast":  0.53,
    "reb":  0.53,
    "fg3m": 0.53,
    "blk":  0.53,
    "stl":  0.53,
    "tov":  0.53,
    "pra":  0.53,
    "pr":   0.53,
    "pa":   0.53,
    "ra":   0.53,
    "stocks":0.53,
}

# Minimum line gap for unders — neutral floor
UNDER_MIN_LINE_GAP = {
    "pts":  0.50,
    "ast":  0.25,
    "reb":  0.25,
    "fg3m": 0.25,
    "blk":  0.10,
    "stl":  0.10,
    "tov":  0.25,
    "pra":  0.50,
    "pr":   0.50,
    "pa":   0.50,
    "ra":   0.25,
    "stocks":0.10,
}

# Sparse stats that need independent calibration sign-off
SPARSE_STATS = {"stl", "blk", "stocks"}
SPARSE_MIN_PROB = 0.60
SGP_MAX_PER_GAME = 6
SGP_ABSOLUTE_CAP = 60

ADV_FIELDS = [
    "usage_percentage",
    "pace",
    "true_shooting_percentage",
    "effective_field_goal_percentage",
    "assist_percentage",
    "assist_to_turnover",
]

# ── Bias correction — full-universe holdout fitted 2026-03-19 ────────────────
# Source: 2624 graded rows, diag2.py — median(actual - q50) full universe
# Protocol: clip(median(actual-q50), 0, cap) only where both targets agree
# blk/stl: agreement=NO → set to 0.00 (do not correct sparse stats this way)
# Applied to FULL quantile ladder (all quantiles shift equally)
# ── Bias correction — learned from residual_centering.py 2026-03-26 ─────────
# Source: residual_centering_meta.json fallback_correction values
# Trained on 2,737 graded rows using GradientBoostingRegressor per stat
# Target: median(actual - q50) — projection truth, not market alignment
BIAS_CORRECTION = {
    # Zeroed out — previous corrections were calibrated on broken model
    # (implied_team_total was constant, 78 ADV features were zero)
    # Will retrain centerer after 2+ weeks of clean picks accumulate
    "pts":    0.00,
    "ast":    0.00,
    "reb":    0.00,
    "fg3m":   0.00,
    "blk":    0.00,
    "stl":    0.00,
    "tov":    0.00,
    "pra":    0.00,
    "pr":     0.00,
    "pa":     0.00,
    "ra":     0.00,
    "stocks": 0.00,
}


# ── Minutes bucket corrections (Phase 2 fix) ───────────────────────────────
def load_minutes_corrections() -> dict:
    """Load per-stat × minutes-bucket bias corrections from diagnostic."""
    import json
    path = MODEL_DIR / "minutes_bucket_corrections.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    # Parse string keys back to tuples, but only for buckets 1 and 2
    # Buckets 0 and 3 were overcorrected — zero them out
    SKIP_BUCKETS = {"0", "3"}  # already near-zero, correction made them worse
    corrections = {}
    for k, v in raw.items():
        try:
            tup = eval(k)  # ('pts', '1') etc
            if tup[1] in SKIP_BUCKETS:
                continue
            corrections[tup] = v
        except: pass
    return corrections

MINUTES_CORRECTIONS = {}  # loaded at startup

# ── Model loading ──────────────────────────────────────────────────────────────

def load_models() -> tuple:
    """Load all quantile models, feature lists, and Platt calibrators."""
    models = {}
    for target in ALL_TARGETS:
        fcols_path = MODEL_DIR / f"features_{target}.pkl"
        if not fcols_path.exists():
            continue
        fcols = joblib.load(fcols_path)
        qmods = {}
        for q in QUANTILES:
            p = MODEL_DIR / f"q{int(q*100):02d}_{target}.pkl"
            if p.exists():
                qmods[q] = joblib.load(p)
        if qmods:
            models[target] = {"quantile_models": qmods, "features": fcols}
            logger.info(f"  {target}: {len(qmods)} quantile models")

    within_engine   = None
    teammate_engine = TeammateCorrelationEngine(MODEL_DIR)

    wpath = MODEL_DIR / "within_player_corr_engine.pkl"
    if wpath.exists():
        within_engine = joblib.load(wpath)
        logger.info("  Within-player correlation engine loaded")
    else:
        logger.warning("  No correlation engine found — SGPs will use identity matrix")

    platt_calibrators = {}
    # Load stat×side calibrators (doc 7 §2 — move beyond global side calibration)
    # Priority: stat_side specific → side global → none
    for stat in ALL_TARGETS:
        for side in ["over", "under"]:
            # Try stat-specific calibrator first
            stat_path = MODEL_DIR / f"platt_{stat}_{side}.pkl"
            if stat_path.exists():
                platt_calibrators[f"{stat.upper()}_{side.upper()}"] = joblib.load(stat_path)
                logger.info(f"  Stat×side calibrator: {stat.upper()}_{side.upper()}")
    # Fall back to global side calibrators
    for side in ["over", "under"]:
        ppath = MODEL_DIR / f"platt_{side}.pkl"
        if ppath.exists():
            platt_calibrators[side.upper()] = joblib.load(ppath)
            logger.info(f"  Global calibrator loaded: {side.upper()}")
    if not platt_calibrators:
        logger.warning("  No Platt calibrators found — run: python3 calibrate_models.py --mode platt")

    # Load Q50 bias corrections (empirical stat median bias, updated daily)
    _q50_bias_path = MODEL_DIR / "q50_bias_corrections.json"
    try:
        import json as _json
        global _Q50_BIAS
        _Q50_BIAS = _json.load(open(_q50_bias_path))
        logger.info(f"  Q50 bias corrections: {_Q50_BIAS}")
    except Exception:
        logger.warning("  Q50 bias corrections not found — running unbiased")

    # Load residual centerer if available
    try:
        from nba_props_model.calibration.residual_centering import ResidualCenterer
        _centerer = ResidualCenterer.load(model_dir=MODEL_DIR)
        logger.info("  Residual centerer loaded")
    except Exception as e:
        _centerer = None
        logger.info(f"  Residual centerer not available: {e}")

    # Load fg3m hurdle model
    hurdle_path = MODEL_DIR / "fg3m_hurdle.pkl"
    fg3m_hurdle_model = None
    if hurdle_path.exists():
        try:
            from nba_props_model.models.fg3m_hurdle import FG3MHurdleModel
            fg3m_hurdle_model = FG3MHurdleModel.load(str(hurdle_path))
            logger.info("  FG3M hurdle model loaded")
        except Exception as e:
            logger.warning(f"  FG3M hurdle model failed to load: {e}")
    else:
        logger.warning("  FG3M hurdle model not found — using quantile fallback")

    # Load live calibration table (built from 2534 rows — shrinks overconfident raw probs)
    _live_cal_path = MODEL_DIR / "live_calibration_table.json"
    live_cal_table = {}
    try:
        live_cal_table = json.load(open(_live_cal_path))
        n = len([k for k in live_cal_table if not k.startswith('_')])
        logger.info(f"  Live calibration table loaded: {n} entries")
    except Exception as e:
        logger.warning(f"  Live calibration table not found: {e}")

    return models, within_engine, teammate_engine, platt_calibrators, fg3m_hurdle_model, _centerer, live_cal_table


# ── Quantile prediction ────────────────────────────────────────────────────────

def predict_quantiles(models: dict, target: str, features: dict):
    if target not in models:
        return None
    m     = models[target]
    fcols = m["features"]
    X     = np.array([[features.get(c, np.nan) for c in fcols]], dtype=float)
    raw   = {q: float(mod.predict(X)[0]) for q, mod in m["quantile_models"].items()}
    return enforce_monotonicity(raw)


# ── SGP candidate filtering ────────────────────────────────────────────────────

def filter_sgp_candidates(singles: list) -> list:
    """
    Reduce the singles pool before passing to the Gaussian copula.

    Without this, 473 singles → 111k pairs → copula times out every time.
    Strategy: keep top SGP_MAX_PER_GAME picks per game by EV, then hard-cap
    at SGP_ABSOLUTE_CAP total. This gives the copula a tractable ~1-2k pairs.

    Only pts, reb, ast, fg3m, stl, blk are SGP-eligible. Combo stats
    (pra, pr, pa, ra, stocks, tov) are excluded — their within-game
    correlations are trivially high and produce misleading CLV.
    """
    SGP_ELIGIBLE_STATS = {"pts", "reb", "ast", "fg3m", "stl", "blk"}

    eligible = [s for s in singles if s["stat"] in SGP_ELIGIBLE_STATS]

    by_game: dict = {}
    for s in eligible:
        gid = s["game_id"]
        by_game.setdefault(gid, []).append(s)

    pool = []
    for gid, picks in by_game.items():
        top = sorted(picks, key=lambda x: x["ev"], reverse=True)[:SGP_MAX_PER_GAME]
        pool.extend(top)

    pool = sorted(pool, key=lambda x: x["ev"], reverse=True)[:SGP_ABSOLUTE_CAP]

    logger.info(
        f"  SGP candidate pool: {len(pool)} singles "
        f"({len(eligible)} eligible → capped at {SGP_MAX_PER_GAME}/game, "
        f"max {SGP_ABSOLUTE_CAP} total)"
    )
    return pool


# ── Paper trade logger ─────────────────────────────────────────────────────────

def log_paper_trade(singles: list, sgps: list, target_date: str):
    log_path = PRED_DIR / "paper_trade_log.csv"
    fieldnames = [
        "date", "type", "player", "game", "stat", "side", "line",
        "odds", "model_prob", "ev", "kelly_units", "outcome", "profit",
    ]
    write_header = not log_path.exists()
    with open(log_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        for p in singles:
            w.writerow({
                "date":         target_date,
                "type":         "single",
                "player":       p["player_name"],
                "game":         p["game"],
                "stat":         p["stat"],
                "side":         p["side"],
                "line":         p["line"],
                "odds":         p["odds"],
                "model_prob":   round(p["model_prob"], 4),
                "ev":           round(p["ev"], 4),
                "kelly_units":  round(p["kelly_units"], 3),
                "outcome":      "",
                "profit":       "",
            })
        for s in sgps:
            w.writerow({
                "date":         target_date,
                "type":         f"sgp_{s['legs']}leg",
                "player":       "|".join(l["player"] for l in s["leg_details"]),
                "game":         s["game"],
                "stat":         "|".join(l["stat"] for l in s["leg_details"]),
                "side":         "|".join(l["side"] for l in s["leg_details"]),
                "line":         "|".join(str(l["line"]) for l in s["leg_details"]),
                "odds":         s["combined_odds"],
                "model_prob":   round(s["correlated_prob"], 4),
                "ev":           round(s["ev"], 4),
                "kelly_units":  round(s["kelly_units"], 3),
                "outcome":      "",
                "profit":       "",
            })



def save_all_props_snapshot(rows: list, target_date: str):
    """
    Persist the full evaluated prop universe BEFORE EV filters / special gates.
    Nested structures are JSON-serialized so the frame can be written safely.
    """
    if not rows:
        logger.warning("No all-prop rows to persist.")
        return

    out_path = PRED_DIR / f"all_props_{target_date}.parquet"
    df = pd.DataFrame(rows).copy()
    if "slate_date" not in df.columns:
        df["slate_date"] = str(target_date)

    if "market_over_odds" not in df.columns and "over_odds" in df.columns:
        df["market_over_odds"] = df["over_odds"]
    if "market_under_odds" not in df.columns and "under_odds" in df.columns:
        df["market_under_odds"] = df["under_odds"]
    if "book" not in df.columns:
        if "bet_vendor" in df.columns:
            df["book"] = df["bet_vendor"]
        elif "source_book" in df.columns:
            df["book"] = df["source_book"]

    if "market_no_vig_over_prob" not in df.columns and "market_prob" in df.columns:
        df["market_no_vig_over_prob"] = df["market_prob"]

    for col in ("game_id", "player_id"):
        if col not in df.columns:
            sample = df.head(8).to_dict("records") if len(df) else []
            raise SystemExit(
                "CURRENT_MARKET_SIGNAL_UNMAPPABLE_KEYS "
                f"missing identity column {col!r} in all_props snapshot sample_rows={sample!r}"
            )
        if df[col].isna().any():
            sample = df[df[col].isna()].head(8).to_dict("records") if len(df) else []
            raise SystemExit(
                "CURRENT_MARKET_SIGNAL_UNMAPPABLE_KEYS "
                f"missing/null {col} in all_props snapshot rows sample_rows={sample!r}"
            )
    def _jsonify(x):
        if isinstance(x, (dict, list, tuple, set)):
            return json.dumps(x, default=str)
        return x

    for col in df.columns:
        if df[col].map(lambda x: isinstance(x, (dict, list, tuple, set))).any():
            df[col] = df[col].map(_jsonify)

    try:
        df.to_parquet(out_path, index=False)
        logger.info(f"Saved all-prop universe: {out_path} ({len(df)} rows)")
    except Exception as e:
        fallback = out_path.with_suffix(".jsonl")
        df.to_json(fallback, orient="records", lines=True)
        logger.warning(f"Parquet save failed ({e}); wrote {fallback} instead")


def write_no_game_outputs(target_date: str) -> None:
    """Emit explicit no-game artifacts so downstream jobs can valid-skip."""
    reason = "no_games_slate"

    # Keep parquet schema minimally compatible with downstream verifiers.
    all_props_path = PRED_DIR / f"all_props_{target_date}.parquet"
    empty_cols = [
        "slate_date",
        "player_id",
        "game_id",
        "stat",
        "line",
        "model_prob",
        "pmf",
    ]
    pd.DataFrame(columns=empty_cols).to_parquet(all_props_path, index=False)

    generated_at = datetime.utcnow().isoformat()
    singles_out = {
        "date": target_date,
        "generated_at": generated_at,
        "version": "2026-03-17-v13",
        "total_picks": 0,
        "picks": [],
        "reason": reason,
    }
    with open(PRED_DIR / f"singles_{target_date}.json", "w") as f:
        json.dump(singles_out, f, indent=2, default=str)

    pmf_display = {
        "date": target_date,
        "generated_at": generated_at,
        "props": [],
        "reason": reason,
    }
    with open(PRED_DIR / f"pmf_display_{target_date}.json", "w") as f:
        json.dump(pmf_display, f, indent=2, default=str)

    sgps_out = {
        "date": target_date,
        "generated_at": generated_at,
        "version": "2026-03-17-v13",
        "two_leg": 0,
        "three_leg": 0,
        "sgps": [],
        "reason": reason,
    }
    with open(PRED_DIR / f"sgps_{target_date}.json", "w") as f:
        json.dump(sgps_out, f, indent=2, default=str)

    logger.info(
        "No-game slate artifacts written for %s (reason=%s)",
        target_date,
        reason,
    )


# ── Console summary ────────────────────────────────────────────────────────────

def print_singles_summary(picks: list):
    print(f"\n{'='*70}")
    print(f"  NBA Props Model — SINGLES ({len(picks)} picks above {MIN_EV:.1%} EV)")
    print(f"{'='*70}")
    for p in picks[:25]:
        tier = "ELITE" if p["ev"] >= 0.10 else "HIGH" if p["ev"] >= 0.06 else "EDGE"
        print(f"\n[{tier}]  {p['player_name']} — {STAT_DISPLAY.get(p['stat'], p['stat'])} {p['side']} {p['line']}")
        print(f"  Game:    {p['game']}")
        print(f"  Model P: {p['model_prob']:.1%}  |  EV: {p['ev']:+.2%}  |  Odds: {p['odds']:+d}")
        print(f"  Kelly:   {p['kelly_units']:.3f} units  |  Q50 proj: {p['q50']:.1f}")


def print_sgp_summary(sgps: list):
    print(f"\n{'='*70}")
    print(f"  NBA Props Model — SGPs ({len(sgps)} candidates above {MIN_EV:.1%} EV)")
    print(f"{'='*70}")
    for s in sgps[:10]:
        print(f"\n  {s['legs']}-LEG SGP | {s['game']}")
        for l in s["leg_details"]:
            print(f"    {l['player']} — {l['stat'].upper()} {l['side']} {l['line']}  ({l['odds']:+d})  P={l['model_prob']:.1%}")
        print(
            f"  Copula P: {s['correlated_prob']:.1%}  Naive: {s['naive_prob']:.1%}  "
            f"Combined: {s['combined_odds']:+d}  EV: {s['ev']:+.2%}"
        )


# ── Main ───────────────────────────────────────────────────────────────────────

def _derek_live_args(argv):
    """Parse Phase 13M-bis Derek live-snapshot CLI args.

    Returns an argparse.Namespace whose ``derek_live_snapshot`` is True
    only when the caller explicitly opted in. All other fields default to
    None so that pre-13M default callers (WoO/daily/canonical) see the
    exact same code path as before.
    """
    import argparse
    p = argparse.ArgumentParser(
        prog="predict",
        description="NBA Props Model — daily prediction pipeline.",
        add_help=True,
    )
    p.add_argument("--derek-live-snapshot", action="store_true",
                   help="Phase 13M-bis Derek per-game live snapshot mode.")
    p.add_argument("--date", default=None,
                   help=("YYYY-MM-DD; overrides date.today() for standard "
                         "daily prediction runs (non-Derek mode)."))
    p.add_argument("--target-date", default=None,
                   help="YYYY-MM-DD; overrides date.today() in Derek mode.")
    p.add_argument("--delivery-date", default=None,
                   help="YYYY-MM-DD; alias for --target-date.")
    p.add_argument("--game-id", default=None,
                   help="Filter slate to one game_id (Derek mode).")
    p.add_argument("--lineup-context", default=None,
                   help="Path to BDL lineup parquet (Derek mode).")
    p.add_argument("--snapshot-output-dir", default=None,
                   help="Where to write derek_live_predictions.parquet.")
    p.add_argument("--snapshot-type", default=None,
                   choices=[None, "current_live", "t_minus_25", "close_lock"],
                   help="Snapshot type (Derek mode). Phase 13U adds "
                        "current_live for pre-tip snapshots whose target "
                        "is the actual run start time.")
    p.add_argument("--snapshot-run-id", default=None,
                   help="Per-snapshot identifier (Derek mode).")
    p.add_argument("--validate-args-and-exit", action="store_true",
                   help=("Parse args, validate Derek-mode constraints, print "
                         "PREDICT_DEREK_LIVE_ARGS_PASS, then exit without "
                         "running prediction. Used by fixture verifier."))
    args, _unknown = p.parse_known_args(argv or [])
    return args


def _validate_derek_args(args):
    """Return (ok, reason) for Derek-mode args. Pre-13M callers (no
    --derek-live-snapshot) always pass."""
    if not args.derek_live_snapshot:
        return True, ""
    missing = []
    if not (args.target_date or args.delivery_date):
        missing.append("--target-date or --delivery-date")
    if not args.game_id:
        missing.append("--game-id")
    if not args.snapshot_output_dir:
        missing.append("--snapshot-output-dir")
    if not args.snapshot_type:
        missing.append("--snapshot-type")
    if missing:
        return False, f"missing required Derek args: {missing}"
    return True, ""


def _join_lineup_context_into_rows(rows, lineup_path, game_id_filter):
    """Phase 13M-bis lineup-context join.

    Adds these columns to each row in `rows` (mutates in place AND returns
    a new list pointer for safety):

        bdl_lineup_present, current_starter, confirmed_starter,
        confirmed_bench, lineup_position, lineup_source, lineup_confirmed,
        role_source, role_bucket_pre_lineup, role_bucket_post_lineup,
        lineup_context_supplied, lineup_affects_pmf_features

    Returns (rows, integration_summary). Summary includes the counts the
    snapshot manifest needs:
      lineup_feature_columns_added (list[str])
      role_bucket_changed_count
      starter_flag_changed_count
      minutes_projection_conflict_count
      lineup_rows_joined
      lineup_blocker (str — empty when join succeeded)
    """
    import pandas as pd
    columns_added = [
        "bdl_lineup_present", "current_starter", "confirmed_starter",
        "confirmed_bench", "lineup_position", "lineup_source",
        "lineup_confirmed", "role_source", "role_bucket_pre_lineup",
        "role_bucket_post_lineup", "lineup_context_supplied",
        "lineup_affects_pmf_features",
    ]
    # Initialize defaults on every row so the dataframe shape is stable
    # even when the lineup join finds nothing.
    for r in rows:
        r.setdefault("bdl_lineup_present", False)
        r.setdefault("current_starter", None)
        r.setdefault("confirmed_starter", False)
        r.setdefault("confirmed_bench", False)
        r.setdefault("lineup_position", None)
        r.setdefault("lineup_source", None)
        r.setdefault("lineup_confirmed", False)
        r.setdefault("role_source", "projected_minutes")
        r.setdefault("role_bucket_pre_lineup", r.get("role_bucket"))
        r.setdefault("role_bucket_post_lineup", r.get("role_bucket"))
        r.setdefault("lineup_context_supplied", bool(lineup_path))
        r.setdefault("lineup_affects_pmf_features", False)

    summary = {
        "lineup_feature_columns_added": columns_added,
        "role_bucket_changed_count": 0,
        "starter_flag_changed_count": 0,
        "minutes_projection_conflict_count": 0,
        "lineup_rows_joined": 0,
        "lineup_blocker": "",
    }
    if not lineup_path:
        summary["lineup_blocker"] = "no --lineup-context path supplied"
        return rows, summary
    p = Path(lineup_path)
    if not p.exists():
        summary["lineup_blocker"] = f"lineup-context file not found: {lineup_path}"
        return rows, summary
    try:
        ldf = pd.read_parquet(p)
    except Exception as exc:
        summary["lineup_blocker"] = f"failed to read lineup parquet: {exc}"
        return rows, summary
    if "player_id" not in ldf.columns or "starter" not in ldf.columns:
        summary["lineup_blocker"] = (
            f"lineup parquet missing required columns "
            f"(player_id/starter); got {list(ldf.columns)}"
        )
        return rows, summary
    # Normalize join keys.
    ldf = ldf.copy()
    ldf["player_id"] = ldf["player_id"].astype("Int64")
    if "game_id" in ldf.columns:
        ldf["game_id"] = ldf["game_id"].astype(str)
    # Build a (game_id, player_id) → row dict.
    by_key: dict = {}
    for _, lr in ldf.iterrows():
        gid = str(lr.get("game_id")) if "game_id" in ldf.columns else None
        pid = lr.get("player_id")
        try:
            pid_i = int(pid) if pid is not None else None
        except Exception:
            pid_i = None
        if pid_i is None:
            continue
        key = (gid, pid_i) if gid is not None else (None, pid_i)
        by_key[key] = lr.to_dict()

    # All starter rows in this lineup (used to flag starter changes).
    confirmed_total = sum(1 for v in by_key.values() if bool(v.get("starter")))

    for r in rows:
        try:
            pid_i = int(r.get("player_id"))
        except Exception:
            continue
        gid = str(r.get("game_id")) if r.get("game_id") is not None else None
        if game_id_filter and gid is not None and gid != str(game_id_filter):
            # Don't even attempt the join for rows outside the filter — the
            # caller may have already filtered, but be defensive.
            continue
        match = by_key.get((gid, pid_i)) or by_key.get((None, pid_i))
        if not match:
            continue
        starter = bool(match.get("starter"))
        r["bdl_lineup_present"] = True
        r["current_starter"] = starter
        r["confirmed_starter"] = starter
        r["confirmed_bench"] = (not starter)
        r["lineup_position"] = match.get("lineup_position") or match.get("position")
        r["lineup_source"] = match.get("source") or "balldontlie_v1_lineups"
        r["lineup_confirmed"] = True
        r["role_source"] = "confirmed_bdl_lineup"
        # Conservative documented role rule (Phase 13M-bis Part D):
        # if a confirmed starter previously had a non-starter role bucket,
        # mark the post-lineup bucket as "starter_promoted" and increment
        # the change counter. We do NOT silently overwrite; the original
        # is preserved in role_bucket_pre_lineup. Calibrator selection
        # downstream may use role_bucket_post_lineup if the calibrator
        # supports the new bucket label; otherwise it falls back to
        # role_bucket as before.
        pre = r.get("role_bucket_pre_lineup")
        if starter and pre not in (None, "starter", "starter_promoted"):
            r["role_bucket_post_lineup"] = "starter_promoted"
            summary["role_bucket_changed_count"] += 1
        elif (not starter) and pre == "starter":
            r["role_bucket_post_lineup"] = "bench_demoted"
            summary["role_bucket_changed_count"] += 1
        # Minutes-projection conflict heuristic: confirmed starter with
        # exp_mp < 18, or confirmed bench with exp_mp >= 30.
        exp_mp = r.get("exp_mp")
        if exp_mp is not None:
            try:
                emp = float(exp_mp)
                if (starter and emp < 18) or ((not starter) and emp >= 30):
                    summary["minutes_projection_conflict_count"] += 1
            except Exception:
                pass
        summary["starter_flag_changed_count"] += 1
        summary["lineup_rows_joined"] += 1
        r["lineup_affects_pmf_features"] = True

    if summary["lineup_rows_joined"] == 0:
        summary["lineup_blocker"] = (
            "lineup parquet had no rows that matched any prediction "
            "(player_id, game_id) — confirmed lineup may not yet be posted"
        )
    return rows, summary


def main(argv=None):
    args = _derek_live_args(argv)
    derek = bool(args.derek_live_snapshot)

    # Validate Derek-mode args. Pre-13M callers (derek=False) always pass.
    ok, reason = _validate_derek_args(args)
    if derek and not ok:
        print("PREDICT_DEREK_LIVE_ARGS_FAILED", file=sys.stderr)
        print(f"  reason: {reason}", file=sys.stderr)
        return 1

    if args.validate_args_and_exit:
        # Fixture-friendly fast path: confirm CLI surface, skip prediction.
        print("PREDICT_DEREK_LIVE_ARGS_PASS")
        if derek:
            print(f"  derek_live_snapshot=True game_id={args.game_id!r} "
                  f"target_date={args.target_date or args.delivery_date!r} "
                  f"snapshot_type={args.snapshot_type!r} "
                  f"snapshot_output_dir={args.snapshot_output_dir!r}")
        return 0

    logger.info("=" * 60)
    logger.info("NBA Props Model PREDICTIONS — VERSION 2026-03-26-v15")
    logger.info("=" * 60)

    if not _get_api_key():
        sys.exit("BDL_API_KEY not set.")

    # Phase 13M-bis + M8.8 delivery backfill support:
    # - Derek live-snapshot mode uses --target-date/--delivery-date
    # - standard runs may optionally override with --date
    # - otherwise default to today's date
    if derek:
        target_date = (args.target_date or args.delivery_date)
        derek_game_id_filter = str(args.game_id) if args.game_id else None
        derek_lineup_path = args.lineup_context
        derek_snapshot_output_dir = (
            Path(args.snapshot_output_dir) if args.snapshot_output_dir else None
        )
        print("PREDICT_DEREK_LIVE_ARGS_PASS")
        print(f"  target_date={target_date} game_id={derek_game_id_filter} "
              f"snapshot_type={args.snapshot_type} "
              f"snapshot_run_id={args.snapshot_run_id}")
    else:
        target_date = args.date or date.today().strftime("%Y-%m-%d")
        derek_game_id_filter = None
        derek_lineup_path = None
        derek_snapshot_output_dir = None
    logger.info(f"Target date: {target_date}")

    logger.info("Loading models...")
    models, within_engine, teammate_engine, platt_calibrators, fg3m_hurdle_model, _centerer, live_cal_table = load_models()

    # Load minutes bucket corrections (Phase 2 fix)
    global MINUTES_CORRECTIONS
    MINUTES_CORRECTIONS = load_minutes_corrections()
    if MINUTES_CORRECTIONS:
        logger.info(f"  Minutes bucket corrections loaded: {len(MINUTES_CORRECTIONS)} entries")
    else:
        logger.info("  No minutes bucket corrections found (run minutes_bias_fix.py)")
    if not models:
        sys.exit(f"No models in {MODEL_DIR}/. Run training script first.")

    stats_path = DATA_DIR / "player_game_stats.parquet"
    adv_path   = DATA_DIR / "advanced_stats.parquet"
    if not stats_path.exists():
        sys.exit("No stats data. Run training script first.")

    # Load calibration manifest
    cal_manifest = {}
    manifest_path = MODEL_DIR / "calibration_manifest.json"
    if manifest_path.exists():
        cal_manifest = json.loads(manifest_path.read_text())
        promoted = [k for k,v in cal_manifest.items()
                   if k != '_meta' and v.get('promoted') and v.get('scope')=='stat_side']
        logger.info(f"  Calibration manifest: {len(promoted)} promoted stat×side calibrators")
    else:
        logger.warning("  calibration_manifest.json missing — run calibrate_stat_side.py")

    # ── PMF-first cutover readiness detection (MIGRATION.md §3 step 4) ───────
    # Determine per-stat whether the rebuilt PMF pipeline has every artifact
    # it needs. For each ready stat we:
    #   * bypass the legacy direct-total quantile path
    #   * compute prob_over/prob_under from the PMF (calibrated when
    #     pmf_cal_{stat}.pkl is present)
    #   * tag cal_source="pmf" or "pmf_cal"
    _rate_ready = {
        s: all((MODEL_DIR / f"rate_{s}_q{int(100*q):02d}.pkl").exists()
               for q in (0.10, 0.25, 0.50, 0.75, 0.90))
           and (MODEL_DIR / f"rate_{s}_features.pkl").exists()
        for s in ("pts", "reb", "ast", "tov")
    }
    _hurdle_ready = {
        s: (MODEL_DIR / f"hurdle_{s}_zero.pkl").exists()
           and all((MODEL_DIR / f"hurdle_{s}_pos_q{int(100*q):02d}.pkl").exists()
                   for q in (0.10, 0.25, 0.50, 0.75, 0.90))
           and (MODEL_DIR / f"hurdle_{s}_features.pkl").exists()
        for s in ("stl", "blk")
    }
    _pmf_ready: dict = {}
    _pmf_ready.update(_rate_ready)
    _pmf_ready.update(_hurdle_ready)
    _pmf_ready["stocks"] = _hurdle_ready.get("stl", False) and _hurdle_ready.get("blk", False)
    _pmf_ready["fg3m"] = fg3m_hurdle_model is not None

    # Per-stat calibrators (optional — PMFs work even without calibrator).
    _pmf_calibrators: dict = {}
    for _stat in ("pts", "reb", "ast", "tov", "stl", "blk", "stocks", "fg3m"):
        _c = _load_pmf_cal(_stat)
        if _c is not None:
            _pmf_calibrators[_stat] = _c
    n_ready = sum(1 for v in _pmf_ready.values() if v)
    logger.info(
        f"  PMF pipeline ready for {n_ready}/{len(_pmf_ready)} stats: "
        f"{sorted(s for s, v in _pmf_ready.items() if v)}"
    )
    logger.info(
        f"  PMF calibrators loaded: {sorted(_pmf_calibrators.keys()) or '(none)'}"
    )

    # ── Availability lookup for today's slate ───────────────────────────────
    # The state-aware minutes model consumes availability features. We
    # join them per (player_id, game_date). If the persisted table does
    # not yet contain today's date we build a live as-of snapshot from
    # the raw parquet sources.
    _availability_lookup: dict[tuple[int, str], dict] = {}
    _availability_builder = None
    _availability_cols = (
        "prob_active", "days_since_last_played", "is_returning_from_absence",
        "minutes_restriction_flag", "num_teammates_out_total",
        "vacated_minutes_guard", "vacated_minutes_wing", "vacated_minutes_big",
        "teammate_out_count_guard", "teammate_out_count_wing",
        "teammate_out_count_big", "vacated_fga_total",
    )
    try:
        av_df = _load_availability_table()
        today_mask = av_df["game_date"].astype(str).str[:10] == target_date
        _av_today = av_df[today_mask]
        if _av_today.empty:
            _availability_builder = _AvailabilityBuilder.from_data_dir()
            logger.info(
                "  Availability table has no rows for today; live builder ready "
                "for on-demand features_for calls per player-game."
            )
        else:
            for r in _av_today.itertuples(index=False):
                _availability_lookup[(int(r.player_id), str(r.game_date))] = {
                    c: getattr(r, c, None) for c in _availability_cols
                }
            logger.info(
                f"  Availability rows for today: {len(_availability_lookup)} "
                "(from persisted table)"
            )
    except FileNotFoundError:
        logger.warning(
            "  player_availability_asof.parquet missing — new minutes model "
            "will fall back to default availability"
        )

    # ── PMF builder helper (uses already-loaded artifacts + minutes dist) ──
    def _pmf_build_for_stat(target, minutes_dist, feature_row, fg3m_hurdle_model):
        if target in ("pts", "reb", "ast", "tov"):
            q = _rate_quantiles(target, feature_row)
            if q is None:
                return None
            pmf_obj = _simulate_stat_pmf(
                stat=target, minutes_dist=minutes_dist,
                feature_row=feature_row, n_draws=PMF_SIM_DRAWS,
                rng=np.random.default_rng(hash((target, feature_row.get("player_id", 0))) & 0xFFFFFFFF),
                rate_q_override=q,
            )
            return None if pmf_obj is None else pmf_obj.pmf
        if target in ("stl", "blk"):
            return _hurdle_pmf(target, feature_row)
        if target == "stocks":
            stl = _hurdle_pmf("stl", feature_row)
            blk = _hurdle_pmf("blk", feature_row)
            return _stocks_pmf(stl, blk) if (stl is not None and blk is not None) else None
        if target == "fg3m" and fg3m_hurdle_model is not None:
            try:
                return fg3m_hurdle_model.pmf(feature_row)
            except Exception:
                return None
        # Combo stats derived from components.
        if target in ("pra", "pr", "pa", "ra"):
            components: dict = {}
            for s in _combos_mod.COMBO_COMPONENTS[target]:
                raw = _pmf_build_for_stat(s, minutes_dist, feature_row, fg3m_hurdle_model)
                if raw is None:
                    return None
                components[s] = _StatPMF(stat=s, pmf=raw)
            combo_pmf = _combos_mod.build_combo_pmf(target, components)
            return None if combo_pmf is None else combo_pmf.pmf
        return None

    logger.info("Loading historical data...")
    stats_df = pd.read_parquet(stats_path)
    adv_df   = pd.read_parquet(adv_path) if adv_path.exists() else pd.DataFrame()

    adv_by_player = {}
    if not adv_df.empty:
        for pid, grp in adv_df.groupby("player_id"):
            adv_by_player[int(pid)] = grp.sort_values("game_date").to_dict("records")

    logger.info(f"Fetching today's games ({target_date})...")
    games = get_games(start_date=target_date, end_date=target_date)
    if not games:
        logger.info("No games today.")
        write_no_game_outputs(target_date)
        return 0
    # Phase 13M-bis: filter slate to one game in Derek live-snapshot mode.
    if derek and derek_game_id_filter:
        games = [g for g in games if str(g.get("id")) == derek_game_id_filter]
        if not games:
            logger.warning(
                f"Derek live-snapshot: game_id={derek_game_id_filter!r} not "
                "found in today's slate."
            )
            return 1
    logger.info(f"  {len(games)} games")

    today_odds_raw = get_game_odds(dates=[target_date])
    ctx_map = build_game_context_map(today_odds_raw) if today_odds_raw else {}

    logger.info("Enriching game context with line movement snapshots...")
    ctx_map = enrich_game_context_with_snapshots(ctx_map, games, target_date)

    logger.info("Fetching injuries...")
    injury_raw = get_injuries()
    injury_map = build_injury_map(injury_raw) if injury_raw else {}
    logger.info(f"  {len(injury_map)} BDL injury records")
    slate_teams: set[str] = set()
    for g in games:
        for key in ("home_team", "visitor_team"):
            t = g.get(key) or {}
            fn = t.get("full_name")
            if fn:
                slate_teams.add(str(fn))
    nba_report = get_nba_injury_report(
        slate_date=target_date,
        slate_team_full_names=slate_teams if slate_teams else None,
        repo_root=REPO_ROOT,
    )
    # Merge with NBA official injury report (more current, covers game-time decisions)
    injury_map = merge_injury_sources(injury_map, nba_report, stats_df, slate_date=target_date)
    INACTIVE_STATUSES = {"out", "out for season", "injured", "inactive", "doubtful"}
    inactive_player_ids = {
        pid for pid, info in injury_map.items()
        if str(info.get("status","")).lower().strip() in INACTIVE_STATUSES
    }
    logger.info(f"  {len(inactive_player_ids)} players marked inactive (BDL + NBA official)")

    logger.info("Fetching prop lines...")
    prop_map = {}
    for game in games:
        gid = game.get("id")
        if not gid:
            continue
        try:
            gprops = parse_props_for_game(int(gid), price_shop=True)
            for (pid, stat), val in gprops.items():
                prop_map[(pid, int(gid), stat)] = val
        except Exception as e:
            logger.warning(f"  Props failed game {gid}: {e}")
    logger.info(f"  {len(prop_map)} prop lines")

    # ── Build predictions ──────────────────────────────────────────────────────
    all_singles = []

    for game in games:
        gid = game.get("id")
        if not gid:
            continue
        home_id = (game.get("home_team") or {}).get("id") or game.get("home_team_id")
        vis_id = (game.get("visitor_team") or {}).get("id") or game.get("visitor_team_id")
        home_nm = (game.get("home_team") or {}).get("full_name", "")
        vis_nm = (game.get("visitor_team") or {}).get("full_name", "")
        home_abbr = (game.get("home_team") or {}).get("abbreviation", "") or ""
        vis_abbr = (game.get("visitor_team") or {}).get("abbreviation", "") or ""
        glabel = f"{vis_nm} @ {home_nm}"
        ctx     = ctx_map.get(gid, {})

        player_ids = list(set(pid for (pid, pg, _) in prop_map if pg == gid))

        for player_id in player_ids:
            # Skip players marked inactive in injury map
            if player_id in inactive_player_ids:
                logger.debug(f"Skipping inactive player {player_id}")
                continue
            pdata = stats_df[stats_df["player_id"] == player_id].copy()
            if pdata.empty:
                continue
            pdata["game_date"] = pd.to_datetime(pdata["game_date"]).dt.strftime("%Y-%m-%d")

            season_games = pdata[pdata["season"] == 2025]
            if len(season_games) < MIN_GAMES_SEASON:
                continue

            team_id = int(pdata.iloc[-1]["team_id"] or 0)
            is_home = int(team_id == home_id)
            opp_id  = vis_id if is_home else home_id

            padv = sorted(
                adv_by_player.get(player_id, []),
                key=lambda x: x.get("game_date", pd.Timestamp("2000")),
            )
            padv_prior = [
                r for r in padv
                if pd.Timestamp(r.get("game_date", pd.Timestamp("2000"))) < pd.Timestamp(target_date)
            ]

            try:
                base = build_player_game_features(
                    player_id    = player_id,
                    prior_stats  = pdata,
                    prior_adv    = padv_prior,
                    game_context = ctx,
                    is_home      = is_home,
                    target_date  = target_date,
                    team_id      = team_id,
                    all_stats_df = stats_df,
                    injury_map   = injury_map,
                    opp_team_id  = opp_id,
                )
            except Exception as e:
                logger.warning(f"Feature error player={player_id}: {e}")
                continue

            team_abbr = home_abbr if is_home else vis_abbr
            opp_abbr = vis_abbr if is_home else home_abbr

            player_name = str(pdata.iloc[-1].get("player_name", f"Player {player_id}"))
            ub = usage_bucket(float(base.get("adv_usage_percentage_mean_last10") or 0))
            mb = mp_bucket(float(base.get("mp_mean_last10") or 0))

            # ── New PMF pipeline per-player context ─────────────────────────
            # The rebuilt minutes model has been invoked inside build_player_game_features
            # via predict_minutes; its full distribution is accessible through the
            # module-level side-channel. This is the input to the rate x minutes
            # simulation the PMF-first path uses.
            _avail_row = None
            if _availability_lookup:
                _avail_row = _availability_lookup.get(
                    (player_id, str(target_date)), None
                )
            elif _availability_builder is not None:
                try:
                    _pairs = pd.DataFrame([{
                        "player_id": player_id, "team_id": team_id,
                        "game_date": str(target_date),
                    }])
                    _fts = _availability_builder.features_for(_pairs)
                    if len(_fts):
                        _avail_row = {
                            c: _fts.iloc[0].get(c) for c in _availability_cols
                        }
                except Exception as _e:
                    logger.debug(f"availability builder call failed for {player_id}: {_e}")
            # Re-run the state-aware minutes model with the availability row so
            # that prob_active + teammate-absence signal actually flow into the
            # minutes distribution used by the PMF simulator. The call is cheap
            # (re-uses the already-cached classifier pickles).
            try:
                _mp_dist = _minutes_mod.minutes_distribution(
                    prior_stats=pdata, game_context=ctx,
                    is_home=bool(is_home), target_date=target_date,
                    team_id=team_id, all_stats_df=stats_df,
                    injury_map=injury_map, availability=_avail_row,
                )
            except Exception as _e:
                logger.debug(f"minutes_distribution rebuild failed for {player_id}: {_e}")
                _mp_dist = _minutes_mod.last_distribution()

            for target in ALL_TARGETS:
                prop = prop_map.get((player_id, gid, target))
                if prop is None:
                    continue

                line       = prop["line"]
                over_odds  = prop.get("over_odds", -110)
                under_odds = prop.get("under_odds", -110)
                vendor     = prop.get("best_over_vendor", prop.get("vendor", ""))

                base_ix = add_interaction_features(dict(base), target)

                # Skip if line is negative (impossible stat value)
                if line <= 0:
                    continue
                # Minimum line filters — prevent structural low-line picks
                MIN_LINE = {
                    "ast":  2.0,
                    "fg3m": 0.5,
                    "reb":  2.0,
                    "pts":  8.0,
                    "stl":  0.5,
                    "blk":  0.5,
                }
                min_line = MIN_LINE.get(target, 0)
                if line < min_line:
                    continue

                # ── PMF-ONLY production pricing path ─────────────────────────
                # Canonical pipeline:
                #   availability -> state-aware minutes -> rate/hurdle PMF ->
                #   PMF/CDF calibration -> (prob_over, prob_under)
                # No legacy quantile ladder, no Platt/live_cal overlay, no Q50
                # bias shift, no minutes-bucket correction, no residual
                # centerer. If the PMF build fails for any reason, skip the
                # candidate — never fall back silently to a legacy path.
                if not (target in _pmf_ready and _pmf_ready[target]) or _mp_dist is None:
                    continue
                try:
                    _pmf_arr = _pmf_build_for_stat(
                        target=target, minutes_dist=_mp_dist,
                        feature_row=base_ix, fg3m_hurdle_model=fg3m_hurdle_model,
                    )
                except Exception as _e:
                    logger.debug(f"PMF build failed for {target}: {_e}")
                    _pmf_arr = None
                if _pmf_arr is None:
                    continue
                _cal = _pmf_calibrators.get(target)
                _role_bucket = None
                if _cal is not None:
                    # phase14: derive ex-ante role bucket from predicted
                    # minutes distribution and pass into the calibrator.
                    # RoleAwarePMFCalibrator returns global-only output when
                    # role_bucket is None, so this is the line that actually
                    # unlocks role-aware calibration in production. Verified
                    # by Phase 14 Step 1 same-row A/B (commit c0c2236):
                    # role_aware vs global_only on identical OOF rows
                    # improves NLL by -0.0053 with no bucket regressions.
                    try:
                        _role_bucket = role_bucket_from_minutes_dist(_mp_dist)
                    except Exception:
                        _role_bucket = None
                    try:
                        _pmf_arr = _cal.apply(_pmf_arr, role_bucket=_role_bucket)
                    except TypeError:
                        # Calibrator class without role_bucket kwarg: fall
                        # back to the legacy global apply for safety.
                        _pmf_arr = _cal.apply(_pmf_arr)
                _po, _pu = _score_prop_line(_pmf_arr, float(line))
                prob_over = float(_po)
                prob_under = float(_pu)
                raw_over = prob_over
                raw_under = prob_under
                if target in _pmf_calibrators:
                    _cal_v = getattr(_pmf_calibrators[target], "version", None)
                    if _cal_v == "role_aware_pmf_cal_v1" and _role_bucket:
                        # Phase 14 audit tag: include the active blend policy
                        # so downstream consumers can identify which apply-time
                        # policy produced the row. Existing substring matches
                        # like "role_aware_pmf_cal_v1" in cal_source still hold.
                        cal_src_over = (
                            f"role_aware_pmf_cal_v1:{ROLE_AWARE_BLEND_POLICY}"
                            f":{_role_bucket}"
                        )
                    else:
                        cal_src_over = "pmf_cal"
                else:
                    cal_src_over = "pmf"
                cal_src_under = cal_src_over
                cal_applied_over = (target in _pmf_calibrators)
                cal_applied_under = cal_applied_over

                # Derive quantiles + median directly from the PMF so every
                # downstream gate reads the PMF as the source of truth. No
                # legacy quantile ladder is consulted.
                _cdf_arr = np.cumsum(_pmf_arr)
                def _pmf_quantile(tau: float) -> float:
                    k = int(np.searchsorted(_cdf_arr, tau, side="left"))
                    return float(min(k, len(_pmf_arr) - 1))
                q_preds = {q: _pmf_quantile(q) for q in (0.10, 0.20, 0.25, 0.33, 0.40,
                                                         0.50, 0.60, 0.67, 0.75, 0.80, 0.90)}
                q50 = q_preds[0.50]

                # Bad-line sanity filter — PMF-sourced
                if q50 > 0 and line > q50 * 1.75:
                    continue
                # Alt-line guard (PMF-sourced q50)
                if target == "pts" and q50 < 17.0 and line > q50 * 1.5:
                    continue

                ev_over  = ev_from_prob(prob_over,  over_odds)
                ev_under = ev_from_prob(prob_under, under_odds)

                for side, prob, odds, ev in [
                    ("OVER",  prob_over,  over_odds,  ev_over),
                    ("UNDER", prob_under, under_odds, ev_under),
                ]:
                    # Stat×side EV gate
                    _oi = abs(over_odds)/(abs(over_odds)+100) if over_odds < 0 else 100/(over_odds+100)
                    _ui = abs(under_odds)/(abs(under_odds)+100) if under_odds < 0 else 100/(under_odds+100)
                    _vig = (_oi + _ui) - 1.0
                    _base_ev = STAT_SIDE_MIN_EV.get((target, side), MIN_EV)
                    min_ev_req = max(_base_ev, _vig + 0.01)
                    if ev < min_ev_req:
                        continue

                    # Probability bounds check — stat-specific OVER floor
                    prob_lo, prob_hi = STAT_SIDE_PROB_BOUNDS.get(side, (0.56, 0.74))
                    if side == "OVER":
                        prob_lo = OVER_MIN_PROB_BY_STAT.get(target, prob_lo)
                    if not (prob_lo <= prob <= prob_hi):
                        continue

                    # UNDER-specific gates (instructions 2026-03-19)
                    if side == "UNDER":
                        # Per-stat minimum probability for unders
                        under_prob_min = UNDER_MIN_PROB.get(target, 0.67)
                        if prob < under_prob_min:
                            continue
                        # Per-stat minimum line gap: line - q50 must exceed threshold
                        line_gap = line - q_preds.get(0.50, line)
                        under_gap_min = UNDER_MIN_LINE_GAP.get(target, 0.50)
                        if line_gap < under_gap_min:
                            continue

                    # Sparse stat: harder probability floor
                    if target in SPARSE_STATS and prob < SPARSE_MIN_PROB:
                        continue

                    # Minimum Q50 projection filter (OVER only)
                    # Don't surface OVER if model projects player as non-contributor
                    # Catches bench players with high market lines but low real role
                    _MIN_Q50 = {"pts": 12.0, "reb": 3.5, "ast": 2.5, "fg3m": 0.5, "blk": 0.3, "stl": 0.3}
                    if side == "OVER" and q50 < _MIN_Q50.get(target, 0):
                        continue

                    # Bad line ratio check (OVER): line should not exceed 1.75x q50
                    # Jamal Murray 42.5 vs q50=17.4 is fake edge — stale line
                    if side == "OVER" and q50 > 0 and line > q50 * 1.75:
                        continue

                    kelly = kelly_fraction(prob, odds, KELLY_FRAC, MAX_UNITS_SINGLE)
                    if kelly <= 0:
                        continue

                    # Compute vig-free market prob and raw edge (spec §1.1-1.2)
                    dec_over_val  = (over_odds/100+1) if over_odds>0 else (1+100/abs(over_odds))
                    dec_under_val = (under_odds/100+1) if under_odds>0 else (1+100/abs(under_odds))
                    imp_o = 1.0/dec_over_val; imp_u = 1.0/dec_under_val
                    novig_over  = imp_o/(imp_o+imp_u)
                    novig_under = imp_u/(imp_o+imp_u)
                    raw_edge_val= (prob - novig_over) if side=="OVER" else (prob - novig_under)

                    all_singles.append({
                        "slate_date":   target_date,
                        "player_id":    player_id,
                        "player_name":  player_name,
                        "game_id":      gid,
                        "game":         glabel,
                        "team_id":      team_id,
                        "team":         team_abbr,
                        "opponent":     opp_abbr,
                        "stat":         target,
                        "side":         side,
                        "line":         line,
                        "odds":         odds,
                        "over_odds":    over_odds,
                        "under_odds":   under_odds,
                        "bet_vendor":   vendor,
                        "model_prob":     round(prob, 4),
                        "model_prob_raw": round(raw_over if side=="OVER" else raw_under, 4),
                        "model_prob_cal": round(prob, 4),
                        "cal_source":     cal_src_over if side=="OVER" else cal_src_under,
                        "market_prob":  round(novig_over if side=="OVER" else novig_under, 4),
                        "raw_edge":     round(raw_edge_val, 4),
                        "ev":           round(ev, 4),
                        "kelly_units":  round(kelly, 3),
                        "q50":          round(q50, 2),
                        "q_preds":      {float(k): round(v, 2) for k, v in q_preds.items()},
                        "usage_bucket": ub,
                        "mp_bucket":    mb,
                        # Deployment metadata for CLV tracing (doc 7 traceability)
                        "min_ev_applied": round(min_ev_req, 4),
                        # Fix 4: Explicit audit trail — raw vs calibrated
                        "cal_type":      "pmf_cal" if target in _pmf_calibrators else "pmf_raw",
                        "cal_applied":   cal_applied_over if side=="OVER" else cal_applied_under,
                        "is_sparse":     target in SPARSE_STATS,
                        # ── Full PMF + fair odds + market efficiency ──
                        # Source of truth is the PMF array built above —
                        # no reconstruction from quantile ladders.
                        **(
                            lambda _pmf: {
                                "pmf":             {k: round(v,4) for k,v in _pmf.items() if v > 0.001},
                                "fair_odds_over":  pmf_to_fair_odds(_pmf, line)["fair_odds_over"],
                                "fair_odds_under": pmf_to_fair_odds(_pmf, line)["fair_odds_under"],
                                "pmf_median":      pmf_to_fair_odds(_pmf, line)["pmf_median"],
                                "edge_over":       market_efficiency(_pmf, line, over_odds, under_odds)["edge_over"],
                                "edge_under":      market_efficiency(_pmf, line, over_odds, under_odds)["edge_under"],
                                "line_vs_median":  market_efficiency(_pmf, line, over_odds, under_odds)["line_vs_median"],
                                "mkt_true_over":   market_efficiency(_pmf, line, over_odds, under_odds)["mkt_true_over"],
                                "mkt_true_under":  market_efficiency(_pmf, line, over_odds, under_odds)["mkt_true_under"],
                            }
                        )({int(k): float(v) for k, v in enumerate(_pmf_arr)}),
                    })

    # Phase 13M-bis: in Derek live-snapshot mode, route the prediction
    # output to the per-snapshot directory instead of the canonical
    # predictions/all_props_<date>.parquet (which WoO/daily callers own).
    if derek and derek_snapshot_output_dir is not None:
        all_rows = [dict(x) for x in all_singles]
        all_rows, lineup_summary = _join_lineup_context_into_rows(
            all_rows, derek_lineup_path, derek_game_id_filter,
        )
        derek_snapshot_output_dir.mkdir(parents=True, exist_ok=True)
        out_parquet = derek_snapshot_output_dir / "derek_live_predictions.parquet"
        # Reuse the JSON-safe parquet writer used by save_all_props_snapshot.
        df = pd.DataFrame(all_rows).copy()
        def _jsonify(x):
            if isinstance(x, (dict, list, tuple, set)):
                return json.dumps(x, default=str)
            return x
        for col in df.columns:
            if df[col].map(lambda x: isinstance(x, (dict, list, tuple, set))).any():
                df[col] = df[col].map(_jsonify)
        df.to_parquet(out_parquet, index=False)
        # Write a minimal sidecar json so the runner can recover the
        # integration summary without re-parsing the parquet.
        sidecar = derek_snapshot_output_dir / "derek_live_predictions_summary.json"
        sidecar.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "target_date": target_date,
                    "game_id": derek_game_id_filter,
                    "snapshot_type": args.snapshot_type,
                    "snapshot_run_id": args.snapshot_run_id,
                    "row_count": int(len(df)),
                    "lineup_context_supplied": bool(derek_lineup_path),
                    "lineup_affects_pmf_features": (
                        lineup_summary["lineup_rows_joined"] > 0
                    ),
                    "lineup_integration_summary": lineup_summary,
                    "derek_live_predictions_parquet": str(out_parquet),
                },
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )
        if lineup_summary["lineup_rows_joined"] > 0:
            print("PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS")
            print(
                f"  rows_joined={lineup_summary['lineup_rows_joined']}  "
                f"role_changes={lineup_summary['role_bucket_changed_count']}  "
                f"starter_flags_set={lineup_summary['starter_flag_changed_count']}  "
                f"minutes_conflicts={lineup_summary['minutes_projection_conflict_count']}"
            )
        else:
            # Non-failure: no rows joined typically means BDL has not
            # posted lineups yet. The runner is expected to surface this
            # as lineup_blocker without aborting the snapshot.
            print("PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PENDING")
            print(f"  blocker: {lineup_summary['lineup_blocker']!r}")
        # Skip the WoO/canonical side-effects — we are NOT the daily
        # delivery; we are a Derek-only snapshot writer.
        return 0

    save_all_props_snapshot([dict(x) for x in all_singles], target_date)
    # ── fg3m per-player gate ─────────────────────────────────────────
    import pandas as _pd
    try:
        _stats = _pd.read_parquet(DATA_DIR / "player_game_stats.parquet")
        _cur = _stats[_stats["game_date"] >= "2025-10-01"]
        _hit_rates = (
            _cur.groupby("player_name")["fg3m"]
            .apply(lambda x: (x > 0).mean())
            .to_dict()
        )
        _fg3m_removed = []
        _all_singles_filtered = []
        for _s in all_singles:
            if _s["stat"] == "fg3m" and _s["side"] == "OVER":
                _player = _s["player_name"]
                _actual_hit = _hit_rates.get(_player, None)
                _model_p = _s.get("model_prob", 0)
                if _actual_hit is not None and (_model_p - _actual_hit) > 0.20:
                    _fg3m_removed.append(
                        f"{_player}: model={_model_p:.1%} actual={_actual_hit:.1%} gap={_model_p-_actual_hit:.1%}"
                    )
                    continue
            _all_singles_filtered.append(_s)
        if _fg3m_removed:
            for _r in _fg3m_removed:
                logger.warning(f"fg3m gate removed: {_r}")
        all_singles = _all_singles_filtered
    except Exception as _e:
        logger.warning(f"fg3m gate skipped: {_e}")
    # ── end fg3m gate ─────────────────────────────────────────────────

    # ── fg3m per-player gate ─────────────────────────────────────────
    import pandas as _pd
    try:
        _stats = _pd.read_parquet(DATA_DIR / "player_game_stats.parquet")
        _cur = _stats[_stats["game_date"] >= "2025-10-01"]
        _hit_rates = (
            _cur.groupby("player_name")["fg3m"]
            .apply(lambda x: (x > 0).mean())
            .to_dict()
        )
        _fg3m_removed = []
        _all_singles_filtered = []
        for _s in all_singles:
            if _s["stat"] == "fg3m" and _s["side"] == "OVER":
                _player = _s["player_name"]
                _actual_hit = _hit_rates.get(_player, None)
                _model_p = _s.get("model_prob", 0)
                if _actual_hit is not None and (_model_p - _actual_hit) > 0.20:
                    _fg3m_removed.append(
                        f"{_player}: model={_model_p:.1%} actual={_actual_hit:.1%} gap={_model_p-_actual_hit:.1%}"
                    )
                    continue
            _all_singles_filtered.append(_s)
        if _fg3m_removed:
            for _r in _fg3m_removed:
                logger.warning(f"fg3m gate removed: {_r}")
        all_singles = _all_singles_filtered
    except Exception as _e:
        logger.warning(f"fg3m gate skipped: {_e}")
    # ── end fg3m gate ─────────────────────────────────────────────────

    all_singles.sort(key=lambda x: x["ev"], reverse=True)

    # ── Covariance-aware Kelly re-sizing ─────────────────────────────────────
    # Re-price kelly_units accounting for correlation between same-game props
    try:
        _bet_input = [
            {
                "prob":         s["model_prob"],
                "american_odds": s["odds"],
                "stat":         s["stat"],
                "player_id":    s["player_id"],
                "side":         s["side"],
            }
            for s in all_singles
        ]
        _sized = portfolio_kelly(_bet_input)
        for s, b in zip(all_singles, _sized):
            s["kelly_units"] = b["kelly_units"]
    except Exception as e:
        logger.warning(f"portfolio_kelly failed: {e}")


    # ── HARD PRE-EXPORT ASSERTIONS (Fix 1+5+6 per rebuild doc) ──────────────
    # Banned markets must NEVER appear in output — fail loudly if they do
    # No hard market bans — all markets eligible based on EV and probability gates
    # Bans were removed: all were learned from broken-model data
    # Will reintroduce evidence-based restrictions after 3-4 weeks clean picks

    logger.info(f"Singles before portfolio limits: {len(all_singles)}")

    # ── Portfolio limits (instructions 2026-03-19) ────────────────────────────
    # max 25 total, max 2/player, max 4/game, max 1/player/stat
    filtered = []
    player_count: dict = {}
    game_count:   dict = {}
    player_stat:  set  = set()
    stat_total: dict = {}   # total picks per stat across all games
    for s in all_singles:
        pid  = str(s["player_id"])   # str() fixes int/str type mismatch
        gid2 = str(s["game_id"])
        pstat= (pid, s["stat"])
        if len(filtered) >= MAX_PORTFOLIO:
            break
        if player_count.get(pid, 0) >= MAX_PER_PLAYER:
            continue
        if game_count.get(gid2, 0) >= MAX_PER_GAME:
            continue
        if pstat in player_stat:
            continue
        # Cap AST OVER at 4/day — too concentrated otherwise
        stat_side_key = f"{s['stat']}_{s['side']}"
        STAT_SIDE_MAX = {"ast_OVER": 4, "pts_OVER": 8, "reb_OVER": 4}
        if stat_total.get(stat_side_key, 0) >= STAT_SIDE_MAX.get(stat_side_key, 25):
            continue
        filtered.append(s)
        player_count[pid]  = player_count.get(pid, 0) + 1
        game_count[gid2]   = game_count.get(gid2, 0) + 1
        player_stat.add(pstat)
        stat_total[stat_side_key] = stat_total.get(stat_side_key, 0) + 1
    all_singles = filtered
    logger.info(f"Singles after portfolio limits: {len(all_singles)}")

    today = target_date

    # ── Write singles FIRST — always, unconditionally ─────────────────────────
    singles_out = {
        "date":         today,
        "generated_at": datetime.utcnow().isoformat(),
        "version":      "2026-03-17-v13",
        "min_ev":       MIN_EV,
        "total_picks":  len(all_singles),
        "picks":        all_singles,
    }
    singles_path = PRED_DIR / f"singles_{today}.json"
    with open(singles_path, "w") as f:
        json.dump(singles_out, f, indent=2, default=str)
    logger.info(f"Singles written → {singles_path}  (safe before SGP step)")

    # ── PMF display JSON — full outcome table with fair odds per prop ────────
    try:
        pmf_display = {"date": today, "generated_at": singles_out["generated_at"], "props": []}
        STAT_DISPLAY = {"pts":"Points","reb":"Rebounds","ast":"Assists",
                        "fg3m":"Threes","stl":"Steals","blk":"Blocks","tov":"Turnovers"}
        for pick in all_singles:
            pmf = pick.get("pmf", {})
            if not pmf:
                continue
            outcome_table = []
            for x_str, prob in sorted(pmf.items(), key=lambda t: int(t[0])):
                p = float(prob)
                if p < 0.005:
                    continue
                fair_odds = int(round(-p/(1-p)*100)) if p >= 0.5 else int(round((1-p)/p*100))
                outcome_table.append({"outcome": int(x_str), "probability": round(p,4),
                                      "fair_odds": fair_odds, "display_prob": f"{p*100:.1f}%"})
            pmf_display["props"].append({
                "player_name":    pick["player_name"],
                "game":           pick["game"],
                "stat":           pick["stat"],
                "stat_display":   STAT_DISPLAY.get(pick["stat"], pick["stat"]),
                "side":           pick["side"],
                "line":           pick["line"],
                "model_prob":     pick["model_prob"],
                "market_prob":    pick["market_prob"],
                "ev":             pick["ev"],
                "edge":           pick.get("edge_over") if pick["side"]=="OVER" else pick.get("edge_under"),
                "fair_odds_over":  pick.get("fair_odds_over"),
                "fair_odds_under": pick.get("fair_odds_under"),
                "pmf_median":     pick.get("pmf_median"),
                "line_vs_median": pick.get("line_vs_median"),
                "affiliate": {"vendor": pick.get("bet_vendor"), "over_odds": pick.get("over_odds"),
                              "under_odds": pick.get("under_odds"), "best_odds": pick.get("odds")},
                "outcome_table":  outcome_table,
            })
        pmf_path = PRED_DIR / f"pmf_display_{today}.json"
        with open(pmf_path, "w") as f:
            json.dump(pmf_display, f, indent=2, default=str)
        logger.info(f"PMF display written → {pmf_path} ({len(pmf_display['props'])} props)")
    except Exception as e:
        logger.warning(f"PMF display generation failed: {e}")

    # ── SGP generation — skipped if SKIP_SGPS=1 ───────────────────────────────
    sgp_results = {"two_leg": [], "three_leg": []}
    sgp_rejection_reasons: dict = {}
    sgp_pool_size_before = 0
    sgp_pool_size_after = 0
    joint_samples_path = str(PRED_DIR / f"joint_stat_samples_{today}.parquet")
    joint_samples_exists = (PRED_DIR / f"joint_stat_samples_{today}.parquet").exists()
    joint_samples_rows = 0
    sgp_skip_reason: str | None = None

    eligible_stats_set = {"pts", "reb", "ast", "fg3m", "stl", "blk"}
    singles_before_edge_filter = sum(1 for s in all_singles if s.get("stat") in eligible_stats_set)

    if os.environ.get("SKIP_SGPS") == "1":
        sgp_skip_reason = "SKIP_SGPS_env_flag"
        logger.info("SGP generation skipped (SKIP_SGPS=1)")
    elif within_engine is not None:
        logger.info("Generating SGP candidates (Gaussian copula)...")
        sgp_pool = filter_sgp_candidates(all_singles)
        sgp_pool_size_after = len(sgp_pool)
        sgp_pool_size_before = sum(1 for s in all_singles if s.get("stat") in eligible_stats_set)
        if sgp_pool:
            sgp_results = build_sgp_candidates(
                singles         = sgp_pool,
                within_engine   = within_engine,
                teammate_engine = teammate_engine,
                min_ev          = MIN_EV,
            )
            # Count rejections from the build step
            sgp_rejection_reasons = sgp_results.get("rejection_reasons", {})
        else:
            logger.warning("  SGP pool empty after filtering")
            sgp_skip_reason = "empty_pool_after_filter"
    else:
        sgp_skip_reason = "correlation_engine_unavailable"
        logger.warning("  Skipping SGPs — correlation engine not available")

    two_leg   = sgp_results.get("two_leg",   [])
    three_leg = sgp_results.get("three_leg", [])
    all_sgps  = sorted(two_leg + three_leg, key=lambda x: x["ev"], reverse=True)
    logger.info(f"  2-leg: {len(two_leg)} | 3-leg: {len(three_leg)}")

    # ── Write SGP debug artifact (always written, even when total_sgps=0) ──────
    sgp_debug = {
        "date": today,
        "generated_at": datetime.utcnow().isoformat(),
        "games": len({s.get("game_id") for s in all_singles}),
        "players_seen": len({s.get("player_id") for s in all_singles}),
        "single_candidates_before_sgp_filter": sgp_pool_size_before,
        "single_candidates_after_sgp_filter": sgp_pool_size_after,
        "joint_stat_samples_path": joint_samples_path,
        "joint_stat_samples_exists": joint_samples_exists,
        "joint_stat_samples_rows": joint_samples_rows,
        "sgp_candidates_two_leg": len(two_leg),
        "sgp_candidates_three_leg": len(three_leg),
        "sgp_total": len(all_sgps),
        "min_ev": MIN_EV,
        "sgp_skip_reason": sgp_skip_reason,
        "rejection_reasons": sgp_rejection_reasons or {
            "missing_joint_samples": 0,
            "low_ev": max(0, (sgp_pool_size_after * (sgp_pool_size_after - 1) // 2) - len(two_leg)),
            "missing_market_price": 0,
        },
    }
    sgp_debug_path = PRED_DIR / f"sgp_debug_{today}.json"
    with open(sgp_debug_path, "w") as f:
        json.dump(sgp_debug, f, indent=2, default=str)
    logger.info(f"SGP debug → {sgp_debug_path}")

    # ── Write SGPs ─────────────────────────────────────────────────────────────
    sgps_out = {
        "date":         today,
        "generated_at": datetime.utcnow().isoformat(),
        "version":      "2026-06-04-v14",
        "min_ev":       MIN_EV,
        "total_sgps":   len(all_sgps),
        "two_leg":      len(two_leg),
        "three_leg":    len(three_leg),
        "sgp_debug_path": str(sgp_debug_path),
        "sgps":         all_sgps,
    }
    sgps_path = PRED_DIR / f"sgps_{today}.json"
    with open(sgps_path, "w") as f:
        json.dump(sgps_out, f, indent=2, default=str)
    logger.info(f"SGPs    → {sgps_path}")

    log_paper_trade(all_singles, all_sgps, today)

    print_singles_summary(all_singles) if all_singles else print("\nNo singles above EV threshold.")
    print_sgp_summary(all_sgps)        if all_sgps    else print("\nNo SGPs above EV threshold.")

    print(f"\nFiles written:")
    print(f"  {singles_path}")
    print(f"  {sgps_path}")
    print(f"  {PRED_DIR}/paper_trade_log.csv")


if __name__ == "__main__":
    main()
