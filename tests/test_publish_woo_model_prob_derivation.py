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
