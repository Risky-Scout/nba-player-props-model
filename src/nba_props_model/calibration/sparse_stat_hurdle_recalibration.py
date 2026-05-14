"""Sparse-stat guarded hurdle recalibration (no market PMF).

Applies two adjustments to sparse stat PMFs:
1) **Zero-mass (p0) calibration** by stat-role with hierarchical shrinkage.
2) **Positive-tail tilt** (exponential reweighting on k>0) to match positive
   mean by stat-role, also with shrinkage.

This is intentionally conservative:
- Parameters are fit on a calibration split and evaluated on a holdout split.
- Any stat-role cell that worsens BOTH NLL and RPS on holdout is rolled back.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SPARSE_STATS = frozenset({"stl", "blk", "stocks", "tov", "fg3m"})


def _repair_pmf(arr: np.ndarray) -> np.ndarray:
    x = np.asarray(arr, dtype=float)
    x = np.clip(np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    s = float(x.sum())
    if not np.isfinite(s) or s <= 0:
        return np.full_like(x, 1.0 / max(len(x), 1))
    return x / s


def _p0(arr: np.ndarray) -> float:
    return float(arr[0]) if len(arr) else 0.0


def _pos_mean(arr: np.ndarray) -> float:
    """E[Y | Y>0] under pmf; returns 0 when P(Y>0)=0."""
    if len(arr) <= 1:
        return 0.0
    p = float(1.0 - arr[0])
    if p <= 1e-12:
        return 0.0
    ks = np.arange(len(arr), dtype=float)
    mu = float(np.dot(ks[1:], arr[1:]) / p)
    return mu


def _nll(arr: np.ndarray, y: int) -> float:
    y = int(np.clip(int(y), 0, len(arr) - 1))
    return -math.log(max(float(arr[y]), 1e-15))


def _rps(arr: np.ndarray, y: int) -> float:
    cdf = np.cumsum(arr)
    obs = (np.arange(len(arr)) >= int(y)).astype(float)
    return float(np.mean((cdf - obs) ** 2))


def apply_hurdle_guarded(
    pmf: np.ndarray,
    *,
    p0_target: float | None = None,
    tail_lambda: float | None = None,
) -> np.ndarray:
    """Apply p0 calibration + exponential tilt on k>0, preserving PMF validity."""
    p = _repair_pmf(pmf)
    n = len(p)
    if n == 0:
        return p

    p0 = float(np.clip(_p0(p), 1e-12, 1.0 - 1e-12))
    if p0_target is not None:
        t0 = float(np.clip(p0_target, 1e-6, 1.0 - 1e-6))
        if abs(t0 - p0) > 1e-12:
            scale = (1.0 - t0) / max(1.0 - p0, 1e-12)
            p = p.copy()
            p[0] = t0
            if n > 1:
                p[1:] *= scale
            p = _repair_pmf(p)

    if tail_lambda is None or n <= 2:
        return p

    lam = float(np.clip(tail_lambda, -2.0, 2.0))
    if abs(lam) < 1e-10:
        return p

    # Exponential tilt only on k>0, conditional on positive tail.
    q = p.copy()
    tail = q[1:]
    ks = np.arange(1, n, dtype=float)
    w = np.exp(np.clip(lam * ks, -30.0, 30.0))
    tail = tail * w
    tail_sum = float(tail.sum())
    if not np.isfinite(tail_sum) or tail_sum <= 0:
        return p
    q[1:] = tail * ((1.0 - q[0]) / tail_sum)
    return _repair_pmf(q)


def load_offsets(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


class SparseHurdleCalibrator:
    """Lightweight JSON-serialized sparse-stat calibrator."""

    def __init__(self, spec: dict[str, Any] | None) -> None:
        self.spec = spec or {}
        self.version = str(self.spec.get("version", "sparse_hurdle_guarded_v1"))
        self.cells = dict(self.spec.get("cells", {}))
        self.stat_fallback = dict(self.spec.get("by_stat", {}))
        self.role_fallback = dict(self.spec.get("by_role", {}))
        self.global_fallback = dict(self.spec.get("global", {}))

    @classmethod
    def load(cls, path: Path) -> "SparseHurdleCalibrator | None":
        if not path.exists():
            return None
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def _params_for(self, stat: str, role_bucket: str) -> dict[str, Any]:
        key = f"{str(stat).lower()}|{str(role_bucket).lower()}"
        if key in self.cells:
            return dict(self.cells[key])
        s = str(stat).lower()
        r = str(role_bucket).lower()
        if s in self.stat_fallback:
            return dict(self.stat_fallback[s])
        if r in self.role_fallback:
            return dict(self.role_fallback[r])
        return dict(self.global_fallback)

    def apply(self, pmf: np.ndarray, *, stat: str, role_bucket: str) -> np.ndarray:
        if str(stat).lower() not in SPARSE_STATS:
            return _repair_pmf(pmf)
        params = self._params_for(stat, role_bucket)
        if params.get("mode") == "identity":
            return _repair_pmf(pmf)
        return apply_hurdle_guarded(
            pmf,
            p0_target=params.get("p0_target"),
            tail_lambda=params.get("tail_lambda"),
        )

    def evaluate_rows(
        self,
        pmfs: list[np.ndarray],
        y: np.ndarray,
        *,
        stat: str,
        role_bucket: str,
    ) -> dict[str, float]:
        nlls_b, rpss_b = [], []
        nlls_a, rpss_a = [], []
        p0s_b, p0s_a = [], []
        for p, yi in zip(pmfs, y):
            pb = _repair_pmf(p)
            pa = self.apply(pb, stat=stat, role_bucket=role_bucket)
            nlls_b.append(_nll(pb, int(yi)))
            rpss_b.append(_rps(pb, int(yi)))
            nlls_a.append(_nll(pa, int(yi)))
            rpss_a.append(_rps(pa, int(yi)))
            p0s_b.append(_p0(pb))
            p0s_a.append(_p0(pa))
        y0 = (np.asarray(y, dtype=int) == 0).astype(float)
        return {
            "n": float(len(y)),
            "p0_error_before": float(np.mean(y0) - np.mean(p0s_b)),
            "p0_error_after": float(np.mean(y0) - np.mean(p0s_a)),
            "pos_mean_before": float(np.mean([_pos_mean(_repair_pmf(p)) for p in pmfs])),
            "pos_mean_after": float(np.mean([_pos_mean(self.apply(_repair_pmf(p), stat=stat, role_bucket=role_bucket)) for p in pmfs])),
            "nll_before": float(np.mean(nlls_b)),
            "nll_after": float(np.mean(nlls_a)),
            "rps_before": float(np.mean(rpss_b)),
            "rps_after": float(np.mean(rpss_a)),
        }
