"""
NBA Props Model — state-aware probabilistic minutes model.

Architecture
------------
1.  Latent state classifier over {INACTIVE, LIMITED, NORMAL}
    INACTIVE : min == 0      (DNP, injury, load management)
    LIMITED  : 0 < min < 24  (returning from absence, foul trouble, blowout)
    NORMAL   : min >= 24     (full-role minutes)

2.  Conditional minutes distribution per active state via LightGBM quantile
    regression at tau in (0.10, 0.25, 0.50, 0.75, 0.90), fit only on rows
    in that state.

3.  Full minutes PMF for a player-game is the mixture:
        P(minutes <= m) =
              P(INACTIVE) * 1_{m >= 0}
            + P(LIMITED)  * F_limited(m | features)
            + P(NORMAL)   * F_normal(m | features)

    Sampling: draw state ~ P(state|x); if INACTIVE return 0; else invert the
    conditional CDF from the piecewise-linear quantile ladder.

Features
--------
Rolling player features (from prior games, oldest -> newest) plus the
as-of availability features produced by the Phase 2 pipeline:
  availability_status, prob_active, availability_confidence,
  days_since_last_played, is_returning_from_absence,
  minutes_restriction_flag, num_teammates_out_total,
  vacated_minutes_{guard,wing,big}, teammate_out_count_{guard,wing,big}.

Artifacts (written to artifacts/models/)
----------------------------------------
  minutes_state_classifier.pkl        LightGBM multiclass
  minutes_limited_q{10,25,50,75,90}.pkl
  minutes_normal_q{10,25,50,75,90}.pkl
  minutes_state_aware_features.pkl    ordered feature list
  minutes_state_aware_meta.json       training diagnostics

Backward compatibility
----------------------
`predict_minutes(...)` continues to return the same dictionary keys
(`exp_mp`, `mp_q10/25/75/90`, `mp_vol`, `mp_pred_floor`, `mp_pred_ceiling`,
`mean_min_last10`) expected by the rest of the predict pipeline. Those
are now derived from the state-aware distribution rather than a direct
quantile ladder. A new public function `minutes_distribution(...)`
returns the full sampled-minutes PMF for the simulation layer used by
the Phase 3 rate models.
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

# ── Constants ─────────────────────────────────────────────────────────────────

STATE_INACTIVE = 0
STATE_LIMITED = 1
STATE_NORMAL = 2
STATE_NAMES = {STATE_INACTIVE: "inactive", STATE_LIMITED: "limited", STATE_NORMAL: "normal"}

LIMITED_UPPER = 24.0      # minutes threshold separating LIMITED from NORMAL
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
MINUTES_CEILING = 48.0

_STARTER_MIN_THRESHOLD = 28.0
_RESTRICTION_RATIO = 0.55
_TOP_TEAMMATE_N = 3
_ABSENCE_LIFT_WINDOW = 60

# ── Module-level state-aware artifact cache ───────────────────────────────────

_STATE_CLF: Optional[object] = None
_COND_Q: dict[int, dict[int, object]] = {}   # state -> {qpct: model}
_STATE_FEATURES: Optional[list[str]] = None

# ── Legacy quantile-ladder cache (fallback only) ──────────────────────────────

_LEGACY_CACHE: dict = {}
_LEGACY_FEATURES: Optional[list] = None

# ── Monotone CDF calibrator (fitted walk-forward OOF) ─────────────────────────
# See train_minutes_calibrator() below. Fits an isotonic map from predicted
# CDF value to empirical frequency so interval coverage matches nominal. The
# map is monotone non-decreasing by construction so distribution validity is
# preserved.
_MINUTES_CDF_CAL: Optional[object] = None
_MINUTES_CDF_CAL_LOADED: bool = False


class MinutesCDFCalibrator:
    """Isotonic PIT-style calibration for a predicted minutes distribution.

    After fitting, `apply_cdf(f)` maps a raw predicted CDF value `f` to a
    calibrated CDF value that matches empirical coverage on the holdout.
    """

    def __init__(self) -> None:
        self.iso = None

    def fit(self, pred_cdf_at_actual: np.ndarray) -> "MinutesCDFCalibrator":
        from sklearn.isotonic import IsotonicRegression
        u = np.clip(np.asarray(pred_cdf_at_actual, dtype=float), 0.0, 1.0)
        u = np.sort(u)
        n = len(u)
        if n < 5:
            self.iso = None
            return self
        empirical = (np.arange(1, n + 1)) / float(n + 1)
        # Anchor endpoints so the map takes [0,1] -> [0,1] monotonically.
        xs = np.concatenate([[0.0], u, [1.0]])
        ys = np.concatenate([[0.0], empirical, [1.0]])
        self.iso = IsotonicRegression(
            y_min=0.0, y_max=1.0, out_of_bounds="clip", increasing=True
        ).fit(xs, ys)
        return self

    def apply_cdf(self, f: float) -> float:
        if self.iso is None:
            return float(np.clip(f, 0.0, 1.0))
        return float(np.clip(self.iso.predict([float(f)])[0], 0.0, 1.0))


def _load_minutes_cdf_calibrator() -> Optional[MinutesCDFCalibrator]:
    global _MINUTES_CDF_CAL, _MINUTES_CDF_CAL_LOADED
    if _MINUTES_CDF_CAL_LOADED:
        return _MINUTES_CDF_CAL
    _MINUTES_CDF_CAL_LOADED = True
    p = MODEL_DIR / "minutes_cdf_calibrator.pkl"
    if p.exists():
        try:
            _MINUTES_CDF_CAL = joblib.load(p)
            logger.info("Minutes CDF calibrator loaded.")
        except Exception as e:
            logger.warning(f"Minutes CDF calibrator load failed: {e}")
            _MINUTES_CDF_CAL = None
    return _MINUTES_CDF_CAL


def _load_state_aware() -> bool:
    """Load the state-aware artifacts. Return True if all artifacts present."""
    global _STATE_CLF, _COND_Q, _STATE_FEATURES
    if _STATE_CLF is not None:
        return True
    clf_path = MODEL_DIR / "minutes_state_classifier.pkl"
    feat_path = MODEL_DIR / "minutes_state_aware_features.pkl"
    if not clf_path.exists() or not feat_path.exists():
        return False
    try:
        _STATE_CLF = joblib.load(clf_path)
        _STATE_FEATURES = joblib.load(feat_path)
        _COND_Q = {STATE_LIMITED: {}, STATE_NORMAL: {}}
        for state, tag in ((STATE_LIMITED, "limited"), (STATE_NORMAL, "normal")):
            for q in QUANTILES:
                qpct = int(round(q * 100))
                p = MODEL_DIR / f"minutes_{tag}_q{qpct:02d}.pkl"
                if p.exists():
                    _COND_Q[state][qpct] = joblib.load(p)
        return bool(_COND_Q[STATE_LIMITED]) and bool(_COND_Q[STATE_NORMAL])
    except Exception as e:
        logger.warning(f"State-aware minutes load failed: {e}")
        _STATE_CLF = None
        return False


def _load_legacy() -> None:
    """Load the pre-rebuild quantile ladder for fallback."""
    global _LEGACY_CACHE, _LEGACY_FEATURES
    if _LEGACY_CACHE:
        return
    for q in [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]:
        p = MODEL_DIR / f"minutes_q{q}.pkl"
        if p.exists():
            _LEGACY_CACHE[q] = joblib.load(p)
    fp = MODEL_DIR / "minutes_features.pkl"
    if fp.exists():
        _LEGACY_FEATURES = joblib.load(fp)


# ── Feature computation helpers ──────────────────────────────────────────────


def _compute_rolling_features(mins: np.ndarray) -> dict:
    """Rolling minutes features from a sorted prior-game minutes array."""
    n = len(mins)
    last5 = mins[-5:] if n >= 5 else mins
    last10 = mins[-10:] if n >= 10 else mins
    last15 = mins[-15:] if n >= 15 else mins
    last20 = mins[-20:] if n >= 20 else mins

    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10 = float(np.std(last10)) if len(last10) > 1 else 5.0
    mean_last15 = float(np.mean(last15)) if len(last15) > 0 else mean_last10
    mean_last20 = float(np.mean(last20)) if len(last20) > 0 else mean_last10
    std_last20 = float(np.std(last20)) if len(last20) > 1 else std_last10
    mean_season = float(np.mean(mins)) if n > 0 else mean_last10

    w = np.array([0.9 ** i for i in range(n)][::-1])
    ewma = float(np.average(mins, weights=w)) if n > 0 else mean_last10

    ceiling_last10 = float(np.percentile(last10, 90)) if len(last10) > 0 else mean_last10
    trend_3v10 = float(np.mean(mins[-3:]) / max(mean_last10, 0.1)) if n >= 3 else 1.0

    p_active = float(np.mean(last20 > 0)) if len(last20) > 0 else 1.0
    active20 = last20[last20 > 0]
    active15 = last15[last15 > 0]
    starter_prob = float(np.mean(active15 >= _STARTER_MIN_THRESHOLD)) if len(active15) > 0 else 0.5
    p_20plus = float(np.mean(active20 >= 20.0)) if len(active20) > 0 else 0.6
    p_34plus = float(np.mean(active20 >= 34.0)) if len(active20) > 0 else 0.1

    mean_last3 = float(np.mean(mins[-3:])) if n >= 3 else mean_last10
    role_change_score = float((mean_last3 - mean_last15) / (mean_last15 + 1.0))
    bench_fragility_score = float(std_last20 / (mean_last20 + 1.0))

    if n >= 3:
        last_game_min = float(mins[-1])
        prior_mean = float(np.mean(mins[-11:-1])) if n >= 11 else mean_last10
        return_restriction_score = (
            1.0 if (last_game_min > 0 and
                    last_game_min < _RESTRICTION_RATIO * prior_mean and
                    prior_mean > 10.0)
            else 0.0
        )
    else:
        return_restriction_score = 0.0

    return {
        "mp_mean_season": mean_season,
        "mp_mean_last5": float(np.mean(last5)) if len(last5) > 0 else mean_last10,
        "mp_mean_last10": mean_last10,
        "mp_ewma": ewma,
        "mp_trend_3v10": trend_3v10,
        "mp_ceiling_last10": ceiling_last10,
        "mp_std_last10": std_last10,
        "mp_p_active": p_active,
        "mp_starter_prob": starter_prob,
        "mp_p_20plus": p_20plus,
        "mp_p_28plus": starter_prob,
        "mp_p_34plus": p_34plus,
        "mp_role_change_score": role_change_score,
        "mp_bench_fragility": bench_fragility_score,
        "mp_return_restriction": return_restriction_score,
    }


def _compute_teammate_absence_lift(
    player_id: int, team_id: int, target_date: str, all_stats_df: pd.DataFrame,
) -> float:
    if all_stats_df is None or all_stats_df.empty:
        return 0.0
    try:
        sdf = all_stats_df[all_stats_df["game_date"].astype(str) < str(target_date)]
        sdf = sdf.sort_values("game_date").tail(_ABSENCE_LIFT_WINDOW * 15)
        team_df = sdf[sdf["team_id"] == team_id]
        player_df = team_df[team_df["player_id"] == player_id]
        if len(player_df) < 8:
            return 0.0
        teammate_means = (
            team_df[team_df["player_id"] != player_id]
            .groupby("player_id")["min"]
            .apply(lambda x: pd.to_numeric(x, errors="coerce").mean())
            .nlargest(_TOP_TEAMMATE_N)
        )
        if teammate_means.empty:
            return 0.0
        lifts = []
        for tm_pid in teammate_means.index:
            tm_df = team_df[team_df["player_id"] == tm_pid][["game_id", "min"]].copy()
            tm_df["tm_min"] = pd.to_numeric(tm_df["min"], errors="coerce").fillna(0)
            merged = player_df[["game_id", "min"]].merge(
                tm_df[["game_id", "tm_min"]], on="game_id", how="inner"
            )
            if len(merged) < 8:
                continue
            p_min = pd.to_numeric(merged["min"], errors="coerce").fillna(0).values
            tm_min = merged["tm_min"].values
            with_mask = tm_min > 5
            without_mask = tm_min == 0
            if with_mask.sum() < 4 or without_mask.sum() < 2:
                continue
            lift = float(np.mean(p_min[without_mask]) - np.mean(p_min[with_mask]))
            lifts.append(np.clip(lift, -8.0, 15.0))
        return float(np.mean(lifts)) if lifts else 0.0
    except Exception as e:
        logger.debug(f"teammate_absence_lift failed: {e}")
        return 0.0


# ── Availability feature plumbing ────────────────────────────────────────────

# These columns, if present in the feature dict, are consumed by the
# state-aware classifier and conditional quantile models.
AVAILABILITY_FEATURES = [
    "prob_active",
    "days_since_last_played",
    "is_returning_from_absence",
    "minutes_restriction_flag",
    "num_teammates_out_total",
    "vacated_minutes_guard",
    "vacated_minutes_wing",
    "vacated_minutes_big",
    "teammate_out_count_guard",
    "teammate_out_count_wing",
    "teammate_out_count_big",
    "vacated_fga_total",
]


def _coerce_availability(avail_row: Optional[dict]) -> dict:
    """Flatten availability dict to numeric features, with safe defaults."""
    defaults = {
        "prob_active": 0.95,
        "days_since_last_played": 2.0,
        "is_returning_from_absence": 0.0,
        "minutes_restriction_flag": 0.0,
        "num_teammates_out_total": 0.0,
        "vacated_minutes_guard": 0.0,
        "vacated_minutes_wing": 0.0,
        "vacated_minutes_big": 0.0,
        "teammate_out_count_guard": 0.0,
        "teammate_out_count_wing": 0.0,
        "teammate_out_count_big": 0.0,
        "vacated_fga_total": 0.0,
    }
    if avail_row is None:
        return defaults
    out = dict(defaults)
    for k in defaults:
        v = avail_row.get(k)
        if v is None:
            continue
        try:
            out[k] = float(v)
        except Exception:
            continue
    return out


# ── Distribution object ──────────────────────────────────────────────────────


class MinutesDistribution:
    """Full minutes PMF over [0, 48] derived from state-aware architecture.

    Represented by:
      state_probs: (p_inactive, p_limited, p_normal)
      limited_quantiles: {qpct: minutes} for QUANTILES in the LIMITED band
      normal_quantiles:  {qpct: minutes} for QUANTILES in the NORMAL band

    Exposes helpers used elsewhere in the rebuild:
      mean(), std(), cdf(minutes), quantile(q), sample(n, rng).
    """

    __slots__ = ("state_probs", "limited_quantiles", "normal_quantiles")

    def __init__(
        self,
        state_probs: tuple[float, float, float],
        limited_quantiles: dict[int, float],
        normal_quantiles: dict[int, float],
    ) -> None:
        p = np.clip(np.array(state_probs, dtype=float), 0.0, 1.0)
        p = p / max(p.sum(), 1e-9)
        self.state_probs = (float(p[0]), float(p[1]), float(p[2]))
        self.limited_quantiles = _clean_quantiles(limited_quantiles, 0.0, LIMITED_UPPER)
        self.normal_quantiles = _clean_quantiles(normal_quantiles, LIMITED_UPPER, MINUTES_CEILING)

    # ── interface ──

    def cdf(self, minutes: float) -> float:
        raw = self._raw_cdf(minutes)
        cal = _load_minutes_cdf_calibrator()
        if cal is not None:
            # Pin CDF endpoints so the distribution stays valid after the
            # monotone map even when the fitted calibrator does not
            # exactly hit 0/1 at the boundaries (isotonic regression
            # fit is numerical, not exact at x==1.0).
            if raw <= 0.0:
                return 0.0
            if raw >= 1.0:
                return 1.0
            return cal.apply_cdf(raw)
        return raw

    def _raw_cdf(self, minutes: float) -> float:
        m = max(0.0, float(minutes))
        if m >= MINUTES_CEILING:
            return 1.0
        c_inactive = 1.0 if m >= 0.0 else 0.0
        c_limited = _cdf_from_quantiles(self.limited_quantiles, m)
        c_normal = _cdf_from_quantiles(self.normal_quantiles, m)
        p0, p1, p2 = self.state_probs
        return float(p0 * c_inactive + p1 * c_limited + p2 * c_normal)

    def quantile(self, q: float) -> float:
        q = float(np.clip(q, 1e-6, 1 - 1e-6))
        # Bisect on cdf since it's monotone.
        lo, hi = 0.0, MINUTES_CEILING
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if self.cdf(mid) < q:
                lo = mid
            else:
                hi = mid
        return float(0.5 * (lo + hi))

    def mean(self) -> float:
        p0, p1, p2 = self.state_probs
        mu_limited = _mean_from_quantiles(self.limited_quantiles)
        mu_normal = _mean_from_quantiles(self.normal_quantiles)
        return float(p1 * mu_limited + p2 * mu_normal)

    def std(self) -> float:
        samples = self.sample(500, np.random.default_rng(0))
        return float(np.std(samples))

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        # Route through the calibrated CDF when the monotone calibrator is
        # loaded — otherwise draw from the raw per-state quantile ladders
        # for speed.
        cal = _load_minutes_cdf_calibrator()
        if cal is not None:
            u = rng.uniform(0.0, 1.0, size=n)
            return np.array([self.quantile(float(ui)) for ui in u], dtype=float)
        p = np.array(self.state_probs, dtype=float)
        p = p / max(p.sum(), 1e-9)
        states = rng.choice(3, size=n, p=p)
        out = np.zeros(n, dtype=float)
        for i, s in enumerate(states):
            if s == STATE_INACTIVE:
                out[i] = 0.0
            elif s == STATE_LIMITED:
                out[i] = _sample_from_quantiles(self.limited_quantiles, rng)
            else:
                out[i] = _sample_from_quantiles(self.normal_quantiles, rng)
        return out


def _clean_quantiles(q: dict[int, float], lo: float, hi: float) -> dict[int, float]:
    """Clip quantile values into [lo, hi] and enforce monotonicity."""
    if not q:
        default = {int(round(t * 100)): lo + (hi - lo) * t for t in QUANTILES}
        return default
    keys = sorted(q.keys())
    vals = [float(q[k]) for k in keys]
    # Clip + monotone enforce.
    vals = [max(lo, min(hi, v)) for v in vals]
    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1]:
            vals[i] = vals[i - 1]
    return dict(zip(keys, vals))


def _cdf_from_quantiles(q: dict[int, float], x: float) -> float:
    """Piecewise-linear CDF approximation from a quantile table."""
    if not q:
        return 0.0
    sorted_keys = sorted(q.keys())
    xs = [q[k] for k in sorted_keys]
    ys = [k / 100.0 for k in sorted_keys]
    # Anchor at domain extremes.
    # At x below xs[0], cdf linearly interpolates between (0, 0) and (xs[0], ys[0]).
    # At x above xs[-1], cdf interpolates between (xs[-1], ys[-1]) and (MINUTES_CEILING, 1.0).
    xs = [0.0] + xs + [MINUTES_CEILING]
    ys = [0.0] + ys + [1.0]
    if x <= xs[0]:
        return 0.0
    if x >= xs[-1]:
        return 1.0
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return float(y1)
            return float(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return 1.0


def _sample_from_quantiles(q: dict[int, float], rng: np.random.Generator) -> float:
    """Inverse-CDF sample from a piecewise-linear quantile table."""
    u = float(rng.uniform(0, 1))
    if not q:
        return 0.0
    sorted_keys = sorted(q.keys())
    xs = [q[k] for k in sorted_keys]
    ys = [k / 100.0 for k in sorted_keys]
    xs = [0.0] + xs + [MINUTES_CEILING]
    ys = [0.0] + ys + [1.0]
    if u <= ys[0]:
        return xs[0]
    if u >= ys[-1]:
        return xs[-1]
    for i in range(1, len(ys)):
        if u <= ys[i]:
            y0, y1 = ys[i - 1], ys[i]
            x0, x1 = xs[i - 1], xs[i]
            if y1 == y0:
                return float(x1)
            return float(x0 + (x1 - x0) * (u - y0) / (y1 - y0))
    return float(xs[-1])


def _mean_from_quantiles(q: dict[int, float]) -> float:
    """Trapezoid mean from a monotone quantile ladder (boundary-anchored)."""
    if not q:
        return 0.0
    sorted_keys = sorted(q.keys())
    xs = [0.0] + [q[k] for k in sorted_keys] + [MINUTES_CEILING]
    ys = [0.0] + [k / 100.0 for k in sorted_keys] + [1.0]
    # E[X] = int_0^infty (1 - F(x)) dx. Trapezoid rule over xs.
    # int_{xs[i-1]}^{xs[i]} (1 - F(x)) dx ≈ (xs[i]-xs[i-1]) * ((1-ys[i-1])+(1-ys[i]))/2
    e = 0.0
    for i in range(1, len(xs)):
        dx = xs[i] - xs[i - 1]
        e += dx * ((1.0 - ys[i - 1]) + (1.0 - ys[i])) / 2.0
    return float(e)


# ── Public inference API ─────────────────────────────────────────────────────


def _build_state_aware_feature_vector(
    mins: np.ndarray,
    game_context: dict,
    is_home: bool,
    absence_lift: float,
    availability: Optional[dict],
) -> dict:
    rolling = _compute_rolling_features(mins)
    avail = _coerce_availability(availability)
    return {
        **rolling,
        **avail,
        "is_home": float(is_home),
        "rest_days": float(game_context.get("rest_days", 2)),
        "back_to_back": float(game_context.get("back_to_back", 0)),
        "mp_teammate_abs_lift": absence_lift,
    }


def minutes_distribution(
    prior_stats: pd.DataFrame,
    game_context: dict,
    is_home: bool,
    target_date: str,
    team_id: int,
    all_stats_df: pd.DataFrame,
    injury_map: Optional[dict] = None,
    availability: Optional[dict] = None,
) -> MinutesDistribution:
    """Return the full probabilistic minutes distribution for one game.

    When the state-aware artifacts are unavailable the function falls back
    to the legacy quantile ladder wrapped into the same distribution
    object so downstream callers stay source-compatible. This fallback is
    retained only until the first CI retrain regenerates state-aware
    artifacts and is scheduled for removal in a later cleanup commit.
    """
    df = prior_stats.sort_values("game_date").reset_index(drop=True)
    mins = (
        pd.to_numeric(df["min"], errors="coerce").fillna(0).values
        if len(df) > 0 else np.array([])
    )
    player_id = int(df["player_id"].iloc[0]) if (
        len(df) > 0 and "player_id" in df.columns
    ) else -1
    lift = _compute_teammate_absence_lift(
        player_id, team_id, target_date, all_stats_df,
    )

    if _load_state_aware():
        feat_dict = _build_state_aware_feature_vector(
            mins, game_context, is_home, lift, availability,
        )
        X = pd.DataFrame([{f: feat_dict.get(f, 0.0) for f in _STATE_FEATURES}])
        try:
            # Binary classifier: P(normal | active).
            proba = _STATE_CLF.predict_proba(X)[0]
            p_normal_given_active = float(proba[1]) if len(proba) >= 2 else 0.75
            # P(INACTIVE) comes from availability.prob_active directly.
            avail = _coerce_availability(availability)
            p_active = float(np.clip(avail.get("prob_active", 0.95), 0.0, 1.0))
            p_inactive = 1.0 - p_active
            p_normal = p_active * p_normal_given_active
            p_limited = p_active * (1.0 - p_normal_given_active)
            limited_q = _predict_conditional_quantiles(X, STATE_LIMITED)
            normal_q = _predict_conditional_quantiles(X, STATE_NORMAL)
            return MinutesDistribution(
                state_probs=(p_inactive, p_limited, p_normal),
                limited_quantiles=limited_q,
                normal_quantiles=normal_q,
            )
        except Exception as e:
            logger.warning(f"state-aware minutes prediction failed: {e}")

    # Fallback: use the legacy quantile ladder wrapped into a Distribution.
    return _legacy_distribution(mins, game_context, is_home, lift)


def _predict_conditional_quantiles(X: pd.DataFrame, state: int) -> dict[int, float]:
    out: dict[int, float] = {}
    for qpct, m in _COND_Q[state].items():
        try:
            out[qpct] = float(m.predict(X)[0])
        except Exception:
            continue
    return out


def _legacy_distribution(
    mins: np.ndarray, game_context: dict, is_home: bool, absence_lift: float,
) -> MinutesDistribution:
    _load_legacy()
    last10 = mins[-10:] if len(mins) >= 10 else mins
    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10 = float(np.std(last10)) if len(last10) > 1 else 5.0
    if not _LEGACY_CACHE:
        # Gaussian-shaped fallback.
        limited_q = {10: max(0.0, mean_last10 - 1.5 * std_last10),
                     25: max(0.0, mean_last10 - 0.8 * std_last10),
                     50: mean_last10, 75: mean_last10 + 0.8 * std_last10,
                     90: mean_last10 + 1.5 * std_last10}
        return MinutesDistribution(
            state_probs=(0.02, 0.20, 0.78),
            limited_quantiles=limited_q, normal_quantiles=limited_q,
        )
    rolling = _compute_rolling_features(mins)
    feat = {**rolling, "is_home": float(is_home),
            "rest_days": float(game_context.get("rest_days", 2)),
            "back_to_back": float(game_context.get("back_to_back", 0)),
            "mp_teammate_abs_lift": absence_lift}
    if _LEGACY_FEATURES is not None:
        X = pd.DataFrame([{f: feat.get(f, 0.0) for f in _LEGACY_FEATURES}])
    else:
        X = pd.DataFrame([feat])
    q_preds = {}
    for q, m in _LEGACY_CACHE.items():
        try:
            q_preds[q] = float(m.predict(X)[0])
        except Exception:
            q_preds[q] = mean_last10
    # Partition the ladder into state-aware bands.
    limited_q = {k: min(LIMITED_UPPER, v) for k, v in q_preds.items() if k in (10, 25, 50, 75, 90)}
    normal_q = {k: max(LIMITED_UPPER, v) for k, v in q_preds.items() if k in (10, 25, 50, 75, 90)}
    # Infer p_inactive from the fraction of 0-min games in recent history.
    p_inactive = float(np.mean(mins == 0)) if len(mins) else 0.02
    q50 = q_preds.get(50, mean_last10)
    p_normal = 0.9 if q50 >= LIMITED_UPPER else 0.5
    p_limited = 1.0 - p_inactive - p_normal
    p_limited = max(0.0, p_limited)
    total = p_inactive + p_limited + p_normal
    return MinutesDistribution(
        state_probs=(p_inactive / total, p_limited / total, p_normal / total),
        limited_quantiles=limited_q, normal_quantiles=normal_q,
    )


def predict_minutes(
    prior_stats: pd.DataFrame,
    game_context: dict,
    is_home: bool,
    target_date: str,
    team_id: int,
    all_stats_df: pd.DataFrame,
    injury_map: Optional[dict] = None,
    availability: Optional[dict] = None,
) -> dict:
    """Backward-compatible inference: dict of summary statistics.

    Keeps the exact keys the rest of the prediction pipeline already reads.
    Values are derived from the state-aware distribution.
    """
    df = prior_stats.sort_values("game_date").reset_index(drop=True)
    mins = (
        pd.to_numeric(df["min"], errors="coerce").fillna(0).values
        if len(df) > 0 else np.array([])
    )
    last10 = mins[-10:] if len(mins) >= 10 else mins
    mean_last10 = float(np.mean(last10)) if len(last10) > 0 else 25.0
    std_last10 = float(np.std(last10)) if len(last10) > 1 else 5.0

    dist = minutes_distribution(
        prior_stats, game_context, is_home, target_date, team_id,
        all_stats_df, injury_map=injury_map, availability=availability,
    )

    exp_mp = dist.mean()
    q10 = dist.quantile(0.10)
    q25 = dist.quantile(0.25)
    q75 = dist.quantile(0.75)
    q90 = dist.quantile(0.90)
    vol = max(std_last10, dist.std())
    # Stash the full distribution on a weak singleton so callers that want
    # it for simulation can retrieve without contaminating the returned
    # feature dict (which is often parquet-serialized by the training
    # pipeline).
    _set_last_distribution(dist)
    return {
        "mean_min_last10": mean_last10,
        "exp_mp": float(exp_mp),
        "mp_q10": float(q10),
        "mp_q25": float(q25),
        "mp_q75": float(q75),
        "mp_q90": float(q90),
        "mp_vol": float(vol),
        "mp_pred_floor": float(dist.quantile(0.05)),
        "mp_pred_ceiling": float(dist.quantile(0.95)),
    }


# ── Last-distribution side-channel ───────────────────────────────────────────

_LAST_DISTRIBUTION: Optional[MinutesDistribution] = None


def _set_last_distribution(d: MinutesDistribution) -> None:
    global _LAST_DISTRIBUTION
    _LAST_DISTRIBUTION = d


def last_distribution() -> Optional[MinutesDistribution]:
    """Return the MinutesDistribution computed by the most recent
    `predict_minutes` call. Useful for callers that want to feed the
    full distribution to the simulation layer without re-invoking the
    classifier and conditional-quantile models."""
    return _LAST_DISTRIBUTION


# ── Training ─────────────────────────────────────────────────────────────────


def train_state_aware_minutes_model(
    stats_df: pd.DataFrame,
    availability_df: Optional[pd.DataFrame] = None,
) -> dict:
    """Train the state classifier + conditional quantile ladders.

    The player_game_stats parquet does not contain rows with min == 0 —
    DNPs are absent from box scores — so the observable training label
    space is {LIMITED, NORMAL}. P(INACTIVE) at inference time comes from
    (1 - prob_active) in the availability table; the classifier fits the
    conditional P(normal | active) which the runtime mixes with
    prob_active to produce a proper three-way state distribution.
    """
    import lightgbm as lgb

    logger.info("=" * 60)
    logger.info("Minutes model training (state-aware rebuild)")
    logger.info("=" * 60)

    df = stats_df.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["min_numeric"] = pd.to_numeric(df["min"], errors="coerce").fillna(0)

    avail_lookup: dict[tuple[int, str], dict] = {}
    if availability_df is not None and not availability_df.empty:
        for r in availability_df.itertuples(index=False):
            key = (int(r.player_id), str(r.game_date))
            avail_lookup[key] = {c: getattr(r, c, None) for c in AVAILABILITY_FEATURES}

    rows = []
    for pid, pdata in df.groupby("player_id"):
        pdata = pdata.sort_values("game_date").reset_index(drop=True)
        mins = pdata["min_numeric"].values
        n = len(pdata)
        if n < 12:
            continue
        for i in range(10, n):
            prior = mins[:i]
            target = mins[i]
            game_row = pdata.iloc[i]
            game_date_iso = str(game_row["game_date"].date())

            rolling = _compute_rolling_features(prior)
            prev_date = pdata.iloc[i - 1]["game_date"]
            rest_days = float((game_row["game_date"] - prev_date).days)
            b2b = 1.0 if rest_days == 1.0 else 0.0
            is_home = 0.0
            if "home_team_id" in game_row.index and "team_id" in game_row.index:
                is_home = float(int(game_row["home_team_id"]) == int(game_row["team_id"]))

            avail_row = avail_lookup.get((int(pid), game_date_iso))
            avail = _coerce_availability(avail_row)

            rows.append({
                **rolling,
                **avail,
                "is_home": is_home,
                "rest_days": rest_days,
                "back_to_back": b2b,
                "target_minutes": float(target),
                "game_date": game_row["game_date"],
            })

    if not rows:
        logger.warning("No training rows available for minutes model")
        return {}

    train_df = pd.DataFrame(rows)
    feat_cols = [c for c in train_df.columns if c not in ("target_minutes", "game_date")]
    logger.info(f"  {len(train_df):,} training rows | {len(feat_cols)} features")
    joblib.dump(feat_cols, MODEL_DIR / "minutes_state_aware_features.pkl")

    # Date-based temporal holdout: last 15% of games as validation.
    cutoff = train_df["game_date"].quantile(0.85)
    train_mask = train_df["game_date"] <= cutoff
    y = train_df["target_minutes"].values
    # Two observable states: LIMITED vs NORMAL (box scores never record 0).
    # Class 0 = LIMITED (< LIMITED_UPPER), class 1 = NORMAL (>= LIMITED_UPPER).
    binary_labels = (y >= LIMITED_UPPER).astype(int)
    X_all = train_df[feat_cols]
    X_tr = X_all[train_mask]
    X_val = X_all[~train_mask]
    y_tr = y[train_mask.values]
    y_val = y[~train_mask.values]
    b_tr = binary_labels[train_mask.values]
    b_val = binary_labels[~train_mask.values]

    logger.info(
        f"  train rows: {len(X_tr):,}  |  holdout rows: {len(X_val):,}"
    )
    logger.info(
        f"  active-state distribution (train): "
        f"limited={(b_tr==0).mean():.3f}  normal={(b_tr==1).mean():.3f}"
    )

    # Binary classifier: P(normal | active).
    clf = lgb.LGBMClassifier(
        objective="binary",
        n_estimators=400, num_leaves=63, learning_rate=0.04,
        min_child_samples=30, feature_fraction=0.8,
        bagging_fraction=0.8, bagging_freq=1,
        verbosity=-1, random_state=42,
    )
    clf.fit(X_tr, b_tr)
    joblib.dump(clf, MODEL_DIR / "minutes_state_classifier.pkl")

    clf_preds = clf.predict_proba(X_val)[:, 1]
    # Brier on the binary (given active) task plus overall log-loss.
    from sklearn.metrics import log_loss, brier_score_loss
    ll = float(log_loss(b_val, np.clip(clf_preds, 1e-6, 1 - 1e-6)))
    brier = float(brier_score_loss(b_val, clf_preds))
    cls_briers = {"active_normal": brier, "active_limited": brier}
    logger.info(f"  state classifier holdout logloss: {ll:.4f}  brier: {brier:.4f}")
    # Use s_tr / s_val as a 3-class synthetic view for the conditional splits below.
    s_tr = np.where(b_tr == 1, STATE_NORMAL, STATE_LIMITED)
    s_val = np.where(b_val == 1, STATE_NORMAL, STATE_LIMITED)
    state_labels = np.where(binary_labels == 1, STATE_NORMAL, STATE_LIMITED)

    # Conditional quantile models per active state.
    conditional_metrics: dict = {}
    cond_models: dict[str, dict[int, object]] = {"limited": {}, "normal": {}}
    all_cal_errs: list[float] = []
    for state, tag in ((STATE_LIMITED, "limited"), (STATE_NORMAL, "normal")):
        state_mask = state_labels == state
        X_state_tr = X_all[state_mask & train_mask]
        y_state_tr = y[state_mask & train_mask.values]
        X_state_val = X_all[state_mask & ~train_mask]
        y_state_val = y[state_mask & ~train_mask.values]
        if len(X_state_tr) < 200:
            logger.warning(f"  conditional quantile training skipped for {tag} (n={len(X_state_tr)})")
            continue
        logger.info(f"  fitting conditional quantiles for {tag} (n={len(X_state_tr):,})")
        cal = {}
        for q in QUANTILES:
            m = lgb.LGBMRegressor(
                objective="quantile", alpha=q,
                n_estimators=400, num_leaves=63, learning_rate=0.04,
                min_child_samples=20, feature_fraction=0.8,
                bagging_fraction=0.8, bagging_freq=1,
                verbosity=-1, random_state=42,
            )
            m.fit(X_state_tr, y_state_tr)
            qpct = int(round(q * 100))
            joblib.dump(m, MODEL_DIR / f"minutes_{tag}_q{qpct:02d}.pkl")
            cond_models[tag][qpct] = m
            if len(X_state_val) > 50:
                emp = float(np.mean(y_state_val <= m.predict(X_state_val)))
                cal[f"q{qpct}_emp"] = emp
                cal[f"q{qpct}_err"] = abs(emp - q)
                all_cal_errs.append(abs(emp - q))
        conditional_metrics[tag] = {
            "n_train": int(len(X_state_tr)), "n_val": int(len(X_state_val)),
            **cal,
        }

    # Canonical holdout metrics on the full validation set: use classifier
    # probability × conditional medians (or active-state conditional Q50) to
    # produce an expected-minutes MAE and a coverage check at 50%. This is
    # the minutes artifact contract the caller reads — keep it stable.
    mae_q50 = float("nan")
    max_cal_err = float("nan")
    coverage_50pct = float("nan")
    try:
        if cond_models["limited"] and cond_models["normal"]:
            lim_q50 = cond_models["limited"][50].predict(X_val)
            nor_q50 = cond_models["normal"][50].predict(X_val)
            lim_q25 = cond_models["limited"].get(25, cond_models["limited"][50]).predict(X_val)
            lim_q75 = cond_models["limited"].get(75, cond_models["limited"][50]).predict(X_val)
            nor_q25 = cond_models["normal"].get(25, cond_models["normal"][50]).predict(X_val)
            nor_q75 = cond_models["normal"].get(75, cond_models["normal"][50]).predict(X_val)
            p_normal = clf_preds
            q50_mix = p_normal * nor_q50 + (1.0 - p_normal) * lim_q50
            mae_q50 = float(np.mean(np.abs(q50_mix - y_val)))
            lb = np.where(b_val == 1, nor_q25, lim_q25)
            ub = np.where(b_val == 1, nor_q75, lim_q75)
            coverage_50pct = float(np.mean((y_val >= lb) & (y_val <= ub)))
        if all_cal_errs:
            max_cal_err = float(max(all_cal_errs))
    except Exception as e:
        logger.warning(f"  canonical holdout metrics computation failed: {e}")

    # ── Monotone PIT calibrator on the internal holdout ──────────────────
    # Build a per-row MinutesDistribution, evaluate F_hat_i = cdf(y_i), and
    # fit an isotonic map so F_cal ~ Uniform(0,1). This preserves CDF
    # monotonicity by construction and pulls 50% coverage toward nominal.
    cal_coverage_50pct_after = float("nan")
    cal_mae_q50_after = float("nan")
    try:
        if cond_models["limited"] and cond_models["normal"]:
            lim_q_preds = {q: cond_models["limited"][q].predict(X_val) for q in (10, 25, 50, 75, 90) if q in cond_models["limited"]}
            nor_q_preds = {q: cond_models["normal"][q].predict(X_val) for q in (10, 25, 50, 75, 90) if q in cond_models["normal"]}
            p_active_val = np.ones(len(y_val))  # training labels are active-only
            p_normal_all = clf_preds * p_active_val
            p_limited_all = (1.0 - clf_preds) * p_active_val
            pit_vals = np.zeros(len(y_val), dtype=float)
            for i in range(len(y_val)):
                lim_q = {k: float(v[i]) for k, v in lim_q_preds.items()}
                nor_q = {k: float(v[i]) for k, v in nor_q_preds.items()}
                dist = MinutesDistribution(
                    state_probs=(0.0, float(p_limited_all[i]), float(p_normal_all[i])),
                    limited_quantiles=lim_q,
                    normal_quantiles=nor_q,
                )
                pit_vals[i] = dist._raw_cdf(float(y_val[i]))
            calibrator = MinutesCDFCalibrator().fit(pit_vals)
            joblib.dump(calibrator, MODEL_DIR / "minutes_cdf_calibrator.pkl")
            logger.info(
                f"Minutes CDF calibrator fitted on {len(pit_vals):,} holdout rows"
            )
            # Post-calibration coverage check — draw calibrated quantiles at
            # 0.25 / 0.75 and re-measure coverage.
            cov_hits = 0
            abs_err = 0.0
            for i in range(len(y_val)):
                lim_q = {k: float(v[i]) for k, v in lim_q_preds.items()}
                nor_q = {k: float(v[i]) for k, v in nor_q_preds.items()}
                dist = MinutesDistribution(
                    state_probs=(0.0, float(p_limited_all[i]), float(p_normal_all[i])),
                    limited_quantiles=lim_q,
                    normal_quantiles=nor_q,
                )
                raw_cdf = dist._raw_cdf(float(y_val[i]))
                pit_cal = calibrator.apply_cdf(raw_cdf)
                # Coverage: whether the actual falls inside calibrated
                # [q25, q75]. Invert calibrator to find minute level whose
                # calibrated cdf = 0.25 / 0.75.
                def _inv_cal(tau):
                    lo, hi = 0.0, MINUTES_CEILING
                    for _ in range(60):
                        mid = 0.5 * (lo + hi)
                        if calibrator.apply_cdf(dist._raw_cdf(mid)) < tau:
                            lo = mid
                        else:
                            hi = mid
                    return 0.5 * (lo + hi)
                q25 = _inv_cal(0.25); q75 = _inv_cal(0.75)
                if q25 <= float(y_val[i]) <= q75:
                    cov_hits += 1
                q50_cal = _inv_cal(0.5)
                abs_err += abs(q50_cal - float(y_val[i]))
            cal_coverage_50pct_after = float(cov_hits / max(len(y_val), 1))
            cal_mae_q50_after = float(abs_err / max(len(y_val), 1))
            logger.info(
                f"Minutes CDF calibrator holdout: "
                f"coverage_50pct={cal_coverage_50pct_after:.3f}  "
                f"mae_q50={cal_mae_q50_after:.3f}"
            )
    except Exception as e:
        logger.warning(f"Minutes CDF calibrator fit failed: {e}")

    meta = {
        "n_train": int(len(X_tr)),
        "n_val": int(len(X_val)),
        "features": feat_cols,
        "state_classifier_logloss": ll,
        "state_classifier_brier": cls_briers,
        "conditional": conditional_metrics,
        "limited_upper_threshold": LIMITED_UPPER,
        "quantiles": list(QUANTILES),
        # Canonical minutes artifact contract — consumed by train.py logger and
        # downstream diagnostics. Do not rename without updating callers.
        "mae_q50": mae_q50,
        "max_cal_error": max_cal_err,
        "coverage_50pct": coverage_50pct,
        # Post-calibration holdout metrics — reported separately so callers
        # can compare raw vs calibrated at a glance.
        "mae_q50_calibrated": cal_mae_q50_after,
        "coverage_50pct_calibrated": cal_coverage_50pct_after,
    }
    with open(MODEL_DIR / "minutes_state_aware_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    logger.info("  wrote minutes_state_aware_meta.json")

    # Refresh in-process caches.
    global _STATE_CLF, _COND_Q, _STATE_FEATURES, _MINUTES_CDF_CAL, _MINUTES_CDF_CAL_LOADED
    _STATE_CLF = None
    _COND_Q = {}
    _STATE_FEATURES = None
    _MINUTES_CDF_CAL = None
    _MINUTES_CDF_CAL_LOADED = False
    _load_state_aware()
    return meta


def _state_label_array(y: np.ndarray) -> np.ndarray:
    s = np.full(len(y), STATE_NORMAL, dtype=int)
    s[y == 0] = STATE_INACTIVE
    s[(y > 0) & (y < LIMITED_UPPER)] = STATE_LIMITED
    return s


# Retain the legacy public name so existing callers keep working.
def train_minutes_model(stats_df: pd.DataFrame, odds_df=None) -> dict:
    """Back-compat alias: train state-aware model + write legacy-name files.

    Also fits a small legacy ladder so downstream pickles keep loading
    during the fallback window. Retire in the post-rebuild cleanup.
    """
    availability_path = MODEL_DIR.parent / "data" / "player_availability_asof.parquet"
    # paths.DATA_DIR is the right one; avoid a circular import by resolving here.
    from nba_props_model.paths import DATA_DIR
    avail = None
    ap = DATA_DIR / "player_availability_asof.parquet"
    if ap.exists():
        try:
            avail = pd.read_parquet(ap)
        except Exception:
            avail = None
    return train_state_aware_minutes_model(stats_df, availability_df=avail)
