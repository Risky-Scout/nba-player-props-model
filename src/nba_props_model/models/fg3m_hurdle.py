"""
fg3m_hurdle.py — Three-Stage FG3M Hurdle Model  (v2)

Stage 1: P(fg3a_volume >= meaningful_threshold | features)
         = "Does this player attempt enough threes to matter?"
         GBM classifier calibrated with isotonic regression.

Stage 2: Expected 3PA count, conditional on being a 3PA player.
         Shrinkage toward per-archetype priors; per-minute rate x exp_minutes.

Stage 3: P(fg3m > line) from Binomial(exp_fg3a, shrunk_fg3_pct),
         conditional on the stage-1 gate passing.

Final:
    P(fg3m > line) = P(meaningful_3pa) * P(fg3m > line | meaningful_3pa)
    P(fg3m = 0)    = [1 - P(meaningful_3pa)] + P(meaningful_3pa) * Binom(0)

Hard constraints:
    - Non-shooting big (archetype 0): P(meaningful_3pa) capped at 0.30
    - P(fg3m > 0) <= P(meaningful_3pa) always
    - Q50 = 0 whenever P(fg3m = 0) >= 0.50

Archetypes (on season_mean_fg3a):
    0: non-shooting big    < 1.0  att/game
    1: low-volume wing     1.0–3.0
    2: moderate shooter    3.0–5.5
    3: high-volume shooter > 5.5
"""

import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from scipy.stats import binom, poisson
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Archetype config ───────────────────────────────────────────────────────────
ARCHETYPE_NAMES  = {0: "non-shooting big", 1: "low-volume wing",
                    2: "moderate shooter",  3: "high-volume shooter"}

# (prior_fg3a_per_game, prior_fg3_pct)  — league-calibrated priors per archetype
ARCHETYPE_PRIORS = {
    0: (0.2, 0.22),   # rim runner — rarely attempts, rarely makes
    1: (1.8, 0.33),   # low-volume corner guys
    2: (4.2, 0.36),   # typical wing shooter
    3: (7.8, 0.38),   # high-usage marksman
}

# Meaningful volume gate thresholds per archetype
# Stage-1 is "does this player regularly attempt >= threshold 3PA/game?"
MEANINGFUL_3PA_THRESH = {0: 0.5, 1: 1.0, 2: 2.0, 3: 3.5}


def assign_archetype(season_mean_fg3a: float) -> int:
    if season_mean_fg3a < 1.0:  return 0
    elif season_mean_fg3a < 3.0: return 1
    elif season_mean_fg3a < 5.5: return 2
    else: return 3


# ── Feature sets ───────────────────────────────────────────────────────────────
# Stage-1: classify whether this player is a meaningful three-point shooter
VOLUME_GATE_FEATURES = [
    'season_mean_fg3a',       # career/season average attempts
    'mean_fg3a_last10',       # recent form
    'mean_fg3a_last5',        # hot/cold streak
    'ewma10_fg3a',            # exponentially-weighted recent
    'zero_pct_fg3a',          # fraction of games with 0 attempts
    'trend_fg3a',             # recent vs. baseline trend
    'per_min_fg3a_last10',    # per-minute attempt rate (controls for minutes)
    'per_min_fg3a_season',    # season per-minute rate
    'archetype',              # discrete tier
]

# Stage-2 additional features for 3PA count prediction
VOLUME_COUNT_FEATURES = VOLUME_GATE_FEATURES + [
    'fg3a_count_last10',      # raw attempt count last 10 games
    'fg3a_count_season',      # raw season count
    'fg3a_per_min_trend_3v10',# per-min 3PA trend (3-game vs 10-game)
    'exp_mp',                 # expected minutes (from minutes model)
    'mp_p_28plus',            # P(starter minutes) — more min = more 3PA
    'opp_allowed_fg3m_guard_ewma',  # matchup-specific 3pm allowed to guards
    'opp_allowed_fg3m_big_ewma',    # matchup-specific 3pm allowed to bigs
]


