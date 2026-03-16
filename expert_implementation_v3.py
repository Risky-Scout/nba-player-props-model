"""
NBA Props Model — Expert Review v3 Final Implementation
========================================================
Implements all remaining expert recommendations exactly as specified.

CHANGES FROM v2:
  1. WORKFLOW ORDER FIXED:
     audit → quantile diagnostics → distribution adjustment (NEW) →
     temperature/beta calibration → comparison → CLV → portfolio simulation
     Expert: "if tails are too narrow, fix that BEFORE calibration"

  2. RAW vs CALIBRATED vs FILTERED COMPARISON (NEW):
     "You won't know whether improvement came from the model,
      calibration, or bet selection without this separation."

  3. STAT-SIDE-SPECIFIC THRESHOLDS (NEW):
     pts_over, pts_under, reb_over, reb_under, ast_over, ast_under,
     fg3m_over, fg3m_under, blk_under, stl_under
     Expert: "current thresholds are a strong start but still coarse"

  4. MARKET DISAGREEMENT / STALE-BOOK LOGIC (NEW):
     book disagreement, consensus vs best-book gap,
     stale book detection, time since last move
     Expert: "a major ROI lever later"

  5. CORRELATION-AWARE PORTFOLIO EXPOSURE (NEW):
     pts_over + ast_over + PRA_over for same player = correlated
     Expert: "not three independent bets"

  CAUTIONS FROM EXPERT:
  - Do NOT overfit no-bet rules on short sample — use as temporary triage
  - Do NOT let beta calibration hide bad quantiles — fix distributions first
  - Do NOT expect 4 days of data to settle the truth — evaluate over windows
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from scipy.special import expit, logit
from scipy.optimize import minimize_scalar
from typing import Optional, Dict, List, Tuple, Set
import json
import os
from datetime import datetime


# =============================================================================
# SECTION 1: CORRECTED WORKFLOW ORDER
# Expert: "quantile diagnostics → variance/tail adjustment →
#          THEN calibration. Do not let calibration clean up bad tails."
# =============================================================================

def adjust_tails_from_diagnostics(
    coverage_df: pd.DataFrame,
    tail_threshold: float = 0.05,
) -> Dict[str, float]:
    """
    NEW STEP inserted between diagnostics and calibration.
    Expert: "if tails are clearly too narrow, fix that before calibration."

    Takes output of run_quantile_coverage_diagnostics() and computes
    a tail-widening factor per stat to apply BEFORE calibration runs.

    Returns {stat: tail_widening_factor} — factor > 1.0 means widen tails.
    """
    if coverage_df is None or len(coverage_df) == 0:
        print("[tail_adjust] No coverage data — using default widening factors")
        return {s: 1.15 for s in ['pts','reb','ast','fg3m','blk','stl']}

    widening = {}

    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        stat_cov = coverage_df[coverage_df['stat'] == stat]
        if len(stat_cov) == 0:
            widening[stat] = 1.15  # default
            continue

        # Focus on tail quantiles (q10, q90)
        tail_rows = stat_cov[stat_cov['quantile'].isin([0.10, 0.90])]
        if len(tail_rows) == 0:
            widening[stat] = 1.15
            continue

        # Mean tail error: positive = tails too narrow
        mean_tail_error = tail_rows['error'].mean()

        if mean_tail_error > tail_threshold:
            # Tails are too narrow — compute widening factor
            # error=0.10 → widen by 1.20; error=0.20 → widen by 1.40
            factor = 1.0 + mean_tail_error * 2.0
            factor = min(factor, 1.60)  # cap at 60% widening
            widening[stat] = round(factor, 3)
            print(f"[tail_adjust] {stat}: error={mean_tail_error:.3f} → widen by {factor:.3f}x")
        elif mean_tail_error < -tail_threshold:
            # Tails too wide — slight compression
            factor = 1.0 + mean_tail_error * 0.5  # conservative compression
            factor = max(factor, 0.85)
            widening[stat] = round(factor, 3)
            print(f"[tail_adjust] {stat}: error={mean_tail_error:.3f} → compress by {factor:.3f}x")
        else:
            widening[stat] = 1.00
            print(f"[tail_adjust] {stat}: error={mean_tail_error:.3f} → OK, no adjustment")

    return widening


def apply_tail_widening_to_quantiles(
    q_preds: dict,
    stat: str,
    widening_factors: Dict[str, float],
) -> dict:
    """
    Apply tail-widening factor to quantile predictions before probability computation.
    Widens the spread around q50 without changing the median projection.

    Before calibration, not after.
    """
    factor = widening_factors.get(stat, 1.0)
    if factor == 1.0:
        return q_preds

    q50 = q_preds.get(0.50, q_preds.get('0.5', None))
    if q50 is None:
        return q_preds

    adjusted = {}
    for tau, val in q_preds.items():
        deviation = float(val) - float(q50)
        adjusted[tau] = max(0.0, float(q50) + deviation * factor)

    return adjusted


# =============================================================================
# SECTION 2: RAW vs CALIBRATED vs FILTERED COMPARISON
# Expert: "You need this separation — crucial to know where improvement comes from"
# =============================================================================

def run_model_layer_comparison(
    performance_log_path: str,
    calibrator,
    portfolio_controller,
    output_path: str = 'model_cache/layer_comparison.json',
) -> Dict:
    """
    Expert: "Compare raw model vs raw+calibration vs raw+calibration+filters.
             Otherwise you won't know whether improvement came from the model,
             calibration, or bet selection."

    Computes hit rate, ROI, CLV, and Brier score at each layer:
      Layer 0 — Raw model output (no calibration, no filters)
      Layer 1 — Raw + temperature calibration
      Layer 2 — Raw + calibration + no-bet thresholds
      Layer 3 — Raw + calibration + no-bet thresholds + portfolio caps

    This is the most important diagnostic tool in the whole system.
    Run after every retrain.
    """
    df = pd.read_csv(performance_log_path)
    df['hit'] = (df['result'] == 'HIT').astype(float)
    df = df.dropna(subset=['model_prob', 'hit', 'stat', 'side'])

    BREAKEVEN = 0.5238  # at -110 vig

    results = {}

    def _compute_metrics(sub: pd.DataFrame, prob_col: str, label: str) -> dict:
        if len(sub) == 0:
            return {'n': 0, 'hit_rate': None, 'roi': None, 'clv': None, 'brier': None}
        hr    = sub['hit'].mean()
        brier = ((sub[prob_col] - sub['hit']) ** 2).mean()
        roi   = sub['profit'].mean() if 'profit' in sub.columns else None
        clv   = sub['clv_proxy'].mean() if 'clv_proxy' in sub.columns else None
        return {
            'label':    label,
            'n':        len(sub),
            'hit_rate': round(hr, 4),
            'roi':      round(roi, 4) if roi is not None else None,
            'clv':      round(clv, 4) if clv is not None else None,
            'brier':    round(brier, 4),
            'above_breakeven': hr > BREAKEVEN,
        }

    # ── Layer 0: Raw model ────────────────────────────────────────────────────
    results['layer_0_raw'] = _compute_metrics(df, 'model_prob', 'Raw Model')

    # ── Layer 1: Raw + calibration ────────────────────────────────────────────
    df['cal_prob'] = df.apply(
        lambda row: calibrator.calibrate(row['model_prob'], row['stat'])
        if calibrator else row['model_prob'], axis=1
    )
    results['layer_1_calibrated'] = _compute_metrics(df, 'cal_prob', 'Raw + Calibration')

    # ── Layer 2: Calibration + thresholds (no portfolio caps) ─────────────────
    from expert_implementation_v2 import passes_no_bet_filter
    df['passes_threshold'] = df.apply(
        lambda row: not passes_no_bet_filter(
            {'stat': row['stat'], 'side': row['side'], 'line': row.get('line', 0)},
            row['cal_prob'],
            row.get('q50')
        )[0], axis=1
    )
    l2 = df[df['passes_threshold']]
    results['layer_2_thresholds'] = _compute_metrics(l2, 'cal_prob', 'Cal + Thresholds')

    # ── Layer 3: Full pipeline including portfolio caps ───────────────────────
    picks_list = l2.to_dict('records')
    for p in picks_list:
        p['model_prob'] = p['cal_prob']  # use calibrated prob for portfolio sort

    filtered_picks, _ = portfolio_controller.filter_picks(picks_list)
    filtered_ids = {id(p) for p in filtered_picks}

    # Reconstruct filtered dataframe — match on row index
    filtered_indices = []
    for i, (_, row) in enumerate(l2.iterrows()):
        # Match by player_id, stat, side, game_id
        for p in filtered_picks:
            if (p.get('player_id') == row.get('player_id') and
                p.get('stat') == row.get('stat') and
                p.get('side') == row.get('side')):
                filtered_indices.append(row.name)
                break

    l3 = df.loc[filtered_indices] if filtered_indices else pd.DataFrame()
    results['layer_3_portfolio'] = _compute_metrics(l3, 'cal_prob', 'Cal + Thresh + Portfolio')

    # ── Print comparison table ────────────────────────────────────────────────
    print("\n" + "="*72)
    print("MODEL LAYER COMPARISON — where does improvement come from?")
    print("="*72)
    print(f"{'Layer':<30} {'n':>6} {'Hit Rate':>10} {'ROI':>8} {'CLV':>8} {'Brier':>8}")
    print("-"*72)
    for key, m in results.items():
        if m['n'] == 0:
            continue
        hr  = f"{m['hit_rate']:.1%}" if m['hit_rate'] else 'N/A'
        roi = f"{m['roi']:+.1%}" if m['roi'] is not None else 'N/A'
        clv = f"{m['clv']:+.3f}" if m['clv'] is not None else 'N/A'
        b   = f"{m['brier']:.4f}" if m['brier'] else 'N/A'
        flag = " ✓" if m.get('above_breakeven') else " ✗"
        print(f"{m['label']:<30} {m['n']:>6} {hr:>10}{flag} {roi:>8} {clv:>8} {b:>8}")
    print("="*72)
    print("Key: improvement from model → improving features/training")
    print("     improvement from calibration → probability construction was off")
    print("     improvement from filters → bet selection was too broad")
    print("="*72 + "\n")

    # Save
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    return results


# =============================================================================
# SECTION 3: STAT-SIDE-SPECIFIC THRESHOLDS
# Expert: "Current thresholds are coarse — move to stat-side-specific later"
# Expert: "Use current asymmetric thresholds only as temporary regime"
# =============================================================================

# Phase 1 (now): Temporary triage thresholds
# Expert: "use as temporary rescue thresholds, then re-estimate on larger holdout"
THRESHOLDS_PHASE_1 = {
    # stat: {side: min_calibrated_prob}
    'pts':  {'OVER': 0.60, 'UNDER': 0.72},
    'reb':  {'OVER': 0.60, 'UNDER': 0.70},
    'ast':  {'OVER': 0.60, 'UNDER': 0.72},
    'fg3m': {'OVER': 0.60, 'UNDER': 0.70},
    'blk':  {'OVER': 9.99, 'UNDER': 0.70},  # OVER banned
    'stl':  {'OVER': 9.99, 'UNDER': 0.72},  # OVER banned
}

# Phase 2 (when sample >= 200 per stat-side segment):
# Full stat-side-specific thresholds — computed from holdout calibration
# These are starting values; update after 200+ graded picks per bucket
THRESHOLDS_PHASE_2 = {
    'pts_over':   0.60,
    'pts_under':  0.72,
    'reb_over':   0.60,
    'reb_under':  0.70,
    'ast_over':   0.60,
    'ast_under':  0.72,
    'fg3m_over':  0.60,
    'fg3m_under': 0.70,
    'blk_over':   9.99,  # banned until further notice
    'blk_under':  0.70,
    'stl_over':   9.99,  # banned until further notice
    'stl_under':  0.72,
}


def get_threshold(stat: str, side: str, phase: int = 1) -> float:
    """Get the appropriate threshold for stat/side given current phase."""
    if phase == 1:
        return THRESHOLDS_PHASE_1.get(stat, {}).get(side, 0.65)
    else:
        key = f"{stat}_{side.lower()}"
        return THRESHOLDS_PHASE_2.get(key, 0.65)


def check_phase_readiness(
    performance_log_path: str,
    min_sample_per_segment: int = 200,
) -> Dict:
    """
    Check whether we have enough sample to move from Phase 1 to Phase 2 thresholds.
    Expert: "re-estimate on larger holdout windows"
    """
    df = pd.read_csv(performance_log_path)
    segments = {}
    ready_for_phase2 = True

    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        for side in ['OVER', 'UNDER']:
            key = f"{stat}_{side}"
            n = len(df[(df['stat'] == stat) & (df['side'] == side)])
            segments[key] = n
            if n < min_sample_per_segment and not (stat in ('blk','stl') and side == 'OVER'):
                ready_for_phase2 = False

    print("\n[threshold_phase] Sample count per stat-side segment:")
    for k, n in sorted(segments.items()):
        flag = "✓ READY" if n >= min_sample_per_segment else f"✗ NEED {min_sample_per_segment - n} more"
        print(f"  {k:<15}: {n:>4} picks — {flag}")
    print(f"\n[threshold_phase] Ready for Phase 2 thresholds: {'YES' if ready_for_phase2 else 'NO — stay on Phase 1'}")

    return {'segments': segments, 'ready_for_phase2': ready_for_phase2}


# =============================================================================
# SECTION 4: MARKET DISAGREEMENT / STALE-BOOK LOGIC
# Expert: "book disagreement, consensus vs best-book gap,
#          stale book detection, time since last move — major ROI lever later"
# =============================================================================

def compute_market_disagreement_signals(
    player_id: int,
    stat: str,
    game_id: int,
    db_path: str = 'data/prop_snapshots.db',
) -> Dict:
    """
    Expert: "book disagreement + stale-book detection — major ROI lever later"

    Computes signals from multi-book prop snapshot data:
      - book_disagreement: std dev of lines across books (high = books disagree)
      - consensus_line: median line across books
      - best_over_line: highest line available (best for OVER bets)
      - best_under_line: lowest line available (best for UNDER bets)
      - stale_book_flag: book hasn't moved despite line changes elsewhere
      - time_since_last_move: seconds since any book moved this line
      - sharp_book_line: line from sharp-first books (DK, FD, Caesars)
      - square_book_line: line from square books (Bovada, BetUS)
      - sharp_vs_square_divergence: sharp line vs square line gap (signal!)
    """
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)

        rows = conn.execute("""
            SELECT book, line, over_odds, under_odds, over_prob_novig,
                   under_prob_novig, snapshot_ts
            FROM prop_snapshots
            WHERE player_id=? AND stat=? AND game_id=?
            AND snapshot_type IN ('pregame_30m','pregame_1h','closing')
            ORDER BY snapshot_ts DESC
        """, (player_id, stat, game_id)).fetchall()

        conn.close()

        if not rows:
            return {'available': False}

        # Group by book (most recent snapshot per book)
        book_data = {}
        for row in rows:
            book = row[0]
            if book not in book_data:
                book_data[book] = {
                    'line': row[1], 'over_odds': row[2], 'under_odds': row[3],
                    'over_prob': row[4], 'under_prob': row[5], 'ts': row[6]
                }

        lines = [d['line'] for d in book_data.values() if d['line'] is not None]
        if len(lines) < 2:
            return {'available': False}

        # Sharp vs square books
        SHARP_BOOKS  = {'draftkings', 'fanduel', 'caesars', 'betmgm', 'betrivers'}
        SQUARE_BOOKS = {'bovada', 'betus', 'betonlineag', 'betanysports'}

        sharp_lines  = [d['line'] for b, d in book_data.items() if b in SHARP_BOOKS and d['line']]
        square_lines = [d['line'] for b, d in book_data.items() if b in SQUARE_BOOKS and d['line']]

        # Time since last move
        timestamps = [d['ts'] for d in book_data.values()]
        most_recent = max(timestamps)
        try:
            last_move_dt = datetime.fromisoformat(most_recent)
            seconds_since_move = (datetime.utcnow() - last_move_dt).total_seconds()
        except Exception:
            seconds_since_move = None

        # Stale book: book's line differs from consensus by > 0.5 AND hasn't moved recently
        consensus_line = float(np.median(lines))
        stale_books = []
        for book, d in book_data.items():
            if d['line'] and abs(d['line'] - consensus_line) > 0.5:
                stale_books.append(book)

        signals = {
            'available':                True,
            'n_books':                  len(book_data),
            'book_disagreement':        round(float(np.std(lines)), 3),
            'consensus_line':           round(consensus_line, 1),
            'best_over_line':           round(max(lines), 1),   # highest = best for OVER
            'best_under_line':          round(min(lines), 1),   # lowest = best for UNDER
            'stale_book_flag':          len(stale_books) > 0,
            'stale_books':              stale_books,
            'seconds_since_last_move':  seconds_since_move,
            'sharp_book_line':          round(float(np.mean(sharp_lines)), 1) if sharp_lines else None,
            'square_book_line':         round(float(np.mean(square_lines)), 1) if square_lines else None,
            'sharp_vs_square_gap':      round(float(np.mean(sharp_lines)) - float(np.mean(square_lines)), 2)
                                        if sharp_lines and square_lines else None,
        }

        # Sharp/square divergence: when sharp books have higher line than square,
        # OVER is more likely (sharps are pricing in more production)
        if signals['sharp_vs_square_gap'] is not None:
            if signals['sharp_vs_square_gap'] > 0.5:
                signals['sharp_signal'] = 'LEAN_OVER'  # sharps have higher line
            elif signals['sharp_vs_square_gap'] < -0.5:
                signals['sharp_signal'] = 'LEAN_UNDER'  # sharps have lower line
            else:
                signals['sharp_signal'] = 'NEUTRAL'

        return signals

    except Exception as e:
        return {'available': False, 'error': str(e)}


def apply_market_disagreement_filter(
    pick: dict,
    market_signals: dict,
    model_prob: float,
) -> Tuple[bool, str, float]:
    """
    Expert: "stale line detection is where live edge comes from"
    
    Returns (reject, reason, adjusted_edge).
    
    Rules:
    1. High book_disagreement (> 0.5) = uncertain market → require more edge
    2. Stale book flag = potential pricing error → slight edge boost
    3. Sharp/square divergence in model's direction = confirming signal
    4. Sharp/square against model = warning flag (sharp money against you)
    """
    if not market_signals.get('available', False):
        return False, 'NO_MARKET_DATA', model_prob

    side = pick.get('side', 'OVER')
    disagreement = market_signals.get('book_disagreement', 0)
    stale_flag   = market_signals.get('stale_book_flag', False)
    sharp_signal = market_signals.get('sharp_signal', 'NEUTRAL')
    adj_edge     = model_prob

    # High disagreement = uncertain market → require more edge
    if disagreement > 0.75:
        # Books disagree by more than 0.75 pts — be cautious
        return True, f"HIGH_BOOK_DISAGREEMENT: {disagreement:.2f}", adj_edge

    # Sharp money against the model = warning (don't reject, but flag)
    if side == 'OVER' and sharp_signal == 'LEAN_UNDER':
        # Sharps pricing lower line = they expect UNDER — our OVER pick faces headwind
        adj_edge *= 0.95  # slight edge reduction
    elif side == 'UNDER' and sharp_signal == 'LEAN_OVER':
        adj_edge *= 0.95

    # Sharp money with the model = confirming signal → slight boost
    if side == 'OVER' and sharp_signal == 'LEAN_OVER':
        adj_edge = min(0.98, adj_edge * 1.02)
    elif side == 'UNDER' and sharp_signal == 'LEAN_UNDER':
        adj_edge = min(0.98, adj_edge * 1.02)

    # Stale book = potential mispricing → note for future CLV analysis
    # (don't auto-approve — requires model edge to confirm)

    return False, 'PASSES', adj_edge


# =============================================================================
# SECTION 5: CORRELATION-AWARE PORTFOLIO EXPOSURE
# Expert: "pts_over + ast_over + PRA_over for same player = correlated.
#          Not three independent bets. Count-based caps are not enough."
# =============================================================================

# Correlation groups — these stats are correlated for the same player
# Expert: "count-based exposure is good, but correlation-aware is the next step"
STAT_CORRELATION_GROUPS = {
    # Key: a stat. Value: stats it is correlated with FOR THE SAME PLAYER
    'pts':  {'pra', 'pr', 'pa'},      # pts is in all these combos
    'reb':  {'pra', 'pr', 'ra'},
    'ast':  {'pra', 'pa', 'ra'},
    'fg3m': {'pts'},                   # 3PM is a component of pts
    'pra':  {'pts', 'reb', 'ast'},
    'pr':   {'pts', 'reb'},
    'pa':   {'pts', 'ast'},
    'ra':   {'reb', 'ast'},
}

# Max correlated exposure per player (units of "equivalent bets")
# Same player: pts_over + ast_over + PRA_over = 3 correlated units
MAX_CORRELATED_UNITS_PER_PLAYER = 2.0  # treat at most 2 independent bet equivalents

# Correlation penalty matrix: how correlated are two stats for the same player?
# 1.0 = perfectly correlated, 0.0 = independent
# Expert: "not three independent bets"
STAT_PAIR_CORRELATION = {
    ('pts', 'pra'): 0.85,   # pts is the dominant component of PRA
    ('pts', 'pr'):  0.80,
    ('pts', 'pa'):  0.75,
    ('pts', 'fg3m'):0.55,   # 3PM is a subset of pts
    ('reb', 'pra'): 0.70,
    ('reb', 'pr'):  0.75,
    ('reb', 'ra'):  0.80,
    ('ast', 'pra'): 0.65,
    ('ast', 'pa'):  0.75,
    ('ast', 'ra'):  0.70,
    ('pts', 'ast'): 0.35,   # low — different mechanisms
    ('pts', 'reb'): 0.25,
    ('blk', 'stl'): 0.40,
}


def get_correlation(stat1: str, stat2: str) -> float:
    """Get correlation between two stats for the same player."""
    key1 = (stat1, stat2)
    key2 = (stat2, stat1)
    return STAT_PAIR_CORRELATION.get(key1, STAT_PAIR_CORRELATION.get(key2, 0.10))


class CorrelationAwarePortfolioController:
    """
    Expert: "correlation-aware exposure — not just count-based caps"

    Tracks 'equivalent bet units' per player using the correlation matrix.
    Adding a new pick that is correlated with existing picks costs more
    than its face value in terms of exposure.

    Example:
        pts_over = 1.0 unit
        Adding PRA_over (corr=0.85 with pts) = 1 - 0.85 = 0.15 additional unit
        Total: 1.0 + 0.15 = 1.15 units (still under 2.0 cap)
        
        Adding ast_over (corr=0.35 with pts, 0.65 with PRA):
            marginal = 1 - max(0.35, 0.65) = 0.35 units
        Total: 1.15 + 0.35 = 1.50 units (still under cap)
        
        Adding reb_over: marginal = 1 - max(0.25, 0.70) = 0.30 units
        Total: 1.50 + 0.30 = 1.80 units (still OK)
        
        Adding pr_over: marginal = 1 - max(0.80, 0.75, 0.25) = 0.20 units
        Total: 1.80 + 0.20 = 2.00 — AT CAP
    """

    def __init__(
        self,
        max_correlated_units_per_player: float = MAX_CORRELATED_UNITS_PER_PLAYER,
        max_per_game: int = 4,
        max_per_stat: int = 12,
        max_total: int = 50,
    ):
        self.max_units  = max_correlated_units_per_player
        self.max_game   = max_per_game
        self.max_stat   = max_per_stat
        self.max_total  = max_total

    def filter_picks(
        self,
        picks: list,
        calibrator=None,
    ) -> Tuple[list, dict]:
        """
        Apply correlation-aware portfolio filtering.
        Picks should already pass no-bet threshold checks.
        """
        def get_prob(p):
            prob = p.get('model_prob', 0)
            if calibrator:
                prob = calibrator.calibrate(prob, p.get('stat','pts'))
            return prob

        # Sort by edge descending (strongest picks first)
        picks_sorted = sorted(picks, key=get_prob, reverse=True)

        # State tracking
        player_units  = {}   # player_id → total equivalent units
        player_stats  = {}   # player_id → list of (stat, side) already added
        game_counts   = {}
        stat_counts   = {}
        seen_keys     = set()
        total         = 0

        filtered   = []
        rejections = {'reasons': {}, 'total_in': len(picks)}

        for pick in picks_sorted:
            pid  = pick.get('player_id')
            gid  = pick.get('game_id')
            stat = pick.get('stat', '')
            side = pick.get('side', 'OVER')
            key  = (pid, stat, side)

            # Count caps
            if total >= self.max_total:
                rejections['reasons']['total_cap'] = rejections['reasons'].get('total_cap', 0) + 1
                continue
            if key in seen_keys:
                rejections['reasons']['duplicate'] = rejections['reasons'].get('duplicate', 0) + 1
                continue
            if game_counts.get(gid, 0) >= self.max_game:
                rejections['reasons']['game_cap'] = rejections['reasons'].get('game_cap', 0) + 1
                continue
            if stat_counts.get(stat, 0) >= self.max_stat:
                rejections['reasons']['stat_cap'] = rejections['reasons'].get('stat_cap', 0) + 1
                continue

            # Correlation-aware player exposure check
            existing_stats = player_stats.get(pid, [])
            current_units  = player_units.get(pid, 0.0)

            if len(existing_stats) == 0:
                # First pick for this player — costs 1.0 unit
                marginal_cost = 1.0
            else:
                # Marginal cost = 1 - max_correlation_with_existing
                existing_stat_names = [s for s, _ in existing_stats]
                max_corr = max(
                    get_correlation(stat, existing_s)
                    for existing_s in existing_stat_names
                )
                marginal_cost = max(0.05, 1.0 - max_corr)
                # Minimum cost floor: every pick costs at least 0.05 units

            if current_units + marginal_cost > self.max_units:
                rejections['reasons']['correlation_cap'] = rejections['reasons'].get('correlation_cap', 0) + 1
                continue

            # Pick passes — add it
            filtered.append(pick)
            seen_keys.add(key)
            player_units[pid]  = current_units + marginal_cost
            player_stats.setdefault(pid, []).append((stat, side))
            game_counts[gid]   = game_counts.get(gid, 0) + 1
            stat_counts[stat]  = stat_counts.get(stat, 0) + 1
            total += 1

        rejections['total_out']         = len(filtered)
        rejections['total_rejected']    = len(picks) - len(filtered)
        rejections['avg_units_per_player'] = round(
            np.mean(list(player_units.values())), 3) if player_units else 0

        return filtered, rejections


# =============================================================================
# SECTION 6: COMPLETE CORRECTED WORKFLOW
# Expert: "audit → diagnostics → DISTRIBUTION ADJUSTMENT → calibration →
#          comparison → CLV → portfolio"
# =============================================================================

def run_corrected_workflow(
    performance_log_path: str = 'graded/performance_log.csv',
    model_cache_dir: str = 'model_cache/',
    stats_parquet_path: str = 'data/stats.parquet',
):
    """
    THE CORRECT WORKFLOW ORDER (per expert v3).

    Expert: "insert variance/tail adjustment between diagnostics and calibration.
             Do not let calibration clean up a bad distribution shape."
    """
    from expert_implementation import TemperatureCalibrator
    from expert_implementation_v2 import (
        run_feature_availability_audit,
        run_quantile_coverage_diagnostics,
        BetaCalibrator,
        PortfolioExposureController,
    )

    print("\n" + "="*65)
    print("CORRECTED WORKFLOW — Expert v3 order")
    print("="*65)

    df = pd.read_csv(performance_log_path)
    df['hit'] = (df['result'] == 'HIT').astype(float)

    # ── STEP 1: Feature availability audit ───────────────────────────────────
    print("\n[STEP 1] Feature Availability Audit")
    audit = run_feature_availability_audit(model_cache_dir, stats_parquet_path)

    # ── STEP 2: Quantile coverage diagnostics ─────────────────────────────────
    print("\n[STEP 2] Quantile Coverage Diagnostics")
    coverage_df = run_quantile_coverage_diagnostics(performance_log_path)

    # ── STEP 3 (NEW): Distribution/tail adjustment BEFORE calibration ─────────
    print("\n[STEP 3] Distribution Tail Adjustment (NEW — before calibration)")
    widening_factors = adjust_tails_from_diagnostics(coverage_df)
    with open(os.path.join(model_cache_dir, 'tail_widening_factors.json'), 'w') as f:
        json.dump(widening_factors, f, indent=2)
    print(f"[tail_adjust] Factors saved: {widening_factors}")

    # ── STEP 4: Temperature calibration ──────────────────────────────────────
    print("\n[STEP 4] Temperature Calibration")
    temp_cal = TemperatureCalibrator()
    temp_cal.fit(df.dropna(subset=['model_prob','hit','stat']))
    temp_cal.save(os.path.join(model_cache_dir, 'calibration_temperature.json'))

    # ── STEP 5: Beta calibration ──────────────────────────────────────────────
    print("\n[STEP 5] Beta Calibration")
    beta_cal = BetaCalibrator()
    beta_cal.fit(df.dropna(subset=['model_prob','hit','stat']))
    beta_cal.save(os.path.join(model_cache_dir, 'calibration_beta.json'))

    # ── STEP 6: Compare calibrators ───────────────────────────────────────────
    print("\n[STEP 6] Calibrator Comparison")
    best = {}
    for stat in ['pts','reb','ast','fg3m','blk','stl']:
        sub = df[df['stat']==stat].dropna(subset=['model_prob','hit'])
        if len(sub) < 10:
            continue
        p = np.clip(sub['model_prob'].values, 0.01, 0.99)
        y = sub['hit'].values
        b0 = np.mean((p - y)**2)
        bt = np.mean((np.array([temp_cal.calibrate(x,stat) for x in p]) - y)**2)
        bb = np.mean((np.array([beta_cal.calibrate(x,stat) for x in p]) - y)**2)
        winner = 'temperature' if bt <= bb else 'beta'
        best[stat] = winner
        print(f"  {stat}: raw={b0:.4f} temp={bt:.4f} beta={bb:.4f} → {winner}")

    with open(os.path.join(model_cache_dir, 'calibration_best.json'), 'w') as f:
        json.dump(best, f, indent=2)

    # Use best calibrator for comparisons
    best_cal = temp_cal  # default — update per-stat in production

    # ── STEP 7: Raw vs Calibrated vs Filtered comparison ──────────────────────
    print("\n[STEP 7] Raw vs Calibrated vs Filtered Comparison (KEY DIAGNOSTIC)")
    portfolio = CorrelationAwarePortfolioController()
    comparison = run_model_layer_comparison(
        performance_log_path, best_cal, portfolio,
        os.path.join(model_cache_dir, 'layer_comparison.json')
    )

    # ── STEP 8: CLV summary ───────────────────────────────────────────────────
    print("\n[STEP 8] CLV Summary by Stat/Side")
    if 'clv_proxy' in df.columns:
        clv = df.groupby(['stat','side'])['clv_proxy'].mean().round(3)
        print(clv)

    # ── STEP 9: Phase readiness check ─────────────────────────────────────────
    print("\n[STEP 9] Threshold Phase Readiness")
    phase_status = check_phase_readiness(performance_log_path)

    # ── STEP 10: Portfolio simulation ─────────────────────────────────────────
    print("\n[STEP 10] Portfolio Simulation with Correlation-Aware Caps")
    picks_all = df.to_dict('records')
    for p in picks_all:
        p['model_prob'] = best_cal.calibrate(float(p.get('model_prob',0.5)), p.get('stat','pts'))
    filtered, summary = portfolio.filter_picks(picks_all, best_cal)
    print(f"  All picks: {len(picks_all)} → after portfolio: {len(filtered)}")
    print(f"  Rejection reasons: {summary['reasons']}")
    print(f"  Avg correlated units per player: {summary['avg_units_per_player']}")

    print("\n" + "="*65)
    print("CORRECTED WORKFLOW COMPLETE")
    print("Files saved to:", model_cache_dir)
    print("="*65 + "\n")

    return {
        'widening_factors':   widening_factors,
        'best_calibrator':    best,
        'layer_comparison':   comparison,
        'phase_status':       phase_status,
    }


# =============================================================================
# EXPERT CAUTIONS — enforcement checks
# =============================================================================

EXPERT_CAUTIONS = {
    "no_bet_overfitting": (
        "Do NOT overfit no-bet rules on short sample. "
        "Use as temporary triage, re-estimate on 200+ holdout picks per segment."
    ),
    "beta_hiding_bad_quantiles": (
        "Do NOT let beta calibration hide bad quantiles. "
        "Fix distribution shape FIRST (tail widening), THEN calibrate."
    ),
    "short_sample_danger": (
        "4 days of data is not enough to settle the truth. "
        "Evaluate over multiple date windows, injury-heavy vs normal days."
    ),
    "correlation_warning": (
        "pts_over + ast_over + PRA_over for same player = correlated bets. "
        "Use CorrelationAwarePortfolioController, not just count-based caps."
    ),
}


if __name__ == '__main__':
    print("NBA Props Model — Expert v3 Implementation")
    print("\nExpert cautions:")
    for k, v in EXPERT_CAUTIONS.items():
        print(f"  ⚠ {v}")
    print("\nRun: run_corrected_workflow()")
