"""
fg3m_hurdle.py — Two-Part Hurdle Model for Three-Point Makes

Architecture:
    Part 1: P(fg3a > 0 | features) — calibrated classifier on attempt propensity
    Part 2: P(fg3m >= k) from Binomial(expected_fg3a, shrunk_fg3_pct)

    Final: P(fg3m > line) = P(fg3a > 0) * P(fg3m > line | fg3a > 0)

Hard constraints:
    - If P(fg3m = 0) >= 0.50: Q50 = 0
    - P(fg3m > 0) cannot exceed P(fg3a > 0)

Archetypes based on season_mean_fg3a:
    0: non-shooting big    (< 1.0)
    1: low-volume wing     (1.0 – 3.0)
    2: moderate shooter    (3.0 – 5.5)
    3: high-volume shooter (> 5.5)
"""

import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from scipy.stats import binom
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARCHETYPE_NAMES = {0: "non-shooting big", 1: "low-volume wing",
                   2: "moderate shooter",  3: "high-volume shooter"}
ARCHETYPE_PRIORS = {0: (0.3, 0.22), 1: (1.8, 0.33),
                    2: (4.2, 0.36),  3: (7.8, 0.38)}

def assign_archetype(season_mean_fg3a: float) -> int:
    if season_mean_fg3a < 1.0: return 0
    elif season_mean_fg3a < 3.0: return 1
    elif season_mean_fg3a < 5.5: return 2
    else: return 3

ATTEMPT_FEATURES = [
    'season_mean_fg3a', 'mean_fg3a_last10', 'mean_fg3a_last5',
    'ewma10_fg3a', 'zero_pct_fg3a', 'trend_fg3a',
    'per_min_fg3a_last10', 'per_min_fg3a_season', 'archetype',
]

def extract_features(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for c in cols:
        out[c] = df[c].fillna(0) if c in df.columns else 0.0
    return out


class FG3MHurdleModel:
    def __init__(self):
        self.attempt_model = None
        self.attempt_scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> 'FG3MHurdleModel':
        logger.info(f"Fitting FG3M hurdle model on {len(df)} rows...")
        df = df.copy()

        fg3a_col = 'season_mean_fg3a' if 'season_mean_fg3a' in df.columns else 'mean_fg3a_last10'
        df['archetype'] = df[fg3a_col].fillna(0).apply(assign_archetype)

        for arch, cnt in df['archetype'].value_counts().sort_index().items():
            logger.info(f"  Archetype {arch} ({ARCHETYPE_NAMES[arch]}): {cnt} ({cnt/len(df):.1%})")

        # Label: does player regularly attempt threes?
        if 'zero_pct_fg3a' in df.columns:
            y_attempt = (df['zero_pct_fg3a'] < 0.80).astype(int)
        elif 'actual' in df.columns:
            y_attempt = (df['actual'] > 0).astype(int)
        else:
            raise ValueError("Need zero_pct_fg3a or actual column")

        logger.info(f"  P(attempts threes) base rate: {y_attempt.mean():.3f}")

        X = extract_features(df, ATTEMPT_FEATURES)
        Xs = self.attempt_scaler.fit_transform(X)

        base = GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                          learning_rate=0.05, subsample=0.8,
                                          random_state=42)
        self.attempt_model = CalibratedClassifierCV(base, cv=5, method='isotonic')
        self.attempt_model.fit(Xs, y_attempt)

        oof = cross_val_predict(
            GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                       learning_rate=0.05, random_state=42),
            Xs, y_attempt, cv=5, method='predict_proba')[:, 1]
        logger.info(f"  OOF mean P(attempt): {oof.mean():.3f} vs actual {y_attempt.mean():.3f}")

        self.is_fitted = True
        logger.info("Done.")
        return self

    def predict_proba(self, features: dict, line: float) -> dict:
        if not self.is_fitted:
            raise RuntimeError("Call fit() first")

        features = dict(features)
        season_fg3a = features.get('season_mean_fg3a',
                       features.get('mean_fg3a_last10', 0))
        archetype = assign_archetype(season_fg3a)
        features['archetype'] = archetype
        prior_fg3a, prior_pct = ARCHETYPE_PRIORS[archetype]

        # Part 1
        X = np.array([[features.get(f, 0) for f in ATTEMPT_FEATURES]])
        Xs = self.attempt_scaler.transform(X)
        p_att = float(self.attempt_model.predict_proba(Xs)[0, 1])
        if archetype == 0:
            p_att = min(p_att, 0.35)

        # Shrunk fg3a
        obs_fg3a = features.get('mean_fg3a_last10',
                    features.get('season_mean_fg3a', prior_fg3a))
        n = max(int(features.get('n_games_season', 20)), 5)
        shrunk_fg3a = (obs_fg3a * n + prior_fg3a * 10) / (n + 10)
        exp_fg3a = max(round(shrunk_fg3a), 1)

        # Shrunk fg3_pct
        obs_pct = features.get('fg3_pct_shrunk', prior_pct)
        s_pct = float(np.clip(
            (obs_pct * obs_fg3a * n + prior_pct * 20) / (obs_fg3a * n + 20),
            0.08, 0.65))

        # Binomial
        k = int(np.floor(line)) + 1
        p_over = float(np.clip(p_att * (1 - binom.cdf(k-1, exp_fg3a, s_pct)),
                               0.0, p_att))
        p_zero = float((1 - p_att) + p_att * binom.pmf(0, exp_fg3a, s_pct))
        q50 = 0.0 if p_zero >= 0.50 else round(exp_fg3a * s_pct, 1)

        return {'p_attempts': round(p_att, 4), 'p_over': round(p_over, 4),
                'p_zero': round(p_zero, 4), 'q50': q50,
                'archetype': archetype, 'archetype_name': ARCHETYPE_NAMES[archetype],
                'shrunk_fg3a': round(shrunk_fg3a, 2), 'shrunk_pct': round(s_pct, 3),
                'expected_fg3a': exp_fg3a}

    def save(self, path: str):
        joblib.dump(self, path)
        logger.info(f"Saved → {path}")

    @classmethod
    def load(cls, path: str) -> 'FG3MHurdleModel':
        return joblib.load(path)


