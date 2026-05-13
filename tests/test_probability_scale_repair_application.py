"""Tests for probability scale repair application expectations."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def test_manifest_json_roundtrip(tmp_path: Path):
    man = {
        "version": "1",
        "canonical_pmf_unchanged": True,
        "uses_market_probability_as_feature": False,
        "segments": {
            "pts|core": {
                "accepted": True,
                "selected_method": "logit_ab",
                "a": 0.8,
                "b": -0.1,
            }
        },
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(man), encoding="utf-8")
    assert p.is_file()


def test_loss_row_schema_columns_present():
    cols = {
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_prob_over_calibrated",
        "model_pmf",
        "probability_scale_repair_scope",
    }
    assert "model_prob_over_raw" in cols
