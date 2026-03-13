#!/usr/bin/env python3
"""
analyze_features.py — NBA Props Model Feature Intelligence Report
=================================================================
VERSION: 2026-03-13-v1

Generates a professional-grade feature intelligence report that a market
maker or quantitative analyst would want to see before a retrain:

  1. Per-stat individual feature importance (aggregated across all quantile models)
  2. Feature importance normalized to % contribution per stat
  3. Cross-stat feature overlap (which features are universally important)
  4. Redundancy analysis — pairwise Pearson correlation in training data
     (highly correlated feature pairs → redundant; consider pruning)
  5. Interaction term analysis — are the manually crafted interactions
     (usage_proxy_x_itt, reb_x_mp, etc.) adding value vs individual features?
  6. Importance by feature GROUP (market odds, rolling stats, minutes,
     advanced stats, vacancy/injury, schedule)
  7. Dead features — features with zero importance across ALL stats
  8. Feature stability — do top features agree across quantile levels?
     (e.g., is the most important Q10 feature the same as Q90?)

Output:
  model_cache/feature_analysis_report.json  — full machine-readable report
  Console: formatted report with tables and actionable insights

Usage:
  python3 analyze_features.py
  python3 analyze_features.py --stat pts
  python3 analyze_features.py --format json
"""

import argparse
import json
import logging
import warnings
from collections import defaultdict
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

MODEL_DIR = Path("model_cache")
DATA_DIR  = Path("data")

STATS = ["pts", "reb", "ast", "fg3m", "stl", "blk"]
COMBO_STATS = ["pra", "pr", "pa", "ra", "stocks"]
ALL_TARGETS = STATS + COMBO_STATS

STAT_DISPLAY = {
    "pts": "Points", "reb": "Rebounds", "ast": "Assists",
    "fg3m": "Threes", "stl": "Steals", "blk": "Blocks",
    "pra": "Pts+Reb+Ast", "pr": "Pts+Reb", "pa": "Pts+Ast",
    "ra": "Reb+Ast", "stocks": "Stl+Blk",
}

QUANTILES = [0.1, 0.2, 0.25, 0.33, 0.4, 0.5, 0.6, 0.67, 0.75, 0.8, 0.9]


# ── Feature group classification ──────────────────────────────────────────────

def classify_feature_group(feature: str) -> str:
    """Classify a feature into a logical group for aggregate analysis."""
    f = feature.lower()

    # Minutes model predictions (standalone quantile model outputs)
    if f.startswith("exp_mp") or f.startswith("mp_q") or f.startswith("mp_pred"):
        return "minutes_model_output"

    # Rolling minutes history
    if f.startswith("mp_") or f.startswith("starter_rate") or f.startswith("games_30") \
       or f.startswith("games_35") or f.startswith("games_20") or f == "role_stability_index":
        return "minutes_history"

    # Market / odds features
    if any(f.startswith(k) for k in [
        "game_total", "spread_for_team", "implied_team_total", "blowout_risk",
        "opp_implied", "opp_pace", "opp_defense", "has_odds",
        "total_move", "spread_move", "steam_", "sharp_",
    ]):
        return "market_odds"

    # Advanced stats (BDL v2)
    if f.startswith("adv_"):
        return "advanced_stats"

    # Vacated opportunity / injury
    if f.startswith("vacated_") or f in ("num_teammates_inactive", "has_injury_data"):
        return "vacancy_injury"

    # Schedule features
    if any(f == k for k in [
        "rest_days", "back_to_back", "three_in_4", "four_in_6",
        "games_last_7", "missed_last_game", "missed_2_of_last5",
    ]):
        return "schedule"

    # 3PM / FG3 specific
    if any(f.startswith(k) for k in ["fg3m_", "fg3a_", "fg3_", "is_low_3pa"]):
        return "fg3_specific"

    # Sparse stat (STL/BLK)
    if any(f.startswith(k) for k in ["stl_p_", "blk_p_", "stl_per_min_blend", "blk_per_min_blend"]):
        return "sparse_stat"

    # Interaction features
    if "_x_" in f or f.startswith("e_") or f in (
        "usage_proxy_x_itt", "fga_x_itt", "reb_x_mp",
        "ast_pct_x_itt", "usage_x_itt", "usage_x_pace",
        "e_pts_proxy", "e_reb_proxy", "e_ast_proxy",
        "blowout_risk_x_mp_vol",
    ):
        return "interaction"

    # Rolling player stats
    if any(k in f for k in ["_per_min_", "_raw_", "usage_proxy_per_min", "pf_per_min"]):
        return "rolling_player_stats"

    # Metadata
    if f in ("is_home", "games_played", "has_advanced_stats"):
        return "metadata"

    return "other"


