#!/usr/bin/env python3
"""
predict_darko_v4.py — NBA Props Model Prediction Engine
VERSION: 2026-03-26-v15

Outputs (SEPARATE FILES):
  predictions/singles_{date}.json   — individual prop bets (EV > 2.5%)
  predictions/sgps_{date}.json      — 2-leg and 3-leg SGPs (EV > 2.5%)
  predictions/paper_trade_log.csv   — forward paper trade ledger

Architecture:
  - Loads Q10-Q90 quantile models per target
  - Monotonicity enforcement BEFORE any probability computation
  - P(over/under) via piecewise linear CDF interpolation
  - SGPs via Gaussian copula simulation (50k samples)
  - Quarter-Kelly sizing, 2-unit cap singles, 1-unit cap SGPs
  - Supports: pts, reb, ast, fg3m, stl, blk, tov + combo props

v13 changes:
  - Bias correction rolled back to 50% magnitude (fix OVER hit rate)
  - BIAS_CORRECTION moved to module-level constant (out of inner loop)
  - Version bump and cleanup
"""

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
import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

try:
    from bdl_client import (
        _get_api_key, parse_minutes,
        get_player_game_stats, get_games, get_game_odds,
        get_injuries, get_advanced_stats_v2,
        build_game_context_map, build_injury_map,
        parse_props_for_game,
        enrich_game_context_with_snapshots,
    )
    from feature_engineering import (
        build_player_game_features,
        add_interaction_features,
        get_feature_cols_for_stat,
        STATS, COMBO_STATS, ALL_TARGETS,
    )
    from correlation_engine import (
        p_over, p_under,
        ev_from_prob, kelly_fraction,
        enforce_monotonicity,
        build_sgp_candidates,
        WithinPlayerCorrelationEngine,
        TeammateCorrelationEngine,
        usage_bucket, mp_bucket,
        american_to_decimal,
        QUANTILES,
    )
except ImportError as e:
    sys.exit(f"Import error: {e}")

# ── Paths ──────────────────────────────────────────────────────────────────────

DATA_DIR  = Path("data")
MODEL_DIR = Path("model_cache")
PRED_DIR  = Path("predictions")
PRED_DIR.mkdir(exist_ok=True)

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
KELLY_FRAC       = 0.25
MAX_UNITS_SINGLE = 1.5     # doc 7 §5: reduced from 2.0 — too much vol for current cal quality
MAX_UNITS_SGP    = 1.0

# ── Deployment gates — calibrated from diagnostic 2026-03-19 ─────────────────
# OVER: require prob >= 0.60 (tighter than before)
# UNDER: reintroduced selectively with strict prob + line-gap + edge gates
# Portfolio limits: max 25 total, max 2/player, max 4/game, max 1/player/stat
MAX_PORTFOLIO     = 25
MAX_PER_PLAYER    = 2
MAX_PER_GAME      = 4
MAX_PER_PLAYER_STAT = 1