def evaluate_tov_calibration(y_true: np.ndarray, q_preds: dict) -> dict:
    rng = np.random.default_rng(42)
    results = {}
    print(f"\n=== Discrete-Aware TOV Calibration ===")
    print(f"n={len(y_true)}  zero%={(y_true==0).mean():.1%}  "
          f"mean={y_true.mean():.2f}  median={np.median(y_true):.1f}")
    print(f"\n{'Q':>5} {'Lower':>7} {'Upper':>7} {'InBounds':>9} {'RandPIT':>8} {'Gap':>6} {'':>6}")
    print("-" * 50)
    for tau, q_pred in sorted(q_preds.items()):
        q_pred = np.asarray(q_pred)
        lower = float(np.mean(y_true < q_pred))
        upper = float(np.mean(y_true <= q_pred))
        u = rng.uniform(0, 1, size=len(y_true))
        rand_pit = float(np.mean((y_true < q_pred) + u * (y_true == q_pred)))
        in_bounds = lower <= tau <= upper
        gap = abs(rand_pit - tau)
        passes = in_bounds or gap < 0.05
        results[tau] = dict(lower=lower, upper=upper, in_bounds=in_bounds,
                            rand_pit=rand_pit, gap=gap, passes=passes)
        print(f"  Q{tau*100:02.0f} {lower:>7.3f} {upper:>7.3f} {str(in_bounds):>9} "
              f"{rand_pit:>8.3f} {gap:>6.3f} {'✓' if passes else '⚠':>6}")
    n_pass = sum(v['passes'] for v in results.values())
    verdict = "✓ PASSES" if n_pass >= len(results) * 0.80 else "⚠ FAILS"
    print(f"\n{n_pass}/{len(results)} pass  →  {verdict}")
    return results


