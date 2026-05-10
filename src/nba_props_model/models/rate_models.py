"""
NBA Props Model — per-minute rate models for the main counting stats.

Each of {pts, reb, ast, tov} is modeled as a per-minute rate distribution
via LightGBM quantile regression at tau in
(0.10, 0.25, 0.50, 0.75, 0.90). The rate distribution is later combined
with the state-aware minutes distribution by
`nba_props_model.models.simulation.simulate_stat_pmf` to produce the full
stat PMF/CDF.

Features used
-------------
Per-minute rate feature gate per stat — production features come from
`nba_props_model.features.engineering` (via `get_feature_cols_for_stat`),
filtered to the stable per-minute-rate subset. Role/opportunity features
are included; teammate-absence features from the Phase 2 pipeline land
here so rate shifts under teammate absence are learnable, not just
minutes shifts.

Training label
--------------
target_rate = stat / max(min, 1.0)    # per-minute rate

Rows with min < 3 are filtered from training to avoid divide-by-near-zero.
Rate is clipped at a conservative upper bound per stat to suppress
short-burst outliers.

Artifacts
---------
  artifacts/models/rate_{stat}_q{10,25,50,75,90}.pkl
  artifacts/models/rate_{stat}_features.pkl
  artifacts/models/rate_models_meta.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from nba_props_model.paths import MODEL_DIR

logger = logging.getLogger(__name__)

RATE_STATS = ("pts", "reb", "ast", "tov")
RATE_QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)

# Conservative upper clips on per-minute rate (coarse anti-outlier).
# Most NBA starters cap at ~1.2 pts/min across a career.
RATE_CLIP: dict[str, float] = {
    "pts": 1.6,   # exceptional games do reach ~1.5
    "reb": 0.9,
    "ast": 0.8,
    "tov": 0.5,
}

MIN_MINUTES_FOR_RATE = 3.0


def _rate_feature_cols(df: pd.DataFrame, stat: str) -> list[str]:
    """Return the feature columns present on df used for this stat's rate.

    Intentionally permissive: whatever engineering.py emits that looks
    numeric and not a leakage target is accepted. Explicit excludes below.
    """
    excluded = {
        "target", "target_rate", "target_minutes", "game_id", "game_date",
        "player_id", "team_id", "home_team_id", "visitor_team_id",
        "season", "team_abbr", "player_name", "position",
        "min", "pts", "reb", "ast", "fg3m", "stl", "blk", "tov",
        "turnover", "fga", "fg3a", "fta", "ftm", "oreb", "dreb", "pf",
        "plus_minus", "min_numeric",
    }
    out = []
    for c in df.columns:
        if c in excluded:
            continue
        try:
            # If the column is numeric-like (or castable), include.
            pd.to_numeric(df[c].head(50), errors="raise")
        except Exception:
            continue
        out.append(c)
    return out


def train_rate_models(
    training_df: pd.DataFrame,
    stats: tuple[str, ...] = RATE_STATS,
) -> dict:
    """Fit rate quantile ladders per stat in `stats`.

    `training_df` is expected to contain the full feature engineering
    output with the raw stat columns (pts, reb, ast, turnover) and a
    `min` column used to compute per-minute rates.
    """
    import lightgbm as lgb

    if training_df is None or training_df.empty:
        return {}

    df = training_df.copy()
    df["min_numeric"] = pd.to_numeric(df["min"], errors="coerce").fillna(0.0)
    df = df[df["min_numeric"] >= MIN_MINUTES_FOR_RATE].reset_index(drop=True)
    if df.empty:
        logger.warning("rate_models: no eligible rows (min >= %s)", MIN_MINUTES_FOR_RATE)
        return {}

    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"])
    else:
        df["game_date"] = pd.Timestamp.now()

    meta: dict = {"stats": [], "quantiles": list(RATE_QUANTILES)}
    for stat in stats:
        source_col = "turnover" if stat == "tov" else stat
        if source_col not in df.columns:
            logger.warning("rate_models: source column %r not present; skipping %s",
                           source_col, stat)
            continue
        y_raw = pd.to_numeric(df[source_col], errors="coerce").fillna(0.0)
        rate = (y_raw / df["min_numeric"]).clip(lower=0.0, upper=RATE_CLIP[stat])
        feat_cols = _rate_feature_cols(df, stat)
        X = df[feat_cols].apply(pd.to_numeric, errors="coerce")

        cutoff = df["game_date"].quantile(0.85)
        tr_mask = df["game_date"] <= cutoff
        X_tr, X_val = X[tr_mask], X[~tr_mask]
        y_tr, y_val = rate[tr_mask], rate[~tr_mask]

        joblib.dump(feat_cols, MODEL_DIR / f"rate_{stat}_features.pkl")
        logger.info(f"  rate_{stat}: {len(X_tr):,} train / {len(X_val):,} val rows, "
                    f"{len(feat_cols)} features")

        stat_meta: dict = {
            "n_train": int(len(X_tr)), "n_val": int(len(X_val)),
            "n_features": len(feat_cols), "clip_upper": RATE_CLIP[stat],
            "calibration": {},
        }
        for q in RATE_QUANTILES:
            m = lgb.LGBMRegressor(
                objective="quantile", alpha=q,
                n_estimators=400, num_leaves=63, learning_rate=0.04,
                min_child_samples=20, feature_fraction=0.8,
                bagging_fraction=0.8, bagging_freq=1,
                verbosity=-1, random_state=42,
            )
            m.fit(X_tr, y_tr)
            qpct = int(round(q * 100))
            joblib.dump(m, MODEL_DIR / f"rate_{stat}_q{qpct:02d}.pkl")
            if len(X_val) > 50:
                emp = float(np.mean(y_val.values <= m.predict(X_val)))
                stat_meta["calibration"][f"q{qpct}"] = {
                    "empirical": emp, "err": abs(emp - q),
                }
        meta["stats"].append(stat_meta | {"stat": stat})

    with open(MODEL_DIR / "rate_models_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    return meta


# ── Inference ────────────────────────────────────────────────────────────────


def _coerce_rate_feature_value(value):
    """Coerce one feature value to a numeric scalar, mirroring training-time
    pd.to_numeric(errors='coerce'). Late-season rows can include
    object-dtype fields (e.g. is_returning_from_absence,
    minutes_restriction_flag) that LightGBM rejects with
    'pandas dtypes must be int, float or bool', causing every quantile
    prediction to fail silently. Returning float (or NaN for unconvertible
    values) lets LightGBM use its learned missing-value path.
    """
    if value is None:
        return np.nan
    if isinstance(value, (dict, list, tuple, set)):
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


_RATE_CACHE: dict[str, dict] = {}


def _load_rate_artifacts(stat: str) -> Optional[dict]:
    if stat in _RATE_CACHE:
        return _RATE_CACHE[stat]
    feat_path = MODEL_DIR / f"rate_{stat}_features.pkl"
    if not feat_path.exists():
        return None
    features = joblib.load(feat_path)
    quantiles: dict[int, object] = {}
    for q in RATE_QUANTILES:
        qpct = int(round(q * 100))
        p = MODEL_DIR / f"rate_{stat}_q{qpct:02d}.pkl"
        if p.exists():
            quantiles[qpct] = joblib.load(p)
    if not quantiles:
        return None
    _RATE_CACHE[stat] = {"features": features, "quantiles": quantiles}
    return _RATE_CACHE[stat]


def rate_quantiles(stat: str, feature_row: dict) -> Optional[dict[int, float]]:
    """Predict per-minute rate quantiles for one player-game.

    Returns None when artifacts are unavailable or every quantile fails.
    Coerces feature values to numeric (training-time pd.to_numeric semantics)
    so object-dtype fields don't silently suppress OOF emission.
    """
    art = _load_rate_artifacts(stat)
    if art is None:
        logger.warning("rate_quantiles[%s]: missing rate artifacts", stat)
        return None
    feats = list(art["features"])
    row = {f: _coerce_rate_feature_value(feature_row.get(f, 0.0)) for f in feats}
    X = pd.DataFrame([row], columns=feats)
    out: dict[int, float] = {}
    failures: list[str] = []
    for qpct, m in art["quantiles"].items():
        try:
            pred = float(m.predict(X)[0])
            if np.isfinite(pred):
                out[qpct] = float(max(0.0, pred))
            else:
                failures.append(f"q{qpct}:nonfinite")
        except Exception as exc:
            failures.append(f"q{qpct}:{type(exc).__name__}:{exc}")
    if not out:
        logger.warning(
            "rate_quantiles[%s]: all quantile predictions failed; "
            "n_features=%d failures_sample=%s",
            stat, len(feats), failures[:3],
        )
        return None
    return out
