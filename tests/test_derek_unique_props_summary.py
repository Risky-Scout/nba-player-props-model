"""Tests for ``deliveries/<DATE>/derek_forward_feed/derek_unique_props_summary.csv``.

The summary is written by ``scripts/build_derek_forward_feed.py``
inside ``write_m88_unified_feed``. It is built from the BDL
``/v2/odds/player_props`` ``over_under`` lines joined to the
canonical PMF surface — one row per (player, stat).

Schema contract (exact column list + order):

  player_name | projected_minutes | stat | pmf_mean | market_line
  | p_over

  • ``pmf_mean`` is the direct PMF expectation from the row PMF.
  • ``market_line`` is the BDL ``line_value`` for the player/stat
    ``over_under`` market.
  • ``p_over`` is the direct PMF tail probability
    ``P(stat > market_line)``.

Quarantined columns (``model_projected_mean``,
``model_probability_over_market_line``, ``model_prob_over_*``,
``model_p_over``) MUST be absent from this file.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]

SUMMARY_EXPECTED_COLUMNS = [
    "player_name",
    "projected_minutes",
    "stat",
    "pmf_mean",
    "market_line",
    "p_over",
]


def _load_build_derek_forward_feed_module():
    spec = importlib.util.spec_from_file_location(
        "_build_derek_forward_feed_test_module",
        REPO / "scripts" / "build_derek_forward_feed.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_build_derek_forward_feed_test_module"] = module
    spec.loader.exec_module(module)
    return module


def _make_unified_df() -> pd.DataFrame:
    """Build an input DataFrame in the shape ``write_m88_unified_feed``
    expects (i.e. ``model_only`` / ``market_comparison`` row layout).

    Critical column names (these flow through the row builder into
    the published feed):

      * ``minutes_mean``       → feed's ``projected_minutes``
      * ``mean``               → feed's ``pmf_mean`` when there is
                                 no ``pmf_json``
      * ``model_p_over``       → feed's
                                 ``direct_pmf_tail_probability_gt_market_line``
    """
    rows = [
        {
            "player_id": 1,
            "player_name": "Alice",
            "stat": "pts",
            "line": 18.5,
            "minutes_mean": 32.0,
            "mean": 19.4,
            "model_p_over": 0.61,
        },
        # Duplicate (player, stat, line) from a different book — must dedupe.
        {
            "player_id": 1,
            "player_name": "Alice",
            "stat": "pts",
            "line": 18.5,
            "minutes_mean": 32.0,
            "mean": 19.4,
            "model_p_over": 0.61,
        },
        {
            "player_id": 1,
            "player_name": "Alice",
            "stat": "reb",
            "line": 6.5,
            "minutes_mean": 32.0,
            "mean": 6.8,
            "model_p_over": 0.53,
        },
        {
            "player_id": 2,
            "player_name": "Bob",
            "stat": "ast",
            "line": 4.5,
            "minutes_mean": 28.0,
            "mean": 4.2,
            "model_p_over": 0.47,
        },
        # Same player+stat, different line — must remain as two rows.
        {
            "player_id": 2,
            "player_name": "Bob",
            "stat": "ast",
            "line": 5.5,
            "minutes_mean": 28.0,
            "mean": 4.2,
            "model_p_over": 0.34,
        },
    ]
    return pd.DataFrame(rows)


def test_summary_exact_schema_and_column_mapping(tmp_path: Path, monkeypatch) -> None:
    """Verify the persisted file has the exact 6-column contract.

    The BDL fetcher is stubbed (no live network), so the test pins
    only the schema + column ordering of the file the writer emits.
    """
    module = _load_build_derek_forward_feed_module()

    out_dir = tmp_path / "deliveries" / "2099-01-15" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

    expected_summary = pd.DataFrame(
        {
            "player_name": ["Alpha Player", "Beta Player"],
            "projected_minutes": [31.5, 28.0],
            "stat": ["pts", "pra"],
            "pmf_mean": [18.25, 29.75],
            "market_line": [17.5, 30.5],
            "p_over": [0.584, 0.462],
        }
    )
    monkeypatch.setattr(
        module,
        "_build_derek_bdl_main_line_summary",
        lambda out_df: expected_summary.copy(),
    )

    df = _make_unified_df()
    manifest = module.write_m88_unified_feed(
        date="2099-01-15",
        out_dir=out_dir,
        df=df,
        run_mode="morning_expected",
        lineup_status={"status": "test"},
    )
    assert manifest is not None

    summary_path = out_dir / "derek_unique_props_summary.csv"
    assert summary_path.is_file(), "summary CSV must be written"

    with summary_path.open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == SUMMARY_EXPECTED_COLUMNS
        records = list(reader)

    # New Derek summary is produced by the BDL-main-line summary builder:
    # one row per player/stat from the summary builder contract.
    assert len(records) == len(expected_summary)

    # Quarantined public columns MUST NOT appear in the persisted file.
    for c in (
        "model_projected_mean",
        "model_probability_over_market_line",
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_p_over",
    ):
        assert c not in reader.fieldnames

    expected_records = expected_summary.astype(str).to_dict("records")
    assert records == expected_records


def test_summary_manifest_records_column_lineage(tmp_path: Path, monkeypatch) -> None:
    module = _load_build_derek_forward_feed_module()
    out_dir = tmp_path / "deliveries" / "2099-01-16" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

    expected_summary = pd.DataFrame(
        {
            "player_name": ["Alpha Player", "Beta Player"],
            "projected_minutes": [31.5, 28.0],
            "stat": ["pts", "pra"],
            "pmf_mean": [18.25, 29.75],
            "market_line": [17.5, 30.5],
            "p_over": [0.584, 0.462],
        }
    )
    monkeypatch.setattr(
        module,
        "_build_derek_bdl_main_line_summary",
        lambda out_df: expected_summary.copy(),
    )

    df = _make_unified_df()
    manifest = module.write_m88_unified_feed(
        date="2099-01-16",
        out_dir=out_dir,
        df=df,
        run_mode="morning_expected",
        lineup_status={"status": "test"},
    )

    assert manifest is not None
    summary_block = manifest.get("unique_props_summary")
    assert summary_block is not None
    assert summary_block["columns"] == SUMMARY_EXPECTED_COLUMNS
    expected_lineage = {
        "pmf_mean": "direct_expectation_from_pmf_json",
        "p_over": "direct_pmf_tail_probability_gt_market_line",
        "market_line": "bdl_player_props_line_value_over_under_consensus",
    }
    assert summary_block["column_lineage"] == expected_lineage
    # The lineage must NEVER name any of the quarantined source
    # columns — public ``pmf_mean`` / ``p_over`` come from the PMF
    # surface, not from ``model_p_over`` / ``model_prob_over_*``.
    lineage_values = set(summary_block["column_lineage"].values())
    for c in (
        "model_projected_mean",
        "model_probability_over_market_line",
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_p_over",
    ):
        assert c not in lineage_values
    assert "files" in manifest
    assert manifest["files"]["unique_props_summary_csv"].endswith(
        "derek_unique_props_summary.csv"
    )


def test_summary_handles_empty_feed_gracefully(tmp_path: Path) -> None:
    module = _load_build_derek_forward_feed_module()
    out_dir = tmp_path / "deliveries" / "2099-01-17" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

    # Empty df triggers the early-return skip block; summary CSV is
    # NOT written (the skip JSON is written instead).
    manifest = module.write_m88_unified_feed(
        date="2099-01-17",
        out_dir=out_dir,
        df=pd.DataFrame(),
        run_mode="morning_expected",
        lineup_status={"status": "test"},
    )
    assert manifest is None
    assert (out_dir / "derek_forward_feed_unified_skip.json").is_file()