# ── Load models and extract importance ────────────────────────────────────────

def load_all_importance() -> dict:
    """
    Load feature importance from all quantile models.
    Returns dict: {target: {feature: importance_score}}
    where importance_score = mean across all quantile levels (gain-weighted).
    """
    importance_by_target = {}

    for target in ALL_TARGETS:
        fcols_path = MODEL_DIR / f"features_{target}.pkl"
        if not fcols_path.exists():
            continue
        fcols = joblib.load(fcols_path)

        # Aggregate importance across all quantile models
        total_importance = defaultdict(float)
        model_count = 0

        for q in QUANTILES:
            mpath = MODEL_DIR / f"q{int(q*100):02d}_{target}.pkl"
            if not mpath.exists():
                continue
            try:
                model = joblib.load(mpath)
                # LightGBM: feature_importance("gain") is more informative than "split"
                imp = model.feature_importance(importance_type="gain")
                for feat, val in zip(fcols, imp):
                    total_importance[feat] += float(val)
                model_count += 1
            except Exception as e:
                logger.debug(f"Could not load {mpath}: {e}")
                continue

        if model_count > 0 and total_importance:
            # Normalize by model count to get per-quantile-model average
            avg_importance = {f: v / model_count for f, v in total_importance.items()}
            importance_by_target[target] = avg_importance
            logger.info(
                f"  {target}: {len(avg_importance)} features from {model_count} models"
            )

    return importance_by_target


def load_feature_importance_csv() -> dict:
    """
    Also load the existing feature_importance_{stat}.csv files as a secondary source.
    These contain importance from Q50 models specifically.
    """
    csv_importance = {}
    for target in ALL_TARGETS:
        csv_path = MODEL_DIR / f"feature_importance_{target}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            csv_importance[target] = dict(zip(df["feature"], df["importance"]))
    return csv_importance


# ── Analysis functions ────────────────────────────────────────────────────────

def normalize_importance(importance: dict) -> dict:
    """Normalize to percentage contribution."""
    total = sum(importance.values())
    if total == 0:
        return {k: 0.0 for k in importance}
    return {k: round(v / total * 100, 3) for k, v in importance.items()}


def rank_features(importance: dict, top_n: int = 20) -> list:
    """Return top N features sorted by importance."""
    return sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]


def dead_features(importance_by_target: dict) -> list:
    """Features with zero importance across ALL targets."""
    all_features = set()
    for imp in importance_by_target.values():
        all_features.update(imp.keys())

    dead = []
    for feat in sorted(all_features):
        if all(importance_by_target.get(t, {}).get(feat, 0) == 0
               for t in importance_by_target):
            dead.append(feat)
    return dead


def cross_stat_importance(importance_by_target: dict) -> dict:
    """
    For each feature, compute its average importance rank across all stats.
    Lower rank = more universally important.
    """
    all_features = set()
    for imp in importance_by_target.values():
        all_features.update(imp.keys())

    # Per-stat rank for each feature
    ranks_by_feat = defaultdict(list)
    for target, imp in importance_by_target.items():
        if target not in STATS:
            continue
        sorted_feats = sorted(imp.items(), key=lambda x: x[1], reverse=True)
        rank_map = {f: i+1 for i, (f, _) in enumerate(sorted_feats)}
        for feat in all_features:
            ranks_by_feat[feat].append(rank_map.get(feat, len(sorted_feats)+1))

    cross_stats = {}
    for feat, ranks in ranks_by_feat.items():
        cross_stats[feat] = {
            "mean_rank":   round(float(np.mean(ranks)), 2),
            "min_rank":    int(min(ranks)),
            "max_rank":    int(max(ranks)),
            "n_zero_stats": sum(1 for r in ranks if r > 50),
            "n_top10":      sum(1 for r in ranks if r <= 10),
        }

    return cross_stats


