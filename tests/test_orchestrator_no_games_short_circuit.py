"""Orchestrator no-games short-circuit tests.

When ``predict.py`` writes its no-games placeholder (``reason ==
"no_games_slate"`` in ``predictions/singles_<date>.json``) the
orchestrator must short-circuit the same-day chain cleanly rather
than letting feature_snapshot / stat_grid / canonical hard-fail on
legitimately empty inputs.

These tests exercise the detection + delivery-package emitter
helpers directly (they live in ``scripts/run_daily_delivery_pipeline.py``)
so the suite stays hermetic and does not require an actual predict
run.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_orchestrator_module(monkeypatch, repo_root: Path):
    spec = importlib.util.spec_from_file_location(
        "_run_daily_delivery_pipeline_under_test",
        SCRIPTS / "run_daily_delivery_pipeline.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "REPO_ROOT", repo_root, raising=True)
    return mod


def _write_no_games_signal(repo_root: Path, date: str) -> Path:
    p = repo_root / "predictions" / f"singles_{date}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"date": date, "reason": "no_games_slate", "picks": []}),
        encoding="utf-8",
    )
    return p


def test_predict_signaled_no_games_slate_detected(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    _write_no_games_signal(tmp_path, "2026-05-16")
    assert mod._predict_signaled_no_games_slate("2026-05-16") == "predictions/singles_2026-05-16.json"


def test_predict_signaled_no_games_slate_returns_none_when_other_reason(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    p = tmp_path / "predictions" / "singles_2026-05-16.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"reason": "odds_api_offline"}), encoding="utf-8")
    assert mod._predict_signaled_no_games_slate("2026-05-16") is None


def test_predict_signaled_no_games_slate_returns_none_when_missing(tmp_path, monkeypatch):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    assert mod._predict_signaled_no_games_slate("2026-05-16") is None


def test_emit_no_games_delivery_package_writes_all_assertion_files(tmp_path, monkeypatch):
    """The workflow's Forced manual delivery outputs assertion checks
    four file paths under deliveries/<date>/. The no-games emitter
    must satisfy all of them so a force-run on a real no-games slate
    finishes without a false-negative failure."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    date = "2026-05-16"
    mod._emit_no_games_delivery_package(date)

    base = tmp_path / "deliveries" / date
    required = [
        base / "manifest.json",
        base / "canonical_source" / "all_props_model_only.parquet",
        base / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet",
        base / "wizard_of_odds" / "market_comparison.parquet",
    ]
    for p in required:
        assert p.is_file(), f"missing required no-games delivery file: {p}"

    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["reason"] == "no_games_slate"
    assert manifest["no_games_slate"] is True
    assert manifest["marker"] == "PIPELINE_SOFT_SKIP_NO_GAMES_SLATE"
    # The Derek forward feed must NOT be fabricated on a no-games slate.
    assert manifest["derek_forward_feed"] is None


def test_emit_no_games_delivery_package_parquets_are_empty_and_flagged(tmp_path, monkeypatch):
    """The no-games delivery files must be schema-shaped but row-empty
    and must carry the explicit ``no_games_slate`` column so anyone
    reading them sees the soft-skip flag (no fabricated PMFs / edges)."""
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    date = "2026-05-16"
    mod._emit_no_games_delivery_package(date)

    base = tmp_path / "deliveries" / date
    canon = pd.read_parquet(base / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet")
    market = pd.read_parquet(base / "wizard_of_odds" / "market_comparison.parquet")
    assert len(canon) == 0
    assert len(market) == 0
    assert "no_games_slate" in canon.columns
    assert "no_games_slate" in market.columns
    # No model surface columns allowed in the canonical placeholder.
    assert "model_prob" in canon.columns  # column exists but empty
    # No fabricated rows means model_prob must NOT be populated.
    assert canon["model_prob"].dropna().empty


def test_short_circuit_emits_marker_and_package_when_no_games(tmp_path, monkeypatch, capsys):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    date = "2026-05-16"
    _write_no_games_signal(tmp_path, date)

    short_circuited = mod._short_circuit_if_no_games(date)
    assert short_circuited is True

    out = capsys.readouterr().out
    assert "PIPELINE_SOFT_SKIP_NO_GAMES_SLATE" in out
    assert f"date={date}" in out
    assert f"package=deliveries/{date}/manifest.json" in out
    assert (tmp_path / "deliveries" / date / "manifest.json").is_file()


def test_short_circuit_returns_false_when_signal_absent(tmp_path, monkeypatch, capsys):
    mod = _load_orchestrator_module(monkeypatch, tmp_path)
    result = mod._short_circuit_if_no_games("2026-05-16")
    assert result is False
    out = capsys.readouterr().out
    assert "PIPELINE_SOFT_SKIP_NO_GAMES_SLATE" not in out
    assert not (tmp_path / "deliveries" / "2026-05-16" / "manifest.json").exists()
