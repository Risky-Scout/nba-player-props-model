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


# ── Derek game-snapshot ``prop_summary`` market-line contract ───────


def test_derek_snapshot_prop_summary_populates_market_line_when_market_available(
    tmp_path: Path,
):
    """``prop_summary.csv`` must populate ``line`` / ``market_line`` /
    ``book`` / ``p_over`` for every (player, stat) where the market
    consensus is available — never leave market fields blank under a
    ``market_coverage_status='full'`` tag.

    Regression for the 2026-05-17 snapshot writer bug where the
    persisted ``prop_summary.csv`` carried ``market_coverage_status=
    full`` with blank ``line``/``market_line``/``book``/``p_over``
    because the writer copied wide PMF rows directly without joining
    the consensus market line from ``market_comparison``.
    """
    mod = _load_module(
        "scripts/build_derek_game_snapshots_from_delivery.py",
        "_derek_snap_prop_summary",
    )

    pmf_obj = {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}
    df_wide = pd.DataFrame({
        "player_id": [1, 2],
        "player_name": ["Player One", "Player Two"],
        "team": ["AAA", "BBB"],
        "opponent": ["BBB", "AAA"],
        "is_home": [True, False],
        "game_id": [10, 10],
        "stat": ["pts", "pts"],
        "role_bucket": ["starter", "rotation"],
        "pmf_json": [json.dumps(pmf_obj), json.dumps(pmf_obj)],
        # Wide source has no real market data — mirror production.
        "line": [None, None],
        "market_line": [None, None],
        "book": [None, None],
        "market_over_odds": [None, None],
        "market_under_odds": [None, None],
        "market_no_vig_over_prob": [None, None],
        "market_coverage_status": ["full", "full"],
    })

    # Two books quote the same main line for Player One; Player Two has
    # no market_comparison rows at all (no_market_line case).
    df_market = pd.DataFrame({
        "player_id": [1, 1],
        "player_name": ["Player One", "Player One"],
        "game_id": [10, 10],
        "stat": ["pts", "pts"],
        "book": ["draftkings", "fanduel"],
        "line": [1.5, 1.5],
        "market_line": [1.5, 1.5],
        "market_over_odds": [-110.0, -105.0],
        "market_under_odds": [-110.0, -115.0],
        "market_no_vig_over_prob": [0.5, 0.49],
    })

    out_dir = tmp_path / "derek_game_snapshots" / "g_10"
    mod._write_outputs(out_dir, df_wide, df_market)
    ps = pd.read_csv(out_dir / "prop_summary.csv")

    row1 = ps[ps["player_name"] == "Player One"].iloc[0]
    row2 = ps[ps["player_name"] == "Player Two"].iloc[0]

    # Player One has consensus market data → all market fields populated.
    assert float(row1["market_line"]) == 1.5
    assert float(row1["line"]) == 1.5
    assert isinstance(row1["book"], str) and row1["book"] in {"draftkings", "fanduel"}
    assert math.isfinite(float(row1["market_over_odds"]))
    assert math.isfinite(float(row1["market_under_odds"]))
    assert math.isfinite(float(row1["market_no_vig_over_prob"]))
    # ``p_over`` is direct PMF P(stat > 1.5) = p2 + p3 = 0.7
    assert abs(float(row1["p_over"]) - 0.7) < 1e-9
    assert abs(float(row1["pmf_mean"]) - 2.0) < 1e-9
    # ``market_coverage_status`` remains ``full`` for fully-covered row.
    assert str(row1["market_coverage_status"]) == "full"

    # Player Two has no market data → market fields blank AND coverage
    # status honestly downgraded to ``no_market_line`` (never silently
    # claims ``full`` with blank fields).
    assert pd.isna(row2["market_line"])
    assert pd.isna(row2["line"])
    assert pd.isna(row2["book"]) or row2["book"] == "" or pd.isna(row2["book"])
    assert pd.isna(row2["p_over"])
    # ``pmf_mean`` is still emitted (PMF-native column is unconditional).
    assert abs(float(row2["pmf_mean"]) - 2.0) < 1e-9
    assert str(row2["market_coverage_status"]) == "no_market_line"

    # No row tagged ``full`` may carry blank market_line OR blank p_over.
    full = ps[ps["market_coverage_status"] == "full"]
    assert int(full["market_line"].isna().sum()) == 0
    assert int(full["p_over"].isna().sum()) == 0


