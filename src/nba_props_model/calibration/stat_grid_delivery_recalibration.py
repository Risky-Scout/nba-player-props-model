from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


VERSION_DEFAULT = "v4_guarded_oof_rollforward"
NO_MARKET_PMF_USED = True


def _artifact_dir() -> Path:
    env = os.environ.get("STAT_GRID_RECALIBRATION_MODEL_DIR") or os.environ.get("SOURCE_RECALIBRATION_MODEL_DIR")
    if env:
        return Path(env)
    return Path("_stat_grid_delivery_calibration_optimizer/artifacts/models")


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return default


def repair_and_validate_pmf(pmf: Any, *, eps: float = 1e-12) -> np.ndarray:
    arr = np.asarray(pmf, dtype=float).reshape(-1)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr = np.clip(arr, 0.0, None)
    total = float(arr.sum())
    if total <= 0.0 or not math.isfinite(total):
        raise ValueError("invalid calibrated PMF: zero/non-finite mass")
    arr = arr / total
    if not np.all(np.isfinite(arr)):
        raise ValueError("invalid calibrated PMF: non-finite value")
    if np.any(arr < -eps):
        raise ValueError("invalid calibrated PMF: negative mass")
    if abs(float(arr.sum()) - 1.0) > 1e-8:
        raise ValueError("invalid calibrated PMF: mass does not sum to 1")
    return arr


def _moments(pmf: np.ndarray) -> tuple[float, float]:
    y = np.arange(len(pmf), dtype=float)
    mu = float(np.dot(y, pmf))
    var = float(np.dot((y - mu) ** 2, pmf))
    return mu, max(var, 1e-12)


def _tilt_to_mean(pmf: np.ndarray, target_mean: float) -> tuple[np.ndarray, bool]:
    pmf = repair_and_validate_pmf(pmf)
    y = np.arange(len(pmf), dtype=float)
    lo_mean = float(y[pmf > 1e-15].min()) if np.any(pmf > 1e-15) else 0.0
    hi_mean = float(y[pmf > 1e-15].max()) if np.any(pmf > 1e-15) else float(len(pmf) - 1)
    target = float(np.clip(target_mean, lo_mean + 1e-9, hi_mean - 1e-9))
    current, _ = _moments(pmf)
    if abs(current - target) < 1e-10:
        return pmf, True

    def tilted(lam: float) -> tuple[np.ndarray, float]:
        z = np.log(np.maximum(pmf, 1e-300)) + lam * y
        z -= float(np.max(z))
        q = np.exp(z)
        q = q / float(q.sum())
        return q, float(np.dot(y, q))

    lo, hi = -50.0, 50.0
    q_best, m_best = pmf, current
    for _ in range(100):
        mid = (lo + hi) / 2.0
        q, m = tilted(mid)
        if abs(m - target) < abs(m_best - target):
            q_best, m_best = q, m
        if m < target:
            lo = mid
        else:
            hi = mid
    exact = abs(m_best - target) <= max(1e-5, 1e-4 * max(1.0, abs(target)))
    return repair_and_validate_pmf(q_best), exact


def _tilt_to_variance(pmf: np.ndarray, target_var: float, *, center: float | None = None) -> tuple[np.ndarray, bool]:
    pmf = repair_and_validate_pmf(pmf)
    y = np.arange(len(pmf), dtype=float)
    mu, var0 = _moments(pmf)
    if center is None:
        center = mu
    target = max(float(target_var), 1e-8)
    if abs(var0 - target) < 1e-10:
        return pmf, True

    # Quadratic exponential tilt. Positive gamma widens; negative narrows.
    qterm = (y - float(center)) ** 2

    def tilted(gamma: float) -> tuple[np.ndarray, float]:
        z = np.log(np.maximum(pmf, 1e-300)) + gamma * qterm
        z -= float(np.max(z))
        q = np.exp(z)
        q = q / float(q.sum())
        mu2 = float(np.dot(y, q))
        var2 = float(np.dot((y - mu2) ** 2, q))
        return q, var2

    # Determine search direction.
    if target > var0:
        lo, hi = 0.0, 10.0
    else:
        lo, hi = -10.0, 0.0

    q_best, v_best = pmf, var0
    for _ in range(120):
        mid = (lo + hi) / 2.0
        q, v = tilted(mid)
        if abs(v - target) < abs(v_best - target):
            q_best, v_best = q, v
        if target > var0:
            if v < target:
                lo = mid
            else:
                hi = mid
        else:
            if v > target:
                hi = mid
            else:
                lo = mid

    exact = abs(v_best - target) <= max(1e-5, 1e-3 * max(1.0, abs(target)))
    return repair_and_validate_pmf(q_best), exact


