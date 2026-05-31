"""Tests for SGP joint probability calibration — hierarchical calibrators, metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

try:
    from sgp_engine.calibration import (
        JointProbabilityCalibrator,
        expected_calibration_error,
        fit_global_joint_calibrator,
        reliability_table,
    )
except ImportError as exc:
    pytest.skip(f"sgp_engine.calibration not available: {exc}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rows(n: int = 500, seed: int = 0) -> pd.DataFrame:
    """Generate synthetic backtest rows where hit_result ≈ raw_joint_probability."""
    rng = np.random.default_rng(seed)
    pred = rng.uniform(0, 1, n)
    hit = (rng.uniform(0, 1, n) < pred).astype(int)
    return pd.DataFrame({"raw_joint_probability": pred, "hit_result": hit})


def _make_biased_rows(n: int = 1_000, pred_val: float = 0.9, actual_rate: float = 0.3) -> pd.DataFrame:
    """Rows where all predictions = pred_val but actual rate = actual_rate."""
    rng = np.random.default_rng(99)
    hit = (rng.uniform(0, 1, n) < actual_rate).astype(int)
    return pd.DataFrame({
        "raw_joint_probability": np.full(n, pred_val),
        "calibrated_joint_probability": np.full(n, pred_val),
        "hit_result": hit,
    })


def _make_perfect_rows(n: int = 2_000) -> pd.DataFrame:
    """Rows where predictions are calibrated: actual frequency matches predicted probability."""
    rng = np.random.default_rng(7)
    pred = rng.uniform(0, 1, n)
    # Bin predictions and set actual rates to match bin means exactly
    bins = np.linspace(0, 1, 21)
    bucket = np.digitize(pred, bins) - 1
    bucket = np.clip(bucket, 0, 19)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    exact_probs = bin_centers[bucket]
    hit = (rng.uniform(0, 1, n) < exact_probs).astype(int)
    return pd.DataFrame({
        "calibrated_joint_probability": pred,
        "hit_result": hit,
    })


# ---------------------------------------------------------------------------
# 1 · Isotonic regression produces monotone non-decreasing predictions
# ---------------------------------------------------------------------------

def test_global_isotonic_fits_monotone():
    """After fitting, calibrator predictions are monotone non-decreasing."""
    df = _make_rows(n=500, seed=0)
    cal = fit_global_joint_calibrator(df, min_n=300)

    test_x = np.linspace(0.01, 0.99, 200)
    preds = cal.predict(test_x)
    for i in range(len(preds) - 1):
        assert preds[i] <= preds[i + 1] + 1e-9, (
            f"Non-monotone at index {i}: preds[{i}]={preds[i]:.4f} > preds[{i+1}]={preds[i+1]:.4f}"
        )


# ---------------------------------------------------------------------------
# 2 · ECE ≈ 0 for perfectly calibrated data
# ---------------------------------------------------------------------------

def test_ece_zero_for_perfect_calibration():
    """ECE should be near 0 for data where predictions match empirical frequencies."""
    df = _make_perfect_rows(n=5_000)
    ece = expected_calibration_error(
        df, pred_col="calibrated_joint_probability", y_col="hit_result", bins=10
    )
    assert ece < 0.05, f"ECE={ece:.4f} is too large for (approximately) perfectly calibrated data"


# ---------------------------------------------------------------------------
# 3 · ECE > 0 for biased predictions
# ---------------------------------------------------------------------------

def test_ece_positive_for_biased_predictions():
    """All predictions = 0.9 but actual rate = 0.3 → ECE should be substantial."""
    df = _make_biased_rows(pred_val=0.9, actual_rate=0.3)
    ece = expected_calibration_error(
        df, pred_col="calibrated_joint_probability", y_col="hit_result", bins=10
    )
    # |0.9 - 0.3| = 0.6 → ECE should be around 0.6
    assert ece > 0.4, f"ECE={ece:.4f} — expected > 0.4 for severely biased predictions"


# ---------------------------------------------------------------------------
# 4 · Hierarchical registry falls back to global for small cells
# ---------------------------------------------------------------------------

def test_hierarchical_registry_falls_back_to_global():
    """A cell with n < 500 rows should use the global calibrator as fallback."""
    from sgp_engine.calibration import HierarchicalCalibratorRegistry  # type: ignore[attr-defined]

    global_df = _make_rows(n=1_000, seed=0)
    global_cal = fit_global_joint_calibrator(global_df, min_n=300)

    registry = HierarchicalCalibratorRegistry(global_calibrator=global_cal)

    # Register a cell calibrator only when n >= 500
    small_df = _make_rows(n=200, seed=1)  # too few rows for its own calibrator
    registry.maybe_register("pts", "core", small_df)

    # Querying an under-threshold cell should return the global calibrator
    cal = registry.get("pts", "core")
    assert cal.cell == "global", f"Expected 'global' fallback, got {cal.cell!r}"


# ---------------------------------------------------------------------------
# 5 · fit_stratified creates separate calibrators for cells with enough data
# ---------------------------------------------------------------------------

def test_fit_stratified_creates_multiple_cells():
    """fit_stratified should produce one calibrator per (stat, role) cell."""
    from sgp_engine.calibration import fit_stratified_joint_calibrators  # type: ignore[attr-defined]

    rng = np.random.default_rng(42)
    n_pts_core = 800
    n_reb_bench = 600

    df_pts = _make_rows(n=n_pts_core, seed=10)
    df_pts["stat"] = "pts"
    df_pts["role_bucket"] = "core"

    df_reb = _make_rows(n=n_reb_bench, seed=20)
    df_reb["stat"] = "reb"
    df_reb["role_bucket"] = "bench"

    combined = pd.concat([df_pts, df_reb], ignore_index=True)
    registry = fit_stratified_joint_calibrators(combined, min_n_per_cell=500)

    assert registry.has_cell("pts", "core"), "Expected a 'pts/core' calibrator"
    assert registry.has_cell("reb", "bench"), "Expected a 'reb/bench' calibrator"


# ---------------------------------------------------------------------------
# 6 · reliability_table has the expected number of bins
# ---------------------------------------------------------------------------

def test_reliability_table_shape():
    """reliability_table returns exactly `bins` rows with the required columns."""
    df = _make_rows(n=2_000, seed=0)
    df["calibrated_joint_probability"] = df["raw_joint_probability"]

    for bins in [5, 10, 20]:
        tab = reliability_table(
            df,
            pred_col="calibrated_joint_probability",
            y_col="hit_result",
            bins=bins,
        )
        assert len(tab) == bins, f"Expected {bins} rows, got {len(tab)}"
        for col in ["n", "mean_pred", "actual_rate", "abs_calibration_error", "weighted_abs_calibration_error"]:
            assert col in tab.columns, f"Missing column '{col}' in reliability_table output"


# ---------------------------------------------------------------------------
# Extra: calibrator predict clamps to (1e-9, 1-1e-9)
# ---------------------------------------------------------------------------

def test_calibrator_predict_clamps_to_valid_range():
    df = _make_rows(n=500, seed=0)
    cal = fit_global_joint_calibrator(df, min_n=300)
    edge_inputs = np.array([0.0, 1.0, -0.5, 1.5, 0.5])
    preds = cal.predict(edge_inputs)
    for p in preds:
        assert 1e-9 <= p <= 1 - 1e-9, f"Prediction {p} outside clamped range"
