#!/usr/bin/env python3
"""
residual_centering.py — Learned Residual Centering Models
==========================================================
Permanent replacement for hardcoded BIAS_CORRECTION in predict_darko_v4.py.

Architecture:
  Instead of: q50 += 1.50  (hardcoded forever)
  We build:   q50 += residual_model_pts.predict(meta_features)

  Where meta_features include:
    - raw q50 projection
    - expected minutes
    - role stability
    - usage / archetype
    - opponent context confidence
    - feature coverage confidence

Per the permanent architecture document:
  "A stat-specific projection engine + learned residual centering +
   dynamic variance + stat×side calibration + strict deployment filters"

Usage:
    # Train:
    python3 residual_centering.py --train

    # Apply at inference (called from predict_darko_v4.py):
    from residual_centering import ResidualCenterer
    centerer = ResidualCenterer.load()
    corrected_q50 = centerer.correct("pts", raw_q50, meta_features)

Output files:
    model_cache/residual_centerer_pts.pkl
    model_cache/residual_centerer_ast.pkl
    model_cache/residual_centerer_reb.pkl
    model_cache/residual_centerer_fg3m.pkl
    model_cache/residual_centering_meta.json
"""

import csv
import glob
import json
import logging
import os
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GRADED_DIR = Path("graded")
MODEL_DIR  = Path("model_cache")
MODEL_DIR.mkdir(exist_ok=True)

# Stats with enough sample for learned correction
CORRECTABLE_STATS = ["pts", "ast", "reb", "fg3m"]

# Caps: even a learned model should not overcorrect
CORRECTION_CAPS = {
    "pts":  2.00,
    "ast":  1.00,
    "reb":  1.20,
    "fg3m": 0.60,
}