def _apply_p0(pmf: np.ndarray, p0_target: float | None, strength: float) -> tuple[np.ndarray, bool]:
    pmf = repair_and_validate_pmf(pmf)
    if p0_target is None or len(pmf) < 2 or strength <= 0:
        return pmf, True
    target = float(np.clip(p0_target, 1e-6, 1.0 - 1e-6))
    cur = float(pmf[0])
    new0 = float(np.clip(cur + strength * (target - cur), 1e-6, 1.0 - 1e-6))
    pos = float(pmf[1:].sum())
    out = pmf.copy()
    out[0] = new0
    if pos <= 1e-12:
        out[1:] = (1.0 - new0) / (len(out) - 1)
    else:
        out[1:] = out[1:] * ((1.0 - new0) / pos)
    return repair_and_validate_pmf(out), True


def _extract_pmf(payload: Any) -> np.ndarray:
    if isinstance(payload, np.ndarray):
        return repair_and_validate_pmf(payload)
    if isinstance(payload, (list, tuple)):
        return repair_and_validate_pmf(payload)
    if isinstance(payload, dict):
        # dict may have string integer keys or named fields.
        if "pmf" in payload:
            return _extract_pmf(payload["pmf"])
        vals = []
        for k, v in sorted(payload.items(), key=lambda kv: int(kv[0]) if str(kv[0]).lstrip("-").isdigit() else str(kv[0])):
            if str(k).lstrip("-").isdigit():
                vals.append(v)
        if vals:
            return repair_and_validate_pmf(vals)
    if isinstance(payload, str):
        s = payload.strip()
        if not s:
            raise ValueError("empty PMF string")
        return _extract_pmf(json.loads(s))
    raise ValueError(f"unsupported PMF payload type: {type(payload)}")


def _key(stat: str | None, role: str | None) -> str:
    return f"{str(stat or '').lower()}|{str(role or '').lower()}"


@dataclass
class StatGridDeliveryRecalibrator:
    params: dict[str, Any]
    enabled: bool = True
    version: str = VERSION_DEFAULT

    def __post_init__(self) -> None:
        self.enabled = bool(self.params.get("enabled", self.enabled))
        self.version = str(self.params.get("version", self.version))
        self.cells = self.params.get("cells", {}) or {}
        self.global_params = self.params.get("global", {}) or {}

    def _params_for(self, stat: str | None, role_bucket: str | None) -> dict[str, Any]:
        stat = str(stat or "").lower()
        role = str(role_bucket or "").lower()
        for k in [f"{stat}|{role}", f"{stat}|*", f"*|{role}", "global"]:
            if k in self.cells:
                return dict(self.cells[k], _selected_key=k)
        g = dict(self.global_params)
        g["_selected_key"] = "global"
        return g

    def apply(self, pmf: Any, *, stat: str | None = None, role_bucket: str | None = None, **kwargs: Any) -> tuple[np.ndarray, dict[str, Any]]:
        raw = _extract_pmf(pmf)
        meta = {
            "source_recalibration_applied": False,
            "source_recalibration_version": self.version,
            "source_recalibration_stage": "identity",
            "mean_multiplier_applied": 1.0,
            "variance_multiplier_applied": 1.0,
            "p0_target_applied": np.nan,
            "mean_tilt_exact": True,
            "variance_tilt_exact": True,
            "pmf_valid": True,
            "market_pmf_used": False,
        }
        if not self.enabled:
            return raw, meta

        p = self._params_for(stat, role_bucket)
        if str(p.get("mode", "identity")) == "identity":
            meta.update({
                "source_recalibration_stage": "identity_rollback",
                "pmf_calibrator_backoff_key": p.get("_selected_key", "global"),
            })
            return raw, meta

        mean_mult = _safe_float(p.get("mean_multiplier", 1.0), 1.0)
        var_mult = _safe_float(p.get("variance_multiplier", 1.0), 1.0)
        p0_target = p.get("p0_target", None)
        if p0_target is not None:
            p0_target = _safe_float(p0_target, float(raw[0]) if len(raw) else 0.0)
        p0_strength = _safe_float(p.get("p0_strength", 0.0), 0.0)

        q = raw
        mu0, var0 = _moments(q)

        # Apply mean first.
        if abs(mean_mult - 1.0) > 1e-8:
            target_mean = float(np.clip(mu0 * mean_mult, 0.0, max(0.0, len(q) - 1.0)))
            q, mean_exact = _tilt_to_mean(q, target_mean)
            meta["mean_tilt_exact"] = bool(mean_exact)

        # Apply p0 after mean for sparse cells.
        if p0_target is not None and p0_strength > 0:
            q, _ = _apply_p0(q, p0_target, p0_strength)

        # Apply variance with guardrails.
        if abs(var_mult - 1.0) > 1e-8:
            mu1, var1 = _moments(q)
            target_var = float(np.clip(var1 * var_mult, 1e-8, ((len(q) - 1) ** 2) / 4.0 + 1e-8))
            q, var_exact = _tilt_to_variance(q, target_var, center=mu1)
            meta["variance_tilt_exact"] = bool(var_exact)

        q = repair_and_validate_pmf(q)
        meta.update({
            "source_recalibration_applied": True,
            "source_recalibration_stage": str(p.get("stage", "v4_mean_p0_variance_guarded")),
            "mean_multiplier_applied": float(mean_mult),
            "variance_multiplier_applied": float(var_mult),
            "p0_target_applied": float(p0_target) if p0_target is not None else np.nan,
            "p0_strength_applied": float(p0_strength),
            "pmf_calibrator_backoff_key": p.get("_selected_key", "global"),
            "pmf_valid": True,
            "market_pmf_used": False,
        })
        return q, meta

    # Compatibility aliases for prior patches.
    def recalibrate_pmf(self, pmf: Any, stat: str | None = None, role_bucket: str | None = None, **kwargs: Any):
        return self.apply(pmf, stat=stat, role_bucket=role_bucket, **kwargs)

    def calibrate_pmf(self, pmf: Any, stat: str | None = None, role_bucket: str | None = None, **kwargs: Any):
        return self.apply(pmf, stat=stat, role_bucket=role_bucket, **kwargs)

    def recalibrate(self, pmf: Any, stat: str | None = None, role_bucket: str | None = None, **kwargs: Any):
        return self.apply(pmf, stat=stat, role_bucket=role_bucket, **kwargs)

    def recalibrate_stat_grid_pmf(self, pmf: Any, stat: str | None = None, role_bucket: str | None = None, **kwargs: Any):
        return self.apply(pmf, stat=stat, role_bucket=role_bucket, **kwargs)


