"""Regression: ``affiliate_dashboard.json`` rows must always carry a
non-null ``model_prob``. Run 25952350180 emitted 424 null-``model_prob``
rows because the producer wrote ``model_probability_for_side`` but never
populated the flat ``model_prob`` key the verifier reads."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "publish_woo_public_export",
    REPO / "scripts" / "publish_woo_public_export.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_derive_model_prob_passes_through_direct_value():
    assert mod.derive_model_prob_for_row({"model_prob": 0.55}) == pytest.approx(0.55)


def test_derive_model_prob_over_uses_over_aliases():
    row = {"side": "OVER", "model_p_over": 0.62}
    assert mod.derive_model_prob_for_row(row) == pytest.approx(0.62)


def test_derive_model_prob_under_uses_under_aliases():
    row = {"side": "UNDER", "prob_under": 0.41}
    assert mod.derive_model_prob_for_row(row) == pytest.approx(0.41)


def test_derive_model_prob_under_falls_back_to_over_complement():
    """When only ``model_prob_over`` is present, an UNDER row gets the
    1 - p_over complement instead of being dropped."""
    row = {"side": "UNDER", "model_prob_over": 0.7}
    assert mod.derive_model_prob_for_row(row) == pytest.approx(0.3)


def test_derive_model_prob_side_agnostic_fallback():
    row = {"side": "OVER", "model_probability": 0.42}
    assert mod.derive_model_prob_for_row(row) == pytest.approx(0.42)


def test_derive_model_prob_rejects_out_of_unit_interval():
    assert mod.derive_model_prob_for_row({"model_prob": 1.5}) is None
    assert mod.derive_model_prob_for_row({"model_prob": -0.1}) is None
    assert mod.derive_model_prob_for_row({"model_prob": 0.0}) is None
    assert mod.derive_model_prob_for_row({"model_prob": 1.0}) is None


def test_derive_model_prob_returns_none_when_no_source_present():
    assert mod.derive_model_prob_for_row({"side": "OVER"}) is None
    assert mod.derive_model_prob_for_row({"player_id": 1}) is None


def test_derive_model_prob_ignores_garbage_strings():
    row = {"side": "OVER", "model_p_over": "not_a_number"}
    assert mod.derive_model_prob_for_row(row) is None


# ── M8.6Q: market_prob propagation (run 25956006497 regression) ──────


def _build_one_row_market_comparison(tmp_path, extra_columns=None):
    import pandas as pd

    row = {
        "player_id": 1,
        "player_name": "Bob",
        "team": "TM",
        "opponent": "OPP",
        "stat": "pts",
        "line": 23.5,
        "book": "bovada",
        "model_prob_over": 0.55,
        "market_over_odds": -110,
        "market_under_odds": -110,
        "market_no_vig_over_prob": 0.52,
        "fair_over_odds_american": -120,
        "fair_under_odds_american": +100,
    }
    if extra_columns:
        row.update(extra_columns)
    df = pd.DataFrame([row])
    woo = tmp_path / "deliveries" / "2026-05-15" / "wizard_of_odds"
    woo.mkdir(parents=True)
    df.to_parquet(woo / "market_comparison.parquet", index=False)
    return df


def test_m86_repair_emits_market_prob_per_row(tmp_path, monkeypatch):
    """The exact regression from run 25956006497: the M8.6 repair pass
    rewrites ``affiliate_dashboard.json`` and must include ``market_prob``
    on every row (the legacy publisher did; the repair pass had been
    dropping it). Verifier:
    ``_check_affiliate`` requires player/stat/side/line/model_prob/market_prob.
    """
    import json

    _build_one_row_market_comparison(tmp_path)
    monkeypatch.chdir(tmp_path)
    mod._m86_repair_woo_monetization_contract_after_publish("2026-05-15")

    out = tmp_path / "public_export" / "wizard_of_odds" / "2026-05-15" / "affiliate_dashboard.json"
    payload = json.loads(out.read_text())
    rows = payload["rows"]
    assert len(rows) == 2  # OVER + UNDER
    for r in rows:
        for key in ("player", "stat", "side", "line", "model_prob", "market_prob"):
            assert key in r, f"row missing required key {key}: {sorted(r.keys())}"
        assert r["model_prob"] is not None
        # market_prob is non-null because the fixture provides no_vig.
        assert r["market_prob"] is not None
    over_row = next(r for r in rows if r["side"] == "OVER")
    under_row = next(r for r in rows if r["side"] == "UNDER")
    assert pytest.approx(over_row["market_prob"] + under_row["market_prob"], abs=1e-9) == 1.0


def test_m86_repair_market_prob_falls_back_to_odds(tmp_path, monkeypatch):
    """When ``market_no_vig_over_prob`` is missing, the repair pass
    derives ``market_prob`` from the American odds pair (no_vig
    by inversion). This is what keeps the public-export contract
    happy on legacy market_comparison rows that don't carry no_vig."""
    import json
    import pandas as pd

    row = {
        "player_id": 1,
        "player_name": "Bob",
        "team": "TM",
        "opponent": "OPP",
        "stat": "pts",
        "line": 23.5,
        "book": "bovada",
        "model_prob_over": 0.55,
        "market_over_odds": -110,
        "market_under_odds": -110,
    }
    df = pd.DataFrame([row])
    woo = tmp_path / "deliveries" / "2026-05-15" / "wizard_of_odds"
    woo.mkdir(parents=True)
    df.to_parquet(woo / "market_comparison.parquet", index=False)

    monkeypatch.chdir(tmp_path)
    mod._m86_repair_woo_monetization_contract_after_publish("2026-05-15")

    out = tmp_path / "public_export" / "wizard_of_odds" / "2026-05-15" / "affiliate_dashboard.json"
    payload = json.loads(out.read_text())
    rows = payload["rows"]
    for r in rows:
        assert "market_prob" in r
        assert r["market_prob"] is not None
        assert 0.0 < r["market_prob"] < 1.0


