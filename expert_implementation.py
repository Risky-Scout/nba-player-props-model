"""
NBA Props Model — Expert Review Implementation
===============================================
Implements ALL recommendations from expert review in priority order.

IMMEDIATE TRIAGE (apply to predict script NOW):
  1. Ban BLK/STL OVERs
  2. Raise thresholds: OVER >= 0.60, UNDER >= 0.68-0.70
  3. Cap volume: one player/stat/game/side
  4. Prefer OVERs until UNDER calibration repaired

CALIBRATION:
  5. Per-stat temperature scaling (start here — sample too small for isotonic)
  6. Side-specific deployment thresholds (not side-specific calibrators yet)
  7. Brier score audit per stat after calibration

MATH FIXES:
  8. Replace piecewise linear CDF with smooth parametric distribution
  9. Widen quantile tails where empirical coverage is too narrow
  10. Separate sparse prop (BLK/STL) probability engine — discrete zero-heavy

LIVE:
  11. Remainder-of-game distribution engine (replaces scaled full-game shift)
  12. Adaptive trust = f(minutes, opportunity_sample, archetype)
"""

import numpy as np
from scipy import stats as scipy_stats
from scipy.special import expit, logit
from scipy.optimize import minimize_scalar, minimize
import pandas as pd
from typing import Optional


# =============================================================================
# SECTION 1: IMMEDIATE TRIAGE — apply to predict_darko_v4.py NOW
# =============================================================================

# Expert: "Ban blk OVER and stl OVER"
BANNED_PICKS = {
    ("blk", "OVER"),   # 21.4% hit rate — catastrophically below breakeven
    ("stl", "OVER"),   # 22.2% hit rate — same
}

# Expert: "no bets below 0.60 raw over probability, no unders below 0.68-0.70"
DEPLOYMENT_THRESHOLDS = {
    "pts":  {"OVER": 0.60, "UNDER": 0.70},
    "reb":  {"OVER": 0.60, "UNDER": 0.68},
    "ast":  {"OVER": 0.60, "UNDER": 0.70},
    "fg3m": {"OVER": 0.60, "UNDER": 0.68},
    "blk":  {"OVER": 9.99, "UNDER": 0.70},  # 9.99 = effectively banned
    "stl":  {"OVER": 9.99, "UNDER": 0.72},  # 9.99 = effectively banned
}

def apply_triage_filter(picks: list) -> list:
    """
    Apply immediate triage rules from expert review.
    Insert this into predict_darko_v4.py BEFORE the EV calculation.
    
    Expert: "No more 300+ bets per slate. Deduplicate one player/stat/game/side."
    """
    filtered = []
    seen = set()  # deduplicate: (player_id, stat, side)

    for pick in picks:
        stat  = pick.get('stat', '')
        side  = pick.get('side', '')
        prob  = float(pick.get('model_prob', 0))
        pid   = pick.get('player_id')
        key   = (pid, stat, side)

        # Rule 1: Ban specific stat/side combinations
        if (stat, side) in BANNED_PICKS:
            continue

        # Rule 2: Enforce minimum probability thresholds
        threshold = DEPLOYMENT_THRESHOLDS.get(stat, {}).get(side, 0.65)
        if prob < threshold:
            continue

        # Rule 3: Deduplicate — one pick per player/stat/side
        if key in seen:
            continue
        seen.add(key)

        filtered.append(pick)

    return filtered


# =============================================================================
# SECTION 2: CALIBRATION ENGINE
# Expert: "Temperature scaling if sample is small and the main problem is
#          overconfidence. Per-stat calibration, NOT 12 tiny isotonic maps."
# =============================================================================

