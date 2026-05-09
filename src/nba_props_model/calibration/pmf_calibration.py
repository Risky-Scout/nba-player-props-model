"""
NBA Props Model — full-PMF / CDF calibration.

Replaces the side-level Platt layer (kept only as a diagnostic fallback)
with a proper CDF calibration trained walk-forward on the full evaluated
universe. The calibrator is monotone-preserving and per-stat.

Method
------
For each stat, we train an isotonic regressor that maps
        predicted CDF values F_pred(y) in [0, 1]
to the empirical distribution of actual outcomes y. The training signal
is the "universal" property of a correctly-specified continuous CDF:
    F_true(Y) ~ Uniform(0, 1)
Because our PMFs are discrete we use the randomized PIT convention:
    u = F_pred(y - 1) + U * p(y), with U ~ Uniform(0, 1),
which yields a uniform RV under perfect calibration. We then fit an
isotonic map g: u -> q such that the transformed CDF g(F_pred(y)) is
uniform on the training folds.

Walk-forward folds respect game_date strictly. Each fold trains on all
prior data and evaluates on a 28-day window; the per-stat g is fit on
the union of out-of-fold (u, q) pairs.

Artifacts
---------
  artifacts/models/pmf_cal_{stat}.pkl
  artifacts/models/pmf_cal_meta.json

Inference
---------
The calibrator is a thin wrapper: given a raw PMF it computes the raw
CDF, applies g monotone-preservingly to every CDF knot, and then
differentiates to recover a calibrated PMF. Monotonicity is guaranteed
by isotonic regression.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from nba_props_model.paths import MODEL_DIR

logger = logging.getLogger(__name__)

CAL_META_PATH = MODEL_DIR / "pmf_cal_meta.json"


# ── Role-aware calibration constants ────────────────────────────────────────

ROLE_MIN_ROWS = {
    "inactive_risk": 250,
    "fringe": 250,
    "bench": 350,
    "rotation": 500,
    "core": 750,
    "starter": 750,
}

ROLE_SHRINK_K = {
    # Phase 14 promotion: monotone_inactive_global_v1
    # Small/noisy buckets shrink heavily toward global; starter/core get more
    # bucket signal where A/B paired-row evidence proved it safe.
    "inactive_risk": 8000.0,
    "fringe": 7000.0,
    "bench": 5000.0,
    "rotation": 3000.0,
    "core": 2000.0,
    "starter": 1500.0,
}

ROLE_WEIGHT_CAP = {
    # Phase 14 promotion: monotone_inactive_global_v1
    # inactive_risk cap=0.0 is belt-and-suspenders; ROLE_GLOBAL_ONLY_BUCKETS
    # short-circuits inactive_risk to global before this cap is consulted.
    "inactive_risk": 0.0,
    "fringe": 0.25,
    "bench": 0.35,
    "rotation": 0.50,
    "core": 0.65,
    "starter": 0.70,
}

# Buckets routed through global-only at apply time. Their fitted bucket
# calibrators in the pickle are intentionally bypassed for these buckets,
# regardless of bucket sample size. Per Phase 14 paired A/B: inactive_risk
# bucket calibration on n=3,309 rows worsened fg3m|inactive_risk by +0.0126
# NLL vs global; routing through global eliminates that residual exactly
# (delta=0.0 vs global on the n=922 wedge cell).
ROLE_GLOBAL_ONLY_BUCKETS = frozenset({"inactive_risk"})

# Identifies the active blend policy for downstream audit/cal_source tagging.
# When this changes, the pickle is unchanged but apply-time semantics differ.
ROLE_AWARE_BLEND_POLICY = "monotone_inactive_global_v1"

ROLE_AWARE_VERSION = "role_aware_pmf_cal_v1"


# ── Calibrator object ────────────────────────────────────────────────────────


@dataclass
class PMFCalibrator:
    """Monotone CDF calibrator for a single stat.

    Fitted by `fit_calibrator` on (u, q) pairs. Applied via `apply` to
    convert a raw discrete PMF into a calibrated PMF of the same length.
    """
    stat: str
    isotonic: IsotonicRegression
    n_train: int
    fold_spans: list[tuple[str, str]]

    def apply(self, pmf: np.ndarray) -> np.ndarray:
        """Return calibrated PMF of same length as input.

        Tail-safe PMF calibration.

        This avoids transforming right-edge CDF knots and differencing the result,
        which can create isolated tail atoms and terminal-bin residual dumps.
        """
        if pmf is None or len(pmf) == 0:
            return pmf

        raw = np.asarray(pmf, dtype=float)
        raw = np.clip(
            np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0),
            0.0,
            None,
        )

        s = float(raw.sum())
        if not np.isfinite(s) or s <= 0:
            return np.full_like(raw, 1.0 / max(len(raw), 1))

        raw = raw / s

        raw_cdf = np.cumsum(raw)
        u_mid = np.clip(raw_cdf - 0.5 * raw, 1e-6, 1.0 - 1e-6)

        h = np.maximum(1e-4, np.minimum(0.02, 0.5 * np.maximum(raw, 1e-4)))
        u_lo = np.clip(u_mid - h, 0.0, 1.0)
        u_hi = np.clip(u_mid + h, 0.0, 1.0)

        g_lo = np.asarray(self.isotonic.transform(u_lo), dtype=float)
        g_hi = np.asarray(self.isotonic.transform(u_hi), dtype=float)

        denom = np.maximum(u_hi - u_lo, 1e-6)
        slope = np.clip((g_hi - g_lo) / denom, 0.05, 20.0)

        corrected = raw * slope
        corrected = np.clip(
            np.nan_to_num(corrected, nan=0.0, posinf=0.0, neginf=0.0),
            0.0,
            None,
        )

        alpha = 0.70
        calibrated = alpha * corrected + (1.0 - alpha) * raw

        return _repair_basketball_tail_shape(raw, calibrated, self.stat)


def _repair_basketball_tail_shape(raw: np.ndarray, cal: np.ndarray, stat: str) -> np.ndarray:
    """Remove endpoint dumps and isolated tail atoms from an NBA stat PMF."""
    raw = np.asarray(raw, dtype=float)
    cal = np.asarray(cal, dtype=float)
    n = len(raw)

    if n == 0:
        return cal

    raw = np.clip(np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    raw_sum = float(raw.sum())
    if not np.isfinite(raw_sum) or raw_sum <= 0:
        raw = np.full(n, 1.0 / n)
    else:
        raw = raw / raw_sum

    cal = np.clip(np.nan_to_num(cal, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    cal_sum = float(cal.sum())
    if not np.isfinite(cal_sum) or cal_sum <= 0:
        return raw.copy()

    cal = cal / cal_sum
    stat_key = str(stat).lower()

    tail_start_by_stat = {
        "pts": 45,
        "reb": 18,
        "ast": 15,
        "tov": 9,
        "fg3m": 4,
        "stl": 5,
        "blk": 5,
        "stocks": 8,
    }

    terminal_cap_by_stat = {
        "pts": 5e-5,
        "reb": 5e-5,
        "ast": 5e-5,
        "tov": 2e-4,
        "fg3m": 1e-6,
        "stl": 2e-4,
        "blk": 2e-4,
        "stocks": 2e-4,
    }

    start = tail_start_by_stat.get(stat_key, int(0.75 * n))
    start = min(max(start, 0), n - 1)

    terminal_cap = terminal_cap_by_stat.get(stat_key, 1e-4)
    terminal_target = min(max(float(raw[-1]) * 2.0, 0.0), terminal_cap)
    excess = max(0.0, float(cal[-1]) - terminal_target)

    if excess > 0.0 and n >= 3:
        cal[-1] -= excess

        lo = start
        hi = n - 1

        if hi > lo:
            weights = raw[lo:hi].copy()
            if float(weights.sum()) <= 1e-12:
                grid = np.arange(hi - lo, dtype=float)
                weights = np.exp(-0.75 * grid)
            weights = weights / float(weights.sum())
            cal[lo:hi] += excess * weights
        else:
            body = raw[:-1].copy()
            body_sum = float(body.sum())
            if body_sum <= 1e-12:
                body = np.ones(n - 1, dtype=float) / max(n - 1, 1)
            else:
                body = body / body_sum
            cal[:-1] += excess * body

    eps = 1e-12
    for k in range(max(start, 1), n - 1):
        if cal[k] > 2e-4 and cal[k - 1] <= eps and cal[k + 1] <= eps:
            atom = float(cal[k])
            cal[k] = 0.0

            lo = max(start, k - 2)
            hi = min(n - 1, k + 3)

            weights = raw[lo:hi].copy()
            if float(weights.sum()) <= 1e-12:
                weights = np.ones(hi - lo, dtype=float)
            weights = weights / float(weights.sum())
            cal[lo:hi] += atom * weights

    cal = np.clip(cal, 0.0, None)
    cal_sum = float(cal.sum())
    if not np.isfinite(cal_sum) or cal_sum <= 0:
        return raw.copy()

    return cal / cal_sum



@dataclass
class RoleAwarePMFCalibrator:
    """Role-aware PMF calibrator.

    Bundles a global isotonic CDF map with optional per-role isotonic
    CDF maps. apply() blends global and role-specific PMFs via
    shrinkage on bucket sample size. Backward compatible: apply() with
    role_bucket=None or unknown falls back to the global calibrator.
    """
    stat: str
    global_calibrator: PMFCalibrator
    bucket_calibrators: dict[str, PMFCalibrator]
    bucket_counts: dict[str, int]
    version: str = ROLE_AWARE_VERSION

    def apply(self, pmf: np.ndarray, role_bucket: Optional[str] = None) -> np.ndarray:
        if pmf is None or len(pmf) == 0:
            return pmf
        raw = np.asarray(pmf, dtype=float)
        raw = np.clip(raw, 0.0, None)
        s = float(raw.sum())
        if not np.isfinite(s) or s <= 0:
            n = max(len(raw), 1)
            return np.full_like(raw, 1.0 / n)
        raw = raw / s

        try:
            global_pmf = self.global_calibrator.apply(raw)
        except Exception as e:
            logger.warning(
                f"RoleAwarePMFCalibrator[{self.stat}]: global apply failed: {e}"
            )
            return raw

        bucket_key = role_bucket if isinstance(role_bucket, str) else None
        if not bucket_key or bucket_key == "unknown":
            return global_pmf
        # Phase 14 monotone_inactive_global_v1: route configured buckets
        # through global-only regardless of fitted bucket calibrator.
        if bucket_key in ROLE_GLOBAL_ONLY_BUCKETS:
            return global_pmf
        bucket_cal = self.bucket_calibrators.get(bucket_key)
        if bucket_cal is None:
            return global_pmf

        try:
            bucket_pmf = bucket_cal.apply(raw)
        except Exception as e:
            logger.warning(
                f"RoleAwarePMFCalibrator[{self.stat}]: bucket apply failed "
                f"for {bucket_key}: {e}; falling back to global"
            )
            return global_pmf

        n = int(self.bucket_counts.get(bucket_key, 0))
        k = ROLE_SHRINK_K.get(bucket_key, 1200.0)
        cap = ROLE_WEIGHT_CAP.get(bucket_key, 0.75)
        denom = n + k
        w = min(cap, n / denom) if denom > 0 else 0.0

        out = (
            (1.0 - w) * np.asarray(global_pmf, dtype=float)
            + w * np.asarray(bucket_pmf, dtype=float)
        )
        out = np.clip(out, 0.0, None)
        s_out = float(out.sum())
        if not np.isfinite(s_out) or s_out <= 0:
            return global_pmf
        return out / s_out


def _randomized_pit(
    pmfs: np.ndarray, outcomes: np.ndarray, rng: np.random.Generator,
) -> np.ndarray:
    """Randomized PIT for discrete outcomes.

    Parameters
    ----------
    pmfs : (n, K) array of PMFs.
    outcomes : length-n array of integer outcomes in [0, K-1].
    rng : numpy Generator.

    Returns
    -------
    u : length-n array of PIT values (Uniform(0,1) under perfect cal).
    """
    n = len(outcomes)
    out = np.empty(n, dtype=float)
    for i, y in enumerate(outcomes):
        y = int(np.clip(y, 0, pmfs.shape[1] - 1))
        below = float(pmfs[i, :y].sum()) if y > 0 else 0.0
        out[i] = below + rng.uniform(0, 1) * float(pmfs[i, y])
    return np.clip(out, 0.0, 1.0)


def _walk_forward_folds(
    dates: np.ndarray, fold_days: int = 28, min_train_days: int = 180,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Yield (train_mask, val_mask) pairs across monotone date windows."""
    dates = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    unique_sorted = np.sort(dates.dt.normalize().unique())
    if len(unique_sorted) == 0:
        return []
    first = unique_sorted[0]
    last = unique_sorted[-1]
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    fold_start = pd.Timestamp(first) + pd.Timedelta(days=min_train_days)
    while fold_start <= pd.Timestamp(last):
        fold_end = fold_start + pd.Timedelta(days=fold_days)
        train_mask = (dates < fold_start).values
        val_mask = ((dates >= fold_start) & (dates < fold_end)).values
        if train_mask.sum() >= 100 and val_mask.sum() >= 20:
            folds.append((train_mask, val_mask))
        fold_start = fold_end
    return folds


