"""Monotone PIT/CDF calibration for discrete PMFs with fallback hierarchy.

This implements a lightweight, JSON-serializable version of isotonic PIT
calibration:
- Fit a monotone map \(g\) such that \(g(U)\) is approximately Uniform(0,1),
  where \(U\) is the PIT value under the raw model.
- Apply \(g\) to every knot of the raw CDF, then differentiate to recover a
  calibrated PMF.

Hierarchy at apply time:
  1) stat-role
  2) stat
  3) role
  4) global

Guardrails:
- PMFs are repaired to sum to 1 and have no negatives after calibration.
- Fit scripts must roll back any stat-role map that worsens BOTH NLL and RPS.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np


def _repair_pmf(pmf: np.ndarray) -> np.ndarray:
    p = np.asarray(pmf, dtype=float)
    p = np.clip(np.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0), 0.0, None)
    s = float(p.sum())
    if not np.isfinite(s) or s <= 0:
        return np.full_like(p, 1.0 / max(len(p), 1))
    return p / s


def _apply_piecewise_linear_map(x: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Monotone piecewise-linear map with endpoint anchoring."""
    if xs.size < 2 or ys.size < 2:
        return np.clip(x, 0.0, 1.0)
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    # Ensure sorted + monotone ys.
    order = np.argsort(xs)
    xs = xs[order]
    ys = ys[order]
    ys = np.maximum.accumulate(ys)
    xs = np.clip(xs, 0.0, 1.0)
    ys = np.clip(ys, 0.0, 1.0)
    return np.clip(np.interp(np.clip(x, 0.0, 1.0), xs, ys), 0.0, 1.0)


def calibrate_pmf_from_map(pmf: np.ndarray, *, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    p = _repair_pmf(pmf)
    if len(p) == 0:
        return p
    cdf = np.cumsum(p)
    cdf_cal = _apply_piecewise_linear_map(cdf, xs, ys)
    # Ensure cdf_cal is non-decreasing and ends at 1.
    cdf_cal = np.maximum.accumulate(cdf_cal)
    cdf_cal[-1] = 1.0
    pmf_cal = np.diff(np.concatenate([[0.0], cdf_cal]))
    pmf_cal = _repair_pmf(pmf_cal)
    return pmf_cal


def pit_mid(pmf: np.ndarray, y: int) -> float:
    p = _repair_pmf(pmf)
    y = int(np.clip(int(y), 0, len(p) - 1))
    return float(np.sum(p[:y]) + 0.5 * p[y])


@dataclass
class CDFMap:
    xs: np.ndarray
    ys: np.ndarray
    n_train: int

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> "CDFMap":
        return cls(
            xs=np.asarray(obj.get("xs", []), dtype=float),
            ys=np.asarray(obj.get("ys", []), dtype=float),
            n_train=int(obj.get("n_train", 0)),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "xs": [float(x) for x in self.xs.tolist()],
            "ys": [float(y) for y in self.ys.tolist()],
            "n_train": int(self.n_train),
        }


class MonotonePMFCDFCalibrator:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec or {}
        self.version = str(self.spec.get("version", "monotone_pit_cdf_v1"))
        self.stat_role = {k: CDFMap.from_json(v) for k, v in self.spec.get("stat_role", {}).items()}
        self.by_stat = {k: CDFMap.from_json(v) for k, v in self.spec.get("by_stat", {}).items()}
        self.by_role = {k: CDFMap.from_json(v) for k, v in self.spec.get("by_role", {}).items()}
        self.global_map = CDFMap.from_json(self.spec.get("global", {"xs": [0.0, 1.0], "ys": [0.0, 1.0], "n_train": 0}))

    @classmethod
    def load(cls, path: Path) -> Optional["MonotonePMFCDFCalibrator"]:
        if not path.exists():
            return None
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def _pick(self, stat: str, role_bucket: str) -> CDFMap:
        stat = str(stat).lower()
        role = str(role_bucket).lower()
        key = f"{stat}|{role}"
        if key in self.stat_role:
            return self.stat_role[key]
        if stat in self.by_stat:
            return self.by_stat[stat]
        if role in self.by_role:
            return self.by_role[role]
        return self.global_map

    def apply(self, pmf: np.ndarray, *, stat: str, role_bucket: str) -> np.ndarray:
        m = self._pick(stat, role_bucket)
        return calibrate_pmf_from_map(pmf, xs=m.xs, ys=m.ys)
