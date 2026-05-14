"""Tests for M8.8 delivery contract."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_delivery_contract_version():
    from nba_props_model.delivery.delivery_contract import DELIVERY_CONTRACT_VERSION

    assert DELIVERY_CONTRACT_VERSION


def test_pipeline_mode_map_complete():
    from nba_props_model.delivery.delivery_contract import PIPELINE_MODE_BY_RUN_MODE, RunMode

    assert set(PIPELINE_MODE_BY_RUN_MODE) == set(RunMode)


def test_infer_run_mode_smoke():
    from nba_props_model.delivery.delivery_contract import RunMode, infer_run_mode_for_delivery_date

    m = infer_run_mode_for_delivery_date(REPO, "2099-01-01")
    assert m == RunMode.BACKTEST


def test_banned_tokens_nonempty():
    from nba_props_model.delivery.delivery_contract import banned_placeholder_tokens

    assert "tbd" in banned_placeholder_tokens()


def test_delivery_specs_unique_paths():
    from nba_props_model.delivery.delivery_contract import delivery_file_specs

    paths = [s.relative_path for s in delivery_file_specs()]
    assert len(paths) == len(set(paths))


def test_assert_contract_coherent():
    from nba_props_model.delivery.delivery_contract import assert_contract_coherent

    assert_contract_coherent()
