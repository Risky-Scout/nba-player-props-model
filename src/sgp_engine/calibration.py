from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression


@dataclass
class JointProbabilityCalibrator:
    calibrator_id: str
    model: IsotonicRegression
    n_train: int
    cell: str = "global"

    def predict(self, x):
        arr = np.asarray(x, dtype=float).reshape(-1)
        return np.clip(self.model.predict(arr), 1e-9, 1 - 1e-9)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> "JointProbabilityCalibrator":
        obj = joblib.load(path)
        if not isinstance(obj, JointProbabilityCalibrator):
            raise TypeError(f"Expected JointProbabilityCalibrator, got {type(obj)}")
        return obj


def fit_global_joint_calibrator(
    backtest_rows: pd.DataFrame,
    *,
    pred_col: str = "raw_joint_probability",
    y_col: str = "hit_result",
    min_n: int = 300,
    out_path: str | Path | None = None,
) -> JointProbabilityCalibrator:
    df = backtest_rows[[pred_col, y_col]].dropna().copy()
    df[pred_col] = df[pred_col].clip(1e-6, 1 - 1e-6).astype(float)
    df[y_col] = df[y_col].astype(int)
    if len(df) < min_n:
        raise ValueError(f"Insufficient rows for joint calibrator: n={len(df)} < {min_n}")
    model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    model.fit(df[pred_col].to_numpy(), df[y_col].to_numpy())
    cal = JointProbabilityCalibrator(
        calibrator_id=f"global_isotonic_n{len(df)}",
        model=model,
        n_train=len(df),
        cell="global",
    )
    if out_path is not None:
        cal.save(out_path)
    return cal


def reliability_table(
    rows: pd.DataFrame,
    *,
    pred_col: str = "calibrated_joint_probability",
    y_col: str = "hit_result",
    bins: int = 20,
) -> pd.DataFrame:
    df = rows[[pred_col, y_col]].dropna().copy()
    df[pred_col] = df[pred_col].clip(0, 1)
    df["bucket"] = pd.cut(df[pred_col], bins=np.linspace(0, 1, bins + 1), include_lowest=True)
    g = df.groupby("bucket", observed=False)
    out = g.agg(
        n=(y_col, "size"),
        mean_pred=(pred_col, "mean"),
        actual_rate=(y_col, "mean"),
    ).reset_index()
    out["abs_calibration_error"] = (out["mean_pred"] - out["actual_rate"]).abs()
    out["weighted_abs_calibration_error"] = out["abs_calibration_error"] * out["n"] / max(len(df), 1)
    return out


def expected_calibration_error(rows: pd.DataFrame, *, pred_col: str, y_col: str, bins: int = 20) -> float:
    tab = reliability_table(rows, pred_col=pred_col, y_col=y_col, bins=bins)
    return float(tab["weighted_abs_calibration_error"].sum())


@dataclass
class HierarchicalCalibratorRegistry:
    """Manages stratified calibrators with fallback hierarchy.

    Cell key format: ``n{leg_count}_{stat_mix}_{role_mix}`` or
    ``n{leg_count}_{relationship_type}`` etc.  Lookup tries increasingly
    general keys until a match is found, then falls back to global_calibrator.
    """
    cells: dict[str, JointProbabilityCalibrator] = field(default_factory=dict)
    global_calibrator: JointProbabilityCalibrator | None = None

    def predict(self, raw_p: float, ticket_features: dict) -> tuple[float, str]:
        """Return (calibrated_p, cell_key_used)."""
        n_legs = ticket_features.get("n_legs")
        relationship_type = ticket_features.get("relationship_type")
        stat_mix = ticket_features.get("stat_mix")
        role_mix = ticket_features.get("role_mix")

        # Build candidate keys from most-specific to least-specific.
        candidates: list[str] = []
        if n_legs and relationship_type and stat_mix:
            candidates.append(f"n{n_legs}_{relationship_type}_{stat_mix}")
        if n_legs and relationship_type and role_mix:
            candidates.append(f"n{n_legs}_{relationship_type}_{role_mix}")
        if n_legs and relationship_type:
            candidates.append(f"n{n_legs}_{relationship_type}")
        if n_legs and stat_mix:
            candidates.append(f"n{n_legs}_{stat_mix}")
        if n_legs and role_mix:
            candidates.append(f"n{n_legs}_{role_mix}")
        if n_legs:
            candidates.append(f"n{n_legs}")
        if relationship_type:
            candidates.append(str(relationship_type))
        if stat_mix:
            candidates.append(str(stat_mix))

        x = np.array([float(raw_p)])
        for key in candidates:
            if key in self.cells:
                p = float(self.cells[key].predict(x)[0])
                return p, key

        if self.global_calibrator is not None:
            p = float(self.global_calibrator.predict(x)[0])
            return p, "global"

        return float(np.clip(raw_p, 1e-9, 1.0 - 1e-9)), "passthrough"

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> "HierarchicalCalibratorRegistry":
        obj = joblib.load(path)
        if not isinstance(obj, HierarchicalCalibratorRegistry):
            raise TypeError(f"Expected HierarchicalCalibratorRegistry, got {type(obj)}")
        return obj

    @property
    def cell_count(self) -> int:
        return len(self.cells)