# ── M8_6_O: affiliate_dashboard count-key contract (run 26005809860 fix) ──
#
# Two writers stamp ``affiliate_dashboard.json`` in sequence:
#   1. ``publish_woo_public_export.py::_write_export``  (legacy, top-level ``count``)
#   2. ``publish_woo_public_export.py::_m86_repair_woo_monetization_contract_after_publish``
#      (M8.6 repair, OVERWRITES the file)
#
# The M8.6 repair pass had been emitting only ``total_rows`` and dropping
# the legacy ``count`` key. The downstream gate in
# ``scripts/verify_corrected_pmf_delivery.py`` reads ``aff.get("count")``
# and so misread 4342 rows as count=0, raising
# ``FATAL: <date> affiliate_dashboard count must be > 0`` and halting the
# workflow before ``Stage and commit`` could publish the corrected Derek
# unique props summary to ``main`` (run 26005809860).
#
# The two regression tests below pin the writer/verifier contract:
#   * writer: M8.6 repair output includes ``count`` matching ``len(rows)``
#     (alongside ``total_rows`` for backwards compatibility).
#   * verifier: ``_affiliate_row_count`` resolves a positive count from
#     any of the three historical payload shapes (``count`` /
#     ``total_rows`` / ``rows`` length) and never silently misreads a
#     populated dashboard as empty.


def test_m86_repair_emits_top_level_count_key_matching_rows_and_total_rows(tmp_path, monkeypatch):
    """Writer-side regression for run 26005809860.

    The M8.6 monetization-repair pass must emit ``count`` (legacy key
    consumed by ``verify_corrected_pmf_delivery.py``) alongside
    ``total_rows`` so the corrected-PMF delivery gate sees the same
    row count the file actually carries.
    """
    import json

    _build_one_row_market_comparison(tmp_path)
    monkeypatch.chdir(tmp_path)
    mod._m86_repair_woo_monetization_contract_after_publish("2026-05-15")

    out = tmp_path / "public_export" / "wizard_of_odds" / "2026-05-15" / "affiliate_dashboard.json"
    payload = json.loads(out.read_text())

    rows = payload["rows"]
    assert len(rows) > 0, "fixture must produce at least one affiliate row"
    assert "count" in payload, (
        "M8.6 repair must emit top-level 'count' (verify_corrected_pmf_delivery.py "
        "reads aff.get('count'); dropping it re-triggers run 26005809860 fatal)"
    )
    assert "total_rows" in payload
    assert payload["count"] == len(rows) == payload["total_rows"]
    assert payload["count"] > 0

    for mirror in (
        tmp_path / "public_export" / "wizard_of_odds" / "latest" / "affiliate_dashboard.json",
        tmp_path / "public_export" / "wizard_of_odds" / "affiliate_dashboard.json",
    ):
        mirror_payload = json.loads(mirror.read_text())
        assert mirror_payload.get("count") == len(rows) == mirror_payload.get("total_rows")


def test_verify_corrected_pmf_delivery_affiliate_row_count_helper():
    """Verifier-side regression for run 26005809860.

    ``_affiliate_row_count`` must resolve a positive row count from
    every historical ``affiliate_dashboard.json`` shape so writer-schema
    drift cannot silently re-break the gate.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "verify_corrected_pmf_delivery",
        REPO / "scripts" / "verify_corrected_pmf_delivery.py",
    )
    vmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vmod)

    legacy = {"rows": [{"x": 1}, {"x": 2}, {"x": 3}], "count": 3}
    assert vmod._affiliate_row_count(legacy) == 3

    m86 = {"rows": [{"x": i} for i in range(4342)], "items": [{"x": i} for i in range(4342)],
           "total_rows": 4342}
    assert vmod._affiliate_row_count(m86) == 4342, (
        "missing top-level 'count' must NOT cause the gate to read 0 — this is the "
        "exact run 26005809860 regression"
    )

    drifted = {"rows": [{"x": i} for i in range(7)]}
    assert vmod._affiliate_row_count(drifted) == 7

    items_only = {"items": [{"x": i} for i in range(5)]}
    assert vmod._affiliate_row_count(items_only) == 5

    empty_stub = {"rows": [], "count": 0}
    assert vmod._affiliate_row_count(empty_stub) == 0

    missing_entirely = {"schema_version": "1.0", "date": "2026-05-17"}
    assert vmod._affiliate_row_count(missing_entirely) == 0

    malformed = {"rows": "not_a_list", "count": "not_an_int"}
    assert vmod._affiliate_row_count(malformed) == 0