def group_importance(importance: dict) -> dict:
    """Sum importance by feature group."""
    group_totals = defaultdict(float)
    total = sum(importance.values())
    for feat, imp in importance.items():
        group = classify_feature_group(feat)
        group_totals[group] += imp
    if total > 0:
        return {g: {"total": round(v, 2), "pct": round(v/total*100, 2)}
                for g, v in sorted(group_totals.items(), key=lambda x: x[1], reverse=True)}
    return {}


def interaction_analysis(importance_by_target: dict) -> dict:
    """
    Evaluate whether manually crafted interaction terms are adding value
    compared to their constituent features.

    For each interaction term, compute:
      - Its importance rank
      - The importance of its constituent features
      - Marginal contribution: is the interaction in top 50% of features?
    """
    INTERACTIONS = {
        "usage_proxy_x_itt": ["usage_proxy_per_min_mean_last10", "implied_team_total"],
        "fga_x_itt":         ["fga_per_min_mean_last10", "implied_team_total"],
        "reb_x_mp":          ["reb_per_min_mean_last10", "mp_mean_last10"],
        "ast_pct_x_itt":     ["adv_assist_percentage_mean_last10", "implied_team_total"],
        "usage_x_itt":       ["adv_usage_percentage_mean_last10", "implied_team_total"],
        "usage_x_pace":      ["usage_proxy_per_min_mean_last10", "adv_pace_mean_last10"],
        "blowout_risk_x_mp_vol": ["blowout_risk", "mp_vol_last10"],
        "e_pts_proxy":       ["pts_per_min_mean_last10", "mp_mean_last10"],
        "e_reb_proxy":       ["reb_per_min_mean_last10", "mp_mean_last10"],
        "e_ast_proxy":       ["ast_per_min_mean_last10", "mp_mean_last10"],
    }

    results = {}
    for interaction, constituents in INTERACTIONS.items():
        stat_results = {}
        for target in STATS:
            imp = importance_by_target.get(target, {})
            all_feats_sorted = sorted(imp.items(), key=lambda x: x[1], reverse=True)
            rank_map = {f: i+1 for i, (f, _) in enumerate(all_feats_sorted)}
            n_feats = len(all_feats_sorted)

            ix_imp  = imp.get(interaction, 0)
            ix_rank = rank_map.get(interaction, n_feats+1)

            const_imps = {c: imp.get(c, 0) for c in constituents}

            if ix_imp > 0 or any(v > 0 for v in const_imps.values()):
                stat_results[target] = {
                    "interaction_importance": round(ix_imp, 2),
                    "interaction_rank":       ix_rank,
                    "constituent_importance": {c: round(v, 2) for c,v in const_imps.items()},
                    "adds_value": ix_rank <= n_feats * 0.5 and ix_imp > 0,
                }

        if stat_results:
            results[interaction] = stat_results

    return results


def quantile_stability(target: str) -> dict:
    """
    Check whether feature importance is consistent across quantile levels.
    High stability = feature matters at all quantiles (robust signal).
    Low stability at Q10/Q90 vs Q50 = feature only matters at median.
    """
    fcols_path = MODEL_DIR / f"features_{target}.pkl"
    if not fcols_path.exists():
        return {}
    fcols = joblib.load(fcols_path)

    q_importances = {}
    for q in QUANTILES:
        mpath = MODEL_DIR / f"q{int(q*100):02d}_{target}.pkl"
        if not mpath.exists():
            continue
        try:
            model = joblib.load(mpath)
            imp   = model.feature_importance(importance_type="gain")
            q_importances[q] = dict(zip(fcols, imp.astype(float)))
        except Exception:
            continue

    if len(q_importances) < 3:
        return {}

    # For each feature: compute rank at Q10, Q50, Q90
    result = {}
    qs_of_interest = [0.1, 0.5, 0.9]

    # Build rank maps for Q10, Q50, Q90
    rank_maps = {}
    for q in qs_of_interest:
        if q in q_importances:
            sorted_f = sorted(q_importances[q].items(), key=lambda x: x[1], reverse=True)
            rank_maps[q] = {f: i+1 for i, (f, _) in enumerate(sorted_f)}

    if len(rank_maps) < 2:
        return {}

    for feat in fcols:
        ranks = [rank_maps[q].get(feat, len(fcols)+1) for q in qs_of_interest if q in rank_maps]
        if len(ranks) >= 2:
            rank_std = float(np.std(ranks))
            result[feat] = {
                "ranks":     {str(q): rank_maps.get(q, {}).get(feat, len(fcols)+1) for q in qs_of_interest if q in rank_maps},
                "rank_std":  round(rank_std, 2),
                "stable":    rank_std < 5.0,   # stable = consistent rank across quantiles
            }

    return result