@dataclass
class DeliveryEventCalibrator:
    params: dict[str, Any]
    enabled: bool = True
    version: str = VERSION_DEFAULT

    def __post_init__(self) -> None:
        self.enabled = bool(self.params.get("event_calibration_enabled", True))
        self.version = str(self.params.get("version", self.version))
        self.weights = self.params.get("event_weights", {}) or {}

    def _weight_for(self, stat: str | None, role_bucket: str | None) -> tuple[float, str]:
        stat = str(stat or "").lower()
        role = str(role_bucket or "").lower()
        for k in [f"{stat}|{role}", f"{stat}|*", f"*|{role}", "global"]:
            if k in self.weights:
                return float(np.clip(_safe_float(self.weights[k], 1.0), 0.0, 1.0)), k
        return 1.0, "identity"

    def calibrate_event_probability(
        self,
        *,
        stat: str | None = None,
        role_bucket: str | None = None,
        raw_model_prob_over: float | None = None,
        model_prob_over: float | None = None,
        market_prob_over_no_vig: float | None = None,
        **kwargs: Any,
    ) -> tuple[float, dict[str, Any]]:
        q = raw_model_prob_over if raw_model_prob_over is not None else model_prob_over
        q = float(np.clip(_safe_float(q, 0.5), 1e-6, 1.0 - 1e-6))
        m = market_prob_over_no_vig
        meta = {
            "raw_model_prob_over": q,
            "calibrated_model_prob_over": q,
            "final_model_prob_over": q,
            "event_market_shrinkage_applied": False,
            "model_market_event_blend_weight": 1.0,
            "event_calibrator_version": self.version,
            "market_pmf_used": False,
        }
        if not self.enabled or m is None:
            return q, meta
        m = float(np.clip(_safe_float(m, q), 1e-6, 1.0 - 1e-6))
        w, key = self._weight_for(stat, role_bucket)
        final = float(np.clip(w * q + (1.0 - w) * m, 1e-6, 1.0 - 1e-6))
        meta.update({
            "market_prob_over_no_vig": m,
            "final_model_prob_over": final,
            "event_market_shrinkage_applied": bool(w < 0.999),
            "model_market_event_blend_weight": float(w),
            "event_calibrator_backoff_key": key,
        })
        return final, meta


def _load_params(model_dir: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    d = Path(model_dir) if model_dir is not None else _artifact_dir()
    p = d / "stat_grid_recalibration_params.json"
    if not p.exists():
        return {
            "enabled": False,
            "version": VERSION_DEFAULT,
            "cells": {},
            "global": {"mode": "identity"},
            "event_calibration_enabled": False,
            "event_weights": {"global": 1.0},
            "market_pmf_used": False,
        }
    data = json.loads(p.read_text())
    data["market_pmf_used"] = False
    return data


def load_stat_grid_delivery_recalibrator(model_dir: str | os.PathLike[str] | None = None) -> StatGridDeliveryRecalibrator:
    return StatGridDeliveryRecalibrator(_load_params(model_dir))


def load_delivery_event_calibrator(model_dir: str | os.PathLike[str] | None = None) -> DeliveryEventCalibrator:
    return DeliveryEventCalibrator(_load_params(model_dir))
