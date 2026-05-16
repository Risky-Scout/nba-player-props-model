"""Feature snapshot pre-canonical seed precedence tests.

Hardens the rule that:

  * Canonical MODEL_ONLY is always preferred when present.
  * The pre-canonical seed is only consulted as a fallback, only when
    the caller passes it explicitly. Generic callers never pick it up.
  * Both inputs ultimately produce a non-empty feature snapshot — i.e.
    the early-ordering bug (``SAME_DAY_SOURCE_INPUTS_MISSING``) is
    fixed when the orchestrator passes the seed path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nba_props_model.features.asof_feature_store import (  # noqa: E402
    MissingSourceInputsError,
    _load_base_universe,
    build_feature_snapshot,
)
from nba_props_model.features.player_prop_feature_contract import RunMode  # noqa: E402


def _write_canonical(repo_root: Path, date: str, df: pd.DataFrame) -> Path:
    out = repo_root / "deliveries" / date / "canonical_source"
    out.mkdir(parents=True, exist_ok=True)
    p = out / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    df.to_parquet(p, index=False)
    return p


def _write_seed(repo_root: Path, date: str, df: pd.DataFrame) -> Path:
    out = repo_root / "data" / "features"
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"precanonical_slate_universe_{date}_morning_expected.parquet"
    df.to_parquet(p, index=False)
    return p


def test_load_base_universe_prefers_canonical_over_seed(tmp_path):
    date = "2026-05-16"
    canonical_df = pd.DataFrame(
        [{"slate_date": date, "player_id": 1, "game_id": 10, "marker": "from_canonical"}]
    )
    seed_df = pd.DataFrame(
        [{"slate_date": date, "player_id": 1, "game_id": 10, "marker": "from_seed"}]
    )
    _write_canonical(tmp_path, date, canonical_df)
    seed_path = _write_seed(tmp_path, date, seed_df)

    result = _load_base_universe(tmp_path, date, precanonical_seed_path=seed_path)
    assert "marker" in result.columns
    assert result["marker"].iloc[0] == "from_canonical"


def test_load_base_universe_uses_seed_only_when_canonical_missing(tmp_path):
    date = "2026-05-16"
    seed_df = pd.DataFrame(
        [{"slate_date": date, "player_id": 1, "game_id": 10, "marker": "from_seed"}]
    )
    seed_path = _write_seed(tmp_path, date, seed_df)
    result = _load_base_universe(tmp_path, date, precanonical_seed_path=seed_path)
    assert result["marker"].iloc[0] == "from_seed"


def test_load_base_universe_ignores_seed_unless_explicit(tmp_path):
    """The seed must NOT become a general fallback. Without the explicit
    ``precanonical_seed_path`` argument, generic callers still see an
    empty DataFrame on a clean slate, which raises
    ``SAME_DAY_SOURCE_INPUTS_MISSING`` upstream."""
    date = "2026-05-16"
    seed_df = pd.DataFrame(
        [{"slate_date": date, "player_id": 1, "game_id": 10, "marker": "from_seed"}]
    )
    _write_seed(tmp_path, date, seed_df)
    result = _load_base_universe(tmp_path, date)
    assert result.empty


def test_build_feature_snapshot_runs_when_only_seed_present(tmp_path):
    date = "2026-05-16"
    seed_df = pd.DataFrame(
        [
            {"slate_date": date, "player_id": 1, "game_id": 10, "team_id": 101},
            {"slate_date": date, "player_id": 2, "game_id": 10, "team_id": 101},
            {"slate_date": date, "player_id": 3, "game_id": 11, "team_id": 102},
        ]
    )
    seed_path = _write_seed(tmp_path, date, seed_df)

    result = build_feature_snapshot(
        tmp_path,
        date,
        RunMode("morning_expected"),
        precanonical_seed_path=seed_path,
    )
    assert result.metadata["n_rows"] == 3
    snap = result.snapshot
    assert {"player_id", "game_id"} <= set(snap.columns)
    # The seed never carried PMFs / model probabilities / market edges; if
    # any of those leaked through, that would mean the snapshot consumed
    # a forbidden field as a base-universe column.
    for forbidden in (
        "pmf",
        "model_p_over",
        "model_p_under",
        "edge",
        "market_no_vig_over_prob",
    ):
        assert forbidden not in snap.columns or snap[forbidden].isna().all()


def test_build_feature_snapshot_without_seed_or_canonical_raises(tmp_path):
    with pytest.raises(MissingSourceInputsError) as exc:
        build_feature_snapshot(tmp_path, "2026-05-16", RunMode("morning_expected"))
    assert "SAME_DAY_SOURCE_INPUTS_MISSING" in str(exc.value)