# ── Redundancy analysis ───────────────────────────────────────────────────────

def redundancy_analysis(target: str, importance: dict, top_n: int = 30) -> dict:
    """
    Compute pairwise Pearson correlation among top_n features using training data.
    High correlation (|r| > 0.85) between two features with similar importance
    suggests one is redundant — the model should be picking one but not both.

    IMPORTANT: Requires the training feature matrix X_{target}.parquet or similar.
    Falls back gracefully if training data unavailable.
    """
    # Check for training features parquet (saved during train run)
    feat_matrix_path = DATA_DIR / f"X_train_{target}.parquet"
    if not feat_matrix_path.exists():
        return {"status": "no_training_data", "pairs": []}

    try:
        X = pd.read_parquet(feat_matrix_path)
    except Exception:
        return {"status": "load_failed", "pairs": []}

    top_feats = [f for f, _ in rank_features(importance, top_n) if f in X.columns]
    if len(top_feats) < 2:
        return {"status": "insufficient_features", "pairs": []}

    X_top   = X[top_feats].astype(float)
    corr    = X_top.corr()

    high_corr_pairs = []
    for i, f1 in enumerate(top_feats):
        for j, f2 in enumerate(top_feats):
            if j <= i:
                continue
            r = corr.loc[f1, f2]
            if abs(r) > 0.85:
                imp1 = importance.get(f1, 0)
                imp2 = importance.get(f2, 0)
                high_corr_pairs.append({
                    "feature_1":   f1,
                    "feature_2":   f2,
                    "pearson_r":   round(r, 4),
                    "imp_1":       round(imp1, 2),
                    "imp_2":       round(imp2, 2),
                    "keep":        f1 if imp1 >= imp2 else f2,   # keep higher importance
                    "drop_candidate": f2 if imp1 >= imp2 else f1,
                })

    return {
        "status": "ok",
        "n_top_features": len(top_feats),
        "n_high_corr_pairs": len(high_corr_pairs),
        "pairs": sorted(high_corr_pairs, key=lambda x: abs(x["pearson_r"]), reverse=True),
    }


# ── Report printing ───────────────────────────────────────────────────────────

