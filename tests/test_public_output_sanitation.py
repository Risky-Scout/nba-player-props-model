"""Public delivery output sanitation contract tests.

These tests assert the writer/output-schema rules for the
"WRITER/OUTPUT SCHEMA ONLY" production fix:

  • Quarantined columns must NEVER appear in any persisted public
    delivery output.
  • ``pmf_mean`` and ``p_over`` must be present where valid.
  • ``p_over`` must be the direct PMF tail probability
    ``P(stat > line)`` — never a rename of ``model_p_over`` /
    ``model_prob_over_*``.
  • ``p_over`` must NOT be invented when no row-level line exists.

Each test exercises a specific writer's sanitization helper /
column-projection rule using small in-memory DataFrames so the
contract is enforced without spinning up a full pipeline.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


QUARANTINED = (
    "model_projected_mean",
    "model_probability_over_market_line",
    "model_prob_over_raw",
    "model_prob_over_active",
    "model_p_over",
)


def _load_module(rel_path: str, attr_name: str):
    spec = importlib.util.spec_from_file_location(
        attr_name, REPO / rel_path,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── PMF math (used by ALL public writers) ───────────────────────────


def test_pmf_direct_mean_equals_expectation():
    mod = _load_module(
        "scripts/build_derek_forward_feed.py", "_derek_pmf_math",
    )
    pmf = {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}
    arr = mod._pmf_array_from_jsonish(pmf)
    # E[X] = 0*0.1 + 1*0.2 + 2*0.3 + 3*0.4 = 2.0
    assert abs(mod._pmf_direct_mean(arr) - 2.0) < 1e-12


def test_pmf_direct_p_over_equals_tail_probability():
    mod = _load_module(
        "scripts/build_derek_forward_feed.py", "_derek_pmf_math",
    )
    pmf = {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}
    arr = mod._pmf_array_from_jsonish(pmf)
    # P(X > 1.5) = P(X=2) + P(X=3) = 0.7
    assert abs(mod._pmf_direct_p_over(arr, 1.5) - 0.7) < 1e-12
    # P(X > 2.5) = P(X=3) = 0.4
    assert abs(mod._pmf_direct_p_over(arr, 2.5) - 0.4) < 1e-12
    # P(X > 3.5) = 0.0
    assert abs(mod._pmf_direct_p_over(arr, 3.5) - 0.0) < 1e-12


def test_pmf_direct_p_over_not_a_rename_of_model_p_over():
    """The conditional ``_model_p_over_line`` and the direct
    ``_pmf_direct_p_over`` are NOT equal on PMFs with positive mass
    at the line."""
    mod_dpd = _load_module(
        "scripts/build_daily_pmf_delivery.py", "_daily_pmf_math",
    )
    # Half mass on 2, half mass on 1: P(X > 1) = 0.5, but
    # conditional p_over_active = 0.5 only because at-line is 0.
    # Use a half-line so they coincide, then a whole-line to diverge.
    import numpy as np
    pmf = np.array([0.0, 0.2, 0.6, 0.2])
    # At line=2.0 (whole), at-line mass = 0.6, p_over = 0.2,
    # p_under = 0.2. Conditional = 0.2 / (0.2 + 0.2) = 0.5.
    # Direct = 0.2.
    direct = mod_dpd._pmf_direct_p_over(pmf, 2.0)
    conditional = mod_dpd._model_p_over_line(pmf, 2.0)
    assert direct is not None and conditional is not None
    assert abs(direct - 0.2) < 1e-12
    assert abs(conditional - 0.5) < 1e-12
    assert abs(direct - conditional) > 0.1


# ── Derek forward feed quarantine sanitation ────────────────────────


def test_derek_forward_feed_drop_quarantined_columns():
    mod = _load_module(
        "scripts/build_derek_forward_feed.py", "_derek_quarantine",
    )
    df = pd.DataFrame({
        "player_name": ["A"],
        "stat": ["pts"],
        "pmf_mean": [10.0],
        "p_over": [0.55],
        "model_p_over": [0.6],
        "model_projected_mean": [10.1],
        "model_prob_over_raw": [0.6],
        "model_prob_over_active": [0.6],
        "model_probability_over_market_line": [0.6],
    })
    out = mod._drop_quarantined_columns(df)
    for c in QUARANTINED:
        assert c not in out.columns
    assert "pmf_mean" in out.columns
    assert "p_over" in out.columns


def test_derek_forward_feed_quarantine_constant_matches_spec():
    mod = _load_module(
        "scripts/build_derek_forward_feed.py", "_derek_quarantine_spec",
    )
    assert set(mod.QUARANTINED_PUBLIC_COLUMNS) == set(QUARANTINED)


# ── Daily PMF delivery (WoO writer) quarantine sanitation ───────────


def test_daily_pmf_delivery_sanitize_drops_quarantined():
    mod = _load_module(
        "scripts/build_daily_pmf_delivery.py", "_daily_pmf_sanitize",
    )
    df = pd.DataFrame({
        "player_name": ["A"],
        "stat": ["pts"],
        "line": [10.5],
        "market_line": [10.5],
        "mean": [10.2],
        "pmf_mean": [10.2],
        "p_over": [0.41],
        "model_p_over": [0.6],
        "model_prob_over_raw": [0.6],
    })
    out = mod._sanitize_public_columns(df)
    for c in QUARANTINED:
        assert c not in out.columns
    assert "pmf_mean" in out.columns
    assert "p_over" in out.columns
    assert "market_line" in out.columns


# ── Derek game-snapshots writer quarantine sanitation ───────────────


def test_derek_game_snapshots_writer_strips_quarantine_and_stamps_pmf_native(
    tmp_path: Path,
):
    mod = _load_module(
        "scripts/build_derek_game_snapshots_from_delivery.py",
        "_derek_game_snaps",
    )
    pmf_obj = {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}
    df_wide = pd.DataFrame({
        "player_id": [1, 2],
        "player_name": ["A", "B"],
        "team": ["X", "Y"],
        "opponent": ["Y", "X"],
        "is_home": [True, False],
        "game_id": [10, 10],
        "stat": ["pts", "pts"],
        "line": [1.5, 2.5],
        "role_bucket": ["starter", "rotation"],
        "pmf_json": [json.dumps(pmf_obj), json.dumps(pmf_obj)],
        # Quarantined input columns — must be stripped.
        "model_p_over": [0.7, 0.4],
        "model_prob_over_active": [0.7, 0.4],
    })
    df_market = df_wide.copy()
    out_dir = tmp_path / "derek_game_snapshots" / "g_10"
    mod._write_outputs(out_dir, df_wide, df_market)

    # Quarantined columns must not appear in any persisted artifact.
    for name in ("prop_summary.csv", "full_pmf_wide.csv", "market_comparison.csv"):
        cols = list(pd.read_csv(out_dir / name).columns)
        for c in QUARANTINED:
            assert c not in cols, f"{c} leaked into {name}"

    # ``pmf_mean`` and ``p_over`` must be present + direct from PMF.
    wide = pd.read_csv(out_dir / "full_pmf_wide.csv")
    assert "pmf_mean" in wide.columns
    assert "p_over" in wide.columns
    # E[X] of pmf above = 2.0; P(X > 1.5) = 0.7; P(X > 2.5) = 0.4.
    assert abs(float(wide.iloc[0]["pmf_mean"]) - 2.0) < 1e-9
    assert abs(float(wide.iloc[0]["p_over"]) - 0.7) < 1e-9
    assert abs(float(wide.iloc[1]["p_over"]) - 0.4) < 1e-9


# ── WoO affiliate dashboard writer quarantine sanitation ────────────


def test_publish_woo_strip_quarantined_keys_helper():
    mod = _load_module(
        "scripts/publish_woo_public_export.py", "_woo_publish",
    )
    rec = {
        "player_id": 1,
        "model_p_over": 0.6,
        "model_prob_over_active": 0.6,
        "pmf_mean": 10.0,
        "p_over": 0.55,
    }
    out = mod._strip_quarantined_keys(rec)
    for c in QUARANTINED:
        assert c not in out
    assert out["pmf_mean"] == 10.0
    assert out["p_over"] == 0.55


def test_publish_woo_pmf_helpers_match_direct_definitions():
    mod = _load_module(
        "scripts/publish_woo_public_export.py", "_woo_publish_math",
    )
    arr = mod._pmf_array_from_pmf_obj({"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4})
    assert arr is not None
    assert abs(mod._pmf_direct_mean(arr) - 2.0) < 1e-12
    assert abs(mod._pmf_direct_p_over(arr, 1.5) - 0.7) < 1e-12
    # No line → no p_over.
    assert mod._pmf_direct_p_over(arr, None) is None
    # Non-numeric line → no p_over.
    assert mod._pmf_direct_p_over(arr, "not-a-line") is None
    # NaN line → no p_over.
    assert mod._pmf_direct_p_over(arr, float("nan")) is None


def test_publish_woo_no_invented_p_over_without_line():
    """Affiliate-dashboard helper must NOT invent ``p_over`` when no
    parseable line is present on the row."""
    mod = _load_module(
        "scripts/publish_woo_public_export.py",
        "_woo_publish_no_invented",
    )
    arr = mod._pmf_array_from_pmf_obj({"0": 0.5, "1": 0.5})
    assert arr is not None
    assert mod._pmf_direct_p_over(arr, None) is None


# ── Outcome-level / distribution-only rows: no fabricated p_over ────


def test_distribution_only_row_must_not_invent_p_over():
    """PMF distribution / outcome-level files have no row-level line.

    The contract says: ``If a PMF/outcome-level file has no row-level
    market line, do not invent p_over.`` This test asserts that the
    Derek game-snapshots stamp helper leaves ``p_over`` as ``None``
    when no ``line`` / ``market_line`` is present.
    """
    mod = _load_module(
        "scripts/build_derek_game_snapshots_from_delivery.py",
        "_derek_game_snaps_no_line",
    )
    df = pd.DataFrame({
        "player_id": [1],
        "stat": ["pts"],
        "pmf_json": [json.dumps({"0": 0.1, "1": 0.2, "2": 0.7})],
        # No ``line`` / ``market_line`` columns at all.
    })
    out = mod._stamp_pmf_native_public_columns(df)
    assert "p_over" in out.columns
    # No line → None, never a fabricated tail value.
    assert pd.isna(out.iloc[0]["p_over"]) or out.iloc[0]["p_over"] is None
    # ``pmf_mean`` should still be set (distribution columns intact).
    assert math.isfinite(float(out.iloc[0]["pmf_mean"]))


# ── Delivery contract spec sanitation ───────────────────────────────


def test_delivery_contract_derek_unified_required_columns_clean():
    """The Derek unified feed contract spec must NOT require any
    quarantined column."""
    import sys
    src = REPO / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from nba_props_model.delivery.delivery_contract import (
        DEREK_UNIFIED_REQUIRED_COLUMNS,
    )

    for c in QUARANTINED:
        assert c not in DEREK_UNIFIED_REQUIRED_COLUMNS, (
            f"DEREK_UNIFIED_REQUIRED_COLUMNS still requires "
            f"quarantined column {c!r}"
        )
    # Public-facing PMF-native fields MUST be required.
    assert "pmf_mean" in DEREK_UNIFIED_REQUIRED_COLUMNS
    assert "p_over" in DEREK_UNIFIED_REQUIRED_COLUMNS
    assert "market_line" in DEREK_UNIFIED_REQUIRED_COLUMNS