def _fit_calibrator_no_save(
    stat: str,
    pmfs: np.ndarray,
    outcomes: np.ndarray,
    dates: np.ndarray,
    fold_days: int = 28,
    min_train_days: int = 180,
    rng: Optional[np.random.Generator] = None,
) -> Optional[PMFCalibrator]:
    """Fit the walk-forward isotonic calibrator for a single stat.

    Does NOT write to disk. Use `fit_calibrator()` for the legacy
    artifact-emitting wrapper, or call this directly when fitting many
    bucket-level calibrators that should not produce per-fit artifacts.
    """
    if rng is None:
        rng = np.random.default_rng(0)
    if len(pmfs) != len(outcomes) or len(pmfs) != len(dates):
        raise ValueError("pmfs/outcomes/dates length mismatch")
    if len(pmfs) < 200:
        logger.warning(f"pmf_calibration[{stat}]: too few rows ({len(pmfs)})")
        return None

    folds = _walk_forward_folds(np.array(dates), fold_days, min_train_days)
    if not folds:
        logger.warning(f"pmf_calibration[{stat}]: no valid folds")
        return None

    # Aggregate OOF PIT values.
    u_oof: list[np.ndarray] = []
    spans: list[tuple[str, str]] = []
    for train_mask, val_mask in folds:
        val_idx = np.where(val_mask)[0]
        pmf_val = pmfs[val_idx]
        y_val = outcomes[val_idx]
        u_val = _randomized_pit(pmf_val, y_val, rng)
        u_oof.append(u_val)
        dates_arr = pd.to_datetime(pd.Series(dates))
        spans.append((
            str(dates_arr[val_idx].min().date()),
            str(dates_arr[val_idx].max().date()),
        ))
    u_full = np.concatenate(u_oof)

    # Calibrate the raw CDF by fitting isotonic regression:
    # target is empirical quantile of u_full ranked ascending.
    u_sorted_idx = np.argsort(u_full)
    u_sorted = u_full[u_sorted_idx]
    empirical_q = (np.arange(1, len(u_sorted) + 1) - 0.5) / len(u_sorted)
    # Fit isotonic g: u -> empirical_q.
    # pmf_cal_endpoint_anchors
    u_fit = np.concatenate([
        np.asarray([0.0, 1e-6], dtype=float),
        np.asarray(u_sorted, dtype=float),
        np.asarray([1.0 - 1e-6, 1.0], dtype=float),
    ])
    q_fit = np.concatenate([
        np.asarray([0.0, 0.0], dtype=float),
        np.asarray(empirical_q, dtype=float),
        np.asarray([1.0, 1.0], dtype=float),
    ])
    w_fit = np.concatenate([
        np.asarray([1000.0, 1000.0], dtype=float),
        np.ones_like(np.asarray(u_sorted, dtype=float)),
        np.asarray([1000.0, 1000.0], dtype=float),
    ])
    order = np.argsort(u_fit)
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(u_fit[order], q_fit[order], sample_weight=w_fit[order])

    return PMFCalibrator(
        stat=stat,
        isotonic=iso,
        n_train=len(u_full),
        fold_spans=spans,
    )


