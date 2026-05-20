"""Tests for verify_derek_forward_feed_contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def test_contract_script_exists():
    assert (REPO / "scripts" / "verify_derek_forward_feed_contract.py").is_file()


def test_verify_passes_on_minimal_unified(tmp_path: Path, monkeypatch):
    from nba_props_model.delivery.delivery_contract import DEREK_UNIFIED_REQUIRED_COLUMNS

    feed = tmp_path / "deliveries" / "2099-06-01" / "derek_forward_feed"
    feed.mkdir(parents=True)
    row = {c: None for c in DEREK_UNIFIED_REQUIRED_COLUMNS}
    row.update(
        {
            "game_date": "2099-06-01",
            "run_date": "2099-06-01",
            "run_id": "test",
            "run_mode": "morning_expected",
            "generated_at_utc": "2099-01-01T00:00:00Z",
            "pipeline_version": "test",
            "model_version": "test",
            "model_artifact_hash": "",
            "source_data_asof_utc": "2099-01-01T00:00:00Z",
            "player_id": 1,
            "player_name": "A",
            "team": "T",
            "opponent": "O",
            "game_id": "g",
            "event_id": None,
            "stat": "pts",
            "role_bucket": "starter",
            "inactive_risk": 0.0,
            "expected_lineup_status": "projected",
            "official_lineup_status": "not_available_yet",
            "injury_status": "ok",
            "injury_source": "x",
            "injury_last_updated_utc": None,
            "lineup_source": "y",
            "lineup_last_updated_utc": None,
            "stale_injury_flag": False,
            "stale_lineup_flag": False,
            "market_status": "no_offered_market",
            "delivery_status": "ready",
            "unavailable_reason": None,
            "calculation_source": "unit_test",
            "calculation_status": "ok",
            "market_line": 9.5,
            "p_over": 0.55,
            "model_prob_under_active": 0.5,
            "fair_over_odds": 100,
            "fair_under_odds": -100,
            "pmf_mean": 10.0,
            "pmf_variance": 1.0,
            "pmf_p10": 5.0,
            "pmf_p50": 10.0,
            "pmf_p90": 15.0,
            "market_prob_over": None,
            "no_vig_market_prob_over": None,
            "edge": 0.0,
            "line": None,
            "projected_minutes": 25.0,
            "minutes_q10": None,
            "minutes_q50": 24.0,
            "minutes_q90": None,
        }
    )
    pd.DataFrame([row]).to_parquet(feed / "derek_forward_feed.parquet", index=False)
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2099-06-01",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_PASS" in res.stdout


def test_verify_fails_when_parquet_missing_and_no_skip_marker(tmp_path: Path):
    feed = tmp_path / "deliveries" / "2099-06-02" / "derek_forward_feed"
    feed.mkdir(parents=True)
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2099-06-02",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "DEREK_FORWARD_FEED_CONTRACT_FAIL" in res.stdout


def test_verify_valid_skip_on_no_games_after_game(tmp_path: Path):
    """After-game runs on a true no-game day must accept the producer's
    honest skip marker instead of red-failing the missing parquet."""
    date = "2099-06-03"
    delivery = tmp_path / "deliveries" / date
    feed = delivery / "derek_forward_feed"
    feed.mkdir(parents=True)
    (feed / "derek_forward_feed_unified_skip.json").write_text(
        '{"unified_feed_status": "skipped_no_rows"}'
    )
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            date,
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "final_after_game",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_VALID_SKIP" in res.stdout


def test_verify_valid_skip_honors_slate_sentinel(tmp_path: Path):
    date = "2099-06-04"
    delivery = tmp_path / "deliveries" / date
    feed = delivery / "derek_forward_feed"
    feed.mkdir(parents=True)
    (delivery / "no_games_today.json").write_text(
        '{"status": "after_game_skipped_no_games_prev_day"}'
    )
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            date,
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "final_after_game",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_VALID_SKIP" in res.stdout


def test_verify_does_not_skip_for_strict_run_modes(tmp_path: Path):
    """Producer skip markers do NOT satisfy the contract for t25/t5/
    morning_expected — those modes require a real parquet."""
    date = "2099-06-05"
    delivery = tmp_path / "deliveries" / date
    feed = delivery / "derek_forward_feed"
    feed.mkdir(parents=True)
    (feed / "derek_forward_feed_unified_skip.json").write_text("{}")
    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            date,
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "t25",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "DEREK_FORWARD_FEED_CONTRACT_FAIL" in res.stdout


# ─────────────────────────────────────────────────────────────────────
# Builder-side guards for ``lineup_last_updated_utc``.
#
# These tests pin the production failure mode observed on GitHub
# Actions run 26186630356 (2026-05-20 woo_afternoon_refresh delivery
# build): when the BDL lineup freshness manifest is absent for the
# slate, the upstream ``pmf_model_review_package/machine_readable/
# model_only.parquet`` ships without ``lineup_last_updated_utc`` and
# the persisted Derek feed inherits the gap, producing
# ``DEREK_FORWARD_FEED_CONTRACT_FAIL
#  missing_columns=['lineup_last_updated_utc']``.
#
# The builder MUST always carry the column on the public Derek feed
# (parquet/csv/jsonl) with null values in projected/morning mode —
# never fabricated timestamps.
# ─────────────────────────────────────────────────────────────────────


def _stub_derek_bdl_main_line_summary(monkeypatch):
    """Patch the BDL main-line summary builder to skip the network.

    The real builder requires ``BDL_API_KEY`` and hits the BDL
    ``/v2/odds/player_props`` endpoint. Tests that exercise
    ``write_m88_unified_feed`` only care that the public derek feed
    schema is honored, so we substitute an empty summary frame with
    the public column contract.
    """
    import sys as _sys

    sys_path_inserted = []
    for sub in ("scripts", "src"):
        p = str(REPO / sub)
        if p not in _sys.path:
            _sys.path.insert(0, p)
            sys_path_inserted.append(p)

    import build_derek_forward_feed as bdff

    def _empty_summary(_out_df):
        return pd.DataFrame(columns=bdff.DEREK_UNIQUE_SUMMARY_COLS)

    monkeypatch.setattr(
        bdff,
        "_build_derek_bdl_main_line_summary",
        _empty_summary,
    )
    return bdff


def _synthetic_latest_rows_df_without_lineup_col(rows: int = 3) -> pd.DataFrame:
    """Build a morning_snapshot-shaped frame that LACKS the column.

    Mirrors the production failure mode where the upstream canonical
    parquet was built on a slate with no BDL lineup freshness manifest
    and dropped the all-None ``lineup_last_updated_utc`` column before
    Derek's per-snapshot writer ran.
    """
    base = []
    for i in range(rows):
        base.append(
            {
                "delivery_date": "2099-06-10",
                "snapshot_time_utc": "2099-06-10T12:00:00Z",
                "player_id": 1000 + i,
                "player_name": f"P {i}",
                "team": "TST",
                "opponent": "OPP",
                "game_id": 999000 + i,
                "stat": "pts",
                "line": 12.5,
                "role_bucket": "starter",
                "minutes_mean": 30.0,
                "minutes_q50": 30.0,
                "p_inactive_used": 0.0,
                "model_version": "test",
                "pmf_source": "test",
                "lineup_source": "bdl_lineup_freshness_manifest",
                "lineup_freshness_status": "projected",
                "expected_lineup_status": "projected",
                "official_lineup_status": "not_available_yet",
                "injury_freshness_status": "fresh",
                "injury_context_source": "test",
                "injury_report_fetched_at_utc": "2099-06-10T11:00:00Z",
                "market_no_vig_over_prob": 0.55,
                "edge": 0.01,
                "pmf_json": '{"10": 0.4, "12": 0.3, "14": 0.2, "16": 0.1}',
                "pmf_active": '{"10": 0.4, "12": 0.3, "14": 0.2, "16": 0.1}',
                "fair_over_odds_american": -110,
                "fair_under_odds_american": -110,
                "market_coverage_status": "full",
                "model_p_under": 0.45,
                "mean": 12.4,
                "median": 12,
                "support_max": 16,
                "player_game_eligible": True,
            }
        )
    df = pd.DataFrame(base)
    assert "lineup_last_updated_utc" not in df.columns, (
        "fixture must intentionally omit the column to mirror the "
        "production failure mode"
    )
    return df


def test_full_derek_feed_includes_lineup_last_updated_utc_column(
    tmp_path: Path,
    monkeypatch,
):
    """Persisted derek_forward_feed.{parquet,csv,jsonl} must carry the
    ``lineup_last_updated_utc`` column even when upstream snapshots
    drop it (BDL freshness manifest absent path).
    """
    bdff = _stub_derek_bdl_main_line_summary(monkeypatch)
    df = _synthetic_latest_rows_df_without_lineup_col(rows=2)
    out_dir = tmp_path / "derek_forward_feed"
    out_dir.mkdir(parents=True)

    bdff.write_m88_unified_feed(
        date="2099-06-10",
        out_dir=out_dir,
        df=df,
        run_mode="morning_expected",
        lineup_status={"status": "pending_pre_tipoff_run"},
    )

    pq = pd.read_parquet(out_dir / "derek_forward_feed.parquet")
    assert "lineup_last_updated_utc" in pq.columns, (
        "DEREK_UNIFIED_REQUIRED_COLUMNS contract requires "
        "lineup_last_updated_utc on derek_forward_feed.parquet "
        f"got cols={sorted(pq.columns)}"
    )

    csv_header = (out_dir / "derek_forward_feed.csv").read_text().splitlines()[0]
    assert "lineup_last_updated_utc" in csv_header.split(","), (
        "lineup_last_updated_utc must appear in the public CSV header"
    )

    jsonl_text = (out_dir / "derek_forward_feed.jsonl").read_text().splitlines()
    assert jsonl_text, "jsonl must contain at least one row"
    import json as _json

    first_record = _json.loads(jsonl_text[0])
    assert "lineup_last_updated_utc" in first_record, (
        "lineup_last_updated_utc must appear on every Derek feed jsonl record"
    )


def test_lineup_last_updated_utc_null_allowed_in_projected_mode(
    tmp_path: Path,
    monkeypatch,
):
    """Projected/morning mode: null ``lineup_last_updated_utc`` values
    must satisfy the contract verifier (no fabricated timestamps).
    """
    bdff = _stub_derek_bdl_main_line_summary(monkeypatch)
    df = _synthetic_latest_rows_df_without_lineup_col(rows=2)
    out_dir = tmp_path / "deliveries" / "2099-06-11" / "derek_forward_feed"
    out_dir.mkdir(parents=True)

    bdff.write_m88_unified_feed(
        date="2099-06-11",
        out_dir=out_dir,
        df=df,
        run_mode="morning_expected",
        lineup_status={"status": "pending_pre_tipoff_run"},
    )

    pq = pd.read_parquet(out_dir / "derek_forward_feed.parquet")
    assert "lineup_last_updated_utc" in pq.columns
    assert pq["lineup_last_updated_utc"].isna().all(), (
        "projected/morning mode must leave lineup_last_updated_utc null "
        "when upstream has no confirmed timestamp — never fabricated"
    )

    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2099-06-11",
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "morning_expected",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        "contract verifier must pass on null-but-present "
        "lineup_last_updated_utc; got:\n"
        + res.stdout
        + res.stderr
    )
    assert "DEREK_FORWARD_FEED_CONTRACT_PASS" in res.stdout


def test_derek_feed_contract_rejects_missing_lineup_last_updated_utc(
    tmp_path: Path,
):
    """If a feed parquet ships without ``lineup_last_updated_utc``,
    the contract verifier must surface
    ``DEREK_FORWARD_FEED_CONTRACT_FAIL`` with the column listed.
    """
    from nba_props_model.delivery.delivery_contract import (
        DEREK_UNIFIED_REQUIRED_COLUMNS,
    )

    feed = tmp_path / "deliveries" / "2099-06-12" / "derek_forward_feed"
    feed.mkdir(parents=True)
    row = {c: None for c in DEREK_UNIFIED_REQUIRED_COLUMNS}
    row.update(
        {
            "game_date": "2099-06-12",
            "run_date": "2099-06-12",
            "run_id": "test",
            "run_mode": "t25",
            "generated_at_utc": "2099-06-12T00:00:00Z",
            "pipeline_version": "test",
            "model_version": "test",
            "model_artifact_hash": "",
            "source_data_asof_utc": "2099-06-12T00:00:00Z",
            "player_id": 1,
            "player_name": "A",
            "team": "T",
            "opponent": "O",
            "game_id": "g",
            "stat": "pts",
            "role_bucket": "starter",
            "inactive_risk": 0.0,
            "expected_lineup_status": "projected",
            "official_lineup_status": "not_available_yet",
            "injury_status": "ok",
            "injury_source": "x",
            "injury_last_updated_utc": None,
            "lineup_source": "y",
            "stale_injury_flag": False,
            "stale_lineup_flag": False,
            "market_status": "no_offered_market",
            "delivery_status": "ready",
            "calculation_source": "unit_test",
            "calculation_status": "ok",
        }
    )
    df = pd.DataFrame([row])
    df = df.drop(columns=["lineup_last_updated_utc"])
    df.to_parquet(feed / "derek_forward_feed.parquet", index=False)

    script = REPO / "scripts" / "verify_derek_forward_feed_contract.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2099-06-12",
            "--repo-root",
            str(tmp_path),
            "--run-mode",
            "t25",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2, res.stdout + res.stderr
    assert "DEREK_FORWARD_FEED_CONTRACT_FAIL" in res.stdout
    assert "lineup_last_updated_utc" in res.stdout


def test_derek_unique_summary_schema_unchanged():
    """The compact ``derek_unique_props_summary.csv`` schema must
    remain exactly the six published columns. Adding the
    ``lineup_last_updated_utc`` column to the FULL feed must not leak
    into the boss-facing compact summary.
    """
    import sys as _sys

    for sub in ("scripts", "src"):
        p = str(REPO / sub)
        if p not in _sys.path:
            _sys.path.insert(0, p)

    import build_derek_forward_feed as bdff

    assert bdff.DEREK_UNIQUE_SUMMARY_COLS == [
        "player_name",
        "projected_minutes",
        "stat",
        "pmf_mean",
        "market_line",
        "p_over",
    ], (
        "derek_unique_props_summary.csv contract is exactly six columns "
        f"got {bdff.DEREK_UNIQUE_SUMMARY_COLS}"
    )


if __name__ == "__main__":
    import pytest  # noqa: F401

    pytest.main([__file__, "-q"])
