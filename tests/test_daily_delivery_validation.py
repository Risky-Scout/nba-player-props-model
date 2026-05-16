"""Tests for the daily PMF delivery validator.

Cases:

    1. Missing minutes artifact -> source_unavailable, fail.
    2. Canonical with player_game_eligible=False -> failed.
    3. Canonical null minutes_mean -> failed.
    4. Canonical deep bench no-line low-minutes -> failed.
    5. Review keys mismatch canonical keys -> failed.
    6. Clean delivery -> passed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load_validator():
    import importlib.util
    p = REPO_ROOT / "scripts" / "validate_daily_pmf_delivery.py"
    spec = importlib.util.spec_from_file_location(
        "validate_daily_pmf_delivery", p
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validator = _load_validator()


SLATE_DATE = "2026-05-15"
TRAIN_THROUGH = "2026-05-14"


def _good_minutes_df():
    return pd.DataFrame([{
        "slate_date": SLATE_DATE,
        "game_id": 9001,
        "player_id": 101,
        "minutes_mean": 30.0,
        "minutes_p10": 24.0,
        "minutes_p50": 30.0,
        "minutes_p90": 36.0,
        "minutes_std": 3.5,
        "rotation_probability": 0.95,
        "starter_probability": 0.85,
        "projected_role": "starter",
        "p_inactive_used": 0.02,
    }])


def _canonical_row(**overrides):
    row = {
        "slate_date": SLATE_DATE,
        "game_id": 9001,
        "player_id": 101,
        "stat": "points",
        "role_bucket": "starter",
        "minutes_mean": 30.0,
        "minutes_p10": 24.0,
        "minutes_p50": 30.0,
        "minutes_p90": 36.0,
        "minutes_std": 3.5,
        "p_inactive_used": 0.02,
        "rotation_probability": 0.95,
        "starter_probability": 0.85,
        "projected_role": "starter",
        "player_game_eligible": True,
        "eligibility_reason": "starter_probability",
        "has_current_market_line": True,
    }
    row.update(overrides)
    return row


def _setup_paths(tmp_path, monkeypatch):
    """Stage tmp_path as the REPO_ROOT for the validator and return
    base/canonical/review/market/derek/manifest write paths."""
    monkeypatch.setattr(validator, "REPO_ROOT", tmp_path)

    artifacts = tmp_path / "artifacts" / "minutes_predictions" / SLATE_DATE
    artifacts.mkdir(parents=True, exist_ok=True)

    canonical_dir = tmp_path / "deliveries" / SLATE_DATE / "canonical_source"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    review_dir = (
        tmp_path / "deliveries" / SLATE_DATE
        / "pmf_model_review_package" / "machine_readable"
    )
    review_dir.mkdir(parents=True, exist_ok=True)
    woo_dir = tmp_path / "deliveries" / SLATE_DATE / "wizard_of_odds"
    woo_dir.mkdir(parents=True, exist_ok=True)
    derek_dir = tmp_path / "deliveries" / SLATE_DATE / "derek_forward_feed"
    derek_dir.mkdir(parents=True, exist_ok=True)

    return {
        "minutes": artifacts / "minutes_predictions.parquet",
        "minutes_eligible": artifacts / "minutes_predictions_eligible.parquet",
        "canonical": canonical_dir / "all_props_model_only.parquet",
        "model_only_legacy": canonical_dir / "player_prop_pmfs_tonight_MODEL_ONLY.parquet",
        "review": review_dir / "model_only.parquet",
        "market_pq": woo_dir / "market_comparison.parquet",
        "derek": derek_dir / "derek_forward_feed.parquet",
    }


def test_validator_fail_when_minutes_artifact_missing(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    # canonical exists but minutes do not.
    pd.DataFrame([_canonical_row()]).to_parquet(paths["canonical"], index=False)
    result = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    assert result["status"] == "source_unavailable"
    codes = {f["code"] for f in result["failures"]}
    assert "minutes_artifact_missing" in codes


def test_validator_fail_when_player_game_eligible_false(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    _good_minutes_df().to_parquet(paths["minutes"], index=False)
    pd.DataFrame([
        _canonical_row(),
        _canonical_row(player_id=999, player_game_eligible=False,
                       eligibility_reason="not_eligible",
                       has_current_market_line=False,
                       role_bucket="fringe"),
    ]).to_parquet(paths["canonical"], index=False)
    result = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    codes = {f["code"] for f in result["failures"]}
    assert "canonical_ineligible_rows" in codes
    assert result["status"] == "failed"


def test_validator_fail_when_canonical_null_minutes_mean(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    _good_minutes_df().to_parquet(paths["minutes"], index=False)
    pd.DataFrame([_canonical_row(minutes_mean=None)]).to_parquet(
        paths["canonical"], index=False
    )
    result = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    codes = {f["code"] for f in result["failures"]}
    assert "canonical_null_minutes_mean" in codes


def test_validator_fail_when_deep_bench_no_line_rows_present(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    _good_minutes_df().to_parquet(paths["minutes"], index=False)
    pd.DataFrame([
        _canonical_row(),
        _canonical_row(
            player_id=999,
            has_current_market_line=False,
            minutes_mean=4.0,
            rotation_probability=0.05,
            starter_probability=0.02,
            role_bucket="fringe",
            player_game_eligible=True,
            eligibility_reason="not_eligible",
        ),
    ]).to_parquet(paths["canonical"], index=False)
    result = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    codes = {f["code"] for f in result["failures"]}
    assert "canonical_deep_bench_no_line_PMFs" in codes


def test_validator_fail_when_review_keys_mismatch_canonical(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    _good_minutes_df().to_parquet(paths["minutes"], index=False)
    canon = pd.DataFrame([_canonical_row()])
    canon.to_parquet(paths["canonical"], index=False)
    review = pd.DataFrame([_canonical_row(player_id=42)])
    review.to_parquet(paths["review"], index=False)
    pd.DataFrame([{"line": 24.5, "game_id": 9001, "player_id": 101}]).to_parquet(
        paths["market_pq"], index=False
    )
    result = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    codes = {f["code"] for f in result["failures"]}
    assert "review_keys_mismatch_canonical" in codes


def _eligible_row(**overrides):
    row = _canonical_row(eligibility_reason="starter_probability", **overrides)
    return row


def _stage_clean_delivery(paths):
    _good_minutes_df().to_parquet(paths["minutes"], index=False)
    pd.DataFrame([_eligible_row()]).to_parquet(paths["minutes_eligible"], index=False)
    pd.DataFrame([_canonical_row()]).to_parquet(paths["canonical"], index=False)
    pd.DataFrame([_canonical_row()]).to_parquet(paths["model_only_legacy"], index=False)
    pd.DataFrame([_canonical_row()]).to_parquet(paths["review"], index=False)
    pd.DataFrame(
        [
            {"line": 24.5 + i, "game_id": 9001, "player_id": 101, "stat": "points"}
            for i in range(5)
        ]
    ).to_parquet(paths["market_pq"], index=False)
    pd.DataFrame([_canonical_row()]).to_parquet(paths["derek"], index=False)


def test_validator_clean_delivery_passes(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    _stage_clean_delivery(paths)
    result = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    assert result["status"] == "passed", result
    assert result["failures"] == []


def test_enrich_manifest_adds_pipeline_contract_paths(tmp_path, monkeypatch):
    paths = _setup_paths(tmp_path, monkeypatch)
    _stage_clean_delivery(paths)
    manifest = validator.validate(SLATE_DATE, TRAIN_THROUGH)
    validator.enrich_delivery_manifest_for_pipeline(
        manifest,
        delivery_date=SLATE_DATE,
        pipeline_mode="woo_morning_monetization",
        snapshot="morning",
    )
    assert manifest["date"] == SLATE_DATE
    assert manifest["run_mode"] == "woo_morning_monetization"
    assert manifest["snapshot"] == "morning"
    assert manifest["canonical_model_only_path"] == (
        "deliveries/2026-05-15/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    assert manifest["all_props_model_only_path"] == (
        "deliveries/2026-05-15/canonical_source/all_props_model_only.parquet"
    )
    assert manifest["market_comparison_path"] == (
        "deliveries/2026-05-15/wizard_of_odds/market_comparison.parquet"
    )
    assert isinstance(manifest.get("warnings"), list)