def fit_calibrator(
    stat: str,
    pmfs: np.ndarray,
    outcomes: np.ndarray,
    dates: np.ndarray,
    fold_days: int = 28,
    min_train_days: int = 180,
    rng: Optional[np.random.Generator] = None,
) -> Optional[PMFCalibrator]:
    """Fit and persist the walk-forward isotonic calibrator for a stat
    to artifacts/models/pmf_cal_{stat}.pkl. Thin wrapper around
    `_fit_calibrator_no_save` that preserves the historical
    artifact-write side effect."""
    cal = _fit_calibrator_no_save(
        stat=stat, pmfs=pmfs, outcomes=outcomes, dates=dates,
        fold_days=fold_days, min_train_days=min_train_days, rng=rng,
    )
    if cal is not None:
        joblib.dump(cal, MODEL_DIR / f"pmf_cal_{stat}.pkl")
    return cal


def fit_role_aware_calibrator(
    stat: str,
    pmfs: np.ndarray,
    outcomes: np.ndarray,
    dates: np.ndarray,
    role_buckets: np.ndarray,
    fold_days: int = 28,
    min_train_days: int = 180,
    rng: Optional[np.random.Generator] = None,
) -> Optional[RoleAwarePMFCalibrator]:
    """Fit a role-aware PMF calibrator: one global isotonic plus one
    isotonic per role bucket meeting ROLE_MIN_ROWS. Buckets below the
    threshold are skipped and apply() falls back to the global
    calibrator at inference. The fitted bundle is saved to
    artifacts/models/pmf_cal_role_{stat}.pkl. Per-bucket isotonics are
    NOT saved as separate artifacts.
    """
    if rng is None:
        rng = np.random.default_rng(0)

    global_cal = _fit_calibrator_no_save(
        stat=stat, pmfs=pmfs, outcomes=outcomes, dates=dates,
        fold_days=fold_days, min_train_days=min_train_days, rng=rng,
    )
    if global_cal is None:
        return None

    role_buckets_arr = np.asarray(role_buckets).astype(str)
    if len(role_buckets_arr) != len(pmfs):
        raise ValueError("role_buckets length mismatch")
    unique_buckets, counts = np.unique(role_buckets_arr, return_counts=True)
    bucket_counts = {str(b): int(c) for b, c in zip(unique_buckets, counts)}

    bucket_calibrators: dict[str, PMFCalibrator] = {}
    dates_arr = np.asarray(dates)
    for bucket in unique_buckets:
        bucket_key = str(bucket)
        if bucket_key == "unknown":
            continue
        n_rows = int(bucket_counts.get(bucket_key, 0))
        min_rows = ROLE_MIN_ROWS.get(bucket_key, 500)
        if n_rows < min_rows:
            logger.info(
                f"pmf_calibration[{stat}]: skipping bucket '{bucket_key}' "
                f"(n={n_rows} < min_rows={min_rows})"
            )
            continue
        idx = np.where(role_buckets_arr == bucket_key)[0]
        bucket_cal = _fit_calibrator_no_save(
            stat=stat, pmfs=pmfs[idx], outcomes=outcomes[idx], dates=dates_arr[idx],
            fold_days=fold_days, min_train_days=min_train_days, rng=rng,
        )
        if bucket_cal is not None:
            bucket_calibrators[bucket_key] = bucket_cal

    bundle = RoleAwarePMFCalibrator(
        stat=stat,
        global_calibrator=global_cal,
        bucket_calibrators=bucket_calibrators,
        bucket_counts=bucket_counts,
    )
    joblib.dump(bundle, MODEL_DIR / f"pmf_cal_role_{stat}.pkl")
    return bundle