def _fit_single_calibrator(
    df: pd.DataFrame,
    pred_col: str,
    y_col: str,
    cell_key: str,
    shrinkage_k: float = 400.0,
) -> JointProbabilityCalibrator:
    """Fit an isotonic calibrator on df, applying Bayesian shrinkage toward the mean."""
    x = df[pred_col].clip(1e-6, 1 - 1e-6).to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    n = len(x)
    global_mean = float(y.mean())
    shrink_w = shrinkage_k / (n + shrinkage_k)
    # Mix actual labels toward global mean to prevent overfitting small cells.
    y_shrunk = (1.0 - shrink_w) * y + shrink_w * global_mean
    model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    model.fit(x, y_shrunk)
    return JointProbabilityCalibrator(
        calibrator_id=f"{cell_key}_isotonic_n{n}",
        model=model,
        n_train=n,
        cell=cell_key,
    )


def fit_stratified_calibrators(
    backtest_rows: pd.DataFrame,
    *,
    pred_col: str = "raw_joint_probability",
    y_col: str = "hit_result",
    min_n_exact: int = 500,
    min_n_parent: int = 300,
    min_n_global: int = 200,
    shrinkage_k: float = 400.0,
) -> HierarchicalCalibratorRegistry:
    """Fit calibrators for each stratum with sufficient backtest data.

    Stratification hierarchy (most-specific first):
      - ``n{n_legs}_{relationship_type}`` (exact)
      - ``n{n_legs}_{stat_mix}``          (parent)
      - ``n{n_legs}``                      (parent)
      - ``{relationship_type}``             (parent)
      - global                              (fallback)

    Cells with fewer than ``min_n_exact`` rows are skipped at exact level but
    may still be fitted at parent level if parent has >= ``min_n_parent`` rows.
    """
    df = backtest_rows[[pred_col, y_col]].copy().dropna()
    df[pred_col] = df[pred_col].clip(1e-6, 1 - 1e-6).astype(float)
    df[y_col] = df[y_col].astype(int)

    cells: dict[str, JointProbabilityCalibrator] = {}

    def _maybe_add_strat(key_col: str, min_n: int) -> None:
        if key_col not in backtest_rows.columns:
            return
        strat_df = backtest_rows[[key_col, pred_col, y_col]].dropna()
        for key_val, grp in strat_df.groupby(key_col):
            if len(grp) < min_n:
                continue
            cell_key = str(key_val)
            if cell_key not in cells:
                cells[cell_key] = _fit_single_calibrator(
                    grp[[pred_col, y_col]], pred_col, y_col, cell_key, shrinkage_k
                )

    # Exact stratum: n_legs × relationship_type.
    if "n_legs" in backtest_rows.columns and "relationship_type" in backtest_rows.columns:
        combo_df = backtest_rows[["n_legs", "relationship_type", pred_col, y_col]].dropna()
        for (n_legs, rel_type), grp in combo_df.groupby(["n_legs", "relationship_type"]):
            if len(grp) < min_n_exact:
                continue
            key = f"n{int(n_legs)}_{rel_type}"
            if key not in cells:
                cells[key] = _fit_single_calibrator(
                    grp[[pred_col, y_col]], pred_col, y_col, key, shrinkage_k
                )

    # Parent strata.
    _maybe_add_strat("stat_mix", min_n_parent)
    _maybe_add_strat("relationship_type", min_n_parent)

    if "n_legs" in backtest_rows.columns:
        n_legs_df = backtest_rows[["n_legs", pred_col, y_col]].dropna()
        for n_legs, grp in n_legs_df.groupby("n_legs"):
            if len(grp) < min_n_parent:
                continue
            key = f"n{int(n_legs)}"
            if key not in cells:
                cells[key] = _fit_single_calibrator(
                    grp[[pred_col, y_col]], pred_col, y_col, key, shrinkage_k
                )

    # Global fallback.
    global_cal: JointProbabilityCalibrator | None = None
    if len(df) >= min_n_global:
        global_cal = _fit_single_calibrator(df, pred_col, y_col, "global", shrinkage_k)
        global_cal = JointProbabilityCalibrator(
            calibrator_id=f"global_isotonic_n{len(df)}",
            model=global_cal.model,
            n_train=len(df),
            cell="global",
        )

    return HierarchicalCalibratorRegistry(cells=cells, global_calibrator=global_cal)
