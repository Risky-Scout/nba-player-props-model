"""Derek forward feed source-contract tests.

The forward feed must always be built from the validated model PMF
surface:

  feature_snapshot
    → minutes_predictions / minutes_predictions_eligible
    → stat_grid (12 mission stats)
    → canonical MODEL_ONLY from stat_grid
    → market_comparison
    → derek_forward_feed   ← here

It must NEVER source model_expected_value / model_probability_over_
market_line / PMF / edge from ``predictions/all_props_*.parquet`` or
from the identity-only pre-canonical slate universe seed. These tests
pin that contract down by exercising the source-contract guard helper
directly (so they stay hermetic and do not require a full delivery
build).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_derek_feed_module(monkeypatch, repo_root: Path):
    """Reload the script module with REPO_ROOT patched to ``repo_root``.

    The module computes REPO_ROOT relative to its own file location at
    import time, so we monkey-patch it after the fact and verify our
    fixture paths line up with the patched root.
    """
    spec = importlib.util.spec_from_file_location(
        "_build_derek_forward_feed_under_test",
        SCRIPTS / "build_derek_forward_feed.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    return mod


def _layout_lineage_files(repo_root: Path, date: str) -> tuple[Path, Path, Path]:
    """Materialize stub canonical/stat-grid/market_comparison files."""
    canonical = (
        repo_root
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    review_pkg_model_only = (
        repo_root
        / "deliveries"
        / date
        / "pmf_model_review_package"
        / "machine_readable"
        / "model_only.parquet"
    )
    stat_grid = repo_root / "predictions" / f"stat_grid_{date}.parquet"
    market_comparison = (
        repo_root / "deliveries" / date / "wizard_of_odds" / "market_comparison.parquet"
    )
    for p in (canonical, review_pkg_model_only, stat_grid, market_comparison):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"")
    return review_pkg_model_only, market_comparison, canonical


def test_source_contract_pass_emits_marker_and_lineage(tmp_path, monkeypatch, capsys):
    date = "2026-05-16"
    mod = _load_derek_feed_module(monkeypatch, tmp_path)
    model_only_path, market_comparison_path, _ = _layout_lineage_files(tmp_path, date)

    lineage = mod._assert_derek_feed_source_contract(
        date=date,
        model_only_path=model_only_path,
        market_comparison_path=market_comparison_path,
    )
    out = capsys.readouterr().out
    assert "DEREK_FORWARD_FEED_SOURCE_CONTRACT_PASS" in out
    assert lineage["model_source_contract"] == "stat_grid_canonical_market_comparison"
    assert lineage["model_source"].endswith("model_only.parquet")
    assert lineage["canonical_source"].endswith(
        "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    assert lineage["stat_grid_source"].endswith(f"stat_grid_{date}.parquet")
    assert lineage["market_comparison_source"].endswith("market_comparison.parquet")


def test_source_contract_violation_when_model_source_is_raw_all_props(tmp_path, monkeypatch, capsys):
    date = "2026-05-16"
    mod = _load_derek_feed_module(monkeypatch, tmp_path)
    _, market_comparison_path, _ = _layout_lineage_files(tmp_path, date)

    bad_model_only = tmp_path / "predictions" / f"all_props_{date}.parquet"
    bad_model_only.parent.mkdir(parents=True, exist_ok=True)
    bad_model_only.write_bytes(b"")

    with pytest.raises(SystemExit) as ex:
        mod._assert_derek_feed_source_contract(
            date=date,
            model_only_path=bad_model_only,
            market_comparison_path=market_comparison_path,
        )
    err = capsys.readouterr().err
    assert ex.value.code == 2
    assert "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION" in err
    assert "predictions/all_props_" in err


def test_source_contract_violation_when_model_source_is_precanonical_seed(tmp_path, monkeypatch, capsys):
    date = "2026-05-16"
    mod = _load_derek_feed_module(monkeypatch, tmp_path)
    _, market_comparison_path, _ = _layout_lineage_files(tmp_path, date)

    bad_seed = (
        tmp_path / "data" / "features" / f"precanonical_slate_universe_{date}_morning_expected.parquet"
    )
    bad_seed.parent.mkdir(parents=True, exist_ok=True)
    bad_seed.write_bytes(b"")

    with pytest.raises(SystemExit) as ex:
        mod._assert_derek_feed_source_contract(
            date=date,
            model_only_path=bad_seed,
            market_comparison_path=market_comparison_path,
        )
    err = capsys.readouterr().err
    assert ex.value.code == 2
    assert "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION" in err
    assert "precanonical_slate_universe_" in err


def test_source_contract_violation_when_canonical_missing(tmp_path, monkeypatch, capsys):
    """Even if model_only_path looks safe, refuse to build if the
    upstream stat-grid → canonical MODEL_ONLY parquet was never
    written. This prevents a regression where the review-package
    model_only.parquet is stale or hand-crafted."""
    date = "2026-05-16"
    mod = _load_derek_feed_module(monkeypatch, tmp_path)

    model_only_path = (
        tmp_path
        / "deliveries"
        / date
        / "pmf_model_review_package"
        / "machine_readable"
        / "model_only.parquet"
    )
    model_only_path.parent.mkdir(parents=True, exist_ok=True)
    model_only_path.write_bytes(b"")

    with pytest.raises(SystemExit) as ex:
        mod._assert_derek_feed_source_contract(
            date=date,
            model_only_path=model_only_path,
            market_comparison_path=None,
        )
    err = capsys.readouterr().err
    assert ex.value.code == 2
    assert "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION" in err
    assert "canonical_MODEL_ONLY_missing" in err


def test_source_contract_violation_when_stat_grid_missing(tmp_path, monkeypatch, capsys):
    date = "2026-05-16"
    mod = _load_derek_feed_module(monkeypatch, tmp_path)

    canonical = (
        tmp_path
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    model_only_path = (
        tmp_path
        / "deliveries"
        / date
        / "pmf_model_review_package"
        / "machine_readable"
        / "model_only.parquet"
    )
    for p in (canonical, model_only_path):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"")

    with pytest.raises(SystemExit) as ex:
        mod._assert_derek_feed_source_contract(
            date=date,
            model_only_path=model_only_path,
            market_comparison_path=None,
        )
    err = capsys.readouterr().err
    assert ex.value.code == 2
    assert "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION" in err
    assert "stat_grid_parquet_missing" in err


def test_source_contract_violation_when_market_comparison_is_all_props(tmp_path, monkeypatch, capsys):
    date = "2026-05-16"
    mod = _load_derek_feed_module(monkeypatch, tmp_path)
    model_only_path, _, _ = _layout_lineage_files(tmp_path, date)

    bad_mc = tmp_path / "predictions" / f"all_props_{date}.parquet"
    bad_mc.parent.mkdir(parents=True, exist_ok=True)
    bad_mc.write_bytes(b"")

    with pytest.raises(SystemExit) as ex:
        mod._assert_derek_feed_source_contract(
            date=date,
            model_only_path=model_only_path,
            market_comparison_path=bad_mc,
        )
    err = capsys.readouterr().err
    assert ex.value.code == 2
    assert "DEREK_FORWARD_FEED_SOURCE_CONTRACT_VIOLATION" in err
    assert "market_comparison_source" in err


def test_source_contract_forbidden_substrings_match_spec():
    """The forbidden-substring set must continue to cover both
    raw-prediction paths AND the pre-canonical seed path so future
    refactors cannot silently widen the contract."""
    spec = importlib.util.spec_from_file_location(
        "_build_derek_forward_feed_under_test_constants",
        SCRIPTS / "build_derek_forward_feed.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    forbidden = set(mod.DEREK_FEED_FORBIDDEN_SOURCE_SUBSTRINGS)
    assert "predictions/all_props_" in forbidden
    assert "precanonical_slate_universe_" in forbidden
    assert mod.DEREK_FEED_MODEL_SOURCE_CONTRACT == "stat_grid_canonical_market_comparison"
