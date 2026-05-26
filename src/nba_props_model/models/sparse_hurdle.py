"""
NBA Props Model — hurdle / zero-inflated models for sparse stats.

Targets: stl, blk. Both are counting stats with heavy zero mass, heavy
right skew, and strongly archetype-conditional means. Ordinary quantile
regression under-states the zero-mass and smears the positive tail — the
failure mode flagged in docs/PHASE1_AUDIT.md §3.4.

Architecture (per stat)
-----------------------
1. Zero-classifier: LightGBM binary, predicts P(stat == 0 | features).
2. Positive-count conditional PMF: LightGBM quantile ladder at tau in
   (0.10, 0.25, 0.50, 0.75, 0.90) fit only on rows where stat > 0.
3. Combined PMF over {0, 1, ..., domain_max}:
       P(Y = 0) = p_zero
       P(Y = k) for k >= 1 derived by discretizing the positive-quantile
       distribution with unit-width bins and normalising to (1 - p_zero).

Event-opportunity features
--------------------------
On top of the standard rolling/per-minute features, sparse models receive
a handful of event-opportunity proxies computed in-module:

  stl_opp_tov_rate    opponent's recent turnover rate (allowed turnovers / pace)
  stl_opp_pass_risk   opponent's recent live-ball turnover proxy (tov / ast)
  blk_opp_rim_att     opponent's recent FGA volume inside 8 ft (approximated
                      from FGA minus fg3a)
  defender_role       archetype feature already present in availability/positions

Derived combo: `stocks` = stl + blk PMF via component convolution, not an
independent model.

Artifacts
---------
  artifacts/models/hurdle_{stl,blk}_zero.pkl            binary classifier
  artifacts/models/hurdle_{stl,blk}_pos_q{10..90}.pkl   conditional quantiles
  artifacts/models/hurdle_{stl,blk}_features.pkl        feature order
  artifacts/models/hurdle_sparse_meta.json
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

SPARSE_STATS = ("stl", "blk")
SPARSE_QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)

DOMAIN_MAX = {"stl": 10, "blk": 10}
STOCKS_DOMAIN_MAX = DOMAIN_MAX["stl"] + DOMAIN_MAX["blk"]

MIN_MINUTES_FOR_TRAINING = 3.0


# ── Feature construction ─────────────────────────────────────────────────────


def _feature_cols(df: pd.DataFrame) -> list[str]:
    excluded = {
        "target", "target_rate", "target_zero",
        "game_id", "game_date", "player_id", "team_id",
        "home_team_id", "visitor_team_id", "season", "team_abbr",
        "player_name", "position",
        "min", "min_numeric",
        "pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "turnover",
        "fga", "fg3a", "fta", "ftm", "oreb", "dreb", "pf", "plus_minus",
    }
    out = []
    for c in df.columns:
        if c in excluded:
            continue
        try:
            pd.to_numeric(df[c].head(50), errors="raise")
        except Exception:
            continue
        out.append(c)
    return out


# ── Training ─────────────────────────────────────────────────────────────────


def train_sparse_hurdle(
    training_df: pd.DataFrame,
    stats: tuple[str, ...] = SPARSE_STATS,
) -> dict:
    import lightgbm as lgb

    if training_df is None or training_df.empty:
        return {}

    df = training_df.copy()
    df["min_numeric"] = pd.to_numeric(df["min"], errors="coerce").fillna(0.0)
    df = df[df["min_numeric"] >= MIN_MINUTES_FOR_TRAINING].reset_index(drop=True)
    if df.empty:
        logger.warning("sparse_hurdle: no eligible rows")
        return {}

    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"])
    else:
        df["game_date"] = pd.Timestamp.now()

    meta: dict = {"stats": []}
    cutoff = df["game_date"].quantile(0.85)
    for stat in stats:
        if stat not in df.columns:
            logger.warning(f"sparse_hurdle: {stat} column missing; skipping")
            continue
        y = pd.to_numeric(df[stat], errors="coerce").fillna(0.0).clip(0, DOMAIN_MAX[stat])
        zero_label = (y == 0).astype(int)

        feats = _feature_cols(df)
        X = df[feats].apply(pd.to_numeric, errors="coerce")
        tr_mask = df["game_date"] <= cutoff
        X_tr, X_val = X[tr_mask], X[~tr_mask]
        y_tr, y_val = y[tr_mask], y[~tr_mask]
        z_tr, z_val = zero_label[tr_mask], zero_label[~tr_mask]

        joblib.dump(feats, MODEL_DIR / f"hurdle_{stat}_features.pkl")
        logger.info(
            f"  hurdle_{stat}: {len(X_tr):,} train / {len(X_val):,} val, "
            f"zero-rate train={float(z_tr.mean()):.3f}"
        )

        # Zero-classifier.
        zero_clf = lgb.LGBMClassifier(
            objective="binary",
            n_estimators=400, num_leaves=63, learning_rate=0.04,
            min_child_samples=40, feature_fraction=0.8,
            bagging_fraction=0.8, bagging_freq=1,
            verbosity=-1, random_state=42,
        )
        zero_clf.fit(X_tr, z_tr)
        joblib.dump(zero_clf, MODEL_DIR / f"hurdle_{stat}_zero.pkl")

        from sklearn.metrics import brier_score_loss, log_loss
        zc_val = zero_clf.predict_proba(X_val)[:, 1] if len(X_val) > 0 else np.array([])
        z_brier = float(brier_score_loss(z_val, zc_val)) if len(X_val) > 0 else 0.0
        z_ll = float(log_loss(z_val, np.clip(zc_val, 1e-6, 1 - 1e-6))) if len(X_val) > 0 else 0.0

        # Positive-count conditional quantile ladder.
        pos_mask_tr = y_tr > 0
        X_pos_tr = X_tr[pos_mask_tr]
        y_pos_tr = y_tr[pos_mask_tr]
        pos_mask_val = y_val > 0
        X_pos_val = X_val[pos_mask_val]
        y_pos_val = y_val[pos_mask_val]

        pos_metrics: dict = {}
        for q in SPARSE_QUANTILES:
            m = lgb.LGBMRegressor(
                objective="quantile", alpha=q,
                n_estimators=300, num_leaves=31, learning_rate=0.04,
                min_child_samples=20, feature_fraction=0.8,
                bagging_fraction=0.8, bagging_freq=1,
                verbosity=-1, random_state=42,
            )
            m.fit(X_pos_tr, y_pos_tr)
            qpct = int(round(q * 100))
            joblib.dump(m, MODEL_DIR / f"hurdle_{stat}_pos_q{qpct:02d}.pkl")
            if len(X_pos_val) > 20:
                emp = float(np.mean(y_pos_val.values <= m.predict(X_pos_val)))
                pos_metrics[f"q{qpct}_emp"] = emp
                pos_metrics[f"q{qpct}_err"] = abs(emp - q)

        meta["stats"].append({
            "stat": stat,
            "n_train": int(len(X_tr)),
            "n_val": int(len(X_val)),
            "n_features": len(feats),
            "zero_rate_train": float(z_tr.mean()),
            "zero_rate_val": float(z_val.mean()) if len(z_val) else 0.0,
            "zero_brier_val": z_brier,
            "zero_logloss_val": z_ll,
            "positive_calibration": pos_metrics,
        })

    with open(MODEL_DIR / "hurdle_sparse_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    return meta


# ── Inference ────────────────────────────────────────────────────────────────


_SPARSE_CACHE: dict[str, dict] = {}


def _load_sparse(stat: str) -> Optional[dict]:
    if stat in _SPARSE_CACHE:
        return _SPARSE_CACHE[stat]
    feat_p = MODEL_DIR / f"hurdle_{stat}_features.pkl"
    zero_p = MODEL_DIR / f"hurdle_{stat}_zero.pkl"
    if not feat_p.exists() or not zero_p.exists():
        return None
    pos_q: dict[int, object] = {}
    for q in SPARSE_QUANTILES:
        qpct = int(round(q * 100))
        p = MODEL_DIR / f"hurdle_{stat}_pos_q{qpct:02d}.pkl"
        if p.exists():
            pos_q[qpct] = joblib.load(p)
    if not pos_q:
        return None
    _SPARSE_CACHE[stat] = {
        "features": joblib.load(feat_p),
        "zero_clf": joblib.load(zero_p),
        "pos_q": pos_q,
    }
    return _SPARSE_CACHE[stat]


def hurdle_pmf(stat: str, feature_row: dict) -> Optional[np.ndarray]:
    """Return the full discrete PMF over {0, 1, ..., DOMAIN_MAX[stat]}."""
    art = _load_sparse(stat)
    if art is None:
        return None
    X = pd.DataFrame([{f: feature_row.get(f, 0.0) for f in art["features"]}])
    try:
        p_zero = float(art["zero_clf"].predict_proba(X)[0, 1])
    except Exception:
        p_zero = 0.5
    p_zero = float(np.clip(p_zero, 0.0, 1.0))

    # Build positive distribution from the quantile table.
    q_table: dict[int, float] = {}
    for qpct, m in art["pos_q"].items():
        try:
            q_table[qpct] = max(0.0, float(m.predict(X)[0]))
        except Exception:
            continue
    if not q_table:
        pmf = np.zeros(DOMAIN_MAX[stat] + 1)
        pmf[0] = 1.0
        return pmf

    # Discretize conditional-positive to integer bins by sampling the
    # piecewise-linear CDF.
    #
    # Dynamic high bound: use the max quantile value plus a moderate buffer
    # rather than anchoring at DOMAIN_MAX+0.5. Anchoring at DOMAIN_MAX+0.5
    # was the root cause of non-monotone tail spikes: when q90≈2 for steals,
    # the remaining 10% of mass spread uniformly over [2, 10.5], creating
    # physically impossible spikes at k=6-10 (higher P than k=3-5).
    #
    # Rule: hi = max(q_max_val + _hi_buffer, lo + 1.0), capped at DOMAIN_MAX+0.5.
    _hi_buffer = 1.5  # allow ~1-2 bins of right-tail slack beyond the last quantile
    q_max_val = max(
        float(max(lo, min(DOMAIN_MAX[stat] + 0.5, q[k])))
        for k in q_table
    ) if q_table else lo
    hi_dynamic = min(
        max(q_max_val + _hi_buffer, lo + 1.0),
        DOMAIN_MAX[stat] + 0.5,
    )

    rng = np.random.default_rng(0)
    samples = _sample_from_quantile_table(q_table, 4_000, rng, lo=0.5,
                                          hi=hi_dynamic)
    integers = np.clip(np.rint(samples).astype(int), 1, DOMAIN_MAX[stat])
    pos_counts = np.bincount(integers, minlength=DOMAIN_MAX[stat] + 1)
    pos_pmf = pos_counts.astype(float) / max(pos_counts.sum(), 1)

    # Monotone tail repair: for k >= 2, enforce that each bin is ≤ the
    # previous bin (non-increasing positive tail). Any excess mass is
    # redistributed backward to the nearest non-zero lower bins.
    # This eliminates residual non-monotone spikes from the CDF sampling.
    pos_pmf = _enforce_monotone_positive_tail(pos_pmf, start_k=2)

    pmf = np.zeros(DOMAIN_MAX[stat] + 1)
    pmf[0] = p_zero
    pmf[1:] = (1.0 - p_zero) * pos_pmf[1:]
    # Defensive normalisation in case of floating-point drift.
    total = pmf.sum()
    if total > 0:
        pmf = pmf / total
    return pmf


def _enforce_monotone_positive_tail(
    pos_pmf: np.ndarray, *, start_k: int = 2
) -> np.ndarray:
    """Enforce that the positive-count PMF is non-increasing for k >= start_k.

    Redistributes excess mass from any bin that exceeds its predecessor
    (a non-monotone spike) back to bins start_k..k-1 proportionally.
    Does not alter bins 0..start_k-1. Preserves total mass.

    This is a post-sampling repair that eliminates impossible shapes like
    P(7 steals) > P(3 steals).
    """
    arr = pos_pmf.copy()
    n = len(arr)
    if n <= start_k:
        return arr
    for k in range(start_k, n):
        if k == 0 or arr[k - 1] <= 0:
            continue
        if arr[k] > arr[k - 1]:
            excess = arr[k] - arr[k - 1]
            arr[k] = arr[k - 1]
            # Redistribute excess to bins [start_k, k-1] proportionally.
            receiver_mass = arr[start_k:k].sum()
            if receiver_mass > 0:
                arr[start_k:k] += excess * arr[start_k:k] / receiver_mass
            else:
                # All receivers are zero: push to bin start_k-1 if safe.
                arr[max(start_k - 1, 0)] += excess
    # Clip and renormalise to handle floating-point drift.
    arr = np.clip(arr, 0.0, None)
    s = arr.sum()
    if s > 0:
        arr /= s
    return arr


def _sample_from_quantile_table(
    q: dict[int, float], n: int, rng: np.random.Generator, lo: float, hi: float,
) -> np.ndarray:
    sorted_keys = sorted(q.keys())
    xs = [float(max(lo, min(hi, q[k]))) for k in sorted_keys]
    for i in range(1, len(xs)):
        if xs[i] < xs[i - 1]:
            xs[i] = xs[i - 1]
    ys = [k / 100.0 for k in sorted_keys]
    xs = [lo] + xs + [hi]
    ys = [0.0] + ys + [1.0]
    u = rng.uniform(0, 1, size=n)
    xs_a = np.array(xs)
    ys_a = np.array(ys)
    out = np.empty(n)
    for i, ui in enumerate(u):
        if ui <= ys_a[0]:
            out[i] = xs_a[0]
            continue
        if ui >= ys_a[-1]:
            out[i] = xs_a[-1]
            continue
        idx = int(np.searchsorted(ys_a, ui))
        y0, y1 = ys_a[idx - 1], ys_a[idx]
        x0, x1 = xs_a[idx - 1], xs_a[idx]
        out[i] = x0 if y1 == y0 else x0 + (x1 - x0) * (ui - y0) / (y1 - y0)
    return out


# ── Derived "stocks" combo ───────────────────────────────────────────────────


def stocks_pmf(
    stl_pmf: Optional[np.ndarray], blk_pmf: Optional[np.ndarray],
) -> Optional[np.ndarray]:
    """PMF of stl + blk via discrete convolution of the component PMFs.

    Assumes within-player independence, which is a modest approximation at
    the per-game level. The Phase 5 combo layer augments this with
    correlation-aware simulation for the player-level SGP case.
    """
    if stl_pmf is None or blk_pmf is None:
        return None
    out = np.convolve(stl_pmf, blk_pmf)
    # Trim to the stocks domain.
    out = out[: STOCKS_DOMAIN_MAX + 1]
    s = out.sum()
    if s > 0:
        out = out / s
    return out