def extract_features(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for c in cols:
        out[c] = pd.to_numeric(df[c], errors='coerce').fillna(0) if c in df.columns else 0.0
    return out


# ── Main model class ───────────────────────────────────────────────────────────

class FG3MHurdleModel:
    """Three-stage FG3M hurdle model."""

    def __init__(self):
        self.volume_gate_model  = None   # Stage 1: P(meaningful_3pa)
        self.volume_gate_scaler = StandardScaler()
        self.is_fitted = False

    # ── Stage 1 training ──────────────────────────────────────────────────────
    def fit(self, df: pd.DataFrame) -> 'FG3MHurdleModel':
        logger.info(f"Fitting FG3M 3-stage hurdle on {len(df)} rows …")
        df = df.copy()

        fg3a_col = ('season_mean_fg3a' if 'season_mean_fg3a' in df.columns
                    else 'mean_fg3a_last10')
        df['archetype'] = df[fg3a_col].fillna(0).apply(assign_archetype)

        for arch, cnt in df['archetype'].value_counts().sort_index().items():
            logger.info(f"  Archetype {arch} ({ARCHETYPE_NAMES[arch]}): "
                        f"{cnt} ({cnt/len(df):.1%})")

        # Stage-1 label: player regularly shoots meaningful 3PA volume
        # Use zero_pct_fg3a < 0.75 AND archetype-specific attempt threshold met
        if 'zero_pct_fg3a' in df.columns and 'mean_fg3a_last10' in df.columns:
            y_gate = (
                (df['zero_pct_fg3a'] < 0.75) &
                (df.apply(lambda r: r['mean_fg3a_last10'] >=
                          MEANINGFUL_3PA_THRESH[int(r['archetype'])], axis=1))
            ).astype(int)
        elif 'actual' in df.columns:
            # Training table fallback: meaningful if > 1 make on average
            y_gate = (df['actual'] > 0.5).astype(int)
        else:
            raise ValueError("Need zero_pct_fg3a + mean_fg3a_last10, or actual column")

        logger.info(f"  Stage-1 positive rate: {y_gate.mean():.3f}")

        X = extract_features(df, VOLUME_GATE_FEATURES)
        Xs = self.volume_gate_scaler.fit_transform(X)

        base = GradientBoostingClassifier(
            n_estimators=400, max_depth=3,
            learning_rate=0.04, subsample=0.8,
            random_state=42,
        )
        self.volume_gate_model = CalibratedClassifierCV(base, cv=5, method='isotonic')
        self.volume_gate_model.fit(Xs, y_gate)

        # OOF calibration check
        oof = cross_val_predict(
            GradientBoostingClassifier(n_estimators=400, max_depth=3,
                                       learning_rate=0.04, random_state=42),
            Xs, y_gate, cv=5, method='predict_proba',
        )[:, 1]
        logger.info(f"  OOF mean P(meaningful_3pa): {oof.mean():.3f} "
                    f"vs actual {y_gate.mean():.3f}")

        self.is_fitted = True
        logger.info("Done — 3-stage FG3M hurdle fitted.")
        return self

    # ── Inference ─────────────────────────────────────────────────────────────
    def predict_proba(self, features: dict, line: float) -> dict:
        """
        Returns full probability decomposition for one player × line.

        features: flat dict (keys match VOLUME_GATE_FEATURES etc.)
        line    : the over/under line (e.g. 1.5)
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() or load() first")

        features = dict(features)

        # ── Archetype assignment ──────────────────────────────────────────────
        season_fg3a = features.get('season_mean_fg3a',
                       features.get('mean_fg3a_last10', 0.0))
        archetype   = assign_archetype(float(season_fg3a))
        features['archetype'] = archetype
        prior_fg3a, prior_pct = ARCHETYPE_PRIORS[archetype]

        # ── Stage 1: P(meaningful_3pa) ────────────────────────────────────────
        X  = np.array([[features.get(f, 0.0) for f in VOLUME_GATE_FEATURES]])
        Xs = self.volume_gate_scaler.transform(X)
        p_meaningful = float(self.volume_gate_model.predict_proba(Xs)[0, 1])

        # Hard cap for non-shooting bigs
        if archetype == 0:
            p_meaningful = min(p_meaningful, 0.30)

        # ── Stage 2: Expected 3PA count (conditional on being a shooter) ──────
        # Shrink observed rate toward archetype prior
        obs_fg3a = float(features.get('mean_fg3a_last10',
                          features.get('season_mean_fg3a', prior_fg3a)))
        n_games  = max(int(features.get('n_games_season', 20)), 5)

        # If minutes model output available, scale by expected minutes
        exp_mp   = float(features.get('exp_mp', 0.0))
        pm_rate  = float(features.get('per_min_fg3a_last10', 0.0))
        if exp_mp > 0 and pm_rate > 0:
            mp_based_fg3a = pm_rate * exp_mp
            # Blend stat-history estimate with per-minute projection
            obs_fg3a = 0.6 * obs_fg3a + 0.4 * mp_based_fg3a

        # Shrink toward prior
        shrunk_fg3a = (obs_fg3a * n_games + prior_fg3a * 10) / (n_games + 10)

        # Matchup adjustment: scale by position-split 3pm allowed ratio
        # Use the guard or big ewma depending on archetype
        if archetype <= 1:
            opp_factor_key = 'opp_allowed_fg3m_guard_ewma'
        else:
            opp_factor_key = 'opp_allowed_fg3m_big_ewma'
        opp_val = float(features.get(opp_factor_key, 0.0) or 0.0)
        if opp_val > 0:
            # Mild matchup adjustment: sqrt to dampen extreme values
            opp_adj = np.sqrt(np.clip(opp_val / max(prior_fg3a, 0.5), 0.6, 1.6))
            shrunk_fg3a *= opp_adj

        exp_fg3a = max(round(shrunk_fg3a, 1), 0.1)

        # ── Stage 3: Shrunk FG3% ──────────────────────────────────────────────
        obs_pct = float(features.get('fg3_pct_shrunk',
                         features.get('fg3_pct_safe', prior_pct)))
        # Volume-weighted shrinkage toward prior
        total_att = max(obs_fg3a * n_games, 1.0)
        shrunk_pct = float(np.clip(
            (obs_pct * total_att + prior_pct * 20) / (total_att + 20),
            0.08, 0.65,
        ))

        # ── Binomial CDF ──────────────────────────────────────────────────────
        k_ceil  = int(np.floor(line)) + 1          # smallest integer > line
        p_over_given_shoots = float(np.clip(
            1.0 - binom.cdf(k_ceil - 1, max(int(round(exp_fg3a)), 1), shrunk_pct),
            0.0, 1.0,
        ))

        # Final probabilities
        p_zero_if_shoots = float(binom.pmf(0, max(int(round(exp_fg3a)), 1), shrunk_pct))
        p_zero    = float((1.0 - p_meaningful) + p_meaningful * p_zero_if_shoots)
        p_over    = float(np.clip(p_meaningful * p_over_given_shoots, 0.0, p_meaningful))

        # Q50: median — 0 if P(fg3m=0) >= 0.50
        q50 = 0.0 if p_zero >= 0.50 else round(exp_fg3a * shrunk_pct, 1)

        return {
            'p_meaningful':       round(p_meaningful, 4),
            'p_over':             round(p_over, 4),
            'p_zero':             round(p_zero, 4),
            'q50':                q50,
            'archetype':          archetype,
            'archetype_name':     ARCHETYPE_NAMES[archetype],
            'shrunk_fg3a':        round(shrunk_fg3a, 2),
            'shrunk_pct':         round(shrunk_pct, 3),
            'expected_fg3a':      exp_fg3a,
            # legacy key name for callers using 'p_attempts'
            'p_attempts':         round(p_meaningful, 4),
        }

    # ── Full PMF output ───────────────────────────────────────────────────────
    FG3M_DOMAIN_MAX = 15

    def pmf(self, features: dict) -> np.ndarray:
        """Return the discrete PMF over {0, 1, ..., FG3M_DOMAIN_MAX}.

        Uses the same three-stage decomposition as `predict_proba` but
        exposes the full distribution rather than a single probability
        at a line. The Phase 6 full-PMF calibration layer consumes this.

        Decomposition:
            P(fg3m = 0) = (1 - p_meaningful)
                        + p_meaningful * Binomial(0 | n, p)
            P(fg3m = k) = p_meaningful * Binomial(k | n, p)  for k >= 1
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() or load() first")

        # Reuse the decomposition via predict_proba at a sentinel line.
        decomp = self.predict_proba(features, line=0.5)
        p_meaningful = float(decomp["p_meaningful"])
        exp_fg3a = max(int(round(float(decomp["expected_fg3a"]))), 1)
        shrunk_pct = float(decomp["shrunk_pct"])

        k_range = np.arange(self.FG3M_DOMAIN_MAX + 1)
        binom_pmf = binom.pmf(k_range, exp_fg3a, shrunk_pct)
        # Extend the Binomial to include tail mass above FG3M_DOMAIN_MAX
        # into the last bin so the PMF sums to 1.
        tail = 1.0 - binom.cdf(self.FG3M_DOMAIN_MAX, exp_fg3a, shrunk_pct)
        binom_pmf = binom_pmf.copy()
        binom_pmf[-1] += max(0.0, tail)

        pmf_out = np.zeros(self.FG3M_DOMAIN_MAX + 1)
        pmf_out[0] = (1.0 - p_meaningful) + p_meaningful * binom_pmf[0]
        pmf_out[1:] = p_meaningful * binom_pmf[1:]

        s = pmf_out.sum()
        if s > 0:
            pmf_out = pmf_out / s
        return pmf_out

    # ── Persistence ───────────────────────────────────────────────────────────
    def save(self, path: str):
        joblib.dump(self, path)
        logger.info(f"Saved → {path}")

    @classmethod
    def load(cls, path: str) -> 'FG3MHurdleModel':
        return joblib.load(path)


# ── TOV / sparse calibration helper (unchanged) ───────────────────────────────

def evaluate_tov_calibration(y_true: np.ndarray, q_preds: dict) -> dict:
    rng = np.random.default_rng(42)
    results = {}
    print(f"\n=== Discrete-Aware TOV Calibration ===")
    print(f"n={len(y_true)}  zero%={(y_true==0).mean():.1%}  "
          f"mean={y_true.mean():.2f}  median={np.median(y_true):.1f}")
    print(f"\n{'Q':>5} {'Lower':>7} {'Upper':>7} {'InBounds':>9} {'RandPIT':>8} {'Gap':>6} {'':>6}")
    print("-" * 50)
    for tau, q_pred in sorted(q_preds.items()):
        q_pred  = np.asarray(q_pred)
        lower   = float(np.mean(y_true < q_pred))
        upper   = float(np.mean(y_true <= q_pred))
        u       = rng.uniform(0, 1, size=len(y_true))
        rand_pit = float(np.mean((y_true < q_pred) + u * (y_true == q_pred)))
        in_bounds = lower <= tau <= upper
        gap     = abs(rand_pit - tau)
        passes  = in_bounds or gap < 0.05
        results[tau] = dict(lower=lower, upper=upper, in_bounds=in_bounds,
                            rand_pit=rand_pit, gap=gap, passes=passes)
        print(f"  Q{tau*100:02.0f} {lower:>7.3f} {upper:>7.3f} {str(in_bounds):>9} "
              f"{rand_pit:>8.3f} {gap:>6.3f} {'✓' if passes else '⚠':>6}")
    n_pass  = sum(v['passes'] for v in results.values())
    verdict = "✓ PASSES" if n_pass >= len(results) * 0.80 else "⚠ FAILS"
    print(f"\n{n_pass}/{len(results)} pass  →  {verdict}")
    return results


# ── CLI self-test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    print("=" * 65)
    print("FG3M 3-Stage Hurdle Model — Self-Test")
    print("=" * 65)

    try:
        tt = pd.read_parquet('data/training_table.parquet')
        print(f"\nTraining table: {len(tt)} rows | {tt['player_id'].nunique()} players")
    except FileNotFoundError:
        print("ERROR: run train.py first"); sys.exit(1)

    fg3m_df = tt[tt['stat'] == 'fg3m'].copy() if 'stat' in tt.columns else tt.copy()
    print(f"FG3M rows: {len(fg3m_df)}")

    hurdle = FG3MHurdleModel()
    hurdle.fit(fg3m_df)

    print("\n=== Sentinel Tests ===")
    print(f"{'Player':<28} {'Line':>5} {'P(OVER)':>9} {'P(MEAN)':>9} {'Q50':>5} {'Arch'}")
    print("-" * 65)

    sentinels = [
        ("Clingan (rim runner)",    {'season_mean_fg3a': 0.3,  'mean_fg3a_last10': 0.2,
                                     'fg3_pct_safe': 0.25, 'zero_pct_fg3a': 0.95,
                                     'n_games_season': 60, 'exp_mp': 22}),
        ("Gary Payton II",          {'season_mean_fg3a': 1.8,  'mean_fg3a_last10': 1.8,
                                     'fg3_pct_safe': 0.31, 'zero_pct_fg3a': 0.45,
                                     'n_games_season': 56, 'exp_mp': 24}),
        ("Scottie Barnes",          {'season_mean_fg3a': 3.0,  'mean_fg3a_last10': 3.0,
                                     'fg3_pct_safe': 0.31, 'zero_pct_fg3a': 0.20,
                                     'n_games_season': 62, 'exp_mp': 34}),
        ("Miles Bridges",           {'season_mean_fg3a': 6.3,  'mean_fg3a_last10': 6.3,
                                     'fg3_pct_safe': 0.33, 'zero_pct_fg3a': 0.05,
                                     'n_games_season': 60, 'exp_mp': 35}),
        ("Jrue Holiday",            {'season_mean_fg3a': 6.5,  'mean_fg3a_last10': 6.5,
                                     'fg3_pct_safe': 0.39, 'zero_pct_fg3a': 0.03,
                                     'n_games_season': 36, 'exp_mp': 33}),
    ]

    for name, feats in sentinels:
        for line in [0.5, 1.5]:
            r = hurdle.predict_proba(feats, line)
            print(f"  {name:<28} {line:>5}  {r['p_over']:>8.1%}  "
                  f"{r['p_meaningful']:>8.1%}  {r['q50']:>4}  {r['archetype_name']}")

    print("\nExpected rough bounds:")
    print("  Clingan  0.5 → p_over 10–25%  | p_meaningful < 30%")
    print("  GP2      0.5 → p_over 30–48%")
    print("  Bridges  0.5 → p_over 68–85%")
    print("  Holiday  1.5 → p_over 60–80%")

    from nba_props_model.paths import MODEL_DIR
    out = MODEL_DIR / "fg3m_hurdle.pkl"
    hurdle.save(str(out))
    print(f"\nSaved to {out}")
