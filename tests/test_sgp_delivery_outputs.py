"""End-to-end tests for SGP delivery output structure."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

try:
    from sgp_engine.bundle import BUNDLE_VERSION
    from sgp_engine.pricing import price_ticket, price_tickets_to_frame
    from sgp_engine.schema import SGPTicket
    from sgp_engine.sports.nba.adapter import build_nba_slate_state_bundle
    from sgp_engine.sports.nba.simulator import NBASimulator
except ImportError as exc:
    pytest.skip(f"sgp_engine not available: {exc}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers — fake delivery factory
# ---------------------------------------------------------------------------

def _write_fake_delivery(
    delivery_root: Path,
    slate_date: str,
    game_id: str = "G_TEST",
    n_players: int = 4,
) -> None:
    """Write a minimal canonical_source delivery for end-to-end testing."""
    src = delivery_root / slate_date / "canonical_source"
    src.mkdir(parents=True, exist_ok=True)

    uniform_pts = {str(k): round(1 / 40, 6) for k in range(40)}
    uniform_reb = {str(k): round(1 / 20, 6) for k in range(20)}
    uniform_ast = {str(k): round(1 / 15, 6) for k in range(15)}

    rows = []
    for i in range(n_players):
        team = "T1" if i % 2 == 0 else "T2"
        opp = "T2" if i % 2 == 0 else "T1"
        pid = f"P{i + 1}"
        for stat, pmf_d in [("pts", uniform_pts), ("reb", uniform_reb), ("ast", uniform_ast)]:
            rows.append({
                "game_id": game_id,
                "player_id": pid,
                "player_name": f"Player {i + 1}",
                "team_id": team,
                "opponent_id": opp,
                "stat": stat,
                "pmf_json": json.dumps(pmf_d),
            })

    df = pd.DataFrame(rows)
    df.to_parquet(src / "player_prop_pmfs_tonight_MODEL_ONLY.parquet", index=False)

    trained = (pd.Timestamp(slate_date) - pd.Timedelta(days=1)).date().isoformat()
    (delivery_root / slate_date / "run_manifest.json").write_text(
        json.dumps({"trained_through_date": trained, "calibrated_through_date": trained})
    )


def _bundle_root(repo_root: Path, slate_date: str) -> Path:
    return repo_root / "deliveries" / slate_date / "sgp_engine" / BUNDLE_VERSION


SLATE_DATE = "2026-04-10"
GAME_ID = "G_TEST"


# ---------------------------------------------------------------------------
# Shared pipeline fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline_repo(tmp_path_factory):
    """Build a complete bundle + run simulation once; shared across tests."""
    tmp = tmp_path_factory.mktemp("delivery_outputs")
    repo = tmp / "repo"
    _write_fake_delivery(repo / "deliveries", SLATE_DATE, game_id=GAME_ID)
    bundle = build_nba_slate_state_bundle(
        repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False
    )
    tape = NBASimulator(bundle, n_sims=20_000, seed=0).run()
    return {"repo": repo, "bundle": bundle, "tape": tape}


# ---------------------------------------------------------------------------
# 1 · Full pipeline writes required files
# ---------------------------------------------------------------------------

def test_full_pipeline_writes_required_files(tmp_path):
    """build_bundle → all required bundle files must exist under sgp_engine/."""
    repo = tmp_path / "repo"
    _write_fake_delivery(repo / "deliveries", SLATE_DATE, game_id=GAME_ID)
    bundle = build_nba_slate_state_bundle(
        repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False
    )

    bundle_dir = _bundle_root(repo, SLATE_DATE)
    required_files = [
        "bundle_manifest.json",
        "player_stat_pmfs.parquet",
        "players.parquet",
        "games.parquet",
        "data_quality_report.json",
    ]
    for fname in required_files:
        path = bundle_dir / fname
        assert path.exists(), f"Required file missing: {path.relative_to(repo)}"


# ---------------------------------------------------------------------------
# 2 · Verify script logic passes on valid outputs
# ---------------------------------------------------------------------------

def test_verify_script_passes_on_valid_outputs(tmp_path):
    """Inline verify_sgp_bundle_asof_contract logic passes for valid bundle."""
    repo = tmp_path / "repo"
    _write_fake_delivery(repo / "deliveries", SLATE_DATE, game_id=GAME_ID)
    build_nba_slate_state_bundle(
        repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False
    )

    bundle_dir = _bundle_root(repo, SLATE_DATE)
    manifest = json.loads((bundle_dir / "bundle_manifest.json").read_text())

    expected = (pd.Timestamp(SLATE_DATE) - pd.Timedelta(days=1)).date().isoformat()
    trained = (
        manifest.get("trained_through_date")
        or manifest.get("asof_contract", {}).get("trained_through_date")
    )
    calibrated = (
        manifest.get("calibrated_through_date")
        or manifest.get("asof_contract", {}).get("calibrated_through_date")
    )

    assert trained == expected, (
        f"trained_through_date mismatch: got {trained!r}, expected {expected!r}"
    )
    assert calibrated == expected, (
        f"calibrated_through_date mismatch: got {calibrated!r}, expected {expected!r}"
    )
    assert manifest.get("bundle_status") == "PASS", (
        f"bundle_status is not PASS: {manifest.get('bundle_status')!r}"
    )


# ---------------------------------------------------------------------------
# 3 · Verify script fails when price grid is missing
# ---------------------------------------------------------------------------

def test_verify_script_fails_on_missing_price_grid(tmp_path):
    """verify_sgp_delivery_outputs must FAIL when price grid file is absent."""
    from sgp_engine.cli import verify_sgp_delivery_outputs  # type: ignore[attr-defined]

    repo = tmp_path / "repo"
    _write_fake_delivery(repo / "deliveries", SLATE_DATE, game_id=GAME_ID)
    build_nba_slate_state_bundle(
        repo, SLATE_DATE, allow_missing_asof_metadata=True, strict=False
    )

    # Do NOT write a price grid file — verify should fail.
    with pytest.raises((SystemExit, ValueError, FileNotFoundError)):
        verify_sgp_delivery_outputs(repo, SLATE_DATE, require_price_grid=True)


# ---------------------------------------------------------------------------
# 4 · Price grid probabilities are in (0, 1)
# ---------------------------------------------------------------------------

def test_price_grid_probabilities_in_range(pipeline_repo):
    """All calibrated_joint_probability values from priced tickets are in (0, 1)."""
    bundle = pipeline_repo["bundle"]
    tape = pipeline_repo["tape"]

    tickets = [
        SGPTicket.from_dict({
            "game_id": GAME_ID,
            "ticket_id": f"T{i}",
            "legs": [
                {"player_id": "P1", "stat": "pts", "line": float(line), "side": "over"},
                {"player_id": "P2", "stat": "reb", "line": float(line2), "side": "over"},
            ],
        })
        for i, (line, line2) in enumerate([(19.5, 9.5), (14.5, 6.5), (24.5, 12.5)])
    ]
    df = price_tickets_to_frame(tickets, tape, bundle.player_stat_pmfs)
    assert "calibrated_joint_probability" in df.columns
    for p in df["calibrated_joint_probability"]:
        assert 0.0 < float(p) < 1.0, f"Probability {p} is outside (0, 1)"


# ---------------------------------------------------------------------------
# 5 · Fair decimal odds are finite and > 1
# ---------------------------------------------------------------------------

def test_fair_odds_finite(pipeline_repo):
    """fair_decimal_odds must be finite and strictly > 1 for every priced ticket."""
    bundle = pipeline_repo["bundle"]
    tape = pipeline_repo["tape"]

    tickets = [
        SGPTicket.from_dict({
            "game_id": GAME_ID,
            "ticket_id": f"T{i}",
            "legs": [
                {"player_id": "P1", "stat": "pts", "line": float(line), "side": "over"},
                {"player_id": "P3", "stat": "ast", "line": 7.5, "side": "over"},
            ],
        })
        for i, line in enumerate([19.5, 14.5, 24.5, 9.5])
    ]
    df = price_tickets_to_frame(tickets, tape, bundle.player_stat_pmfs)
    assert "fair_decimal_odds" in df.columns
    for odds in df["fair_decimal_odds"]:
        assert np.isfinite(float(odds)), f"fair_decimal_odds is not finite: {odds}"
        assert float(odds) > 1.0, f"fair_decimal_odds <= 1.0: {odds}"