def print_full_report(importance_by_target: dict, args):
    stats_to_show = [args.stat] if args.stat else ALL_TARGETS

    print("\n" + "="*80)
    print("  NBA PROPS MODEL — FEATURE INTELLIGENCE REPORT")
    print("  Built from LightGBM gain-based feature importance (all 11 quantile models)")
    print("="*80)

    # ── 1. Per-stat top features ──────────────────────────────────────────────
    print("\n── PER-STAT TOP FEATURES (importance % contribution) ──────────────────────\n")

    for target in stats_to_show:
        if target not in importance_by_target:
            continue
        imp = importance_by_target[target]
        norm = normalize_importance(imp)
        top = rank_features(norm, 20)
        groups = group_importance(imp)

        print(f"  {STAT_DISPLAY.get(target, target).upper()} ({target})")
        print(f"  {'Feature':48s} {'%Imp':>7}  {'Group'}")
        print(f"  {'─'*72}")
        for feat, pct in top:
            group = classify_feature_group(feat)
            print(f"  {feat:48s} {pct:6.2f}%  [{group}]")

        # Dead features for this stat
        dead = [f for f, v in imp.items() if v == 0]
        if dead:
            print(f"\n  Zero-importance features ({len(dead)}): {', '.join(dead[:8])}{'...' if len(dead)>8 else ''}")

        # Group summary
        print(f"\n  Group totals:")
        for group, gdata in list(groups.items())[:6]:
            print(f"    {group:30s}  {gdata['pct']:5.1f}%")
        print()

    # ── 2. Cross-stat universal features ─────────────────────────────────────
    cross = cross_stat_importance(importance_by_target)
    universal = sorted(
        [(f, d) for f, d in cross.items() if d["n_top10"] >= 4],
        key=lambda x: x[1]["mean_rank"]
    )

    print("\n── UNIVERSALLY IMPORTANT FEATURES (top-10 in 4+ stats) ────────────────────\n")
    print(f"  {'Feature':48s} {'MeanRank':>9}  {'Top-10 in N stats':>17}  {'Min rank'}")
    print(f"  {'─'*78}")
    for feat, data in universal[:20]:
        print(f"  {feat:48s} {data['mean_rank']:9.1f}  {data['n_top10']:17d}  {data['min_rank']}")

    # ── 3. Dead features (zero importance everywhere) ─────────────────────────
    dead_all = dead_features(importance_by_target)
    print(f"\n── DEAD FEATURES (zero importance in ALL targets) ──────────────────────────\n")
    if dead_all:
        print(f"  {len(dead_all)} dead features — candidates for removal at next retrain:\n")
        for i, feat in enumerate(dead_all):
            group = classify_feature_group(feat)
            print(f"  {feat:48s}  [{group}]")
    else:
        print("  None — all features have non-zero importance in at least one target.")
    print()

    # ── 4. Interaction term analysis ─────────────────────────────────────────
    ix_analysis = interaction_analysis(importance_by_target)
    print("\n── INTERACTION TERM ANALYSIS ───────────────────────────────────────────────\n")
    print(f"  {'Interaction':38s}  {'Value?':>7}  Stats where it ranks in top 50%")
    print(f"  {'─'*72}")
    for ix, stat_results in ix_analysis.items():
        adds_val = sum(1 for r in stat_results.values() if r.get("adds_value"))
        best_stats = [t for t, r in stat_results.items() if r.get("adds_value")]
        print(f"  {ix:38s}  {'YES' if adds_val>0 else 'NO':>7}  {', '.join(best_stats)}")

    # ── 5. Feature group breakdown across all stats ───────────────────────────
    print("\n── FEATURE GROUP CONTRIBUTION (all stats average) ──────────────────────────\n")
    all_group_totals = defaultdict(float)
    total_all = 0.0
    for target in STATS:
        imp = importance_by_target.get(target, {})
        for feat, val in imp.items():
            all_group_totals[classify_feature_group(feat)] += val
            total_all += val

    print(f"  {'Group':35s}  {'%Total':>8}")
    print(f"  {'─'*46}")
    for group, val in sorted(all_group_totals.items(), key=lambda x: x[1], reverse=True):
        pct = val / total_all * 100 if total_all > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {group:35s}  {pct:7.2f}%  {bar}")

    # ── 6. Key insight callouts ───────────────────────────────────────────────
    print("\n── KEY INSIGHTS FOR NEXT RETRAIN ───────────────────────────────────────────\n")

    # Check if market odds features are dead (the main known problem)
    market_dead_in = []
    for target in STATS:
        imp = importance_by_target.get(target, {})
        market_feats = ["implied_team_total", "game_total", "blowout_risk", "spread_for_team"]
        if all(imp.get(f, 0) == 0 for f in market_feats):
            market_dead_in.append(target)

    if market_dead_in:
        print(f"  ⚠ CRITICAL: Market odds features (implied_team_total, game_total) have")
        print(f"    ZERO importance in: {', '.join(market_dead_in)}")
        print(f"    ROOT CAUSE: BDL v1/odds only covers 2025-26 season. Most training rows")
        print(f"    have NaN odds. Retrain will fix this as snapshot data accumulates.")
        print(f"    EXPECTED: After retrain, market features should rank in top 15 for pts/reb/ast.")

    # Check vacancy features
    vacated_dead_in = []
    for target in STATS:
        imp = importance_by_target.get(target, {})
        if imp.get("vacated_minutes", 0) == 0 and imp.get("num_teammates_inactive", 0) == 0:
            vacated_dead_in.append(target)
    if vacated_dead_in:
        print(f"\n  ⚠ Vacancy/injury features also zero: {', '.join(vacated_dead_in)}")
        print(f"    EXPECTED: Will improve as injury_snapshots.parquet accumulates.")

    # Line movement features
    lm_feats = ["total_move", "spread_move", "steam_total_up", "steam_total_down"]
    lm_all_dead = all(
        all(importance_by_target.get(t, {}).get(f, 0) == 0 for t in STATS)
        for f in lm_feats
    )
    if lm_all_dead:
        print(f"\n  ℹ Line movement features (total_move, spread_move) are NEW as of 2026-03-13.")
        print(f"    They will have zero importance in current models (trained before snapshots existed).")
        print(f"    EXPECTED after retrain: non-zero importance for pts, reb, ast, fg3m.")
    else:
        for feat in lm_feats:
            for target in STATS:
                imp_val = importance_by_target.get(target, {}).get(feat, 0)
                if imp_val > 0:
                    norm_imp = normalize_importance(importance_by_target[target])
                    pct = norm_imp.get(feat, 0)
                    print(f"  ✓ {feat} has {pct:.2f}% importance in {target}")

    print()

    print("="*80)
    print(f"  Report based on {sum(len(v) for v in importance_by_target.values())} feature-model pairs")
    print(f"  Source: model_cache/ quantile models (gain-based importance, all Q levels)")
    print("="*80 + "\n")