if __name__ == "__main__":
    import sys
    print("=" * 60)
    print("FG3M Hurdle Model + TOV Discrete Calibration")
    print("=" * 60)

    try:
        tt = pd.read_parquet('data/training_table.parquet')
        print(f"\nTraining table: {len(tt)} rows | {tt['player_id'].nunique()} players")
    except FileNotFoundError:
        print("ERROR: run train.py first"); sys.exit(1)

    # FG3M
    fg3m_df = tt[tt['stat'] == 'fg3m'].copy() if 'stat' in tt.columns else tt.copy()
    print(f"\nFG3M rows: {len(fg3m_df)}")
    if 'actual' in fg3m_df.columns:
        print(f"Zero fraction: {(fg3m_df['actual']==0).mean():.1%}")
    print(f"season_mean_fg3a: {fg3m_df['season_mean_fg3a'].min():.1f}–{fg3m_df['season_mean_fg3a'].max():.1f}")

    hurdle = FG3MHurdleModel()
    hurdle.fit(fg3m_df)

    print("\n=== Sentinel Tests ===")
    print(f"{'Player':<28} {'Line':>5} {'P(OVER)':>9} {'Q50':>5} {'Arch'}")
    print("-" * 60)

    sentinels = [
        ("Clingan (rim runner)",    {'season_mean_fg3a': 0.3,  'mean_fg3a_last10': 0.2,
                                     'fg3_pct_shrunk': 0.25, 'zero_pct_fg3a': 0.95,
                                     'zero_pct_fg3m': 0.95, 'n_games_season': 60}),
        ("Gary Payton II",          {'season_mean_fg3a': 1.8,  'mean_fg3a_last10': 1.8,
                                     'fg3_pct_shrunk': 0.31, 'zero_pct_fg3a': 0.45,
                                     'zero_pct_fg3m': 0.64, 'n_games_season': 56}),
        ("Scottie Barnes",          {'season_mean_fg3a': 3.0,  'mean_fg3a_last10': 3.0,
                                     'fg3_pct_shrunk': 0.31, 'zero_pct_fg3a': 0.20,
                                     'zero_pct_fg3m': 0.48, 'n_games_season': 62}),
        ("Miles Bridges (shooter)", {'season_mean_fg3a': 6.3,  'mean_fg3a_last10': 6.3,
                                     'fg3_pct_shrunk': 0.33, 'zero_pct_fg3a': 0.05,
                                     'zero_pct_fg3m': 0.18, 'n_games_season': 60}),
        ("Jrue Holiday (shooter)",  {'season_mean_fg3a': 6.5,  'mean_fg3a_last10': 6.5,
                                     'fg3_pct_shrunk': 0.39, 'zero_pct_fg3a': 0.03,
                                     'zero_pct_fg3m': 0.11, 'n_games_season': 36}),
        ("Kon Knueppel (vol)",      {'season_mean_fg3a': 8.0,  'mean_fg3a_last10': 8.0,
                                     'fg3_pct_shrunk': 0.44, 'zero_pct_fg3a': 0.01,
                                     'zero_pct_fg3m': 0.03, 'n_games_season': 64}),
    ]

    for name, feats in sentinels:
        for line in [0.5, 1.5]:
            r = hurdle.predict_proba(feats, line)
            print(f"  {name:<28} {line:>5}  {r['p_over']:>8.1%}  {r['q50']:>4}  {r['archetype_name']}")

    print("\nExpected:")
    print("  Clingan   0.5 → 15–30%  |  GP2    0.5 → 30–45%")
    print("  Bridges   0.5 → 70–85%  |  Holiday 1.5 → 65–80%")

    Path('model_cache').mkdir(exist_ok=True)
    hurdle.save('model_cache/fg3m_hurdle.pkl')
    print(f"\n✓ Saved to model_cache/fg3m_hurdle.pkl")

    # TOV
    print("\n" + "=" * 60)
    print("TOV Discrete-Aware Calibration")
    print("=" * 60)
    tov_df = tt[tt['stat'] == 'tov'].copy() if 'stat' in tt.columns else pd.DataFrame()
    if 'actual' not in tov_df.columns or len(tov_df) < 50:
        print(f"TOV rows in training table: {len(tov_df)}")
        tov_pkls = list(Path('model_cache').glob('tov_q*.pkl'))
        print(f"TOV model files: {[p.name for p in sorted(tov_pkls)]}")
        if not tov_pkls:
            print("No TOV pkl files found. Check model_cache/ after retrain.")
        else:
            pgs = pd.read_parquet('data/player_game_stats.parquet')
            y_tov = pgs['turnover'].dropna().values
            print(f"\nTurnover distribution from player_game_stats ({len(y_tov)} rows):")
            print(f"  Zero%={(y_tov==0).mean():.1%}  Mean={y_tov.mean():.2f}  "
                  f"Median={np.median(y_tov):.1f}  P90={np.percentile(y_tov,90):.1f}")
            print("\nNote: full discrete calibration requires aligned (features, actuals) pairs.")
            print("This is available in the training table after retrain with 'stat' column present.")
    else:
        y_tov = tov_df['actual'].values
        feat_cols = [c for c in tov_df.columns
                     if c not in {'actual','stat','player_id','player_name',
                                  'game_id','game_date','usage_bucket','mp_bucket'}]
        X_tov = tov_df[feat_cols].fillna(0)
        q_preds = {}
        for tau in [0.10,0.20,0.25,0.33,0.40,0.50,0.60,0.67,0.75,0.80,0.90]:
            p = f'model_cache/tov_q{int(tau*100)}.pkl'
            if Path(p).exists():
                try: q_preds[tau] = joblib.load(p).predict(X_tov)
                except: pass
        if q_preds:
            evaluate_tov_calibration(y_tov, q_preds)
        else:
            print("No TOV pkl files found in model_cache/")
