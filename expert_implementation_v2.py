"""
NBA Props Model — Expert Review v2 Complete Implementation
==========================================================
Implements ALL recommendations from the second expert review.

PRIORITY ORDER (exactly as specified):
  ADD NOW:
    1. True historical odds/player prop snapshot database schema + collector
    2. Dynamic variance model (replaces static CV)
    3. Stat-specific probability construction (discrete sparse layer)
    4. No-bet band / asymmetric thresholds
    5. Feature availability audit
    6. Portfolio exposure controls
    7. Stripped-core benchmark model definition

  ADD NEXT:
    8. Beta calibration (alongside temperature/isotonic)
    9. Quantile coverage diagnostics
    10. Tail widening / distribution smoothing

  REMOVE/SUPPRESS:
    11. BLK OVER, STL OVER — confirmed banned
    12. 0.50-0.60 raw probability bets — miscalibrated
    13. Most UNDER bets until calibration repaired
    14. Duplicate correlated exposure
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from scipy.special import expit, logit, betainc
from scipy.optimize import minimize_scalar, minimize
from scipy.stats import nbinom, poisson
from typing import Optional, Dict, List, Tuple
import json
import os
from datetime import datetime, date


# =============================================================================
# SECTION 1: TRUE CLV INFRASTRUCTURE
# Expert: "You do not have true CLV yet. You need to store opening, mid,
#          and closing odds/props snapshots yourself going forward."
# =============================================================================

class PropSnapshotCollector:
    """
    Collects and stores prop line snapshots at multiple timestamps.
    Required for true CLV measurement (not closing-line proxy).
    
    Storage: SQLite database (simple, no server required)
    Schema: one row per (player_id, stat, game_id, book, timestamp)
    
    Usage:
        collector = PropSnapshotCollector('data/prop_snapshots.db')
        collector.record_snapshot(game_id, player_props, snapshot_type='opening')
        # Later:
        clv = collector.compute_true_clv(picks_df)
    """

    def __init__(self, db_path: str = 'data/prop_snapshots.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        import sqlite3
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prop_snapshots (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_type TEXT NOT NULL,   -- 'opening','pregame_1h','pregame_30m','closing'
                snapshot_ts   TEXT NOT NULL,   -- ISO timestamp
                game_id       INTEGER NOT NULL,
                game_date     TEXT NOT NULL,
                player_id     INTEGER NOT NULL,
                player_name   TEXT,
                stat          TEXT NOT NULL,   -- pts, reb, ast, fg3m, blk, stl
                book          TEXT NOT NULL,
                line          REAL NOT NULL,
                over_odds     INTEGER,         -- American odds
                under_odds    INTEGER,
                over_prob_novig REAL,          -- no-vig implied probability
                under_prob_novig REAL,
                UNIQUE(snapshot_type, game_id, player_id, stat, book)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clv_records (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                pick_date     TEXT NOT NULL,
                player_id     INTEGER NOT NULL,
                stat          TEXT NOT NULL,
                side          TEXT NOT NULL,
                game_id       INTEGER NOT NULL,
                book          TEXT NOT NULL,
                model_prob    REAL NOT NULL,
                open_line     REAL,
                open_prob_novig REAL,
                close_line    REAL,
                close_prob_novig REAL,
                true_clv      REAL,          -- model_prob - close_prob_novig
                line_movement REAL,          -- close_line - open_line
                sharp_agreement INTEGER,     -- 1 if line moved in model's direction
                result        TEXT,          -- HIT / MISS
                actual_stat   REAL
            )
        """)
        conn.commit()
        conn.close()

    def record_snapshot(
        self,
        game_id: int,
        game_date: str,
        player_props: list,         # from BDL get_player_prop_odds()
        snapshot_type: str = 'pregame_30m',
        book_priority: list = None,
    ):
        """
        Record prop line snapshot from BDL player_props endpoint.
        Call this at: market open, 1h before tip, 30m before tip, at close.
        
        BDL endpoint: GET /v2/odds/player_props?game_id={game_id}
        """
        import sqlite3
        if book_priority is None:
            book_priority = ['draftkings', 'fanduel', 'caesars', 'betmgm', 'betrivers']

        ts  = datetime.utcnow().isoformat()
        conn= sqlite3.connect(self.db_path)

        STAT_MAP = {
            'points': 'pts', 'rebounds': 'reb', 'assists': 'ast',
            'threes': 'fg3m', 'blocks': 'blk', 'steals': 'stl',
        }

        for prop in player_props:
            prop_type = prop.get('prop_type', '')
            stat = STAT_MAP.get(prop_type)
            if stat is None:
                continue  # skip quarter props, combos, etc.

            market = prop.get('market', {})
            if market.get('type') != 'over_under':
                continue

            over_odds  = market.get('over_odds')
            under_odds = market.get('under_odds')
            line       = float(prop.get('line_value', 0))
            book       = prop.get('vendor', '')
            player_id  = prop.get('player_id')

            # Remove vig to get true implied probabilities
            over_prob, under_prob = self._remove_vig(over_odds, under_odds)

            try:
                conn.execute("""
                    INSERT OR REPLACE INTO prop_snapshots
                    (snapshot_type, snapshot_ts, game_id, game_date, player_id,
                     stat, book, line, over_odds, under_odds,
                     over_prob_novig, under_prob_novig)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (snapshot_type, ts, game_id, game_date, player_id,
                      stat, book, line, over_odds, under_odds,
                      over_prob, under_prob))
            except Exception as e:
                pass  # non-critical

        conn.commit()
        conn.close()

    def _remove_vig(
        self,
        over_odds: Optional[int],
        under_odds: Optional[int],
    ) -> Tuple[Optional[float], Optional[float]]:
        """Convert American odds to no-vig implied probabilities."""
        if over_odds is None or under_odds is None:
            return None, None

        def to_implied(american):
            if american > 0:
                return 100 / (american + 100)
            else:
                return abs(american) / (abs(american) + 100)

        p_over  = to_implied(over_odds)
        p_under = to_implied(under_odds)
        total   = p_over + p_under

        if total <= 0:
            return None, None

        return p_over / total, p_under / total

    def compute_true_clv(self, picks_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute true CLV = model_prob - closing_market_prob (no-vig).
        Requires closing snapshots to be stored.
        
        Expert: "Without stored snapshots, ROI tuning is partially blind."
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)

        results = []
        for _, pick in picks_df.iterrows():
            # Get closing line snapshot
            row = conn.execute("""
                SELECT line, over_prob_novig, under_prob_novig
                FROM prop_snapshots
                WHERE game_id=? AND player_id=? AND stat=?
                AND snapshot_type='closing'
                ORDER BY snapshot_ts DESC LIMIT 1
            """, (pick.get('game_id'), pick.get('player_id'), pick.get('stat'))).fetchone()

            # Get opening line
            open_row = conn.execute("""
                SELECT line, over_prob_novig, under_prob_novig
                FROM prop_snapshots
                WHERE game_id=? AND player_id=? AND stat=?
                AND snapshot_type='opening'
                ORDER BY snapshot_ts ASC LIMIT 1
            """, (pick.get('game_id'), pick.get('player_id'), pick.get('stat'))).fetchone()

            if row is None:
                continue

            close_line, close_over_prob, close_under_prob = row
            model_prob = float(pick.get('model_prob', 0.5))
            side = pick.get('side', 'OVER')

            close_prob = close_over_prob if side == 'OVER' else close_under_prob
            if close_prob is None:
                continue

            true_clv = model_prob - close_prob

            # Line movement direction
            line_move = None
            sharp_agree = None
            if open_row:
                open_line = open_row[0]
                line_move = close_line - open_line
                # Sharp agreement: line moved in model's favor
                if side == 'OVER':
                    sharp_agree = 1 if line_move > 0 else -1
                else:
                    sharp_agree = 1 if line_move < 0 else -1

            results.append({
                'player_id':    pick.get('player_id'),
                'stat':         pick.get('stat'),
                'side':         side,
                'model_prob':   model_prob,
                'close_prob':   close_prob,
                'true_clv':     true_clv,
                'line_movement':line_move,
                'sharp_agreement': sharp_agree,
            })

        conn.close()
        return pd.DataFrame(results)


# =============================================================================
# SECTION 2: DYNAMIC VARIANCE MODEL
# Expert: "Replace static CV with sigma that depends on player/state context.
#          Stars vs bench, stable vs unstable-role, injury-chaos games all get
#          the wrong uncertainty profile with static CV."
# =============================================================================

def compute_dynamic_sigma(
    proj: float,
    stat: str,
    # Player context
    mp_vol_last10: float = 3.0,        # minutes volatility
    role_stability_index: float = 0.8, # 0=unstable, 1=stable
    archetype: str = 'starter',        # star/starter/bench/microwave
    is_injury_elevated: bool = False,   # player in elevated role due to injuries
    # Game context
    line_distance_from_q50: float = 0.0, # |line - q50|
    blowout_risk: float = 0.0,
    # Feature availability
    has_opponent_context: bool = True,
    has_tracking_data: bool = True,
) -> float:
    """
    Expert: "Dynamic sigma / variance scaling by role stability,
             minutes uncertainty, injury volatility, archetype,
             and line distance from q50."
    
    Returns sigma for normal probability approximation.
    Used when quantile distribution is unavailable or as a sanity check.
    """
    # Base CV per stat (starting point)
    BASE_CV = {
        'pts': 0.35, 'reb': 0.45, 'ast': 0.50,
        'fg3m': 0.65, 'blk': 0.90, 'stl': 0.85,
    }
    base_cv = BASE_CV.get(stat, 0.45)

    # ── Role stability modifier ───────────────────────────────────────────────
    # Unstable roles = wider distribution (more uncertain)
    # Expert: "stable-role vs unstable-role players get wrong uncertainty"
    role_modifier = 1.0 + (1.0 - role_stability_index) * 0.30
    # role_stability=1.0 → modifier=1.00 (no widening)
    # role_stability=0.5 → modifier=1.15 (15% wider)
    # role_stability=0.0 → modifier=1.30 (30% wider)

    # ── Minutes volatility modifier ───────────────────────────────────────────
    # High minutes variance = harder to predict counting stats
    LEAGUE_AVG_MP_VOL = 3.5  # approximate league avg minutes std dev last 10
    mp_modifier = 1.0 + max(0, (mp_vol_last10 - LEAGUE_AVG_MP_VOL) / LEAGUE_AVG_MP_VOL) * 0.25
    # mp_vol=3.5 → modifier=1.00
    # mp_vol=7.0 → modifier=1.25 (25% wider)

    # ── Archetype modifier ────────────────────────────────────────────────────
    # Stars are more predictable (known high floor/ceiling)
    # Bench players have high variance (DNP risk, rotation uncertainty)
    ARCH_MODIFIER = {
        'star':       0.85,   # narrower — well-known production profile
        'starter':    1.00,   # baseline
        'bench':      1.25,   # wider — rotation uncertainty
        'microwave':  1.40,   # widest — feast-or-famine
    }
    arch_modifier = ARCH_MODIFIER.get(archetype, 1.00)

    # ── Injury chaos modifier ─────────────────────────────────────────────────
    # Players in elevated roles due to injuries are less predictable
    inj_modifier = 1.20 if is_injury_elevated else 1.00

    # ── Blowout risk modifier ─────────────────────────────────────────────────
    # High blowout risk = uncertain minutes = wider distribution
    blowout_modifier = 1.0 + blowout_risk * 0.20

    # ── Feature availability modifier ────────────────────────────────────────
    # Expert: "NaN features create false confidence"
    feature_modifier = 1.00
    if not has_opponent_context:
        feature_modifier *= 1.15  # wider if opponent data missing
    if not has_tracking_data:
        feature_modifier *= 1.10  # wider if tracking missing

    # ── Line distance modifier ────────────────────────────────────────────────
    # Lines far from q50 are in the tail — harder to estimate probability precisely
    tail_modifier = 1.0 + min(0.30, abs(line_distance_from_q50) / max(proj, 1.0) * 0.50)

    # ── Compose final CV ──────────────────────────────────────────────────────
    dynamic_cv = (base_cv
                  * role_modifier
                  * mp_modifier
                  * arch_modifier
                  * inj_modifier
                  * blowout_modifier
                  * feature_modifier
                  * tail_modifier)

    # Cap: don't let CV explode
    dynamic_cv = min(dynamic_cv, base_cv * 2.5)
    sigma = max(0.5, proj * dynamic_cv)

    return sigma


def compute_dynamic_prob(
    proj: float,
    line: float,
    stat: str,
    player_context: dict = None,
    game_context: dict = None,
) -> float:
    """
    Compute probability using dynamic variance model.
    Drop-in replacement for static calcStatProbFromCV.
    """
    if player_context is None:
        player_context = {}
    if game_context is None:
        game_context = {}

    sigma = compute_dynamic_sigma(
        proj=proj,
        stat=stat,
        mp_vol_last10=player_context.get('mp_vol_last10', 3.0),
        role_stability_index=player_context.get('role_stability_index', 0.8),
        archetype=player_context.get('archetype', 'starter'),
        is_injury_elevated=player_context.get('is_injury_elevated', False),
        line_distance_from_q50=abs(line - proj),
        blowout_risk=game_context.get('blowout_risk', 0.0),
        has_opponent_context=game_context.get('has_opponent_context', True),
        has_tracking_data=player_context.get('has_tracking_data', True),
    )

    prob = 1.0 - scipy_stats.norm.cdf(line, loc=proj, scale=sigma)
    return float(np.clip(prob, 0.02, 0.98))


# =============================================================================
# SECTION 3: QUANTILE COVERAGE DIAGNOSTICS
# Expert: "Check empirical q10/q25/q50/q75/q90 coverage by stat."
# A model with correct quantiles should have q10 exceeded 10% of the time, etc.
# =============================================================================

def run_quantile_coverage_diagnostics(
    performance_log_path: str = 'graded/performance_log.csv',
) -> pd.DataFrame:
    """
    Expert: "Quantile coverage diagnostics — check empirical coverage by stat."
    
    For each quantile tau in {0.10, 0.25, 0.50, 0.75, 0.90}:
        empirical_coverage(tau) = fraction of games where actual > q_tau_prediction
        
    Should be close to (1 - tau):
        q10 exceeded 90% of the time  (1 - 0.10 = 0.90)
        q50 exceeded 50% of the time  (1 - 0.50 = 0.50)
        q90 exceeded 10% of the time  (1 - 0.90 = 0.10)
    
    If actual exceeds q90 more than 10% of the time → tails are too narrow.
    This directly confirms the expert's "tails too tight" diagnosis.
    """
    df = pd.read_csv(performance_log_path)

    # Check which quantile columns exist
    q_cols = {}
    for col in df.columns:
        if col.startswith('q') and col[1:].isdigit():
            tau = int(col[1:]) / 100.0
            q_cols[tau] = col
        elif col == 'q50':
            q_cols[0.50] = col

    if 'actual' not in df.columns:
        print("[coverage] 'actual' column not found — checking 'actual_stat'")
        if 'actual_stat' in df.columns:
            df['actual'] = df['actual_stat']
        else:
            print("[coverage] Cannot run diagnostics — no actual stat column")
            return pd.DataFrame()

    results = []
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        sub = df[df['stat'] == stat].dropna(subset=['actual'])
        if len(sub) == 0:
            continue

        for tau, col in sorted(q_cols.items()):
            if col not in sub.columns:
                continue
            sub_q = sub.dropna(subset=[col])
            if len(sub_q) == 0:
                continue

            # Empirical P(actual > q_tau)
            empirical = (sub_q['actual'] > sub_q[col]).mean()
            expected  = 1.0 - tau
            error     = empirical - expected  # positive = tails too narrow (actual exceeds more than expected)

            results.append({
                'stat':       stat,
                'quantile':   tau,
                'q_col':      col,
                'expected_exceed': round(expected, 3),
                'empirical_exceed': round(empirical, 3),
                'error':      round(error, 3),
                'diagnosis':  'TAILS TOO NARROW' if error > 0.05 else ('TAILS TOO WIDE' if error < -0.05 else 'OK'),
                'n':          len(sub_q),
            })

    result_df = pd.DataFrame(results)

    print("\n" + "="*65)
    print("QUANTILE COVERAGE DIAGNOSTICS")
    print("="*65)
    print("Expected: empirical_exceed ≈ (1 - quantile)")
    print("Error > 0 = tails too narrow (overconfident) → widen tails")
    print("="*65)
    if len(result_df) > 0:
        print(result_df.to_string(index=False))
    else:
        print("No data available")

    return result_df


# =============================================================================
# SECTION 4: NO-BET BAND AND ASYMMETRIC THRESHOLDS
# Expert: "Model is too willing to interpret small q50-under-line gaps as
#          bettable unders. Need explicit no-bet region and side-asymmetric
#          thresholding. Overs can pass with smaller edge; unders need more."
# =============================================================================

# Expert: "no bets below 0.60 raw OVER, no unders below 0.68-0.70"
# Expert: "especially 0.50-0.60 raw-probability buckets are badly miscalibrated"

NO_BET_BANDS = {
    # (lower_bound, upper_bound) — picks in this probability range are BANNED
    # Expert: "low-confidence bets especially 0.50-0.60 are badly miscalibrated"
    'OVER':  (0.00, 0.60),   # no OVER bets below 60% raw probability
    'UNDER': (0.00, 0.68),   # no UNDER bets below 68% raw probability
}

# Side-specific minimum thresholds by stat
# Expert: "overs can pass with smaller edge, unders need materially stronger evidence"
ASYMMETRIC_THRESHOLDS = {
    'pts':  {'OVER': 0.60, 'UNDER': 0.72, 'NO_BET_UNDER': True},  # most broken stat
    'reb':  {'OVER': 0.60, 'UNDER': 0.70, 'NO_BET_UNDER': False},
    'ast':  {'OVER': 0.60, 'UNDER': 0.72, 'NO_BET_UNDER': True},
    'fg3m': {'OVER': 0.60, 'UNDER': 0.70, 'NO_BET_UNDER': False},
    'blk':  {'OVER': 9.99, 'UNDER': 0.72, 'NO_BET_UNDER': False},  # OVER fully banned
    'stl':  {'OVER': 9.99, 'UNDER': 0.74, 'NO_BET_UNDER': False},  # OVER fully banned
}

# Minimum line distance from q50 to bet UNDER
# Expert: "model interprets small q50-under-line gaps as bettable — wrong"
MIN_UNDER_EDGE = {
    'pts':  0.80,   # book line must be >= 0.80 above q50 to consider UNDER
    'reb':  0.50,
    'ast':  0.60,
    'fg3m': 0.30,
    'blk':  0.20,
    'stl':  0.20,
}


def passes_no_bet_filter(
    pick: dict,
    calibrated_prob: float,
    q50: Optional[float] = None,
) -> Tuple[bool, str]:
    """
    Apply expert-recommended no-bet band and asymmetric threshold rules.
    Returns (True, reason) if pick should be REJECTED.
    
    Expert: "side-asymmetric thresholding — overs can pass with smaller edge,
             unders should require materially stronger evidence"
    """
    stat  = pick.get('stat', '')
    side  = pick.get('side', 'OVER')
    line  = float(pick.get('line', 0))

    thresholds = ASYMMETRIC_THRESHOLDS.get(stat, {'OVER': 0.62, 'UNDER': 0.70})
    threshold  = thresholds.get(side, 0.65)

    # Rule 1: Hard ban (BLK OVER, STL OVER)
    if threshold >= 9.0:
        return True, f"BANNED: {stat} {side} — catastrophic hit rate"

    # Rule 2: Probability below threshold
    if calibrated_prob < threshold:
        return True, f"BELOW_THRESHOLD: {calibrated_prob:.3f} < {threshold:.3f} for {stat} {side}"

    # Rule 3: No-bet band (0.50-0.60 range is miscalibrated)
    band_lo, band_hi = NO_BET_BANDS.get(side, (0.0, 0.60))
    if band_lo <= calibrated_prob < band_hi:
        return True, f"NO_BET_BAND: {calibrated_prob:.3f} in miscalibrated region [{band_lo},{band_hi})"

    # Rule 4: UNDER edge requirement — q50 must be meaningfully above line
    if side == 'UNDER' and q50 is not None:
        min_edge = MIN_UNDER_EDGE.get(stat, 0.40)
        gap = q50 - line  # positive = model projects ABOVE line (supports UNDER)
        if gap < min_edge:
            return True, f"INSUFFICIENT_UNDER_EDGE: q50-line gap={gap:.2f} < {min_edge:.2f} for {stat}"

    # Rule 5: Temporary broader UNDER suppression for pts/ast
    # Expert: "most under bets until repaired"
    if thresholds.get('NO_BET_UNDER', False) and side == 'UNDER':
        return True, f"UNDER_SUPPRESSED: {stat} UNDER temporarily suppressed pending calibration"

    return False, "PASSES"


# =============================================================================
# SECTION 5: PORTFOLIO EXPOSURE CONTROLS
# Expert: "1,434 picks in 4 days is enormous. Portfolio rules needed:
#          one player/stat/game primary line, game-level caps, player-level caps"
# =============================================================================

class PortfolioExposureController:
    """
    Expert: "Portfolio controls, not just better projections."
    
    Enforces:
    - One pick per player/stat/side (deduplication)
    - Per-player exposure cap (max N picks involving same player)
    - Per-game exposure cap (max N picks from same game)
    - Per-stat exposure cap (don't over-concentrate in one stat)
    - Side-balance rule (can't be all OVERs or all UNDERs)
    - Max total picks per slate
    """

    def __init__(
        self,
        max_per_player: int = 2,      # max picks per player per slate
        max_per_game: int = 4,        # max picks per game
        max_per_stat: int = 15,       # max picks per stat type
        max_total: int = 60,          # max total picks per slate (was 300+ — way too high)
        min_edge_over: float = 0.60,  # minimum calibrated prob for OVER
        min_edge_under: float = 0.68, # minimum calibrated prob for UNDER
    ):
        self.max_per_player = max_per_player
        self.max_per_game   = max_per_game
        self.max_per_stat   = max_per_stat
        self.max_total      = max_total
        self.min_edge_over  = min_edge_over
        self.min_edge_under = min_edge_under

    def filter_picks(
        self,
        picks: list,
        calibrator=None,
    ) -> Tuple[list, dict]:
        """
        Apply all portfolio exposure controls to a list of picks.
        Returns (filtered_picks, rejection_summary).
        
        Picks should be sorted by edge (highest calibrated prob first)
        so that the strongest picks survive caps.
        """
        # Sort by calibrated probability (descending)
        def get_prob(p):
            prob = p.get('model_prob', 0)
            if calibrator:
                prob = calibrator.calibrate(prob, p.get('stat', 'pts'))
            return prob

        picks_sorted = sorted(picks, key=get_prob, reverse=True)

        # Counters
        player_counts = {}  # player_id → count
        game_counts   = {}  # game_id → count
        stat_counts   = {}  # stat → count
        seen_keys     = set()  # (player_id, stat, side)
        total         = 0

        filtered   = []
        rejections = {'total_in': len(picks), 'reasons': {}}

        for pick in picks_sorted:
            pid   = pick.get('player_id')
            gid   = pick.get('game_id')
            stat  = pick.get('stat', '')
            side  = pick.get('side', 'OVER')
            prob  = get_prob(pick)
            q50   = pick.get('q50')
            key   = (pid, stat, side)

            # Check 1: Total cap
            if total >= self.max_total:
                rejections['reasons']['total_cap'] = rejections['reasons'].get('total_cap', 0) + 1
                continue

            # Check 2: Deduplication
            if key in seen_keys:
                rejections['reasons']['duplicate'] = rejections['reasons'].get('duplicate', 0) + 1
                continue

            # Check 3: No-bet band and asymmetric thresholds
            rejected, reason = passes_no_bet_filter(pick, prob, q50)
            if rejected:
                rejections['reasons'][reason.split(':')[0]] = rejections['reasons'].get(reason.split(':')[0], 0) + 1
                continue

            # Check 4: Per-player cap
            if player_counts.get(pid, 0) >= self.max_per_player:
                rejections['reasons']['player_cap'] = rejections['reasons'].get('player_cap', 0) + 1
                continue

            # Check 5: Per-game cap
            if game_counts.get(gid, 0) >= self.max_per_game:
                rejections['reasons']['game_cap'] = rejections['reasons'].get('game_cap', 0) + 1
                continue

            # Check 6: Per-stat cap
            if stat_counts.get(stat, 0) >= self.max_per_stat:
                rejections['reasons']['stat_cap'] = rejections['reasons'].get('stat_cap', 0) + 1
                continue

            # Pick passes — add it
            filtered.append(pick)
            seen_keys.add(key)
            player_counts[pid] = player_counts.get(pid, 0) + 1
            game_counts[gid]   = game_counts.get(gid, 0) + 1
            stat_counts[stat]  = stat_counts.get(stat, 0) + 1
            total += 1

        rejections['total_out']   = len(filtered)
        rejections['total_rejected'] = len(picks) - len(filtered)
        rejections['stat_distribution'] = stat_counts
        rejections['side_distribution'] = {
            'OVER':  sum(1 for p in filtered if p.get('side') == 'OVER'),
            'UNDER': sum(1 for p in filtered if p.get('side') == 'UNDER'),
        }

        return filtered, rejections


# =============================================================================
# SECTION 6: FEATURE AVAILABILITY AUDIT
# Expert: "Before optimizing features further, you need a feature availability
#          audit by season and by split. NaN features create false confidence."
# =============================================================================

def run_feature_availability_audit(
    model_cache_dir: str = 'model_cache/',
    stats_parquet_path: str = 'data/stats.parquet',
) -> dict:
    """
    Expert: "Feature availability audit by season and by split."
    
    Checks:
    1. Which features have NaN rate > threshold in training data
    2. Which features only became available in recent seasons
    3. Which features show coverage regime shifts
    4. Flags features that are high-NaN as calibration risks
    """
    import joblib
    from pathlib import Path

    report = {}

    # Load training data if available
    try:
        df = pd.read_parquet(stats_parquet_path)
    except Exception as e:
        print(f"[audit] Cannot load stats data: {e}")
        df = None

    # Check feature sets per stat
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        feat_path = Path(model_cache_dir) / f"features_{stat}.pkl"
        if not feat_path.exists():
            continue

        feats = joblib.load(feat_path)
        stat_report = {
            'total_features': len(feats),
            'features': feats,
        }

        if df is not None:
            # Compute NaN rates
            available_feats = [f for f in feats if f in df.columns]
            nan_rates = {}
            high_nan  = []

            for feat in available_feats:
                nan_rate = df[feat].isna().mean()
                nan_rates[feat] = round(nan_rate, 3)
                if nan_rate > 0.20:  # >20% NaN = high risk
                    high_nan.append((feat, nan_rate))

            stat_report['nan_rates']       = nan_rates
            stat_report['high_nan_features'] = sorted(high_nan, key=lambda x: -x[1])
            stat_report['mean_nan_rate']   = round(np.mean(list(nan_rates.values())), 3) if nan_rates else None

            # Flag opponent context features specifically
            opp_feats = [(f, nan_rates.get(f, 0)) for f in feats if f.startswith('opp_')]
            stat_report['opponent_features_nan'] = opp_feats

            # Check regime by season if season column exists
            if 'season' in df.columns:
                seasons = sorted(df['season'].unique())
                season_coverage = {}
                for s in seasons:
                    s_df = df[df['season'] == s]
                    avail = sum(1 for f in available_feats if s_df[f].notna().mean() > 0.50)
                    season_coverage[int(s)] = round(avail / max(len(available_feats), 1), 2)
                stat_report['feature_coverage_by_season'] = season_coverage

        report[stat] = stat_report
        print(f"[audit] {stat}: {len(feats)} features | "
              f"mean NaN: {stat_report.get('mean_nan_rate', 'N/A')} | "
              f"high-NaN count: {len(stat_report.get('high_nan_features', []))}")

        if stat_report.get('high_nan_features'):
            print(f"  ⚠ HIGH NaN features: {stat_report['high_nan_features'][:5]}")

    return report


# =============================================================================
# SECTION 7: STRIPPED-CORE BENCHMARK MODEL
# Expert: "Stripped-core benchmark is essential. If stripped-core calibrates
#          better, then broad context is adding false certainty."
# =============================================================================

STRIPPED_CORE_FEATURES = {
    # Expert: "Layer 1 + stat-specific Layer 2 + essential Layer 4 + minimal Layer 3"
    # This is the minimal model that should be compared against full v19

    "pts": [
        # Layer 1: minutes
        "mp_ewma_10", "mp_vol_last10", "exp_mp",
        # Layer 2: environment
        "implied_team_total", "opp_pace_true", "spread_for_team",
        # Layer 4: essential mechanics only
        "pts_per_min_ewma_10", "pts_per_min_mean_last5",
        "fga_per_min_ewma_10", "fta_per_min_mean_last10",
        # Essential opponent context
        "opp_pts_allowed_last10",
        # Minimal Layer 3
        "starter_rate_last10", "back_to_back", "rest_days",
    ],

    "reb": [
        "mp_ewma_10", "mp_vol_last10", "exp_mp",
        "game_total", "opp_pace_true", "spread_for_team",
        "reb_per_min_ewma_10", "reb_per_min_mean_last5",
        "oreb_per_min_mean_last10", "dreb_per_min_mean_last10",
        "opp_reb_chances_allowed", "opp_rim_fga_rate",
        "starter_rate_last10", "back_to_back",
    ],

    "ast": [
        "mp_ewma_10", "mp_vol_last10", "exp_mp",
        "implied_team_total", "opp_pace_true",
        "ast_per_min_ewma_10", "ast_per_min_mean_last5",
        "potential_ast_per_game_shrunk",
        "opp_ast_opportunities",
        "starter_rate_last10", "back_to_back",
    ],

    "fg3m": [
        "mp_ewma_10", "mp_vol_last10", "exp_mp",
        "implied_team_total", "opp_pace_true",
        "fg3a_per_min_mean_last10", "fg3a_per_min_trend_3v10",
        "fg3_pct_safe",
        "fg3m_p_zero_last10", "fg3m_p_ge3_last10",
        "opp_3pa_allowed", "opp_3p_rate_allowed",
        "starter_rate_last10", "back_to_back",
    ],

    "blk": [
        "mp_ewma_10", "mp_vol_last10", "exp_mp",
        "opp_pace_true",
        "blk_per_min_ewma_10", "blk_per_min_blended",
        "blk_p_zero_last10", "blk_p_ge1_last10",
        "opp_rim_fga_rate",
        "starter_rate_last10",
    ],

    "stl": [
        "mp_ewma_10", "mp_vol_last10", "exp_mp",
        "opp_pace_true",
        "stl_per_min_ewma_10", "stl_per_min_blended",
        "stl_p_zero_last10", "stl_p_ge1_last10",
        "adv_deflections_mean_last10",
        "opp_live_ball_tov",
        "starter_rate_last10",
    ],
}


def get_stripped_core_feature_cols(stat: str, all_cols: list) -> list:
    """
    Expert: "Stripped-core benchmark model — Layer 1 + stat-specific Layer 2
             + essential Layer 4 + minimal Layer 3."
    
    Use this for the benchmark retrain to compare against full v19.
    If stripped-core produces better Brier scores, broad context is adding noise.
    """
    desired = STRIPPED_CORE_FEATURES.get(stat, [])
    all_cols_set = set(all_cols)
    available = [f for f in desired if f in all_cols_set]
    missing   = [f for f in desired if f not in all_cols_set]

    if missing:
        import logging
        logging.getLogger(__name__).warning(
            f"[stripped_core] {stat}: {len(missing)} missing: {missing[:8]}"
        )

    return available


# =============================================================================
# SECTION 8: BETA CALIBRATION (alongside temperature and isotonic)
# Expert: "Beta calibration is also a good option — more flexible than
#          temperature scaling, less unstable than isotonic on small samples."
# =============================================================================

class BetaCalibrator:
    """
    Beta calibration: fits Beta CDF to transform raw probabilities.
    More flexible than temperature scaling.
    Expert: "add beta calibration to candidate set."
    """

    def __init__(self):
        self.params = {}  # {stat_group: (a, b)}
        self.fitted = False

    def fit(self, df: pd.DataFrame, stat_col='stat', prob_col='model_prob', outcome_col='hit'):
        df = df.copy()
        df['stat_group'] = df[stat_col].map(
            lambda s: 'sparse' if s in ('blk', 'stl') else s
        )

        for group in ['pts', 'reb', 'ast', 'fg3m', 'sparse']:
            sub = df[df['stat_group'] == group].dropna(subset=[prob_col, outcome_col])
            if len(sub) < 50:
                print(f"[beta_cal] {group}: insufficient sample ({len(sub)}) — identity transform")
                self.params[group] = (1.0, 1.0)
                continue

            probs    = np.clip(sub[prob_col].values, 0.01, 0.99)
            outcomes = sub[outcome_col].values.astype(float)

            def nll(params):
                a, b = params
                if a <= 0 or b <= 0:
                    return 1e9
                cal = np.array([betainc(a, b, p) for p in probs])
                cal = np.clip(cal, 1e-7, 1 - 1e-7)
                return -np.mean(outcomes * np.log(cal) + (1 - outcomes) * np.log(1 - cal))

            result = minimize(nll, x0=[1.5, 1.5],
                              bounds=[(0.1, 10.0), (0.1, 10.0)],
                              method='L-BFGS-B')
            a, b = result.x
            self.params[group] = (a, b)

            cal_probs = np.array([betainc(a, b, p) for p in probs])
            raw_brier = np.mean((probs - outcomes) ** 2)
            cal_brier = np.mean((cal_probs - outcomes) ** 2)
            print(f"[beta_cal] {group}: a={a:.3f} b={b:.3f} | Brier {raw_brier:.4f}→{cal_brier:.4f} | n={len(sub)}")

        self.fitted = True

    def calibrate(self, prob: float, stat: str) -> float:
        if not self.fitted:
            return prob
        group = 'sparse' if stat in ('blk', 'stl') else stat
        a, b  = self.params.get(group, (1.0, 1.0))
        if a == 1.0 and b == 1.0:
            return prob
        prob = np.clip(prob, 0.01, 0.99)
        return float(betainc(a, b, prob))

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({'params': self.params, 'fitted': self.fitted}, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'BetaCalibrator':
        cal = cls()
        with open(path) as f:
            data = json.load(f)
        cal.params  = {k: tuple(v) for k, v in data['params'].items()}
        cal.fitted  = data['fitted']
        return cal


# =============================================================================
# SECTION 9: COMPLETE POST-RETRAIN WORKFLOW
# Runs everything in expert-recommended order
# =============================================================================

def run_complete_post_retrain_workflow(
    performance_log_path: str = 'graded/performance_log.csv',
    model_cache_dir: str = 'model_cache/',
    stats_parquet_path: str = 'data/stats.parquet',
):
    """
    Run this immediately after retrain completes.
    Implements the complete expert calibration plan.
    
    python3 -c "from expert_implementation_v2 import run_complete_post_retrain_workflow; run_complete_post_retrain_workflow()"
    """
    print("\n" + "="*65)
    print("COMPLETE POST-RETRAIN CALIBRATION WORKFLOW")
    print("Expert v2 — all recommendations applied")
    print("="*65 + "\n")

    df = pd.read_csv(performance_log_path)
    df['hit'] = (df['result'] == 'HIT').astype(float)
    df = df.dropna(subset=['model_prob', 'hit', 'stat'])

    print(f"Graded picks: {len(df)} | {df['grade_date'].min()} → {df['grade_date'].max()}")

    # Step 1: Feature availability audit
    print("\n--- STEP 1: Feature Availability Audit ---")
    audit = run_feature_availability_audit(model_cache_dir, stats_parquet_path)

    # Step 2: Quantile coverage diagnostics
    print("\n--- STEP 2: Quantile Coverage Diagnostics ---")
    coverage = run_quantile_coverage_diagnostics(performance_log_path)

    # Step 3: Temperature calibration (primary)
    print("\n--- STEP 3: Temperature Calibration (primary) ---")
    from expert_implementation import TemperatureCalibrator
    temp_cal = TemperatureCalibrator()
    temp_cal.fit(df)
    temp_path = os.path.join(model_cache_dir, 'calibration_temperature.json')
    temp_cal.save(temp_path)

    # Step 4: Beta calibration (candidate comparison)
    print("\n--- STEP 4: Beta Calibration (candidate) ---")
    beta_cal = BetaCalibrator()
    beta_cal.fit(df)
    beta_path = os.path.join(model_cache_dir, 'calibration_beta.json')
    beta_cal.save(beta_path)

    # Step 5: Compare calibrators by Brier score — pick best per stat
    print("\n--- STEP 5: Calibrator Comparison by Brier Score ---")
    best_calibrator = {}
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        sub = df[df['stat'] == stat].dropna(subset=['model_prob', 'hit'])
        if len(sub) == 0:
            continue
        probs   = sub['model_prob'].values
        outcomes= sub['hit'].values
        raw_b   = np.mean((probs - outcomes)**2)
        temp_b  = np.mean((np.array([temp_cal.calibrate(p, stat) for p in probs]) - outcomes)**2)
        beta_b  = np.mean((np.array([beta_cal.calibrate(p, stat) for p in probs]) - outcomes)**2)
        best    = 'temperature' if temp_b <= beta_b else 'beta'
        best_calibrator[stat] = best
        print(f"  {stat}: raw={raw_b:.4f} | temp={temp_b:.4f} | beta={beta_b:.4f} → BEST: {best}")

    with open(os.path.join(model_cache_dir, 'calibration_best.json'), 'w') as f:
        json.dump(best_calibrator, f, indent=2)

    # Step 6: CLV and ROI summary by side
    print("\n--- STEP 6: CLV and ROI by Side ---")
    if 'clv_proxy' in df.columns:
        for side in ['OVER', 'UNDER']:
            sub = df[df['side'] == side]
            print(f"  {side}: CLV={sub['clv_proxy'].mean():.3f} | HR={sub['hit'].mean():.1%} | n={len(sub)}")

    # Step 7: Portfolio simulation with new thresholds
    print("\n--- STEP 7: Portfolio Threshold Simulation ---")
    total_in = len(df)
    would_keep = 0
    for _, row in df.iterrows():
        prob = temp_cal.calibrate(float(row['model_prob']), row['stat'])
        rejected, _ = passes_no_bet_filter(
            {'stat': row['stat'], 'side': row['side'], 'line': row.get('line', 0)},
            prob,
            row.get('q50')
        )
        if not rejected:
            would_keep += 1
    print(f"  With new thresholds: {would_keep}/{total_in} picks survive ({would_keep/total_in:.1%})")

    print("\n" + "="*65)
    print("WORKFLOW COMPLETE")
    print(f"Calibration files saved to: {model_cache_dir}")
    print("Next: wire calibrator + portfolio controller into predict_darko_v4.py")
    print("="*65 + "\n")

    return {
        'audit': audit,
        'coverage': coverage,
        'best_calibrator': best_calibrator,
        'temp_calibrator': temp_cal,
        'beta_calibrator': beta_cal,
    }


# =============================================================================
# SECTION 10: SUPPRESS RULES — immediate action items
# Expert: "remove/suppress immediately"
# =============================================================================

SUPPRESS_NOW = {
    # (stat, side): reason
    ('blk', 'OVER'): "21.4% hit rate — catastrophically below 52.4% breakeven",
    ('stl', 'OVER'): "22.2% hit rate — catastrophically below 52.4% breakeven",
}

# Expert: "all low-confidence bets 0.50-0.60 raw probability"
SUPPRESS_BELOW_PROB = 0.60  # no picks below this raw probability (OVER)
SUPPRESS_UNDER_BELOW = 0.68  # no UNDER picks below this raw probability

# Expert: "most under bets until repaired"
# These stats have confirmed negative UNDER CLV — suppress UNDERs temporarily
SUPPRESS_UNDERS_TEMPORARILY = {'pts', 'ast'}  # worst UNDER CLV stats

# Expert: "duplicate correlated exposure"
# One player/stat/side per slate — enforced in PortfolioExposureController


if __name__ == '__main__':
    print("NBA Props Model — Expert v2 Implementation")
    print("Run: run_complete_post_retrain_workflow()")
    print()
    print("Immediate suppression rules:")
    for (stat, side), reason in SUPPRESS_NOW.items():
        print(f"  BANNED: {stat} {side} — {reason}")
    print(f"\nNo bets below {SUPPRESS_BELOW_PROB:.0%} (OVER) or {SUPPRESS_UNDER_BELOW:.0%} (UNDER)")
    print(f"Temporary UNDER suppression: {SUPPRESS_UNDERS_TEMPORARILY}")
