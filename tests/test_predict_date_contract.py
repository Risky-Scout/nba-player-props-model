"""Pipeline-level date-contract for predict + feature snapshot preconditions."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pd = pytest.importorskip("pandas")

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_orchestrator():
    p = REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py"
    spec = importlib.util.spec_from_file_location("run_daily_delivery_pipeline_mod", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _load_orchestrator()


def test_predict_uses_scripts_wrapper_with_explicit_date(mod):
    """Regression: pipeline must call ``scripts/predict.py``, not the
    pipelines module, because that module's __main__ silently drops
    CLI flags. ``--date <delivery_date>`` must be present in the cmd."""
    assert mod.PREDICT == REPO_ROOT / "scripts" / "predict.py"

    captured = {}

    def fake_run(cmd, *, allow_fail, label):
        captured["cmd"] = list(cmd)
        captured["label"] = label
        return 0

    with patch.object(mod, "_run", side_effect=fake_run):
        mod._predict("2026-05-15")

    assert captured["cmd"][1] == str(REPO_ROOT / "scripts" / "predict.py")
    assert "--date" in captured["cmd"]
    di = captured["cmd"].index("--date")
    assert captured["cmd"][di + 1] == "2026-05-15"
    assert captured["label"] == "predict 2026-05-15"


def test_predict_date_contract_pass(mod, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pred = tmp_path / "predictions"
    pred.mkdir()
    (pred / "all_props_2026-05-15.parquet").write_bytes(b"x")
    (pred / "pmf_display_2026-05-15.json").write_text("{}")
    (pred / "singles_2026-05-15.json").write_text("{}")
    mod._assert_predict_date_contract("2026-05-15")
    out = capsys.readouterr().out
    assert "PREDICT_DATE_CONTRACT_PASS date=2026-05-15" in out


def test_predict_date_contract_violation_when_actual_date_is_next_day(
    mod, tmp_path, monkeypatch, capsys
):
    """Forced manual delivery for 2026-05-15 must not silently accept
    a 2026-05-16 no-game artifact pair."""
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pred = tmp_path / "predictions"
    pred.mkdir()
    (pred / "all_props_2026-05-16.parquet").write_bytes(b"x")
    (pred / "pmf_display_2026-05-16.json").write_text("{}")
    (pred / "singles_2026-05-16.json").write_text("{}")

    with pytest.raises(SystemExit) as excinfo:
        mod._assert_predict_date_contract("2026-05-15")

    out = capsys.readouterr().out
    assert "PREDICT_DATE_CONTRACT_VIOLATION" in out
    assert "requested_date=2026-05-15" in out
    assert "actual_logged_or_output_date=2026-05-16" in out
    assert int(excinfo.value.code or 0) != 0


def test_require_feature_snapshot_missing_fails_with_marker(
    mod, tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        mod._require_feature_snapshot(
            date="2026-05-15",
            run_mode_stamp="morning_expected",
            path=None,
        )
    msg = str(excinfo.value)
    assert "FEATURE_SNAPSHOT_MISSING_AFTER_BUILD" in msg
    assert (
        "path=data/features/player_prop_features_2026-05-15_morning_expected.parquet"
        in msg
    )


def test_require_feature_snapshot_empty_fails(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    feat_dir = tmp_path / "data" / "features"
    feat_dir.mkdir(parents=True)
    p = feat_dir / "player_prop_features_2026-05-15_morning_expected.parquet"
    pd.DataFrame({"player_id": []}).to_parquet(p, index=False)
    with pytest.raises(SystemExit) as excinfo:
        mod._require_feature_snapshot(
            date="2026-05-15",
            run_mode_stamp="morning_expected",
            path=p,
        )
    assert "FEATURE_SNAPSHOT_EMPTY" in str(excinfo.value)


def test_require_feature_snapshot_pass_emits_marker(mod, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    feat_dir = tmp_path / "data" / "features"
    feat_dir.mkdir(parents=True)
    p = feat_dir / "player_prop_features_2026-05-15_morning_expected.parquet"
    pd.DataFrame({"player_id": [1, 2, 3]}).to_parquet(p, index=False)
    out = mod._require_feature_snapshot(
        date="2026-05-15",
        run_mode_stamp="morning_expected",
        path=p,
    )
    captured = capsys.readouterr().out
    assert "PLAYER_PROP_FEATURE_SNAPSHOT_PASS" in captured
    assert "rows=3" in captured
    assert out == p