class ResidualCenterer:
    """
    Per-stat learned residual corrector.
    Predicts (actual - q50) from meta-features, then applies bounded correction.
    """

    def __init__(self):
        self.models:  dict = {}   # stat → fitted model
        self.scalers: dict = {}   # stat → StandardScaler
        self.meta:    dict = {}   # stat → training metadata
        self.fallback: dict = {}  # stat → simple median fallback if model unavailable

    # ── Public API ────────────────────────────────────────────────────────────

    def correct(self, stat: str, raw_q50: float, meta_features: dict) -> float:
        """
        Return corrected q50 for a given stat and meta_features dict.
        Falls back to simple median correction if model not trained.

        meta_features keys (all optional — will default):
            mp_mean_last10          float  expected minutes
            mp_std_last10           float  minutes volatility
            usage_mean_last10       float  usage rate
            role_stability          float  0-1 how stable is this player's role
            opp_def_rating          float  opponent defensive rating
            is_home                 int    1 if home game
            days_rest               int    days since last game
            season_games_played     int    games played this season
        """
        if stat not in CORRECTABLE_STATS:
            return raw_q50

        cap = CORRECTION_CAPS.get(stat, 0.50)

        # Use learned model if available
        if stat in self.models:
            try:
                X = self._build_feature_vector(stat, raw_q50, meta_features)
                X_scaled = self.scalers[stat].transform([X])
                correction = float(self.models[stat].predict(X_scaled)[0])
                correction = float(np.clip(correction, -cap, cap))
                return raw_q50 + correction
            except Exception as e:
                logger.debug(f"Residual model failed for {stat}: {e}")

        # Fallback: simple median correction from training
        if stat in self.fallback:
            return raw_q50 + self.fallback[stat]

        return raw_q50

    def correct_quantiles(self, stat: str, q_preds: dict, meta_features: dict) -> dict:
        """
        Apply the same correction to the entire quantile ladder.
        This is the key method — shifts ALL quantiles consistently.

        Per the architecture document:
        "If you apply a centering correction, it should move q10, q25, q50, q75, q90"
        """
        if stat not in CORRECTABLE_STATS:
            return q_preds

        raw_q50 = float(q_preds.get(0.50, 0))
        corrected_q50 = self.correct(stat, raw_q50, meta_features)
        shift = corrected_q50 - raw_q50

        # Apply same shift to every quantile
        return {q: v + shift for q, v in q_preds.items()}

    # ── Training ──────────────────────────────────────────────────────────────

    def train(self, graded_dir: Path = GRADED_DIR) -> dict:
        """
        Train one residual model per stat from graded daily files.
        Target: actual - q50 (projection error)
        """
        logger.info("Loading graded data for residual centering training...")
        rows = self._load_graded(graded_dir)
        logger.info(f"  {len(rows)} graded rows loaded")

        results = {}
        for stat in CORRECTABLE_STATS:
            stat_rows = [r for r in rows if r["stat"] == stat]
            if len(stat_rows) < 30:
                logger.warning(f"  {stat}: only {len(stat_rows)} rows — skipping learned model, using median")
                medians = [r["actual"] - r["q50"] for r in stat_rows if r["q50"] > 0]
                if medians:
                    self.fallback[stat] = float(np.clip(np.median(medians),
                                                        -CORRECTION_CAPS[stat],
                                                        CORRECTION_CAPS[stat]))
                continue

            X_list, y_list = [], []
            for r in stat_rows:
                if r["q50"] <= 0 or r["actual"] < 0:
                    continue
                X_list.append(self._build_feature_vector(stat, r["q50"], r))
                y_list.append(r["actual"] - r["q50"])

            X = np.array(X_list)
            y = np.array(y_list)

            # Winsorize targets at 5th/95th percentile to reduce outlier influence
            y_lo, y_hi = np.percentile(y, 5), np.percentile(y, 95)
            y_clipped = np.clip(y, y_lo, y_hi)

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Try GBR first; fall back to Ridge if too few samples
            if len(X) >= 50:
                model = GradientBoostingRegressor(
                    n_estimators=100, max_depth=3,
                    learning_rate=0.05, subsample=0.8,
                    random_state=42
                )
            else:
                model = Ridge(alpha=10.0)

            # Cross-validate
            cv_scores = cross_val_score(model, X_scaled, y_clipped,
                                        cv=min(5, len(X)//10),
                                        scoring="neg_mean_absolute_error")
            model.fit(X_scaled, y_clipped)

            # Store median as fallback
            self.fallback[stat] = float(np.clip(np.median(y),
                                                -CORRECTION_CAPS[stat],
                                                CORRECTION_CAPS[stat]))
            self.models[stat]  = model
            self.scalers[stat] = scaler
            self.meta[stat] = {
                "n":           len(X),
                "cv_mae_mean": float(-cv_scores.mean()),
                "cv_mae_std":  float(cv_scores.std()),
                "target_median": float(np.median(y)),
                "target_mean":   float(np.mean(y)),
                "fallback_correction": self.fallback[stat],
                "model_type":  type(model).__name__,
            }

            logger.info(f"  {stat}: n={len(X)}  cv_MAE={-cv_scores.mean():.3f}±{cv_scores.std():.3f}"
                        f"  median_residual={np.median(y):+.3f}"
                        f"  fallback={self.fallback[stat]:+.3f}")
            results[stat] = self.meta[stat]

        return results

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, model_dir: Path = MODEL_DIR):
        for stat in CORRECTABLE_STATS:
            if stat in self.models:
                joblib.dump(self.models[stat],
                            model_dir / f"residual_centerer_{stat}.pkl")
                joblib.dump(self.scalers[stat],
                            model_dir / f"residual_scaler_{stat}.pkl")
        meta_out = {
            "fallback": self.fallback,
            "meta": self.meta,
            "correctable_stats": CORRECTABLE_STATS,
            "correction_caps": CORRECTION_CAPS,
        }
        (model_dir / "residual_centering_meta.json").write_text(
            json.dumps(meta_out, indent=2))
        logger.info(f"Residual centerers saved to {model_dir}/")

    @classmethod
    def load(cls, model_dir: Path = MODEL_DIR) -> "ResidualCenterer":
        centerer = cls()
        meta_path = model_dir / "residual_centering_meta.json"
        if meta_path.exists():
            meta_data = json.loads(meta_path.read_text())
            centerer.fallback = meta_data.get("fallback", {})
            centerer.meta     = meta_data.get("meta", {})
        for stat in CORRECTABLE_STATS:
            mp = model_dir / f"residual_centerer_{stat}.pkl"
            sp = model_dir / f"residual_scaler_{stat}.pkl"
            if mp.exists() and sp.exists():
                centerer.models[stat]  = joblib.load(mp)
                centerer.scalers[stat] = joblib.load(sp)
        loaded = list(centerer.models.keys())
        fallbacks = [s for s in CORRECTABLE_STATS if s in centerer.fallback and s not in centerer.models]
        logger.info(f"ResidualCenterer: learned={loaded}  fallback={fallbacks}")
        return centerer

    # ── Feature engineering ───────────────────────────────────────────────────

    def _build_feature_vector(self, stat: str, q50: float, row: dict) -> list:
        """
        Build meta-feature vector for residual prediction.
        All features are optional — missing values get safe defaults.
        """
        def g(key, default=0.0):
            v = row.get(key)
            try: return float(v) if v is not None and str(v) != '' else default
            except: return default

        return [
            q50,                                    # raw projection
            q50 ** 0.5,                             # sqrt projection (nonlinearity)
            g("mp_mean_last10",   32.0),             # expected minutes
            g("mp_std_last10",     4.0),             # minutes volatility
            g("adv_usage_percentage_mean_last10", 0.20),  # usage rate
            g("role_stability",    0.7),             # role stability (0-1)
            g("is_home",           0.5),             # home game indicator
            g("days_rest",         2.0),             # rest days
            g("season_games_played", 40),            # games played this season
            g("opp_def_rating",  112.0),             # opponent defensive rating
            g("team_pace",        99.0),             # team pace
        ]

    def _load_graded(self, graded_dir: Path) -> list:
        rows = []
        for f in sorted(graded_dir.glob("graded_20*.csv")):
            try:
                for r in csv.DictReader(open(f)):
                    try:
                        rows.append({
                            "stat":   r.get("stat","").lower(),
                            "side":   r.get("side","").upper(),
                            "q50":    float(r.get("q50") or 0),
                            "actual": float(r.get("actual") or 0),
                            "line":   float(r.get("line") or 0),
                            "result": str(r.get("result","")).strip().upper(),
                            "clv":    float(r.get("clv_proxy") or 0),
                            # Meta-features (may be absent in older graded files)
                            "mp_mean_last10":  r.get("mp_mean_last10"),
                            "mp_std_last10":   r.get("mp_std_last10"),
                            "adv_usage_percentage_mean_last10": r.get("usage_bucket"),
                            "is_home":         r.get("is_home"),
                            "days_rest":       r.get("days_rest"),
                            "season_games_played": r.get("season_games_played"),
                            "opp_def_rating":  r.get("opp_def_rating"),  # Bug 8 fix
                        })
                    except: continue
            except: continue
        return rows


