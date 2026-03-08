#!/usr/bin/env python3
"""
predict_darko_v4.py — NBA Props Model Prediction Engine
VERSION: 2026-02-28-v11

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

v11 changes:
  - Singles written to disk BEFORE SGP generation (guarantees data on timeout)
  - SGP candidate pool capped to top 6 per game by EV before copula
  - Workflow timeout raised to 60 min
"""

import csv
import json
import logging
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

DATA_DIR  = Path("data")
MODEL_DIR = Path("model_cache")
PRED_DIR  = Path("predictions"); PRED_DIR.mkdir(exist_ok=True)

STAT_DISPLAY = {
    "pts":"Points","reb":"Rebounds","ast":"Assists","fg3m":"Threes",
    "stl":"Steals","blk":"Blocks","tov":"Turnovers",
    "pra":"Pts+Reb+Ast","pr":"Pts+Reb","pa":"Pts+Ast",
    "ra":"Reb+Ast","stocks":"Stl+Blk",
}

MIN_EV              = 0.025
MIN_GAMES_SEASON    = 15
KELLY_FRAC          = 0.25
MAX_UNITS_SINGLE    = 2.0
MAX_UNITS_SGP       = 1.0
SGP_MAX_PER_GAME    = 6      # cap: top N singles per game fed into copula
SGP_ABSOLUTE_CAP    = 60     # hard ceiling on total SGP candidate pool


ADV_FIELDS = [
    "usage_percentage","pace",
    "true_shooting_percentage","effective_field_goal_percentage",
    "assist_percentage","assist_to_turnover",
]


# ── Model loading ──────────────────────────────────────────────────────────────