# ── JSON report builder ───────────────────────────────────────────────────────

def build_json_report(importance_by_target: dict) -> dict:
    """Build machine-readable JSON report."""
    report = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "model_version": "see model_cache/training_meta.json",
        "targets":      list(importance_by_target.keys()),
        "per_stat":     {},
        "cross_stat":   {},
        "dead_features": [],
        "interactions": {},
        "group_summary": {},
    }

    for target, imp in importance_by_target.items():
        norm = normalize_importance(imp)
        top  = rank_features(norm, 30)
        report["per_stat"][target] = {
            "top_features": [{"feature": f, "pct": p, "group": classify_feature_group(f)}
                             for f, p in top],
            "group_breakdown": group_importance(imp),
            "n_features":      len(imp),
            "n_zero":          sum(1 for v in imp.values() if v == 0),
        }

    report["cross_stat"] = cross_stat_importance(importance_by_target)
    report["dead_features"] = dead_features(importance_by_target)
    report["interactions"]  = interaction_analysis(importance_by_target)

    # Overall group summary
    all_group = defaultdict(float)
    total = 0.0
    for target in STATS:
        for feat, val in importance_by_target.get(target, {}).items():
            all_group[classify_feature_group(feat)] += val
            total += val
    report["group_summary"] = {
        g: {"total": round(v, 2), "pct": round(v/total*100, 2)}
        for g, v in sorted(all_group.items(), key=lambda x: x[1], reverse=True)
    } if total > 0 else {}

    return report


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NBA Props Model Feature Intelligence Report"
    )
    parser.add_argument("--stat",   type=str, default=None,
                        help="Show detail for one stat only (pts, reb, ast, etc.)")
    parser.add_argument("--format", type=str, default="console",
                        choices=["console", "json", "both"],
                        help="Output format (default: console)")
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("NBA Props Model — Feature Intelligence Analysis")
    logger.info("="*60)

    if not MODEL_DIR.exists():
        logger.error(f"model_cache/ not found. Run training first.")
        return

    logger.info("Loading quantile models and extracting feature importance...")
    importance_by_target = load_all_importance()

    if not importance_by_target:
        logger.warning("No models found in model_cache/. Falling back to CSV importance files.")
        importance_by_target = load_feature_importance_csv()

    if not importance_by_target:
        logger.error("No importance data available. Train the model first.")
        return

    logger.info(f"Loaded importance for {len(importance_by_target)} targets")

    if args.format in ("console", "both"):
        print_full_report(importance_by_target, args)

    if args.format in ("json", "both"):
        report = build_json_report(importance_by_target)
        out_path = MODEL_DIR / "feature_analysis_report.json"
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"JSON report saved → {out_path}")


if __name__ == "__main__":
    main()