class TemperatureCalibrator:
    """
    Temperature scaling calibration per stat.
    
    Expert: "Use temperature scaling first — it is stable with small samples.
             Isotonic only where sample is strong enough."
    
    Learns a single temperature T per stat that soft-scales all probabilities:
        calibrated = sigmoid(logit(raw_prob) / T)
    
    T > 1.0 = overconfident model → soften probabilities (our case)
    T < 1.0 = underconfident model → sharpen probabilities
    """

    def __init__(self):
        self.temperatures = {}      # {stat: T}
        self.fitted = False

    def fit(self, df: pd.DataFrame, stat_col='stat', prob_col='model_prob', outcome_col='hit'):
        """
        Fit temperature per stat using negative log-likelihood minimization.
        
        Expert: "Per-stat calibration first: pts, reb, ast, fg3m, sparse (blk+stl pooled)"
        """
        # Pool blk and stl per expert recommendation (small samples)
        df = df.copy()
        df['stat_group'] = df[stat_col].map(
            lambda s: 'sparse' if s in ('blk', 'stl') else s
        )

        for group in ['pts', 'reb', 'ast', 'fg3m', 'sparse']:
            sub = df[df['stat_group'] == group].copy()
            if len(sub) < 30:
                print(f"[calibration] {group}: insufficient sample ({len(sub)}) — using T=1.0")
                self.temperatures[group] = 1.0
                continue

            probs   = np.clip(sub[prob_col].values, 0.01, 0.99)
            outcomes= sub[outcome_col].values.astype(float)

            def nll(T):
                T = max(T, 0.1)  # prevent collapse
                cal = expit(logit(probs) / T)
                cal = np.clip(cal, 1e-7, 1 - 1e-7)
                return -np.mean(outcomes * np.log(cal) + (1 - outcomes) * np.log(1 - cal))

            result = minimize_scalar(nll, bounds=(0.5, 5.0), method='bounded')
            T = result.x
            self.temperatures[group] = T

            # Report calibration improvement
            raw_brier  = np.mean((probs - outcomes) ** 2)
            cal_probs  = expit(logit(probs) / T)
            cal_brier  = np.mean((cal_probs - outcomes) ** 2)
            print(f"[calibration] {group}: T={T:.3f} | Brier raw={raw_brier:.4f} → cal={cal_brier:.4f} | n={len(sub)}")

        self.fitted = True

    def calibrate(self, prob: float, stat: str) -> float:
        """Apply temperature scaling to a raw model probability."""
        if not self.fitted:
            return prob

        group = 'sparse' if stat in ('blk', 'stl') else stat
        T = self.temperatures.get(group, 1.0)

        if T == 1.0:
            return prob

        prob = np.clip(prob, 0.01, 0.99)
        return float(expit(logit(prob) / T))

    def save(self, path: str):
        import json
        with open(path, 'w') as f:
            json.dump({'temperatures': self.temperatures, 'fitted': self.fitted}, f, indent=2)
        print(f"[calibration] Saved to {path}")

    @classmethod
    def load(cls, path: str) -> 'TemperatureCalibrator':
        import json
        cal = cls()
        with open(path) as f:
            data = json.load(f)
        cal.temperatures = data['temperatures']
        cal.fitted = data['fitted']
        return cal


