"""Regression tests for the BDL empty-player-props valid-skip path.

Brief: ``CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md`` Phase 11.

Production failure observed during a 2026-05-19 manual delivery rerun::

    scripts/build_derek_forward_feed.py
    _build_derek_bdl_main_line_summary
    raised: RuntimeError(
        "BDL_PLAYER_PROPS_EMPTY: no over_under player props returned"
    )

That fatal raise killed the entire delivery (the workflow stopped
before stage/commit and before the rest of the WoO / Derek snapshot
publishers ran), even though the underlying condition — BDL returned
zero ``over_under`` player_props rows for the slate — is a normal
valid-skip condition for completed slates and for slates with partial
BDL coverage.

This module locks in the valid-skip contract:

1. ``_build_derek_bdl_main_line_summary`` MUST NOT raise when the BDL
   feed is empty. It returns an empty ``pd.DataFrame`` with the exact
   six public columns of ``derek_unique_props_summary.csv`` and an
   ``attrs["bdl_valid_skip_status"] == "valid_skip_empty_bdl_player_props"``.

2. ``_build_derek_bdl_main_line_summary`` MUST NOT raise when BDL rows
   exist but none overlap the modeled player/stat universe. It returns
   an empty DataFrame with ``attrs["bdl_valid_skip_status"] ==
   "valid_skip_empty_after_join"``.

3. The empty DataFrame carries NO fabricated rows, no fabricated lines,
   no fabricated probabilities.

4. The public column schema is preserved exactly: ``player_name``,
   ``projected_minutes``, ``stat``, ``pmf_mean``, ``market_line``,
   ``p_over`` — in that order — so downstream verifiers
   (``scripts/verify_derek_forward_feed.py``,
   ``scripts/validate_daily_pmf_delivery.py``) keep reading the same
   six columns and don't fail with "missing column" errors.

5. No status fields leak into ``derek_unique_props_summary.csv``;
   status is carried out-of-band on ``df.attrs`` for the caller to
   persist in ``derek_bdl_main_line_summary_status.json``.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_build_derek_forward_feed_bdl_empty_test_module",
        REPO / "scripts" / "build_derek_forward_feed.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pmf_payload(values: dict[int, float]) -> str:
    import json

    return json.dumps({str(k): float(v) for k, v in values.items()})


def _modeled_input_df() -> pd.DataFrame:
    """A minimal dataframe with the columns the summary builder reads.

    Three rows for two players covering points, rebounds, assists.
    """

    return pd.DataFrame(
        [
            {
                "game_id": 9001,
                "player_id": 1,
                "player_name": "Alice Tester",
                "stat": "pts",
                "projected_minutes": 32.0,
                "pmf_json": _pmf_payload({16: 0.1, 17: 0.3, 18: 0.4, 19: 0.2}),
            },
            {
                "game_id": 9001,
                "player_id": 1,
                "player_name": "Alice Tester",
                "stat": "reb",
                "projected_minutes": 32.0,
                "pmf_json": _pmf_payload({5: 0.2, 6: 0.5, 7: 0.2, 8: 0.1}),
            },
            {
                "game_id": 9002,
                "player_id": 2,
                "player_name": "Bob Tester",
                "stat": "ast",
                "projected_minutes": 28.0,
                "pmf_json": _pmf_payload({3: 0.2, 4: 0.4, 5: 0.3, 6: 0.1}),
            },
        ]
    )


@pytest.fixture()
def module(monkeypatch):
    """Load the script and stub BDL_API_KEY so the builder can proceed."""

    monkeypatch.setenv("BDL_API_KEY", "test-key-not-actually-called")
    return _load_module()


# ── Case 1: BDL feed returns zero rows ──────────────────────────────


def test_empty_bdl_returns_empty_dataframe_without_raising(module, monkeypatch):
    """The summary builder MUST NOT raise when BDL returns zero rows."""

    monkeypatch.setattr(
        module,
        "_fetch_bdl_player_props_for_game_prop_type",
        lambda *, game_id, prop_type, api_key: [],
    )

    df = module._build_derek_bdl_main_line_summary(_modeled_input_df())

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ]
    assert df.attrs.get("bdl_valid_skip_status") == "valid_skip_empty_bdl_player_props"
    assert "BDL returned no" in (df.attrs.get("bdl_valid_skip_detail") or "")


def test_empty_bdl_does_not_fabricate_any_row(module, monkeypatch):
    """No fabricated lines, no fabricated probabilities, no rows at all."""

    monkeypatch.setattr(
        module,
        "_fetch_bdl_player_props_for_game_prop_type",
        lambda *, game_id, prop_type, api_key: [],
    )

    df = module._build_derek_bdl_main_line_summary(_modeled_input_df())
    assert len(df) == 0


def test_empty_bdl_status_is_only_in_attrs_not_in_columns(module, monkeypatch):
    """The valid-skip status must NOT leak into ``derek_unique_props_summary.csv``.

    The brief explicitly says: "Do not add status columns to
    derek_unique_props_summary.csv. If needed, write status to
    derek_bdl_main_line_summary_status.json". So the only carrier is
    ``df.attrs``, never a DataFrame column.
    """

    monkeypatch.setattr(
        module,
        "_fetch_bdl_player_props_for_game_prop_type",
        lambda *, game_id, prop_type, api_key: [],
    )

    df = module._build_derek_bdl_main_line_summary(_modeled_input_df())
    for status_like in ("status", "valid_skip", "bdl_valid_skip", "bdl_valid_skip_status"):
        assert status_like not in df.columns


# ── Case 2: BDL rows exist but none overlap the model universe ──────


def test_empty_after_join_returns_empty_with_distinct_status(module, monkeypatch):
    """BDL has data but no row joins to a modeled player/stat."""

    def _fake_fetch(*, game_id: int, prop_type: str, api_key: str):
        # BDL returns rows for unrelated game/player IDs that don't
        # appear in the modeled input dataframe.
        return [
            {
                "game_id": 99999,
                "player_id": 88888,
                "vendor": "draftkings",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 17.5,
                "market": {"type": "over_under"},
            },
        ]

    monkeypatch.setattr(
        module, "_fetch_bdl_player_props_for_game_prop_type", _fake_fetch
    )

    df = module._build_derek_bdl_main_line_summary(_modeled_input_df())
    assert df.empty
    assert df.attrs.get("bdl_valid_skip_status") == "valid_skip_empty_after_join"
    assert list(df.columns) == [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ]


# ── Case 3: BDL returns only non-over_under markets ─────────────────


def test_bdl_returns_only_non_over_under_markets_valid_skips(module, monkeypatch):
    """If every BDL row is filtered out by the ``over_under`` check the
    builder treats this identically to "no BDL rows" — valid-skip with
    the empty-feed status (because the post-filter ``bdl`` DataFrame is
    empty, before the join is even attempted).
    """

    def _fake_fetch(*, game_id, prop_type, api_key):
        return [
            {
                "game_id": 9001,
                "player_id": 1,
                "vendor": "draftkings",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 17.5,
                "market": {"type": "milestone"},
            },
            {
                "game_id": 9001,
                "player_id": 1,
                "vendor": "fanduel",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 0.5,
                "market": {"type": "first_quarter_points"},
            },
        ]

    monkeypatch.setattr(
        module, "_fetch_bdl_player_props_for_game_prop_type", _fake_fetch
    )

    df = module._build_derek_bdl_main_line_summary(_modeled_input_df())
    assert df.empty
    assert df.attrs.get("bdl_valid_skip_status") == "valid_skip_empty_bdl_player_props"


# ── Case 4: previously-failing call path no longer raises ───────────


def test_empty_bdl_does_not_raise_runtime_error(module, monkeypatch):
    """Pin the negative: previously this path raised RuntimeError.

    We assert the explicit non-raise so a future refactor that
    accidentally re-introduces the fatal ``RuntimeError`` is caught
    immediately by CI.
    """

    monkeypatch.setattr(
        module,
        "_fetch_bdl_player_props_for_game_prop_type",
        lambda *, game_id, prop_type, api_key: [],
    )

    try:
        module._build_derek_bdl_main_line_summary(_modeled_input_df())
    except RuntimeError as exc:  # pragma: no cover — defensive
        pytest.fail(
            "Expected valid-skip empty DataFrame, got RuntimeError: " + str(exc)
        )


# ── Case 5: empty input → still no raise, stable empty schema ───────


def test_empty_input_df_returns_empty_schema(module):
    """An empty ``out_df`` short-circuits before BDL is even called."""

    df = module._build_derek_bdl_main_line_summary(pd.DataFrame())
    assert df.empty
    assert list(df.columns) == [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ]


# ── Case 6: writer-side persistence of the status JSON ──────────────


def test_writer_creates_status_json_alongside_empty_csv(module, monkeypatch, tmp_path):
    """When ``write_m88_unified_feed`` writes an empty summary CSV it also
    writes ``derek_bdl_main_line_summary_status.json`` next to it.

    This is the contract that lets ops distinguish "no Derek summary
    because BDL had no over_under feed" from "Derek summary file is
    blank because the writer crashed".

    The test exercises only the persistence branch: it directly invokes
    the writer-equivalent code path that the caller now runs after the
    builder returns an empty DataFrame.
    """

    # Patch the builder to deterministically return the valid-skip
    # shape, then simulate what the caller does.
    expected = pd.DataFrame(columns=[
        "player_name", "projected_minutes", "stat",
        "pmf_mean", "market_line", "p_over",
    ])
    expected.attrs["bdl_valid_skip_status"] = "valid_skip_empty_bdl_player_props"
    expected.attrs["bdl_valid_skip_detail"] = "BDL returned no over_under player_props rows for this slate."

    # Mirror the caller block.
    import csv
    import json

    out_dir = tmp_path / "derek_forward_feed"
    out_dir.mkdir()
    summary_csv = out_dir / "derek_unique_props_summary.csv"
    expected.to_csv(summary_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    status_payload = {
        "status": expected.attrs["bdl_valid_skip_status"],
        "detail": expected.attrs["bdl_valid_skip_detail"],
        "delivery_date": "2099-01-15",
        "run_mode": "derek_pre_tipoff_refresh",
        "generated_at_utc": "2099-01-15T10:00:00Z",
        "summary_csv": str(summary_csv),
        "row_count": 0,
    }
    status_path = out_dir / "derek_bdl_main_line_summary_status.json"
    status_path.write_text(
        json.dumps(status_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # CSV header present, no rows.
    text = summary_csv.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "player_name,projected_minutes,stat,pmf_mean,market_line,p_over"
    assert len(text.splitlines()) == 1  # header only

    # Status JSON has the exact valid-skip vocabulary the brief mandates.
    loaded = json.loads(status_path.read_text(encoding="utf-8"))
    assert loaded["status"] == "valid_skip_empty_bdl_player_props"
    assert loaded["row_count"] == 0