def test_derek_snapshot_market_comparison_populates_p_over_when_market_line_present(
    tmp_path: Path,
):
    """``market_comparison.csv`` must populate ``p_over`` on every row
    that carries a non-null ``market_line``.

    Regression for the 2026-05-17 snapshot where 2260/2260 persisted
    rows had ``market_line`` non-null AND ``p_over`` null (the wide
    PMF distribution had to be joined onto market_comparison to
    compute the direct tail probability).
    """
    mod = _load_module(
        "scripts/build_derek_game_snapshots_from_delivery.py",
        "_derek_snap_market_comparison",
    )

    pmf_obj = {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}
    df_wide = pd.DataFrame({
        "player_id": [1],
        "player_name": ["Player One"],
        "team": ["AAA"],
        "opponent": ["BBB"],
        "is_home": [True],
        "game_id": [10],
        "stat": ["pts"],
        "role_bucket": ["starter"],
        "pmf_json": [json.dumps(pmf_obj)],
    })
    df_market = pd.DataFrame({
        "player_id": [1, 1, 1],
        "player_name": ["Player One"] * 3,
        "game_id": [10, 10, 10],
        "stat": ["pts", "pts", "pts"],
        "book": ["draftkings", "fanduel", "betmgm"],
        "line": [1.5, 2.5, 0.5],
        "market_line": [1.5, 2.5, 0.5],
        "market_over_odds": [-110.0, 100.0, -300.0],
        "market_under_odds": [-110.0, -120.0, 250.0],
        "market_no_vig_over_prob": [0.5, 0.45, 0.85],
    })

    out_dir = tmp_path / "derek_game_snapshots" / "g_10"
    mod._write_outputs(out_dir, df_wide, df_market)
    mc = pd.read_csv(out_dir / "market_comparison.csv")

    # Every row with market_line non-null must have p_over non-null.
    with_ml = mc[mc["market_line"].notna()]
    assert len(with_ml) == 3
    assert int(with_ml["p_over"].isna().sum()) == 0

    # Direct PMF tail probability check for each alternate line.
    by_line = {float(r["market_line"]): float(r["p_over"]) for _, r in mc.iterrows()}
    # P(X > 1.5) = 0.3 + 0.4 = 0.7
    assert abs(by_line[1.5] - 0.7) < 1e-9
    # P(X > 2.5) = 0.4
    assert abs(by_line[2.5] - 0.4) < 1e-9
    # P(X > 0.5) = 0.2 + 0.3 + 0.4 = 0.9
    assert abs(by_line[0.5] - 0.9) < 1e-9


# ── WoO ``affiliate_dashboard.json`` model-prob exposure contract ───