class BetaCalibrator:
    """
    Beta calibration — more flexible than temperature scaling,
    less unstable than isotonic on small samples.
    Expert: "Beta calibration is also a good option here."
    
    Fits a Beta distribution to transform raw probabilities.
    Maps [0,1] → [0,1] with learned a, b parameters.
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
            sub = df[df['stat_group'] == group].copy()
            if len(sub) < 50:
                self.params[group] = (1.0, 1.0)  # identity transform
                continue

            probs    = np.clip(sub[prob_col].values, 0.01, 0.99)
            outcomes = sub[outcome_col].values.astype(float)

            def nll(params):
                a, b = params
                if a <= 0 or b <= 0:
                    return 1e9
                # Beta CDF transformation
                from scipy.special import betainc
                cal = np.array([betainc(a, b, p) for p in probs])
                cal = np.clip(cal, 1e-7, 1 - 1e-7)
                return -np.mean(outcomes * np.log(cal) + (1 - outcomes) * np.log(1 - cal))

            result = minimize(nll, x0=[1.0, 1.0],
                              bounds=[(0.1, 10.0), (0.1, 10.0)],
                              method='L-BFGS-B')
            self.params[group] = tuple(result.x)

            a, b = result.x
            print(f"[beta_cal] {group}: a={a:.3f} b={b:.3f} | n={len(sub)}")

        self.fitted = True

    def calibrate(self, prob: float, stat: str) -> float:
        if not self.fitted:
            return prob
        from scipy.special import betainc
        group = 'sparse' if stat in ('blk', 'stl') else stat
        a, b = self.params.get(group, (1.0, 1.0))
        if a == 1.0 and b == 1.0:
            return prob
        prob = np.clip(prob, 0.01, 0.99)
        return float(betainc(a, b, prob))


def run_calibration_workflow(performance_log_path: str,
                             output_path: str = 'model_cache/calibration.json',
                             method: str = 'temperature'):
    """
    Full calibration workflow. Run after each retrain.
    Expert: "Recompute Brier and bucket accuracy after calibration."
    
    Usage:
        run_calibration_workflow('graded/performance_log.csv')
    """
    df = pd.read_csv(performance_log_path)
    df['hit'] = (df['result'] == 'HIT').astype(float)
    df = df.dropna(subset=['model_prob', 'hit'])

    print(f"[calibration] Fitting on {len(df)} graded picks")
    print(f"[calibration] Date range: {df['grade_date'].min()} → {df['grade_date'].max()}")

    if method == 'temperature':
        cal = TemperatureCalibrator()
    else:
        cal = BetaCalibrator()

    cal.fit(df)

    if method == 'temperature':
        cal.save(output_path)

    # Audit calibration bucket accuracy
    print("\n[calibration] BUCKET ACCURACY AUDIT (well-calibrated = predicted ≈ actual):")
    df['prob_bucket'] = pd.cut(df['model_prob'],
                                bins=[0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 1.0])
    audit = df.groupby('prob_bucket', observed=True).agg(
        predicted=('model_prob', 'mean'),
        actual=('hit', 'mean'),
        n=('hit', 'count')
    ).round(3)
    print(audit)

    return cal


# =============================================================================
# SECTION 3: SMOOTH PROBABILITY ENGINE
# Expert: "Replace piecewise linear CDF with smoother parametric distribution.
#          Widen tails where empirical coverage is too narrow.
#          The boundary handling L<=q10 => P=0.90 implies too much certainty."
# =============================================================================

def compute_pregame_prob_smooth(
    q_preds: dict,
    line: float,
    stat: str,
    calibrator: Optional[TemperatureCalibrator] = None,
) -> float:
    """
    Expert-recommended replacement for piecewise linear CDF interpolation.
    
    Problems with old approach:
    - L <= q10 → P = 0.90 implies certainty beyond estimated quantile support
    - L >= q90 → P = 0.10 same problem
    - Piecewise linear creates kinks in the distribution
    
    New approach:
    1. Fit a smooth distribution through the quantile points
    2. Use skew-normal or mixture distribution for asymmetric props
    3. Widen tails explicitly using empirical tail factors
    4. Apply calibration
    """
    if not q_preds or len(q_preds) < 3:
        return _fallback_prob_smooth(line, q_preds.get(0.5, 10.0), stat)

    # Sort quantiles
    taus = sorted(q_preds.keys())
    vals = [q_preds[t] for t in taus]

    # Fit normal distribution from quantile pairs
    # Use Q25-Q75 (more robust than Q10-Q90 for fitting)
    q25 = q_preds.get(0.25, None)
    q75 = q_preds.get(0.75, None)
    q50 = q_preds.get(0.50, None)
    q10 = q_preds.get(0.10, None)
    q90 = q_preds.get(0.90, None)

    if q25 is not None and q75 is not None and q50 is not None:
        # IQR-based sigma estimate
        iqr = q75 - q25
        sigma_iqr = iqr / 1.3490   # normal IQR/sigma ratio

        # Also estimate from Q10-Q90 if available
        if q10 is not None and q90 is not None:
            sigma_tail = (q90 - q10) / 2.5631  # normal P10-P90 span
            # Weight the two estimates — tail estimate widens distribution
            # Expert: "widen tails where empirical coverage is too narrow"
            TAIL_WIDENING = _get_tail_widening_factor(stat)
            sigma = max(sigma_iqr, sigma_tail * TAIL_WIDENING)
        else:
            sigma = sigma_iqr

        mu = q50
        sigma = max(sigma, 0.3)  # minimum sigma floor

        # Check for skewness — sparse stats are zero-heavy (right-skewed)
        if stat in ('blk', 'stl', 'fg3m'):
            # Use sparse-specific engine instead
            return _sparse_prop_probability(q_preds, line, stat, calibrator)

        # Normal CDF probability
        raw_prob = 1.0 - scipy_stats.norm.cdf(line, loc=mu, scale=sigma)

    else:
        # Fallback to improved piecewise with wider boundary handling
        raw_prob = _piecewise_cdf_widened(q_preds, line, taus, vals)

    # Apply temperature calibration
    raw_prob = float(np.clip(raw_prob, 0.02, 0.98))
    if calibrator is not None:
        raw_prob = calibrator.calibrate(raw_prob, stat)

    return float(np.clip(raw_prob, 0.02, 0.98))


def _get_tail_widening_factor(stat: str) -> float:
    """
    Expert: "Widen tails where empirical coverage is too narrow."
    Based on empirical calibration results showing systematic overconfidence.
    Higher factor = wider tails = less extreme probabilities.
    """
    return {
        'pts':  1.15,   # 15% wider tails vs raw sigma estimate
        'reb':  1.20,
        'ast':  1.20,
        'fg3m': 1.25,   # fg3m has high variance — widen more
        'blk':  1.50,   # sparse — very wide
        'stl':  1.50,
    }.get(stat, 1.20)


def _piecewise_cdf_widened(q_preds: dict, line: float, taus: list, vals: list) -> float:
    """
    Improved piecewise CDF with wider boundary handling.
    Expert: "boundary handling L<=q10 => P=0.90 implies too much certainty."
    
    Old: P(over | L <= q10) = 0.90
    New: extrapolate with fat tails beyond the quantile support
    """
    n = len(vals)
    if n == 0:
        return 0.5

    # Below support — extrapolate with heavy tail (not 0.90 cutoff)
    if line <= vals[0]:
        # How far below q10 is the line?
        tau_low = float(taus[0])
        # Use normal extrapolation: P = 1 - phi(z) where z accounts for distance
        dist_below = (vals[0] - line) / max(vals[-1] - vals[0], 0.5)
        return min(0.95, 1.0 - tau_low + dist_below * tau_low * 0.5)

    # Above support
    if line >= vals[-1]:
        tau_high = float(taus[-1])
        dist_above = (line - vals[-1]) / max(vals[-1] - vals[0], 0.5)
        return max(0.05, (1.0 - tau_high) * np.exp(-dist_above * 2.0))

    # Interior: standard piecewise linear
    for i in range(n - 1):
        if vals[i] <= line < vals[i + 1]:
            frac = (line - vals[i]) / max(vals[i+1] - vals[i], 1e-9)
            tau  = float(taus[i]) + frac * (float(taus[i+1]) - float(taus[i]))
            return max(0.02, min(0.98, 1.0 - tau))

    return 0.5


def _fallback_prob_smooth(line: float, proj: float, stat: str) -> float:
    """Smooth fallback when quantile distribution unavailable."""
    cv_map = {'pts':0.35,'reb':0.45,'ast':0.50,'fg3m':0.65,'blk':0.90,'stl':0.85}
    tail   = _get_tail_widening_factor(stat)
    cv     = cv_map.get(stat, 0.45) * tail
    sigma  = max(0.5, proj * cv)
    return float(np.clip(1.0 - scipy_stats.norm.cdf(line, loc=proj, scale=sigma), 0.02, 0.98))


# =============================================================================
# SECTION 4: SPARSE PROP ENGINE
# Expert: "Blocks and steals cannot be treated like points/rebounds.
#          Use a discrete zero-heavy calibration layer or count-based
#          post-processing. Suppress overs until repaired."
# =============================================================================

def _sparse_prop_probability(
    q_preds: dict,
    line: float,
    stat: str,
    calibrator: Optional[TemperatureCalibrator] = None,
) -> float:
    """
    Discrete zero-heavy probability engine for BLK and STL.
    Expert: "sparse discrete props behave poorly with continuous CDF shifting."
    
    Uses a zero-inflated Poisson approximation:
        P(X = 0) = pi_0 (zero-inflation from q_preds)
        P(X > 0) ~ Poisson(lambda)
    
    For props with line = 0.5:
        P(OVER 0.5) = 1 - P(X = 0) = 1 - pi_0
    For props with line = 1.5:
        P(OVER 1.5) = P(X >= 2) from Poisson
    """
    q50  = q_preds.get(0.50, 1.0)
    q10  = q_preds.get(0.10, 0.0)
    q25  = q_preds.get(0.25, 0.0)

    # Estimate zero probability from quantile positions
    # If q25 = 0: at least 25% of games are zeros
    # If q10 = 0: at least 10% are zeros
    if q25 is not None and q25 <= 0.01:
        p_zero = 0.30  # at least 25%, conservatively estimate 30%
    elif q10 is not None and q10 <= 0.01:
        p_zero = 0.15
    else:
        p_zero = 0.05

    # Poisson lambda for non-zero games
    mu_nonzero = q50 / max(1.0 - p_zero, 0.01)
    mu_nonzero = max(0.1, mu_nonzero)

    # Compute P(X > line) using zero-inflated Poisson
    line_ceil = int(np.ceil(line))  # e.g., line=0.5 → ceil=1

    # P(X >= line_ceil) = (1 - p_zero) * P(Poisson >= line_ceil | lambda=mu_nonzero)
    p_nonzero  = 1.0 - p_zero
    p_pois_over = 1.0 - scipy_stats.poisson.cdf(line_ceil - 1, mu_nonzero)
    raw_prob   = p_nonzero * p_pois_over

    raw_prob = float(np.clip(raw_prob, 0.02, 0.98))

    # CRITICAL: Expert says suppress OVER for sparse stats
    # Even after computing probability, UNDER is much more reliable for BLK/STL
    # Apply additional conservatism to OVER probabilities
    if line < 1.0:  # line = 0.5 (OVER 0.5 blocks)
        raw_prob = min(raw_prob, 0.65)  # cap OVER probability — market knows rim protectors

    if calibrator is not None:
        raw_prob = calibrator.calibrate(raw_prob, stat)

    return float(np.clip(raw_prob, 0.02, 0.98))


# =============================================================================
# SECTION 5: ADAPTIVE TRUST FOR LIVE MODEL
# Expert: "k should depend on stat family, player archetype,
#          opportunity sample size, and game state."
# =============================================================================

def compute_adaptive_trust(
    min_played: float,
    stat: str,
    opp_sample: float = 0.0,    # e.g., FGA count for pts, 3PA for fg3m, rim events for blk
    opportunity_sample: float = None,  # alias
    archetype: str = 'star',    # 'star', 'starter', 'bench', 'microwave'
    game_state: str = 'normal', # 'clutch', 'blowout', 'normal'
) -> dict:
    """
    Expert recommendation:
        trust(m, n, r) = m / (m + k_s * a_r * b_n)
    
    where:
        k_s = stat-specific base prior weight
        a_r = archetype modifier (bench/microwave updates faster)
        b_n = opportunity sample quality modifier
    
    Returns separate trust values for opportunity rate vs conversion rate.
    """
    # Base prior weights (from v5)
    K_BASE = {
        'pts': 12.0, 'reb': 16.0, 'ast': 16.0,
        'fg3m': 22.0, 'blk': 30.0, 'stl': 30.0,
        'fg3a': 10.0,
    }
    k_base = K_BASE.get(stat, 15.0)
    # Resolve alias
    if opportunity_sample is not None:
        opp_sample = opportunity_sample

    # Archetype modifier (a_r)
    # Expert: "bench microwave scorers should update faster on shot rate"
    A_ARCHETYPE = {
        'star':      1.20,   # trust pregame longer for well-known stars
        'starter':   1.00,   # neutral
        'bench':     0.80,   # update faster — higher variance role
        'microwave': 0.70,   # feast-or-famine scorer — update fast on shot rate
    }
    a_r = A_ARCHETYPE.get(archetype, 1.00)

    # Opportunity sample quality modifier (b_n)
    # Expert: "FG3 makes should trust 3PA faster than 3P%"
    # Higher opportunity sample = trust observed faster (lower b_n)
    OPP_THRESHOLDS = {
        'pts': 5.0,   # 5 FGA = meaningful sample
        'reb': 3.0,
        'ast': 2.0,
        'fg3m': 4.0,  # 4 3PA = meaningful for make rate
        'fg3a': 2.0,  # fewer attempts needed for rate
        'blk': 2.0,
        'stl': 2.0,
    }
    opp_thresh = OPP_THRESHOLDS.get(stat, 3.0)
    if opp_sample >= opp_thresh * 2:
        b_n = 0.75   # strong sample — update faster
    elif opp_sample >= opp_thresh:
        b_n = 1.00   # adequate sample — neutral
    else:
        b_n = 1.30   # thin sample — trust prior more

    # Game state modifier
    # Expert: "Blocks/steals should trust slower unless extraordinary event support"
    G_STATE = {'clutch': 0.90, 'normal': 1.00, 'blowout': 1.10}
    g = G_STATE.get(game_state, 1.00)

    # Final adaptive k
    k_adaptive = k_base * a_r * b_n * g

    # Opportunity trust (updates faster)
    k_opp  = k_adaptive * 0.60
    k_conv = k_adaptive * 1.50

    trust_opp  = min_played / (min_played + k_opp)
    trust_conv = min_played / (min_played + k_conv)
    trust_full = min_played / (min_played + k_adaptive)

    return {
        'trust_opportunity':  round(min(0.90, trust_opp), 3),
        'trust_conversion':   round(min(0.80, trust_conv), 3),
        'trust_full':         round(min(0.90, trust_full), 3),
        'k_adaptive':         round(k_adaptive, 2),
        'k_base':             k_base,
        'a_archetype':        a_r,
        'b_opportunity':      b_n,
    }


# =============================================================================
# SECTION 6: LIVE REMAINDER DISTRIBUTION ENGINE
# Expert: "Replace full-game distribution shift with remainder modeling.
#          final = actual + remainder
#          P(final > line) = P(remainder > line - actual)"
# =============================================================================

def compute_remainder_distribution(
    stat: str,
    actual: float,
    min_played: float,
    adj_min_remaining: float,
    pregame_q50: float,
    pregame_min: float,
    pregame_q_preds: dict,
    live_opp_rate: Optional[float],    # e.g., live FGA/min for pts
    live_conv_rate: Optional[float],   # e.g., live FG% for pts
    opp_sample: float,
    archetype: str = 'starter',
    game_state: str = 'normal',
    pace_adj: float = 1.0,
    calibrator: Optional[TemperatureCalibrator] = None,
) -> dict:
    """
    Expert-recommended live probability architecture.
    Models the REMAINDER as a fresh distribution, not a scaled full-game.
    
    Key insight: as game progresses, the remainder distribution becomes
    increasingly independent of the full-game pregame projection.
    At 40 min played, the remainder is essentially a fresh 8-minute model.
    """
    needed = pregame_q50 - actual   # remaining stat needed to match pregame projection
    game_progress = min_played / max(min_played + adj_min_remaining, 1.0)

    # ── Get adaptive trust ────────────────────────────────────────────────────
    trust = compute_adaptive_trust(min_played, stat, opp_sample=opp_sample, archetype=archetype, game_state=game_state)

    # ── Compute pregame remainder distribution ────────────────────────────────
    # What did the pregame model expect for the REMAINING minutes?
    pregame_rate    = pregame_q50 / max(pregame_min, 1.0)
    pregame_rem_mean= pregame_rate * adj_min_remaining * pace_adj

    # ── Compute live-informed remainder ──────────────────────────────────────
    if live_opp_rate is not None and live_conv_rate is not None:
        # Split opportunity and conversion
        trust_opp  = trust['trust_opportunity']
        trust_conv = trust['trust_conversion']

        # Derive pregame opportunity and conversion rates
        # (approximated — ideally from separate pregame tracking features)
        pregame_opp_rate  = pregame_rate * 1.15   # FGA rate slightly above pts/min
        pregame_conv_rate = pregame_rate / max(pregame_opp_rate, 0.01)

        blended_opp_rate  = (1 - trust_opp) * pregame_opp_rate  + trust_opp * live_opp_rate
        blended_conv_rate = (1 - trust_conv) * pregame_conv_rate + trust_conv * live_conv_rate
        live_rem_rate     = blended_opp_rate * blended_conv_rate

    elif live_opp_rate is not None:
        # Opportunity only (no conversion data)
        trust_full       = trust['trust_full']
        live_rem_rate    = (1 - trust_full) * pregame_rate + trust_full * live_opp_rate

    else:
        # No live opportunity data — use full blended rate
        live_rate     = actual / max(min_played, 0.1)
        trust_full    = trust['trust_full']
        live_rem_rate = (1 - trust_full) * pregame_rate + trust_full * live_rate

    live_rem_rate *= pace_adj
    mean_remainder = live_rem_rate * adj_min_remaining

    # ── Variance of remainder (narrows as game progresses) ───────────────────
    SHRINK_SPEED = {
        'pts': 0.85, 'reb': 0.80, 'ast': 0.78,
        'fg3m': 0.70, 'blk': 0.50, 'stl': 0.50,
    }
    shrink = SHRINK_SPEED.get(stat, 0.75)
    BASE_CV = {'pts':0.35,'reb':0.45,'ast':0.50,'fg3m':0.65,'blk':0.90,'stl':0.85}
    base_cv = BASE_CV.get(stat, 0.45)
    var_retained = max(0.15, 1.0 - game_progress * shrink)
    tail_factor  = _get_tail_widening_factor(stat)
    live_cv      = base_cv * var_retained * tail_factor
    sd_remainder = max(0.3, mean_remainder * live_cv)

    # ── Probability: P(remainder > needed) ───────────────────────────────────
    needed_stat = max(0.0, pregame_q50 - actual)  # how much more needed

    if stat in ('blk', 'stl', 'fg3m'):
        # Sparse: use discrete approximation
        line_for_remainder = needed_stat
        raw_prob = _sparse_remainder_prob(mean_remainder, sd_remainder, line_for_remainder, stat)
    else:
        # Continuous: smooth normal for remainder
        if sd_remainder > 0:
            raw_prob = 1.0 - scipy_stats.norm.cdf(needed_stat, loc=mean_remainder, scale=sd_remainder)
        else:
            raw_prob = 1.0 if mean_remainder > needed_stat else 0.0

    raw_prob = float(np.clip(raw_prob, 0.02, 0.98))

    if calibrator is not None:
        raw_prob = calibrator.calibrate(raw_prob, stat)

    return {
        'prob':             float(np.clip(raw_prob, 0.02, 0.98)),
        'mean_remainder':   round(mean_remainder, 2),
        'sd_remainder':     round(sd_remainder, 2),
        'live_proj':        round(actual + mean_remainder, 1),
        'needed':           round(needed_stat, 2),
        'var_retained':     round(var_retained, 3),
        'trust':            trust,
        'game_progress':    round(game_progress, 3),
        'method':           'remainder_distribution_v1',
    }


def _sparse_remainder_prob(
    mean_rem: float,
    sd_rem: float,
    needed: float,
    stat: str,
) -> float:
    """P(remainder > needed) for sparse props using negative binomial."""
    if mean_rem <= 0:
        return 0.02

    needed_int = int(np.ceil(needed))

    # Fit negative binomial to (mean, variance)
    # E[X] = mu, Var[X] = mu + mu^2/r → r = mu^2 / (var - mu)
    var = max(sd_rem**2, mean_rem + 0.01)
    r   = max(0.5, mean_rem**2 / (var - mean_rem)) if var > mean_rem else 2.0
    p   = r / (r + mean_rem)

    from scipy.stats import nbinom
    prob = 1.0 - nbinom.cdf(needed_int - 1, r, p)
    return float(np.clip(prob, 0.02, 0.98))


# =============================================================================
# SECTION 7: CALIBRATION WORKFLOW — run this after retrain completes
# =============================================================================

def post_retrain_calibration_workflow(
    performance_log_path: str = 'graded/performance_log.csv',
    output_dir: str = 'model_cache/',
):
    """
    Complete post-retrain calibration workflow.
    Expert: "build per-stat calibrators, start with temperature scaling."
    
    Run this immediately after retrain completes:
        python3 -c "from expert_implementation import post_retrain_calibration_workflow; post_retrain_calibration_workflow()"
    """
    import os
    df = pd.read_csv(performance_log_path)
    df['hit'] = (df['result'] == 'HIT').astype(float)
    df = df.dropna(subset=['model_prob', 'hit', 'stat'])

    print(f"\n{'='*60}")
    print("POST-RETRAIN CALIBRATION WORKFLOW")
    print(f"{'='*60}")
    print(f"Total graded: {len(df)} | Range: {df['grade_date'].min()} → {df['grade_date'].max()}")

    # Step 1: Temperature scaling (primary method)
    print("\n--- Step 1: Temperature Scaling ---")
    temp_cal = TemperatureCalibrator()
    temp_cal.fit(df)
    temp_cal.save(os.path.join(output_dir, 'calibration_temperature.json'))

    # Step 2: Brier score comparison
    print("\n--- Step 2: Brier Score by Stat ---")
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'blk', 'stl']:
        sub = df[df['stat'] == stat]
        if len(sub) == 0:
            continue
        probs = sub['model_prob'].values
        hits  = sub['hit'].values
        raw_brier = np.mean((probs - hits)**2)
        cal_probs = np.array([temp_cal.calibrate(p, stat) for p in probs])
        cal_brier = np.mean((cal_probs - hits)**2)
        print(f"  {stat}: raw={raw_brier:.4f} → calibrated={cal_brier:.4f} | Δ={cal_brier-raw_brier:+.4f}")

    # Step 3: Deployment threshold recommendations
    print("\n--- Step 3: Deployment Thresholds (expert-recommended) ---")
    print("  OVER thresholds (after calibration):")
    for stat, thresholds in DEPLOYMENT_THRESHOLDS.items():
        over_t  = thresholds['OVER']
        under_t = thresholds['UNDER']
        if over_t > 9:
            print(f"    {stat} OVER: BANNED (hit rate below breakeven)")
        else:
            print(f"    {stat} OVER: {over_t:.2f} | UNDER: {under_t:.2f}")

    # Step 4: CLV audit
    print("\n--- Step 4: CLV by Stat/Side ---")
    if 'clv_proxy' in df.columns:
        clv = df.groupby(['stat', 'side'])['clv_proxy'].mean().round(3)
        print(clv)
        print("\nTarget: positive CLV on both sides. Negative UNDER CLV = model mispricing.")

    print(f"\n{'='*60}")
    print("Calibration complete. Files saved to:", output_dir)
    print("Next: wire calibrator into predict_darko_v4.py at inference time")
    print(f"{'='*60}\n")

    return temp_cal


# =============================================================================
# SECTION 8: HOW TO WIRE INTO predict_darko_v4.py
# =============================================================================

INTEGRATION_INSTRUCTIONS = """
=================================================================
INTEGRATION INSTRUCTIONS FOR predict_darko_v4.py
=================================================================