STAT_SIDE_MIN_EV = {
    # OVER thresholds — major stats
    ("pts",  "OVER"):  0.025,
    ("reb",  "OVER"):  0.025,
    ("ast",  "OVER"):  0.025,
    ("fg3m", "OVER"):  0.030,
    # OVER thresholds — sparse (still tightly controlled)
    ("stl",  "OVER"):  0.999,   # banned per diagnostic: HR=0.216 CLV=+0.037 too noisy
    ("blk",  "OVER"):  0.999,   # banned per diagnostic: HR=0.260 not enough signal
    ("tov",  "OVER"):  0.035,
    ("pra",  "OVER"):  0.025,
    ("pr",   "OVER"):  0.025,
    ("pa",   "OVER"):  0.025,
    ("ra",   "OVER"):  0.030,
    ("stocks","OVER"): 0.999,   # banned
    # UNDER thresholds — controlled reintroduction per diagnostic
    # pts UNDER: CLV=-0.102 — require strong gates
    ("pts",  "UNDER"): 0.060,
    # ast UNDER: CLV=-0.104 — require strong gates
    ("ast",  "UNDER"): 0.050,
    # reb UNDER: CLV=-0.112 — require strong gates
    ("reb",  "UNDER"): 0.999,   # suppressed: CLV=-0.112 consistently negative
    # fg3m UNDER: CLV=-0.092 — reintroduce with strict gate
    ("fg3m", "UNDER"): 0.999,   # BANNED per rebuild doc: CLV=-0.099, hit_rt=0.531 noise
    # blk/stl UNDER: still allowed if very tight
    ("blk",  "UNDER"): 0.070,
    ("stl",  "UNDER"): 0.999,   # CLV=-0.073 stl under too noisy
    ("tov",  "UNDER"): 0.050,
    ("pra",  "UNDER"): 0.060,
    ("pr",   "UNDER"): 0.060,
    ("pa",   "UNDER"): 0.060,
    ("ra",   "UNDER"): 0.050,
    ("stocks","UNDER"):0.999,
}

# Per-stat per-side probability bounds
# OVER: require >= 0.60 (diagnostic shows overs need tighter prob floor)
# UNDER: require >= 0.67–0.72 depending on stat (per instructions)
# Per-stat OVER probability floors
# pts: 0.60 (most graded data, most calibrated)
# reb/ast: 0.56 (less data, reb correction reset — allow more plays through)
# fg3m: 0.57 (sparse but reasonable)
STAT_SIDE_PROB_BOUNDS = {
    "OVER":  (0.56, 0.74),   # global floor — per-stat override below
    "UNDER": (0.67, 0.80),
}
# Per-stat OVER minimum probability (overrides global floor)
OVER_MIN_PROB_BY_STAT = {
    "pts":  0.60,
    "reb":  0.56,
    "ast":  0.56,
    "fg3m": 0.57,
    "pra":  0.58,
    "pr":   0.57,
    "pa":   0.57,
    "ra":   0.56,
}

# Per-stat UNDER minimum probability floors (stricter per instructions)
UNDER_MIN_PROB = {
    "pts":  0.72,
    "ast":  0.70,
    "reb":  0.67,
    "fg3m": 0.66,
    "blk":  0.74,
    "stl":  0.99,   # effectively banned
}

# Per-stat UNDER minimum line-gap (line - q50 must exceed this)
# Prevents betting unders when model is only marginally below the line
UNDER_MIN_LINE_GAP = {
    "pts":  1.25,
    "ast":  0.75,
    "reb":  0.60,
    "fg3m": 0.50,
    "blk":  0.20,
    "stl":  0.99,   # effectively banned
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
    "pts":    1.135,  # learned: +1.135 (2737 rows, updated from +0.51)
    "ast":    0.190,  # learned: +0.190 (updated from +0.155)
    "reb":    0.010,  # learned: +0.010 (confirms near-zero — reset was correct)
    "fg3m":  -0.010,  # learned: -0.010 (unchanged)
    "blk":    0.00,   # no correction
    "stl":    0.00,   # no correction
    "tov":    0.00,   # insufficient data
    "pra":    1.335,  # pts+reb+ast = 1.135+0.010+0.190
    "pr":     1.145,  # pts+reb = 1.135+0.010
    "pa":     1.325,  # pts+ast = 1.135+0.190
    "ra":     0.200,  # reb+ast = 0.010+0.190
    "stocks": 0.00,   # stl+blk both 0.00
}


# ── Minutes bucket corrections (Phase 2 fix) ───────────────────────────────
def load_minutes_corrections() -> dict:
    """Load per-stat × minutes-bucket bias corrections from diagnostic."""
    import json
    path = Path("model_cache/minutes_bucket_corrections.json")
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

    return models, within_engine, teammate_engine, platt_calibrators


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