def load_models() -> tuple:
    """Load all quantile models and feature lists."""
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

    return models, within_engine, teammate_engine


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

    We only keep stats the copula models well (pts, reb, ast, fg3m, stl, blk).
    Combo stats (pra, pr, pa, ra, stocks, tov) are excluded from SGPs because
    their within-game correlations are trivially high and produce misleading CLV.
    """
    SGP_ELIGIBLE_STATS = {"pts", "reb", "ast", "fg3m", "stl", "blk"}

    # Filter to eligible stats only
    eligible = [s for s in singles if s["stat"] in SGP_ELIGIBLE_STATS]

    # Group by game, keep top N by EV per game
    by_game: dict = {}
    for s in eligible:
        gid = s["game_id"]
        by_game.setdefault(gid, []).append(s)

    pool = []
    for gid, picks in by_game.items():
        top = sorted(picks, key=lambda x: x["ev"], reverse=True)[:SGP_MAX_PER_GAME]
        pool.extend(top)

    # Hard ceiling
    pool = sorted(pool, key=lambda x: x["ev"], reverse=True)[:SGP_ABSOLUTE_CAP]

    logger.info(f"  SGP candidate pool: {len(pool)} singles "
                f"({len(eligible)} eligible → capped at {SGP_MAX_PER_GAME}/game, "
                f"max {SGP_ABSOLUTE_CAP} total)")
    return pool


# ── Paper trade logger ─────────────────────────────────────────────────────────

def log_paper_trade(singles: list, sgps: list, target_date: str):
    log_path = PRED_DIR / "paper_trade_log.csv"
    fieldnames = [
        "date","type","player","game","stat","side","line",
        "odds","model_prob","ev","kelly_units","outcome","profit",
    ]
    write_header = not log_path.exists()
    with open(log_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        for p in singles:
            w.writerow({
                "date": target_date, "type": "single",
                "player": p["player_name"], "game": p["game"],
                "stat": p["stat"], "side": p["side"],
                "line": p["line"], "odds": p["odds"],
                "model_prob": round(p["model_prob"],4),
                "ev": round(p["ev"],4),
                "kelly_units": round(p["kelly_units"],3),
                "outcome": "", "profit": "",
            })
        for s in sgps:
            w.writerow({
                "date": target_date,
                "type": f"sgp_{s['legs']}leg",
                "player": "|".join(l["player"] for l in s["leg_details"]),
                "game": s["game"],
                "stat": "|".join(l["stat"] for l in s["leg_details"]),
                "side": "|".join(l["side"] for l in s["leg_details"]),
                "line": "|".join(str(l["line"]) for l in s["leg_details"]),
                "odds": s["combined_odds"],
                "model_prob": round(s["correlated_prob"],4),
                "ev": round(s["ev"],4),
                "kelly_units": round(s["kelly_units"],3),
                "outcome": "", "profit": "",
            })


# ── Console summary ────────────────────────────────────────────────────────────

def print_singles_summary(picks: list):
    print(f"\n{'='*70}")
    print(f"  NBA Props Model — SINGLES ({len(picks)} picks above {MIN_EV:.1%} EV)")
    print(f"{'='*70}")
    for p in picks[:25]:
        tier = "ELITE" if p["ev"] >= 0.10 else "HIGH" if p["ev"] >= 0.06 else "EDGE"
        print(f"\n[{tier}]  {p['player_name']} — {STAT_DISPLAY.get(p['stat'],p['stat'])} {p['side']} {p['line']}")
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
        print(f"  Copula P: {s['correlated_prob']:.1%}  Naive: {s['naive_prob']:.1%}  "
              f"Combined: {s['combined_odds']:+d}  EV: {s['ev']:+.2%}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("NBA Props Model PREDICTIONS — VERSION 2026-02-28-v11")
    logger.info("=" * 60)

    if not _get_api_key():
        sys.exit("BDL_API_KEY not set.")

    target_date = date.today().strftime("%Y-%m-%d")
    logger.info(f"Target date: {target_date}")

    logger.info("Loading models...")
    models, within_engine, teammate_engine = load_models()
    if not models:
        sys.exit("No models in model_cache/. Run training script first.")

    stats_path = DATA_DIR / "player_game_stats.parquet"
    adv_path   = DATA_DIR / "advanced_stats.parquet"
    if not stats_path.exists():
        sys.exit("No stats data. Run training script first.")

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

    # ── Build predictions ─────────────────────────────────────────────────────
    all_singles = []

    for game in games:
        gid      = game.get("id")
        home_id  = (game.get("home_team") or {}).get("id")
        vis_id   = (game.get("visitor_team") or {}).get("id")
        home_nm  = (game.get("home_team") or {}).get("full_name","")
        vis_nm   = (game.get("visitor_team") or {}).get("full_name","")
        glabel   = f"{vis_nm} @ {home_nm}"
        ctx      = ctx_map.get(gid, {})

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
                vendor     = prop.get("best_over_vendor", prop.get("vendor",""))

                base_ix = add_interaction_features(dict(base), target)
                q_preds = predict_quantiles(models, target, base_ix)
                if q_preds is None:
                    continue

                q50 = q_preds.get(0.50, line)

                prob_over  = p_over(q_preds, line)
                prob_under = p_under(q_preds, line)
                ev_over    = ev_from_prob(prob_over,  over_odds)
                ev_under   = ev_from_prob(prob_under, under_odds)

                for side, prob, odds, ev in [
                    ("OVER",  prob_over,  over_odds,  ev_over),
                    ("UNDER", prob_under, under_odds, ev_under),
                ]:
                    if ev < MIN_EV:
                        continue
                    kelly = kelly_fraction(prob, odds, KELLY_FRAC, MAX_UNITS_SINGLE)
                    if kelly <= 0:
                        continue

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
                        "bet_vendor":   vendor,
                        "model_prob":   round(prob, 4),
                        "market_prob":  round(prop.get("implied_prob_over", 0.5)
                                              if side == "OVER"
                                              else 1 - prop.get("implied_prob_over", 0.5), 4),
                        "ev":           round(ev, 4),
                        "kelly_units":  round(kelly, 3),
                        "q50":          round(q50, 2),
                        "q_preds":      {float(k): round(v,2) for k,v in q_preds.items()},
                        "usage_bucket": ub,
                        "mp_bucket":    mb,
                    })

    all_singles.sort(key=lambda x: x["ev"], reverse=True)
    logger.info(f"Singles above EV threshold: {len(all_singles)}")

    today = target_date

    # ── Write singles FIRST — guarantees data even if SGP step times out ──────
    singles_out = {
        "date":         today,
        "generated_at": datetime.utcnow().isoformat(),
        "version":      "2026-02-28-v11",
        "min_ev":       MIN_EV,
        "total_picks":  len(all_singles),
        "picks":        all_singles,
    }
    singles_path = PRED_DIR / f"singles_{today}.json"
    with open(singles_path, "w") as f:
        json.dump(singles_out, f, indent=2, default=str)
    logger.info(f"Singles written → {singles_path}  (safe before SGP step)")

    # ── SGP generation ─────────────────────────────────────────────────────────
    logger.info("Generating SGP candidates (Gaussian copula)...")
    sgp_results = {"two_leg": [], "three_leg": []}

    if within_engine is not None:
        # ── CRITICAL: cap candidates before copula to prevent timeout ─────────
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
        "version":      "2026-02-28-v11",
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