STEP 1: Load calibrator at startup (once, not per pick)
--------------------------------------------------------
from expert_implementation import TemperatureCalibrator, apply_triage_filter
import json, os

CAL_PATH = 'model_cache/calibration_temperature.json'
if os.path.exists(CAL_PATH):
    calibrator = TemperatureCalibrator.load(CAL_PATH)
else:
    calibrator = None
    print("[WARNING] No calibration file — using raw model probabilities")


STEP 2: Apply calibration at inference (per pick)
--------------------------------------------------
# After computing raw model_prob:
if calibrator is not None:
    pick['model_prob_raw'] = pick['model_prob']
    pick['model_prob'] = calibrator.calibrate(pick['model_prob'], pick['stat'])


STEP 3: Use smooth probability engine (replace old CDF function)
-----------------------------------------------------------------
from expert_implementation import compute_pregame_prob_smooth

# Replace: prob = queryQuantileDistribution(q_preds, line)
# With:
prob = compute_pregame_prob_smooth(q_preds, line, stat, calibrator)


STEP 4: Apply triage filter (at the end, before output)
--------------------------------------------------------
picks = apply_triage_filter(picks)


STEP 5: Live model — replace calcLiveProbabilityV3/V4/V5
---------------------------------------------------------
from expert_implementation import compute_remainder_distribution

result = compute_remainder_distribution(
    stat=stat, actual=actual,
    min_played=min_played, adj_min_remaining=adj_min_remaining,
    pregame_q50=pregame_proj, pregame_min=pregame_min,
    pregame_q_preds=q_preds,
    live_opp_rate=live_fga_rate,    # None if unavailable
    live_conv_rate=live_fg_pct,     # None if unavailable
    opp_sample=live_fga,
    archetype=player_archetype,
    game_state='clutch' if is_clutch else 'normal',
    pace_adj=pace_factor,
    calibrator=calibrator,
)
prob = result['prob']
live_proj = result['live_proj']


STEP 6: Post-retrain calibration (run once after each retrain)
--------------------------------------------------------------
python3 -c "
from expert_implementation import post_retrain_calibration_workflow
post_retrain_calibration_workflow('graded/performance_log.csv', 'model_cache/')
"
=================================================================
"""

if __name__ == '__main__':
    print("Expert Implementation Module")
    print("Run post_retrain_calibration_workflow() after retrain completes")
    print(INTEGRATION_INSTRUCTIONS)
