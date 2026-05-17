"""Regression tests for the PMF-column normalisation path that feeds
``_build_derek_bdl_main_line_summary`` inside ``write_m88_unified_feed``.

This test reproduces the production failure observed on 2026-05-17::

    DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS:
    one of pmf_json, pmf_active, pmf is required

The upstream snapshot delivered the final per-row PMF under
``pmf_active`` (the M8.9 active-PMF promotion column name) instead of
``pmf_json``. Without normalisation, every Derek feed row dict ends up
with ``pmf_json=None`` and the BDL main-line summary builder cannot
compute ``pmf_mean`` / ``p_over`` from a real PMF.

The fix in ``scripts/build_derek_forward_feed.py`` introduces a single
canonical priority order — ``pmf_json`` → ``pmf_active`` → ``pmf`` —
applied per-row inside the row-builder loop, and re-asserted at the
dataframe boundary via ``_ensure_pmf_json_column`` immediately before
``_build_derek_bdl_main_line_summary`` is called.

This test:

  1. Constructs an upstream dataframe whose only PMF column is
     ``pmf_active`` (NO ``pmf_json`` column at all).
  2. Stubs the BDL HTTP fetch with deterministic over_under lines.
  3. Calls ``write_m88_unified_feed`` end-to-end.
  4. Asserts the summary CSV is written with the exact 6-column contract,
     one row per (player, stat), with ``pmf_mean`` and ``p_over``
     computed directly from the upstream ``pmf_active`` PMF.
  5. Asserts the public ``derek_forward_feed.{csv,parquet,jsonl}``
     outputs still DROP ``pmf_json`` (private column).
  6. Asserts the helper-level contract: ``_pick_row_pmf_value`` returns
     the first non-empty value across the canonical priority, and
     ``_ensure_pmf_json_column`` materialises ``pmf_json`` from a
     fallback column when needed.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_build_derek_forward_feed_pmf_norm_test_module",
        REPO / "scripts" / "build_derek_forward_feed.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pmf_payload_dict(values: dict[int, float]) -> str:
    """Return a JSON-serialised PMF payload (matches the canonical
    MODEL_ONLY shipping format)."""
    return json.dumps({str(k): float(v) for k, v in values.items()})


# A tiny but valid PMF for the points stat. P(X > 17.5) = 0.4 + 0.2 = 0.6,
# E[X] = 16*0.1 + 17*0.3 + 18*0.4 + 19*0.2 = 17.7.
_ALICE_POINTS_PMF = _pmf_payload_dict({16: 0.1, 17: 0.3, 18: 0.4, 19: 0.2})

# Rebounds PMF. P(X > 6.5) = 0.2 + 0.1 = 0.3.
# E[X] = 5*0.2 + 6*0.5 + 7*0.2 + 8*0.1 = 6.2.
_ALICE_REB_PMF = _pmf_payload_dict({5: 0.2, 6: 0.5, 7: 0.2, 8: 0.1})

# Bob assists PMF. P(X > 4.5) = 0.3 + 0.1 = 0.4.
# E[X] = 3*0.2 + 4*0.4 + 5*0.3 + 6*0.1 = 4.3.
_BOB_AST_PMF = _pmf_payload_dict({3: 0.2, 4: 0.4, 5: 0.3, 6: 0.1})


def _upstream_df_with_pmf_active_only() -> pd.DataFrame:
    """Build the production-shape upstream dataframe.

    Critical: the PMF payload lives under ``pmf_active`` ONLY. There is
    NO ``pmf_json`` column on this dataframe. This is exactly the
    snapshot shape that broke the live morning delivery and surfaced
    ``DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS``.
    """
    rows = [
        {
            "game_id": 9001,
            "player_id": 1,
            "player_name": "Alice Tester",
            "stat": "pts",
            "line": 17.5,
            "minutes_mean": 32.0,
            "minutes_q50": 31.5,
            "mean": 17.7,
            "pmf_active": _ALICE_POINTS_PMF,
            "model_version": "test-v1",
            "delivery_date": "2099-01-15",
            "role_bucket": "starter",
            "market_no_vig_over_prob": 0.55,
            "edge": 0.05,
            "fair_over_odds_american": -120,
            "fair_under_odds_american": 100,
            "snapshot_time_utc": "2099-01-15T10:00:00Z",
            "injury_freshness_status": "fresh",
            "lineup_freshness_status": "fresh",
            "expected_lineup_status": "near_tip_projected",
            "official_lineup_status": "not_available_yet",
        },
        {
            "game_id": 9001,
            "player_id": 1,
            "player_name": "Alice Tester",
            "stat": "reb",
            "line": 6.5,
            "minutes_mean": 32.0,
            "minutes_q50": 31.5,
            "mean": 6.2,
            "pmf_active": _ALICE_REB_PMF,
            "model_version": "test-v1",
            "delivery_date": "2099-01-15",
            "role_bucket": "starter",
            "market_no_vig_over_prob": 0.48,
            "edge": -0.01,
            "fair_over_odds_american": 110,
            "fair_under_odds_american": -130,
            "snapshot_time_utc": "2099-01-15T10:00:00Z",
            "injury_freshness_status": "fresh",
            "lineup_freshness_status": "fresh",
            "expected_lineup_status": "near_tip_projected",
            "official_lineup_status": "not_available_yet",
        },
        {
            "game_id": 9002,
            "player_id": 2,
            "player_name": "Bob Tester",
            "stat": "ast",
            "line": 4.5,
            "minutes_mean": 28.0,
            "minutes_q50": 27.0,
            "mean": 4.3,
            "pmf_active": _BOB_AST_PMF,
            "model_version": "test-v1",
            "delivery_date": "2099-01-15",
            "role_bucket": "rotation",
            "market_no_vig_over_prob": 0.42,
            "edge": -0.02,
            "fair_over_odds_american": 130,
            "fair_under_odds_american": -150,
            "snapshot_time_utc": "2099-01-15T10:00:00Z",
            "injury_freshness_status": "fresh",
            "lineup_freshness_status": "fresh",
            "expected_lineup_status": "near_tip_projected",
            "official_lineup_status": "not_available_yet",
        },
    ]
    df = pd.DataFrame(rows)
    # Hard assertion of the precondition this test reproduces.
    assert "pmf_json" not in df.columns, (
        "test precondition: upstream snapshot must not carry pmf_json"
    )
    assert "pmf_active" in df.columns
    return df


def _stub_bdl_fetch(_module) -> None:
    """Monkeypatch ``_fetch_bdl_player_props_for_game_prop_type`` with a
    deterministic in-memory response for the three (game_id, prop_type)
    combos referenced by the upstream df.
    """

    bdl_table: dict[tuple[int, str], list[dict[str, Any]]] = {
        (9001, "points"): [
            {
                "game_id": 9001,
                "player_id": 1,
                "vendor": "draftkings",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 17.5,
                "market": {"type": "over_under"},
            },
            {
                "game_id": 9001,
                "player_id": 1,
                "vendor": "fanduel",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 17.5,
                "market": {"type": "over_under"},
            },
        ],
        (9001, "rebounds"): [
            {
                "game_id": 9001,
                "player_id": 1,
                "vendor": "draftkings",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 6.5,
                "market": {"type": "over_under"},
            },
        ],
        (9002, "assists"): [
            {
                "game_id": 9002,
                "player_id": 2,
                "vendor": "draftkings",
                "updated_at": "2099-01-15T11:00:00Z",
                "line_value": 4.5,
                "market": {"type": "over_under"},
            },
        ],
    }

    def _fake_fetch(*, game_id: int, prop_type: str, api_key: str):
        return list(bdl_table.get((int(game_id), prop_type), []))

    _module._fetch_bdl_player_props_for_game_prop_type = _fake_fetch


def test_pick_row_pmf_value_canonical_priority():
    mod = _load_module()
    assert mod.PMF_VALUE_COLUMN_PRIORITY == ("pmf_json", "pmf_active", "pmf")
    # pmf_json wins when present.
    assert mod._pick_row_pmf_value({"pmf_json": "A", "pmf_active": "B", "pmf": "C"}) == "A"
    # Fall back to pmf_active when pmf_json is missing/None/NaN.
    assert mod._pick_row_pmf_value({"pmf_active": "B", "pmf": "C"}) == "B"
    assert mod._pick_row_pmf_value({"pmf_json": None, "pmf_active": "B"}) == "B"
    assert mod._pick_row_pmf_value({"pmf_json": float("nan"), "pmf_active": "B"}) == "B"
    # Fall back to pmf when both higher priorities are missing.
    assert mod._pick_row_pmf_value({"pmf": "C"}) == "C"
    # No PMF anywhere → None.
    assert mod._pick_row_pmf_value({"other": 1}) is None
    # Works with pd.Series (the type DataFrame.iterrows yields).
    series = pd.Series({"pmf_active": "B"})
    assert mod._pick_row_pmf_value(series) == "B"


def test_ensure_pmf_json_column_materialises_from_fallback():
    mod = _load_module()
    df = pd.DataFrame(
        [
            {"pmf_active": "A1", "stat": "pts"},
            {"pmf_active": "A2", "stat": "reb"},
        ]
    )
    assert "pmf_json" not in df.columns
    out = mod._ensure_pmf_json_column(df)
    assert "pmf_json" in out.columns
    assert list(out["pmf_json"]) == ["A1", "A2"]
    # Idempotent when pmf_json is already present (pmf_json wins).
    df2 = pd.DataFrame([{"pmf_json": "J1", "pmf_active": "A1"}])
    out2 = mod._ensure_pmf_json_column(df2)
    assert list(out2["pmf_json"]) == ["J1"]
    # No PMF column at all → unchanged (downstream will raise the
    # explicit missing-cols error, which is the correct signal).
    df3 = pd.DataFrame([{"stat": "pts"}])
    out3 = mod._ensure_pmf_json_column(df3)
    assert "pmf_json" not in out3.columns


def test_pre_existing_market_line_does_not_collide_in_summary_merge(monkeypatch):
    """Direct-call unit test for the merge-collision fix.

    Before the fix, ``out_df`` carried the PMF-native public column
    ``market_line`` (added by the writer-schema sanitation pass) and
    ``_build_derek_bdl_main_line_summary`` merged it against the BDL
    consensus line of the same name. pandas auto-suffixed the join to
    ``market_line_x`` / ``market_line_y``; the iteration then read
    ``r.get("market_line")`` → ``None`` for every row and the summary
    raised ``DEREK_BDL_SUMMARY_EMPTY_AFTER_JOIN``.

    The fix drops the pre-existing ``market_line`` (and any sibling
    ``p_over``) from ``base`` before the BDL merge so the BDL
    ``line_value`` becomes the authoritative ``market_line`` on the
    joined frame.
    """
    mod = _load_module()
    _stub_bdl_fetch(mod)
    monkeypatch.setenv("BDL_API_KEY", "x-fake-test-key")

    # Exact shape ``out_df`` has when reaching the summary builder
    # after the writer's PMF-native sanitation pass: it already carries
    # ``market_line`` and ``p_over`` as public columns from the
    # writer, and ``pmf_json`` carries the final PMF.
    base = pd.DataFrame(
        [
            {
                "game_id": 9001,
                "player_id": 1,
                "player_name": "Alice Tester",
                "stat": "pts",
                "line": 17.5,
                "market_line": 17.5,  # <-- collision-trigger column
                "p_over": 0.61,  # <-- second sibling that also collides
                "pmf_json": _ALICE_POINTS_PMF,
                "projected_minutes": 32.0,
            }
        ]
    )
    summary = mod._build_derek_bdl_main_line_summary(base)
    assert list(summary.columns) == [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ]
    assert len(summary) == 1
    row = summary.iloc[0]
    # The persisted ``market_line`` comes from BDL ``line_value``
    # (authoritative), not from the row's own pre-existing public
    # ``market_line``. They happen to match in this test but the
    # important guarantee is that ``market_line`` (no _x/_y suffix)
    # is a real numeric column on the output.
    assert float(row["market_line"]) == 17.5
    # ``p_over`` on the output must be the DIRECT PMF tail probability
    # ``P(stat > market_line)``, not the legacy 0.61 that was on ``base``.
    assert math.isclose(float(row["p_over"]), 0.6, rel_tol=1e-9)
    # ``pmf_mean`` must be the direct PMF expectation, not anything
    # carried from upstream "mean" / "model_*" columns.
    assert math.isclose(float(row["pmf_mean"]), 17.7, rel_tol=1e-9)


def test_build_derek_bdl_main_line_summary_raises_on_no_pmf_column(monkeypatch):
    """Regression sentinel: when NEITHER ``pmf_json`` NOR ``pmf_active``
    NOR ``pmf`` is on the input dataframe, the builder must raise the
    exact production error string.

    This pins the diagnostic so future refactors cannot silently
    downgrade the failure mode."""
    mod = _load_module()
    monkeypatch.setenv("BDL_API_KEY", "x-fake-test-key")
    df = pd.DataFrame(
        [
            {"game_id": 1, "player_id": 1, "player_name": "X", "stat": "pts"},
        ]
    )
    with pytest.raises(RuntimeError) as exc:
        mod._build_derek_bdl_main_line_summary(df)
    assert "DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS" in str(exc.value)
    assert "one of pmf_json, pmf_active, pmf is required" in str(exc.value)


def test_write_m88_normalises_upstream_pmf_active_into_pmf_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end reproduction of the production failure.

    Without the per-row + dataframe-level normalisation, this test
    would hit ``DEREK_BDL_SUMMARY_MISSING_REQUIRED_COLUMNS`` or an
    empty summary; with the fix it produces a correctly populated
    summary CSV that reflects the BDL line + direct PMF math.
    """
    mod = _load_module()
    _stub_bdl_fetch(mod)
    monkeypatch.setenv("BDL_API_KEY", "x-fake-test-key")

    out_dir = tmp_path / "deliveries" / "2099-01-15" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

    df = _upstream_df_with_pmf_active_only()
    manifest = mod.write_m88_unified_feed(
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
        assert reader.fieldnames == [
            "player_name",
            "projected_minutes",
            "stat",
            "pmf_mean",
            "market_line",
            "p_over",
        ]
        records = list(reader)

    by_key = {(r["player_name"], r["stat"]): r for r in records}
    assert set(by_key.keys()) == {
        ("Alice Tester", "pts"),
        ("Alice Tester", "reb"),
        ("Bob Tester", "ast"),
    }, "one row per (player, stat) from BDL over_under lines"

    # pmf_mean = direct E[X] from the upstream pmf_active payload.
    assert math.isclose(float(by_key[("Alice Tester", "pts")]["pmf_mean"]), 17.7, rel_tol=1e-9)
    assert math.isclose(float(by_key[("Alice Tester", "reb")]["pmf_mean"]), 6.2, rel_tol=1e-9)
    assert math.isclose(float(by_key[("Bob Tester", "ast")]["pmf_mean"]), 4.3, rel_tol=1e-9)

    # p_over = direct PMF tail probability against the BDL market line.
    assert math.isclose(float(by_key[("Alice Tester", "pts")]["p_over"]), 0.6, rel_tol=1e-9)
    assert math.isclose(float(by_key[("Alice Tester", "reb")]["p_over"]), 0.3, rel_tol=1e-9)
    assert math.isclose(float(by_key[("Bob Tester", "ast")]["p_over"]), 0.4, rel_tol=1e-9)

    # market_line must come from the stubbed BDL over_under line_value.
    assert float(by_key[("Alice Tester", "pts")]["market_line"]) == 17.5
    assert float(by_key[("Alice Tester", "reb")]["market_line"]) == 6.5
    assert float(by_key[("Bob Tester", "ast")]["market_line"]) == 4.5

    # No null market_line / p_over (acceptance criteria #6 + #7).
    for row in records:
        assert row["market_line"] not in ("", "None", None)
        assert row["p_over"] not in ("", "None", None)

    # No duplicate (player, stat) rows (acceptance criteria #5).
    assert len(records) == len({(r["player_name"], r["stat"]) for r in records})

    # Quarantined fields must be absent (acceptance criteria #3 + #4).
    for c in (
        "model_projected_mean",
        "model_probability_over_market_line",
        "model_prob_over_raw",
        "model_prob_over_active",
        "model_p_over",
    ):
        assert c not in reader.fieldnames

    # Public derek_forward_feed.* outputs must NOT carry pmf_json
    # (acceptance criterion #8 — private column stripped before persist).
    feed_csv = out_dir / "derek_forward_feed.csv"
    feed_parquet = out_dir / "derek_forward_feed.parquet"
    feed_jsonl = out_dir / "derek_forward_feed.jsonl"
    assert feed_csv.is_file()
    assert feed_parquet.is_file()
    assert feed_jsonl.is_file()

    with feed_csv.open() as f:
        feed_cols = csv.DictReader(f).fieldnames or []
    assert "pmf_json" not in feed_cols
    feed_pq_cols = list(pd.read_parquet(feed_parquet).columns)
    assert "pmf_json" not in feed_pq_cols
    with feed_jsonl.open() as f:
        first_line = f.readline()
    if first_line.strip():
        first_rec = json.loads(first_line)
        assert "pmf_json" not in first_rec