def test_affiliate_dashboard_exposes_pmf_mean_and_p_over_aliases(tmp_path: Path):
    """The WoO affiliate dashboard JSON payload must expose ``pmf_mean``
    and ``p_over`` aliases alongside the legacy ``model_prob`` /
    ``model_prob_over`` fields so the public props feed (and the
    nba-props.html template that reads it) can render model probability
    under a stable PMF-native name. Market probability and book / line
    fields must remain populated; alternate lines must not be dropped.
    """
    import os
    import shutil
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        woo = Path("deliveries") / "2026-05-17" / "wizard_of_odds"
        woo.mkdir(parents=True)

        # Two alternate lines × one book — verifies alternates survive.
        df_market = pd.DataFrame({
            "player_id": [1, 1],
            "player_name": ["Player One", "Player One"],
            "team": ["AAA", "AAA"],
            "opponent": ["BBB", "BBB"],
            "game_id": [10, 10],
            "stat": ["pts", "pts"],
            "book": ["draftkings", "draftkings"],
            "line": [1.5, 2.5],
            "market_line": [1.5, 2.5],
            "market_over_odds": [-110.0, 100.0],
            "market_under_odds": [-110.0, -120.0],
            "fair_over_odds_american": [-100.0, 110.0],
            "fair_under_odds_american": [-100.0, -130.0],
            "market_no_vig_over_prob": [0.5, 0.45],
            "model_prob_over": [0.7, 0.4],
            # PMF-native fields the M8.6 repair pass must alias forward.
            "pmf_mean": [2.0, 2.0],
            "p_over": [0.7, 0.4],
            "edge": [0.2, -0.05],
            "calibration_support_status": ["supported", "supported"],
            "accuracy_support_status": ["supported", "supported"],
            "edge_publish_status": ["publishable", "publishable"],
            "promotion_status": ["no_market_superiority_claim"] * 2,
            "market_superiority_claim_allowed": [False, False],
        })
        df_market.to_parquet(woo / "market_comparison.parquet")

        mod = _load_module(
            "scripts/publish_woo_public_export.py",
            "_woo_publish_aff_dash",
        )
        mod._m86_repair_woo_monetization_contract_after_publish("2026-05-17")

        aff_path = Path("public_export") / "wizard_of_odds" / "2026-05-17" / "affiliate_dashboard.json"
        aff = json.loads(aff_path.read_text())
        rows = aff["rows"]

        # OVER + UNDER for each of 2 lines = 4 rows; alternates preserved.
        assert len(rows) == 4, f"expected 4 rows (alternates preserved), got {len(rows)}"

        for r in rows:
            # PMF-native aliases populated.
            assert r.get("pmf_mean") is not None, f"pmf_mean missing: {r}"
            assert r.get("p_over") is not None, f"p_over missing: {r}"
            assert r.get("market_line") is not None, f"market_line missing: {r}"
            # Legacy model-prob fields preserved (kept for backward compat).
            assert r.get("model_prob") is not None
            assert r.get("model_prob_over") is not None
            # Market probability + book + line preserved.
            assert r.get("market_prob") is not None
            assert r.get("book")
            assert r.get("line") is not None
            assert r.get("side_odds") is not None

        # Strictly-quarantined names must not leak into the public payload.
        strict_quarantine = (
            "model_projected_mean",
            "model_probability_over_market_line",
            "model_prob_over_raw",
            "model_prob_over_active",
            "model_p_over",
        )
        for r in rows:
            for q in strict_quarantine:
                assert q not in r, f"quarantined key {q!r} leaked into affiliate row"
    finally:
        os.chdir(cwd)


def test_woo_market_comparison_and_publishable_edges_carry_pmf_native_columns():
    """``market_comparison.parquet`` and ``publishable_edges.parquet``
    are the canonical WoO public delivery surfaces. Both MUST carry
    ``pmf_mean``, ``p_over``, market probability, ``line`` and
    ``book`` on every persisted row. This is enforced by the
    delivery contract spec so the verifier rejects schema drift
    before the daily delivery pipeline can stage / commit a malformed
    artifact.
    """
    import sys
    src = REPO / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from nba_props_model.delivery.delivery_contract import (
        _WOO_EDGE_CORE,
        delivery_file_specs,
    )

    # The market_comparison / publishable_edges files use _WOO_EDGE_CORE.
    required = {
        "pmf_mean",
        "p_over",
        "market_line",
        "line",
        "book",
        "market_no_vig_over_prob",  # market probability
    }
    missing = required - set(_WOO_EDGE_CORE)
    assert not missing, (
        f"_WOO_EDGE_CORE is missing PMF-native + market fields: "
        f"{sorted(missing)}. _WOO_EDGE_CORE={_WOO_EDGE_CORE}"
    )

    # The file specs for ``market_comparison`` and ``publishable_edges``
    # must reference the edge contract (so the daily delivery verifier
    # actually enforces these columns on the persisted files).
    target_files = {
        "wizard_of_odds/market_comparison.parquet",
        "wizard_of_odds/market_comparison.csv",
        "wizard_of_odds/publishable_edges.parquet",
        "wizard_of_odds/publishable_edges.csv",
    }
    specs_by_path = {s.relative_path: s for s in delivery_file_specs()}
    for rel in target_files:
        spec = specs_by_path.get(rel)
        assert spec is not None, f"missing delivery spec for {rel}"
        cols = set(spec.required_columns or ())
        for col in required:
            assert col in cols, (
                f"delivery spec for {rel} does not require {col!r}; "
                f"required_columns={sorted(cols)}"
            )

    # Quarantined names must NEVER be required by the WoO row contract.
    for c in QUARANTINED:
        assert c not in _WOO_EDGE_CORE, (
            f"WoO edge core contract still requires quarantined column "
            f"{c!r}"
        )