def load_calibrator(stat: str):
    """Load the role-aware bundle for `stat` if present; otherwise fall
    back to the legacy global PMFCalibrator artifact. Returns None if
    neither artifact is available or loadable. The return type is the
    union of `RoleAwarePMFCalibrator | PMFCalibrator | None`; both
    expose an `apply()` method, with the role-aware variant accepting
    an optional `role_bucket=` keyword."""
    role_p = MODEL_DIR / f"pmf_cal_role_{stat}.pkl"
    if role_p.exists():
        try:
            return joblib.load(role_p)
        except Exception as e:
            logger.warning(
                f"Failed loading role-aware calibrator {stat}: {e}; "
                "falling back to legacy global artifact"
            )
    p = MODEL_DIR / f"pmf_cal_{stat}.pkl"
    if not p.exists():
        return None
    try:
        return joblib.load(p)
    except Exception as e:
        logger.warning(f"Failed loading calibrator {stat}: {e}")
        return None


# ── Batch pipeline ───────────────────────────────────────────────────────────


def fit_all(
    per_stat_inputs: dict[str, tuple],
    fold_days: int = 28,
    min_train_days: int = 180,
    rng: Optional[np.random.Generator] = None,
) -> dict[str, dict]:
    """Fit one calibrator per stat and write a meta JSON summary.

    Accepts mixed-shape inputs per stat:
      * 3-tuple `(pmfs, outcomes, dates)`            → legacy global cal
      * 4-tuple `(pmfs, outcomes, dates, role_buckets)` → role-aware cal

    A single call may mix shapes safely; tuple length is detected per
    stat. Returns metadata dict mirroring what is written to
    artifacts/models/pmf_cal_meta.json.
    """
    if rng is None:
        rng = np.random.default_rng(0)
    meta: dict = {"stats": {}, "fold_days": fold_days, "min_train_days": min_train_days}
    any_role_aware = False
    for stat, inputs in per_stat_inputs.items():
        if len(inputs) == 4:
            pmfs, outcomes, dates, role_buckets = inputs
            cal = fit_role_aware_calibrator(
                stat=stat, pmfs=pmfs, outcomes=outcomes, dates=dates,
                role_buckets=role_buckets,
                fold_days=fold_days, min_train_days=min_train_days, rng=rng,
            )
            if cal is None:
                meta["stats"][stat] = {
                    "fitted": False, "role_aware": True,
                    "reason": "insufficient data",
                }
                continue
            any_role_aware = True
            u_raw = _randomized_pit(pmfs, outcomes, rng)
            # Apply the role-aware calibrator row-by-row so that
            # diagnostics measure the actual blended cal — not the
            # global isotonic alone.
            pmfs_cal = np.stack([
                cal.apply(pmfs[i], role_bucket=str(role_buckets[i]))
                for i in range(len(pmfs))
            ], axis=0)
            u_cal = _randomized_pit(pmfs_cal, outcomes, rng)
            meta["stats"][stat] = {
                "fitted": True,
                "role_aware": True,
                "calibration_version": ROLE_AWARE_VERSION,
                "n_train": int(cal.global_calibrator.n_train),
                "fold_spans": cal.global_calibrator.fold_spans,
                "bucket_counts": dict(cal.bucket_counts),
                "fitted_buckets": sorted(cal.bucket_calibrators.keys()),
                "pit_mean_raw": float(np.mean(u_raw)),
                "pit_std_raw": float(np.std(u_raw)),
                "pit_mean_cal": float(np.mean(u_cal)),
                "pit_std_cal": float(np.std(u_cal)),
            }
        elif len(inputs) == 3:
            pmfs, outcomes, dates = inputs
            cal = fit_calibrator(
                stat=stat, pmfs=pmfs, outcomes=outcomes, dates=dates,
                fold_days=fold_days, min_train_days=min_train_days, rng=rng,
            )
            if cal is None:
                meta["stats"][stat] = {
                    "fitted": False, "role_aware": False,
                    "reason": "insufficient data",
                }
                continue
            u_raw = _randomized_pit(pmfs, outcomes, rng)
            u_cal = cal.isotonic.transform(np.clip(u_raw, 0.0, 1.0))
            meta["stats"][stat] = {
                "fitted": True,
                "role_aware": False,
                "n_train": int(cal.n_train),
                "fold_spans": cal.fold_spans,
                "pit_mean_raw": float(np.mean(u_raw)),
                "pit_std_raw": float(np.std(u_raw)),
                "pit_mean_cal": float(np.mean(u_cal)),
                "pit_std_cal": float(np.std(u_cal)),
            }
        else:
            raise ValueError(
                f"per_stat_inputs[{stat}] must be a 3-tuple or 4-tuple, "
                f"got len={len(inputs)}"
            )
    if any_role_aware:
        meta["calibration_version"] = ROLE_AWARE_VERSION
    with open(CAL_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    return meta
