"""OOF event-neutral probability scaling (no market labels/features)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.isotonic import IsotonicRegression


EPS = 1e-12

FORBIDDEN_TRAINING_FEATURE_NAMES = frozenset(
    {
        "market_prob",
        "market_prob_over",
        "market_over",
        "no_vig",
        "book_prob",
        "odds_implied_prob",
        "vig_free",
        "edge",
    }
)


def assert_no_forbidden_training_columns(columns: Iterable[str]) -> None:
    """Fail if any column name exactly (case-insensitive) matches a forbidden training feature."""
    low = {str(c).lower() for c in columns}
    hit = sorted(low & {x.lower() for x in FORBIDDEN_TRAINING_FEATURE_NAMES})
    if hit:
        raise SystemExit(f"FATAL: forbidden market-derived training column names present: {hit}")
def clip01(p: float | np.ndarray) -> float | np.ndarray:
    return np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)


def logit(p: np.ndarray) -> np.ndarray:
    p = clip01(p)
    return np.log(p / (1.0 - p))


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))


def binary_logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = clip01(p)
    y = np.asarray(y, dtype=float)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def brier_score(p: np.ndarray, y: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.mean((p - y) ** 2))


def calibration_slope_intercept(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """OLS of y on logit(p); returns (slope, intercept)."""
    p = clip01(np.asarray(p, dtype=float))
    y = np.asarray(y, dtype=float)
    if len(p) < 5:
        return (float("nan"), float("nan"))
    x = logit(p)
    xm = x - x.mean()
    ym = y - y.mean()
    denom = float(np.dot(xm, xm))
    if denom <= 1e-12:
        return (float("nan"), float("nan"))
    slope = float(np.dot(xm, ym) / denom)
    intercept = float(y.mean() - slope * x.mean())
    return slope, intercept


def ece_10bin(p: np.ndarray, y: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(p) < 10:
        return float("nan")
    edges = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi if hi < 1.0 else p <= 1.0)
        n = int(m.sum())
        if n == 0:
            continue
        conf = float(p[m].mean())
        acc = float(y[m].mean())
        ece += (n / len(p)) * abs(acc - conf)
    return float(ece)


def chronological_date_folds(
    dates: Iterable[str], n_folds: int = 5
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return list of (train_dates, val_dates) as string arrays.

    Each val fold is a contiguous block of sorted unique dates; train is strictly
    earlier dates only (no leakage on game_date).
    """
    u = np.array(sorted(set(str(d) for d in dates if d is not None and str(d))), dtype=object)
    if len(u) < n_folds + 1:
        n_folds = max(2, min(n_folds, len(u) - 1))
    if len(u) < 3:
        return []
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    blocks = np.array_split(u, n_folds)
    for val_block in blocks:
        if val_block.size == 0:
            continue
        first_val = str(val_block.min())
        train_mask = u < first_val
        train_dates = u[train_mask]
        if train_dates.size == 0:
            continue
        folds.append((train_dates, val_block))
    return folds


def apply_logit_ab(p: float | np.ndarray, a: float, b: float) -> np.ndarray:
    z = a * logit(np.asarray(p, dtype=float)) + b
    return sigmoid(z)


def apply_shrink_to_half(p: float | np.ndarray, lam: float) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    return np.clip(0.5 + lam * (p - 0.5), EPS, 1.0 - EPS)


def fit_isotonic_values(
    p_train: np.ndarray, y_train: np.ndarray
) -> tuple[np.ndarray, np.ndarray] | None:
    if len(p_train) < 10:
        return None
    iso = IsotonicRegression(y_min=EPS, y_max=1.0 - EPS, out_of_bounds="clip")
    iso.fit(p_train, y_train)
    xt = np.linspace(0.0, 1.0, 33)
    yt = iso.predict(xt)
    return xt.astype(float), yt.astype(float)


def apply_isotonic_table(p: np.ndarray, xt: np.ndarray, yt: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    p_clip = np.clip(p, float(xt[0]), float(xt[-1]))
    return np.interp(p_clip, xt, yt)


def blend_iso_parent(
    p: np.ndarray,
    xt: np.ndarray,
    yt: np.ndarray,
    parent_cal: np.ndarray,
    w: float,
) -> np.ndarray:
    return np.clip(
        w * apply_isotonic_table(p, xt, yt) + (1.0 - w) * parent_cal,
        EPS,
        1.0 - EPS,
    )


def load_probability_scale_manifest(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def lookup_segment_spec(
    manifest: dict[str, Any], stat: str, role_bucket: str
) -> tuple[str | None, dict[str, Any] | None]:
    segs = manifest.get("segments") or {}
    st = str(stat).lower()
    rb = str(role_bucket or "unknown").lower()
    order = (f"{st}|{rb}", f"{st}|*", "global")
    for k in order:
        if k in segs and isinstance(segs[k], dict):
            return k, segs[k]
    return None, None


def apply_manifest_to_probability(
    p_over: float | None,
    *,
    stat: str,
    role_bucket: str,
    manifest: dict[str, Any] | None,
) -> tuple[float | None, str | None, str | None, bool]:
    """Return (p_active, scope_key, method, applied_accepted).

    If manifest missing or segment not accepted, returns (p_over, None, None, False).
    """
    if p_over is None or not math.isfinite(float(p_over)):
        return None, None, None, False
    if manifest is None:
        return float(p_over), None, None, False
    key, spec = lookup_segment_spec(manifest, stat, role_bucket)
    if spec is None or not bool(spec.get("accepted", False)):
        return float(p_over), None, None, False
    method = str(spec.get("selected_method") or "")
    p0 = float(np.clip(p_over, EPS, 1.0 - EPS))
    p_arr = np.array([p0], dtype=float)
    out: np.ndarray
    if method in ("logit_ab", "hierarchical_logit_shrinkage"):
        a = float(spec.get("a", 1.0))
        b = float(spec.get("b", 0.0))
        out = apply_logit_ab(p_arr, a, b)
    elif method == "shrink_to_half":
        lam = float(spec.get("lambda", spec.get("lambda_shrink", 1.0)))
        out = apply_shrink_to_half(p_arr, lam)
    elif method == "shrunk_isotonic":
        xt = np.asarray(spec.get("isotonic_x") or [], dtype=float)
        yt = np.asarray(spec.get("isotonic_y") or [], dtype=float)
        w = float(spec.get("isotonic_weight", 0.25))
        pt = spec.get("parent_transform")
        if isinstance(pt, dict) and str(pt.get("method") or "") == "logit_ab":
            pa = float(pt.get("a", 1.0))
            pb = float(pt.get("b", 0.0))
            parent = apply_logit_ab(p_arr, pa, pb)
        else:
            parent = np.asarray(spec.get("parent_p_cal") or p_arr, dtype=float)
        if xt.size < 2 or yt.size < 2:
            return float(p_over), key, method, False
        out = blend_iso_parent(p_arr, xt, yt, parent, w)
    else:
        return float(p_over), key, method, False
    val = float(out[0])
    if not math.isfinite(val):
        return float(p_over), key, method, False
    return float(np.clip(val, EPS, 1.0 - EPS)), key, method, True
