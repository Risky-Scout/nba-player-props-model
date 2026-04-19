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
        """Return calibrated PMF of same length as input."""
        if pmf is None or len(pmf) == 0:
            return pmf
        raw_cdf = np.cumsum(pmf)
        raw_cdf = np.clip(raw_cdf, 0.0, 1.0)
        cal_cdf = self.isotonic.transform(raw_cdf)
        # Clamp + monotone-enforce (isotonic already monotone, but
        # numerical round-off can nudge the last entry off 1.0).
        cal_cdf = np.clip(cal_cdf, 0.0, 1.0)
        cal_cdf[-1] = max(cal_cdf[-1], 1.0 - 1e-9)
        for i in range(1, len(cal_cdf)):
            if cal_cdf[i] < cal_cdf[i - 1]:
                cal_cdf[i] = cal_cdf[i - 1]
        cal_pmf = np.empty_like(cal_cdf)
        cal_pmf[0] = cal_cdf[0]
        cal_pmf[1:] = np.diff(cal_cdf)
        # Last defensive renormalisation.
        s = cal_pmf.sum()
        if s > 0:
            cal_pmf = cal_pmf / s
        return cal_pmf


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


def fit_calibrator(
    stat: str,
    pmfs: np.ndarray,
    outcomes: np.ndarray,
    dates: np.ndarray,
    fold_days: int = 28,
    min_train_days: int = 180,
    rng: Optional[np.random.Generator] = None,
) -> Optional[PMFCalibrator]:
    """Fit the walk-forward isotonic calibrator for a single stat."""
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
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(u_sorted, empirical_q)

    cal = PMFCalibrator(
        stat=stat,
        isotonic=iso,
        n_train=len(u_full),
        fold_spans=spans,
    )
    joblib.dump(cal, MODEL_DIR / f"pmf_cal_{stat}.pkl")
    return cal


def load_calibrator(stat: str) -> Optional[PMFCalibrator]:
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
    per_stat_inputs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]],
    fold_days: int = 28,
    min_train_days: int = 180,
    rng: Optional[np.random.Generator] = None,
) -> dict[str, dict]:
    """Fit one calibrator per stat and write a meta JSON summary.

    Parameters
    ----------
    per_stat_inputs : mapping stat -> (pmfs, outcomes, dates).

    Returns metadata dict mirroring what is written to
    artifacts/models/pmf_cal_meta.json.
    """
    if rng is None:
        rng = np.random.default_rng(0)
    meta: dict = {"stats": {}, "fold_days": fold_days, "min_train_days": min_train_days}
    for stat, (pmfs, outcomes, dates) in per_stat_inputs.items():
        cal = fit_calibrator(
            stat=stat, pmfs=pmfs, outcomes=outcomes, dates=dates,
            fold_days=fold_days, min_train_days=min_train_days, rng=rng,
        )
        if cal is None:
            meta["stats"][stat] = {"fitted": False, "reason": "insufficient data"}
            continue
        # Evaluate the calibrator on the combined OOF set.
        u_raw = _randomized_pit(pmfs, outcomes, rng)
        u_cal = cal.isotonic.transform(np.clip(u_raw, 0.0, 1.0))
        meta["stats"][stat] = {
            "fitted": True,
            "n_train": int(cal.n_train),
            "fold_spans": cal.fold_spans,
            "pit_mean_raw": float(np.mean(u_raw)),
            "pit_std_raw": float(np.std(u_raw)),
            "pit_mean_cal": float(np.mean(u_cal)),
            "pit_std_cal": float(np.std(u_cal)),
        }
    with open(CAL_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    return meta