def main():
    logger.info("=" * 60)
    logger.info("NBA Props Model PREDICTIONS — VERSION 2026-03-26-v15")
    logger.info("=" * 60)

    if not _get_api_key():
        sys.exit("BDL_API_KEY not set.")

    target_date = date.today().strftime("%Y-%m-%d")
    logger.info(f"Target date: {target_date}")

    logger.info("Loading models...")
    models, within_engine, teammate_engine, platt_calibrators = load_models()

    # Load minutes bucket corrections (Phase 2 fix)
    global MINUTES_CORRECTIONS
    MINUTES_CORRECTIONS = load_minutes_corrections()
    if MINUTES_CORRECTIONS:
        logger.info(f"  Minutes bucket corrections loaded: {len(MINUTES_CORRECTIONS)} entries")
    else:
        logger.info("  No minutes bucket corrections found (run minutes_bias_fix.py)")
    if not models:
        sys.exit("No models in model_cache/. Run training script first.")

    stats_path = DATA_DIR / "player_game_stats.parquet"
    adv_path   = DATA_DIR / "advanced_stats.parquet"
    if not stats_path.exists():
        sys.exit("No stats data. Run training script first.")

    # Load calibration manifest
    cal_manifest = {}
    manifest_path = Path("model_cache/calibration_manifest.json")
    if manifest_path.exists():
        cal_manifest = json.loads(manifest_path.read_text())
        promoted = [k for k,v in cal_manifest.items()
                   if k != '_meta' and v.get('promoted') and v.get('scope')=='stat_side']
        logger.info(f"  Calibration manifest: {len(promoted)} promoted stat×side calibrators")
    else:
        logger.warning("  calibration_manifest.json missing — run calibrate_stat_side.py")

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
        logger.warning("No games today.")
        return
    logger.info(f"  {len(games)} games")

    today_odds_raw = get_game_odds(dates=[target_date])
    ctx_map = build_game_context_map(today_odds_raw) if today_odds_raw else {}

    logger.info("Enriching game context with line movement snapshots...")
    ctx_map = enrich_game_context_with_snapshots(ctx_map, games, target_date)

    logger.info("Fetching injuries...")
    injury_raw = get_injuries()
    injury_map = build_injury_map(injury_raw) if injury_raw else {}
    logger.info(f"  {len(injury_map)} injury records")

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
        gid     = game.get("id")
        home_id = (game.get("home_team") or {}).get("id")
        vis_id  = (game.get("visitor_team") or {}).get("id")
        home_nm = (game.get("home_team") or {}).get("full_name", "")
        vis_nm  = (game.get("visitor_team") or {}).get("full_name", "")
        glabel  = f"{vis_nm} @ {home_nm}"
        ctx     = ctx_map.get(gid, {})

        player_ids = list(set(pid for (pid, pg, _) in prop_map if pg == gid))

        for player_id in player_ids:
            pdata = stats_df[stats_df["player_id"] == player_id]
            if pdata.empty:
                continue

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
                )
            except Exception as e:
                logger.debug(f"Feature error player={player_id}: {e}")
                continue

            player_name = str(pdata.iloc[-1].get("player_name", f"Player {player_id}"))
            ub = usage_bucket(float(base.get("adv_usage_percentage_mean_last10") or 0))
            mb = mp_bucket(float(base.get("mp_mean_last10") or 0))

            for target in ALL_TARGETS:
                prop = prop_map.get((player_id, gid, target))
                if prop is None:
                    continue

                line       = prop["line"]
                over_odds  = prop.get("over_odds", -110)
                under_odds = prop.get("under_odds", -110)
                vendor     = prop.get("best_over_vendor", prop.get("vendor", ""))

                base_ix = add_interaction_features(dict(base), target)
                q_preds = predict_quantiles(models, target, base_ix)
                if q_preds is None:
                    continue

                # Apply bias correction — shift entire quantile distribution
                bias    = BIAS_CORRECTION.get(target, 0.0)
                q_preds = {q: v + bias for q, v in q_preds.items()}

                # Apply minutes-bucket correction (Phase 2 fix)
                # Use 50% of correction per rebuild doc:
                # "use 50-75% of the holdout correction initially, then recheck"
                # Hard cap: never shift pts more than +1.5 from minutes correction alone
                mp_b = str(mb)
                min_corr_raw = MINUTES_CORRECTIONS.get((target, mp_b), 0.0)
                # Fix 3: Use 75% for pts (still under-projected), 50% for others
                # Per rebuild doc: "use 50-75% initially, then recheck"
                # pts buckets 1+2 still show +2.71/+2.75 residual — increase to 75%
                pct = 0.75 if target == "pts" else 0.50
                min_corr = min_corr_raw * pct
                if target == "pts":
                    min_corr = float(np.clip(min_corr, -1.0, 1.5))
                elif target in ("reb","ast"):
                    min_corr = float(np.clip(min_corr, -0.5, 0.8))
                if min_corr != 0.0:
                    q_preds = {q: v + min_corr for q, v in q_preds.items()}

                q50     = q_preds.get(0.50, line)

                # Bad-line sanity filter (permanent architecture — deployment layer)
                # Skip if market line is more than 1.75x the model projection
                # Tightened from 2.5x — REB/AST unders were slipping through at 1.8x
                if q50 > 0 and line > q50 * 1.75:
                    continue
                # Alt-line guard: if line > 1.5x q50 AND q50 < 15 for pts,
                # this is almost certainly an alt/inflated line (Jalen Duren pattern)
                if target == "pts" and q50 < 17.0 and line > q50 * 1.5:
                    continue
                # Skip if line is negative (impossible stat value)
                if line <= 0:
                    continue
                # Minimum line filters — prevent structural low-line picks
                MIN_LINE = {
                    "ast":  2.0,
                    "fg3m": 0.5,
                    "reb":  2.0,
                    "pts":  8.0,   # raised: avoid bench padding
                    "stl":  0.5,
                    "blk":  0.5,
                }
                min_line = MIN_LINE.get(target, 0)
                if line < min_line:
                    continue



                prob_over  = p_over(q_preds, line)
                prob_under = p_under(q_preds, line)

                # Apply Platt calibration — stat×side specific if available (doc 7 §2)
                # Priority: stat_SIDE → global SIDE → raw
                def _apply_cal(prob, stat_key, side_key):
                    """Apply calibrator. Returns (cal_prob, cal_source)."""
                    stat_side_key = f"{stat_key.upper()}_{side_key.upper()}"
                    if stat_side_key in platt_calibrators:
                        cal = platt_calibrators[stat_side_key]
                        try:
                            cal_prob = float(np.clip(
                                cal.predict_proba([[prob]])[0][1], 0.01, 0.99))
                            return cal_prob, 'stat_side'
                        except Exception:
                            pass
                    if side_key.upper() in platt_calibrators:
                        cal = platt_calibrators[side_key.upper()]
                        try:
                            cal_prob = float(np.clip(
                                cal.predict_proba([[prob]])[0][1], 0.01, 0.99))
                            return cal_prob, 'global_side'
                        except Exception:
                            pass
                    return prob, 'raw_none'

                raw_over   = prob_over
                raw_under  = prob_under
                prob_over,  cal_src_over  = _apply_cal(prob_over,  target, "OVER")
                prob_under, cal_src_under = _apply_cal(prob_under, target, "UNDER")
                cal_applied_over  = (cal_src_over  != 'raw_none')
                cal_applied_under = (cal_src_under != 'raw_none')

                ev_over  = ev_from_prob(prob_over,  over_odds)
                ev_under = ev_from_prob(prob_under, under_odds)

                for side, prob, odds, ev in [
                    ("OVER",  prob_over,  over_odds,  ev_over),
                    ("UNDER", prob_under, under_odds, ev_under),
                ]:
                    # Stat×side EV gate
                    min_ev_req = STAT_SIDE_MIN_EV.get((target, side), MIN_EV)
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
                    _MIN_Q50 = {"pts": 12.0, "reb": 3.5, "ast": 2.5, "fg3m": 0.5}
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
                        "player_id":    player_id,
                        "player_name":  player_name,
                        "game_id":      gid,
                        "game":         glabel,
                        "team_id":      team_id,
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
                        "cal_type":      f"{target.upper()}_{side}" if (f"{target.upper()}_{side}" in platt_calibrators) else ("global" if side in platt_calibrators else "raw_no_calibrator"),
                        "cal_applied":   cal_applied_over if side=="OVER" else cal_applied_under,
                        "is_sparse":     target in SPARSE_STATS,
                    })

    all_singles.sort(key=lambda x: x["ev"], reverse=True)

    # ── HARD PRE-EXPORT ASSERTIONS (Fix 1+5+6 per rebuild doc) ──────────────
    # Banned markets must NEVER appear in output — fail loudly if they do
    BANNED_MARKETS = {
        ("blk",  "OVER"),
        ("stl",  "OVER"),
        ("reb",  "UNDER"),
        ("fg3m", "UNDER"),
        ("stl",  "UNDER"),
    }
    SUPPRESSED_MARKETS = {
        ("pts",  "UNDER"),
        ("ast",  "UNDER"),
        ("fg3m", "OVER"),
        ("blk",  "UNDER"),
    }
    violations = []
    for s in all_singles:
        key = (s["stat"], s["side"])
        if key in BANNED_MARKETS:
            violations.append(f"BANNED market in picks: {s['player_name']} {s['stat']} {s['side']}")
        if key in SUPPRESSED_MARKETS and s.get("model_prob", 0) < 0.67:
            violations.append(f"SUPPRESSED market below threshold: {s['player_name']} {s['stat']} {s['side']} prob={s.get('model_prob',0):.3f}")
    if violations:
        for v in violations:
            logger.error(f"ASSERTION FAILED: {v}")
        all_singles = [s for s in all_singles
                      if (s["stat"], s["side"]) not in BANNED_MARKETS]
        logger.warning(f"Removed {len(violations)} banned/invalid picks before export")

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

    # ── SGP generation — skipped if SKIP_SGPS=1 ───────────────────────────────
    sgp_results = {"two_leg": [], "three_leg": []}

    if os.environ.get("SKIP_SGPS") == "1":
        logger.info("SGP generation skipped (SKIP_SGPS=1)")
    elif within_engine is not None:
        logger.info("Generating SGP candidates (Gaussian copula)...")
        sgp_pool = filter_sgp_candidates(all_singles)
        if sgp_pool:
            sgp_results = build_sgp_candidates(
                singles         = sgp_pool,
                within_engine   = within_engine,
                teammate_engine = teammate_engine,
                min_ev          = MIN_EV,
            )
        else:
            logger.warning("  SGP pool empty after filtering")
    else:
        logger.warning("  Skipping SGPs — correlation engine not available")

    two_leg   = sgp_results.get("two_leg",   [])
    three_leg = sgp_results.get("three_leg", [])
    all_sgps  = sorted(two_leg + three_leg, key=lambda x: x["ev"], reverse=True)
    logger.info(f"  2-leg: {len(two_leg)} | 3-leg: {len(three_leg)}")

    # ── Write SGPs ─────────────────────────────────────────────────────────────
    sgps_out = {
        "date":         today,
        "generated_at": datetime.utcnow().isoformat(),
        "version":      "2026-03-17-v13",
        "min_ev":       MIN_EV,
        "total_sgps":   len(all_sgps),
        "two_leg":      len(two_leg),
        "three_leg":    len(three_leg),
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
