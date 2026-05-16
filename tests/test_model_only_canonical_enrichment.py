"""MODEL_ONLY enrichment from minutes_predictions_eligible + schema contract."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
SRC = REPO / "src"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SRC))


from build_daily_pmf_delivery import (  # noqa: E402
    _validate_eligibility_contract_for_model_only,
)
from build_model_only_canonical_from_stat_grid import (  # noqa: E402
    MODEL_ONLY_PUBLISH_COLUMNS,
    merge_eligibility_minutes_into_model_only,
    _assert_publish_schema_preflight,
    _inject_slate_date,
    _normalize_minutes_q_to_p_aliases,
    _require_join_keys,
)


def _eligible_row(*, slate_date="2026-06-02", game_id=90001, player_id=123):
    return {
        "slate_date": slate_date,
        "game_id": game_id,
        "player_id": player_id,
        "minutes_mean": 28.0,
        "minutes_p10": 20.0,
        "minutes_p50": 28.0,
        "minutes_p90": 34.0,
        "minutes_std": 6.0,
        "p_inactive_used": 0.05,
        "rotation_probability": 0.88,
        "starter_probability": 0.92,
        "projected_role": "starter",
        "has_current_market_line": True,
        "eligibility_reason": "starter_probability",
    }


def _full_stat_grid_like_row(**overrides):
    base = {
        "slate_date": "2026-06-02",
        "game_id": 90001,
        "player_id": 123,
        "stat": "pts",
        "minutes_mean": 30.0,
        "minutes_p10": 22.0,
        "minutes_p50": 30.0,
        "minutes_p90": 36.0,
        "minutes_std": 5.0,
        "p_inactive_used": 0.02,
        "rotation_probability": 0.80,
        "starter_probability": 0.70,
        "projected_role": "starter",
        "player_game_eligible": True,
        "eligibility_reason": "minutes_floor",
        "has_current_market_line": False,
    }
    base.update(overrides)
    return base


def test_normalize_minutes_q_to_p_aliases():
    df = pd.DataFrame(
        {
            "minutes_q10": [10.0],
            "minutes_q50": [20.0],
            "minutes_q90": [30.0],
        }
    )
    out = _normalize_minutes_q_to_p_aliases(df)
    assert "minutes_p10" in out.columns
    assert "minutes_p50" in out.columns
    assert "minutes_p90" in out.columns
    assert float(out["minutes_p50"].iloc[0]) == 20.0


def test_q_aliases_do_not_duplicate_if_p_present():
    df = pd.DataFrame(
        {
            "minutes_q50": [99.0],
            "minutes_p50": [20.0],
        }
    )
    out = _normalize_minutes_q_to_p_aliases(df)
    assert float(out["minutes_p50"].iloc[0]) == 20.0


def test_join_keys_missing_column():
    df = pd.DataFrame({"game_id": [1], "player_id": [2]})
    with pytest.raises(SystemExit, match="MODEL_ONLY_JOIN_KEYS_MISSING"):
        _require_join_keys(df)


def test_join_keys_null_player_id():
    df = pd.DataFrame(
        {"slate_date": ["2026-06-02"], "game_id": [1], "player_id": [float("nan")]}
    )
    with pytest.raises(SystemExit, match="MODEL_ONLY_JOIN_KEYS_MISSING"):
        _require_join_keys(df)


def test_schema_validator_marker(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("NBA_ALLOW_LEGACY_NO_ELIGIBILITY", raising=False)
    df = pd.DataFrame({"minutes_mean": [24.0]})
    fake = tmp_path / "p.parquet"
    with pytest.raises(SystemExit, match="MODEL_ONLY_SCHEMA_MISSING_COLUMNS"):
        _validate_eligibility_contract_for_model_only(df, fake)


def test_validator_ineligible_marker(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("NBA_ALLOW_LEGACY_NO_ELIGIBILITY", raising=False)
    df = pd.DataFrame([_full_stat_grid_like_row(player_game_eligible=False)])
    fake = tmp_path / "p.parquet"
    with pytest.raises(SystemExit, match="MODEL_ONLY_INELIGIBLE_ROWS_PRESENT"):
        _validate_eligibility_contract_for_model_only(df, fake)


def test_eligibility_join_source_missing_when_gap_and_no_file(tmp_path: Path):
    sparse = pd.DataFrame(
        [{"game_id": 90001, "player_id": 123, "stat": "pts"}]
    )
    sparse = _inject_slate_date(sparse, "2026-06-02")
    sparse = _require_join_keys(sparse)
    with pytest.raises(SystemExit, match="MODEL_ONLY_ELIGIBILITY_JOIN_SOURCE_MISSING"):
        merge_eligibility_minutes_into_model_only(
            sparse,
            delivery_date="2026-06-02",
            repo_root=tmp_path,
        )


def test_merge_joins_sparse_stat_grid(tmp_path: Path):
    elig_p = tmp_path / "eligible.parquet"
    pd.DataFrame([_eligible_row()]).to_parquet(elig_p, index=False)
    grid = pd.DataFrame([{"game_id": 90001, "player_id": 123, "stat": "pts"}])
    grid = _inject_slate_date(grid, "2026-06-02")
    grid = _require_join_keys(grid)
    out = merge_eligibility_minutes_into_model_only(
        grid,
        delivery_date="2026-06-02",
        repo_root=tmp_path,
        minutes_eligible_path=elig_p,
    )
    assert float(out["minutes_std"].iloc[0]) == 6.0
    assert bool(out["player_game_eligible"].iloc[0]) is True


def test_merge_eligible_q_aliases_and_role_bucket_fallback(tmp_path: Path):
    row = _eligible_row()
    del row["projected_role"]
    row["minutes_q10"] = row.pop("minutes_p10")
    row["minutes_q50"] = row.pop("minutes_p50")
    row["minutes_q90"] = row.pop("minutes_p90")
    row["role_bucket"] = "rotation"
    elig_p = tmp_path / "eligible.parquet"
    pd.DataFrame([row]).to_parquet(elig_p, index=False)
    grid = pd.DataFrame([{"game_id": 90001, "player_id": 123, "stat": "pts"}])
    grid = _inject_slate_date(grid, "2026-06-02")
    grid = _require_join_keys(grid)
    out = merge_eligibility_minutes_into_model_only(
        grid,
        delivery_date="2026-06-02",
        repo_root=tmp_path,
        minutes_eligible_path=elig_p,
    )
    assert "minutes_p50" in out.columns
    assert str(out["projected_role"].iloc[0]) == "rotation"


def test_publish_schema_preflight_after_merge(tmp_path: Path):
    elig_p = tmp_path / "eligible.parquet"
    pd.DataFrame([_eligible_row(game_id=1, player_id=2)]).to_parquet(elig_p, index=False)
    bare = pd.DataFrame([{"game_id": 1, "player_id": 2, "stat": "pts"}])
    bare = _inject_slate_date(bare, "2026-06-02")
    bare = _require_join_keys(bare)
    enr = merge_eligibility_minutes_into_model_only(
        bare,
        delivery_date="2026-06-02",
        repo_root=tmp_path,
        minutes_eligible_path=elig_p,
    )
    for c in MODEL_ONLY_PUBLISH_COLUMNS:
        assert c in enr.columns
    fake = Path("/tmp/nonexistent_audit_only.parquet")
    _assert_publish_schema_preflight(enr, fake)


def test_skip_eligible_read_when_stat_grid_has_full_contract(tmp_path: Path):
    """No eligible parquet on disk — merge path skipped when stat-grid is complete."""
    row = _full_stat_grid_like_row()
    df = pd.DataFrame([row])
    df = _normalize_minutes_q_to_p_aliases(df)
    df = _inject_slate_date(df, "2026-06-02")
    df = _require_join_keys(df)
    out = merge_eligibility_minutes_into_model_only(
        df,
        delivery_date="2026-06-02",
        repo_root=tmp_path,
    )
    assert float(out["minutes_p50"].iloc[0]) == 30.0


def test_dual_parquet_writes_share_identical_schema(tmp_path: Path):
    elig_p = tmp_path / "eligible.parquet"
    pd.DataFrame([_eligible_row()]).to_parquet(elig_p, index=False)
    grid = pd.DataFrame([{"game_id": 90001, "player_id": 123, "stat": "pts"}])
    grid = _inject_slate_date(grid, "2026-06-02")
    grid = _require_join_keys(grid)
    df = merge_eligibility_minutes_into_model_only(
        grid,
        delivery_date="2026-06-02",
        repo_root=tmp_path,
        minutes_eligible_path=elig_p,
    )
    p1 = tmp_path / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    p2 = tmp_path / "all_props_model_only.parquet"
    df.to_parquet(p1, index=False)
    df.to_parquet(p2, index=False)
    r1 = pd.read_parquet(p1)
    r2 = pd.read_parquet(p2)
    assert list(r1.columns) == list(r2.columns)
    assert len(r1) == len(r2)


def test_explicit_model_only_path_skips_all_props_rebuild_documented():
    """Regression guard: build_daily reads explicit --model-only without rebuilding."""
    src = (SCRIPTS / "build_daily_pmf_delivery.py").read_text(encoding="utf-8")
    assert "--model-only" in src
    assert "build_canonical_from_predictions" in src
