"""Tests for SGP bundle adapter — source discovery, schema normalization, bundle build."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

try:
    from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle
    from sgp_engine.bundle import BUNDLE_VERSION
except ImportError as exc:
    pytest.skip(f"sgp_engine.sports.nba.adapter not available: {exc}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Fake delivery factory
# ---------------------------------------------------------------------------

def _make_fake_delivery(
    root: Path,
    slate_date: str,
    pmf_col: str = "pmf_json",
    n_players: int = 3,
) -> Path:
    """Create a minimal canonical_source delivery under root/deliveries/slate_date/.

    Parameters
    ----------
    root:
        Repository root (build_nba_slate_state_bundle takes this as repo_root).
    slate_date:
        e.g. "2026-03-01"
    pmf_col:
        Column name used for the PMF data — "pmf_json" (default) or "pmf_active" etc.
    n_players:
        Number of fake players to generate (each gets pts + reb rows).
    """
    delivery_dir = root / "deliveries" / slate_date
    delivery_dir.mkdir(parents=True, exist_ok=True)

    src = delivery_dir / "canonical_source"
    src.mkdir(parents=True, exist_ok=True)

    uniform_pts = {str(k): round(1 / 40, 6) for k in range(40)}
    uniform_reb = {str(k): round(1 / 20, 6) for k in range(20)}

    rows = []
    for i in range(n_players):
        team = "TEA" if i % 2 == 0 else "TEB"
        opp = "TEB" if i % 2 == 0 else "TEA"
        base = {
            "game_id": f"G_{slate_date.replace('-', '')}",
            "player_id": f"P{i + 1}",
            "player_name": f"Player {i + 1}",
            "team_id": team,
            "opponent": opp,  # intentionally using 'opponent' not 'opponent_id'
            "slate_date": slate_date,
        }
        for stat, pmf_d in [("pts", uniform_pts), ("reb", uniform_reb)]:
            row = dict(base, stat=stat)
            row[pmf_col] = json.dumps(pmf_d)
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_parquet(src / "player_prop_pmfs_tonight_MODEL_ONLY.parquet", index=False)

    # Write a run manifest so the as-of contract can find trained/calibrated dates.
    trained_through = (pd.Timestamp(slate_date) - pd.Timedelta(days=1)).date().isoformat()
    manifest = {
        "trained_through_date": trained_through,
        "calibrated_through_date": trained_through,
    }
    (delivery_dir / "run_manifest.json").write_text(json.dumps(manifest))

    return delivery_dir


def _bundle_root(repo_root: Path, slate_date: str) -> Path:
    return repo_root / "deliveries" / slate_date / "sgp_engine" / BUNDLE_VERSION


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

SLATE_DATE = "2026-03-15"


def test_canonical_source_preferred_over_wizard_of_odds(tmp_path):
    """canonical_source/ is chosen even when wizard_of_odds/ also exists."""
    repo = tmp_path / "repo"
    delivery_dir = _make_fake_delivery(repo, SLATE_DATE)

    # Also write a wizard_of_odds/ parquet that has different (corrupt) PMFs
    woo = delivery_dir / "wizard_of_odds"
    woo.mkdir()
    corrupt_df = pd.DataFrame([{
        "game_id": "WRONG",
        "player_id": "WRONG",
        "team_id": "XXX",
        "opponent_id": "YYY",
        "stat": "pts",
        "pmf_json": json.dumps({"0": 1.0}),
    }])
    corrupt_df.to_parquet(woo / "full_pmfs_wide.parquet", index=False)

    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    assert bundle is not None
    # Should NOT have loaded from wizard_of_odds — the corrupt WRONG game_id shouldn't appear
    player_ids = set(bundle.player_stat_pmfs["player_id"].astype(str))
    assert "WRONG" not in player_ids
    assert "P1" in player_ids


def test_canonical_source_works_when_woo_missing(tmp_path):
    """Bundle builds successfully with only canonical_source present."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE)
    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    assert bundle is not None
    assert len(bundle.player_stat_pmfs) > 0


def test_pmf_active_column_normalized_to_pmf_json(tmp_path):
    """Delivery using 'pmf_active' column: adapter normalizes it to 'pmf_json'."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE, pmf_col="pmf_active")
    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    assert "pmf_json" in bundle.player_stat_pmfs.columns
    assert len(bundle.player_stat_pmfs) > 0


def test_opponent_column_normalized(tmp_path):
    """'opponent' column in source is renamed to 'opponent_id' in bundle."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE)
    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    assert "opponent_id" in bundle.player_stat_pmfs.columns
    opponents = bundle.player_stat_pmfs["opponent_id"].dropna().unique()
    # Should map to real team IDs, not NaN
    assert len(opponents) > 0
    for opp in opponents:
        assert str(opp) not in {"nan", "None", "UNK"}


def test_source_file_audit_written(tmp_path):
    """data_quality_report.json (the source audit) is written alongside the bundle."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE)
    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    dq_path = bundle.root / "data_quality_report.json"
    assert dq_path.exists(), f"data_quality_report.json not found at {dq_path}"
    dq = json.loads(dq_path.read_text())
    assert "status" in dq
    assert "checks" in dq


def test_bundle_manifest_written(tmp_path):
    """bundle_manifest.json is written and has required fields."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE)
    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    manifest_path = bundle.root / "bundle_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    for key in ["schema_version", "sport", "slate_date", "bundle_status"]:
        assert key in manifest, f"Missing manifest key: {key}"
    assert manifest["sport"] == "nba"
    assert manifest["slate_date"] == SLATE_DATE


def test_asof_contract_passes_when_metadata_available(tmp_path):
    """Bundle asof_contract is PASS when trained/calibrated dates equal D-1."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE)  # helper writes D-1 dates in run_manifest.json
    bundle = build_nba_slate_state_bundle(
        repo, SLATE_DATE,
        allow_missing_asof_metadata=False,
        strict=False,
    )
    manifest = bundle.manifest
    asof = manifest.get("asof_contract", {})
    assert asof.get("status") == "PASS", (
        f"Expected asof_contract.status=PASS, got {asof.get('status')!r}. "
        f"Reasons: {asof.get('reasons')}"
    )


def test_missing_pmf_source_raises(tmp_path):
    """No PMF source file → FileNotFoundError (or sub-exception)."""
    repo = tmp_path / "repo"
    slate_date = "2026-04-01"
    # Create an empty delivery folder with NO PMF files, just the run manifest
    delivery_dir = repo / "deliveries" / slate_date
    delivery_dir.mkdir(parents=True, exist_ok=True)
    trained = (pd.Timestamp(slate_date) - pd.Timedelta(days=1)).date().isoformat()
    (delivery_dir / "run_manifest.json").write_text(
        json.dumps({"trained_through_date": trained, "calibrated_through_date": trained})
    )

    with pytest.raises((FileNotFoundError, ValueError)):
        build_nba_slate_state_bundle(repo, slate_date, allow_missing_asof_metadata=True)


def test_all_pmf_valid_flags_set(tmp_path):
    """All rows in player_stat_pmfs have pmf_valid == True when PMFs are good."""
    repo = tmp_path / "repo"
    _make_fake_delivery(repo, SLATE_DATE, n_players=5)
    bundle = build_nba_slate_state_bundle(repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False)
    pmfs = bundle.player_stat_pmfs
    assert "pmf_valid" in pmfs.columns
    invalid = pmfs[~pmfs["pmf_valid"].fillna(False)]
    assert len(invalid) == 0, (
        f"{len(invalid)} rows have pmf_valid=False:\n{invalid[['player_id', 'stat', 'pmf_valid']].to_string()}"
    )