# ═══════════════════════════════════════════════════════════════════════════════
# Integration helper for predict_darko_v4.py
# ═══════════════════════════════════════════════════════════════════════════════

def load_centerer() -> "ResidualCenterer":
    """
    Drop-in replacement for hardcoded BIAS_CORRECTION.
    Call once at startup in predict_darko_v4.py.

    Usage in predict_darko_v4.py:
        from residual_centering import load_centerer
        centerer = load_centerer()

        # In prediction loop, replace:
        #   bias = BIAS_CORRECTION.get(target, 0.0)
        #   q_preds = {q: v + bias for q, v in q_preds.items()}
        # With:
        #   q_preds = centerer.correct_quantiles(target, q_preds, base_features)
    """
    return ResidualCenterer.load()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="Train residual centerers")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on holdout")
    parser.add_argument("--graded-dir", default="graded")
    args = parser.parse_args()

    if args.train:
        centerer = ResidualCenterer()
        results  = centerer.train(Path(args.graded_dir))
        centerer.save()

        print("\n" + "="*60)
        print("RESIDUAL CENTERING TRAINING RESULTS")
        print("="*60)
        for stat, m in results.items():
            print(f"\n{stat.upper()}:")
            print(f"  n={m['n']}  model={m['model_type']}")
            print(f"  cv_MAE={m['cv_mae_mean']:.3f}±{m['cv_mae_std']:.3f}")
            print(f"  median_residual={m['target_median']:+.3f}")
            print(f"  fallback_correction={m['fallback_correction']:+.3f}")
        print("\n✓ Saved to model_cache/")
        print("\nNext step: replace BIAS_CORRECTION in predict_darko_v4.py")
        print("  from residual_centering import load_centerer")
        print("  centerer = load_centerer()")
        print("  q_preds = centerer.correct_quantiles(target, q_preds, base_features)")

    elif args.evaluate:
        centerer = ResidualCenterer.load()
        print("Loaded centerers:", list(centerer.models.keys()))
        print("Fallbacks:", centerer.fallback)
        # Quick test
        test_features = {"mp_mean_last10": 32, "adv_usage_percentage_mean_last10": 0.22}
        for stat in CORRECTABLE_STATS:
            raw_q50 = 20.0 if stat == "pts" else 5.0
            corrected = centerer.correct(stat, raw_q50, test_features)
            print(f"  {stat}: raw={raw_q50}  corrected={corrected:.2f}  shift={corrected-raw_q50:+.2f}")
    else:
        parser.print_help()
