"""Tests for ``deliveries/<DATE>/derek_forward_feed/derek_unique_props_summary.csv``.

The summary is written by ``scripts/build_derek_forward_feed.py``
inside ``write_m88_unified_feed``. It is a thin column-mapping +
dedupe view on top of the full feed, exposing only what Derek's
downstream consumers need.

Schema contract (exact column list + order):

  player_name | projected_minutes | stat | market_line
  | model_projected_mean (← pmf_mean)
  | model_probability_over_market_line (← model_prob_over_active)
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
    "market_line",
    "model_projected_mean",
    "model_probability_over_market_line",
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
                                 ``model_prob_over_active``
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


def test_summary_exact_schema_and_column_mapping(tmp_path: Path) -> None:
    """Verify that the file has the exact 6-column contract and
    that ``model_projected_mean`` maps from ``pmf_mean`` and
    ``model_probability_over_market_line`` maps from
    ``model_prob_over_active``."""
    module = _load_build_derek_forward_feed_module()

    out_dir = tmp_path / "deliveries" / "2099-01-15" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

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

    # Dedupe: Alice/pts/18.5 had two book-level rows; summary
    # collapses to one. Alice has pts + reb (2 rows). Bob has ast
    # at 4.5 and 5.5 (2 rows). Total = 4 unique props.
    assert len(records) == 4

    by_key = {(r["player_name"], r["stat"], r["market_line"]): r for r in records}
    alice_pts = by_key[("Alice", "pts", "18.5")]
    assert alice_pts["projected_minutes"] == "32.0"
    assert alice_pts["model_projected_mean"] == "19.4"
    assert alice_pts["model_probability_over_market_line"] == "0.61"

    bob_5_5 = by_key[("Bob", "ast", "5.5")]
    assert bob_5_5["model_probability_over_market_line"] == "0.34"


def test_summary_manifest_records_column_lineage(tmp_path: Path) -> None:
    module = _load_build_derek_forward_feed_module()
    out_dir = tmp_path / "deliveries" / "2099-01-16" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

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
    assert summary_block["column_lineage"] == {
        "model_projected_mean": "pmf_mean",
        "model_probability_over_market_line": "model_prob_over_active",
    }
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
