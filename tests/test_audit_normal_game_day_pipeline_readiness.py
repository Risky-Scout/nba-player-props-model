"""Tests for the normal game-day pipeline readiness audit.

The audit must:

  * pass the workflow_dispatch contract check on the production yaml.
  * hard-fail condition #03 (schedule no-games gate) when BDL says
    games_count == 0 — i.e. the audit refuses to declare game-day
    readiness on a confirmed no-games slate.
  * hard-fail condition #03 when BDL lookup itself fails (None).
  * report status=pending_pipeline_execution on data-dependent
    conditions (feature_snapshot/minutes/stat_grid/canonical/market/
    derek/woo/m86) when their artifacts do not exist yet for the
    target date — this is the pre-flight readiness mode.
  * pass condition #04 (pre-canonical seed scope) because the seed
    module is identity-only and the canonical + Derek builders
    explicitly reject seed sources.
  * pass condition #14 (artifact upload) because the workflow YAML
    contains both core and full upload-artifact steps + the forced-
    manual assertion.
  * lookahead: when --delivery-date is no-games, walk forward and
    pick the next games_count>0 date.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _load_audit_module(monkeypatch=None):
    spec = importlib.util.spec_from_file_location(
        "_audit_normal_game_day_pipeline_readiness_under_test",
        SCRIPTS / "audit_normal_game_day_pipeline_readiness.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ── workflow dispatch ────────────────────────────────────────────────────


def test_cond_01_workflow_dispatch_passes_on_production_yaml():
    mod = _load_audit_module()
    f = mod.cond_01_workflow_dispatch("2026-05-17", "woo_morning_monetization")
    assert f.status == "pass", f"evidence={f.evidence}"
    assert f.marker == "NORMAL_GAME_DAY_WORKFLOW_DISPATCH_CONTRACT_PASS"
    assert f.blocking is False


# ── schedule / no-games gate ─────────────────────────────────────────────


def test_cond_03_hard_fails_when_bdl_returns_zero():
    mod = _load_audit_module()
    f = mod.cond_03_schedule_no_games_gate("2026-05-16", 0, "bdl returned []")
    assert f.status == "fail"
    assert f.blocking is True
    assert "NORMAL_GAME_DAY_SCHEDULE_CONTRACT_FAIL" in (f.marker or "")


def test_cond_03_hard_fails_when_bdl_lookup_fails():
    mod = _load_audit_module()
    f = mod.cond_03_schedule_no_games_gate("2026-05-17", None, "BDL outage")
    assert f.status == "fail"
    assert f.blocking is True


def test_cond_03_passes_when_bdl_has_games():
    mod = _load_audit_module()
    f = mod.cond_03_schedule_no_games_gate("2026-05-19", 8, "bdl returned 8 rows")
    assert f.status == "pass"
    assert f.blocking is False
    assert "NORMAL_GAME_DAY_SCHEDULE_CONTRACT_PASS" in (f.marker or "")
    assert "games_count=8" in (f.marker or "")


# ── pre-canonical seed scope ─────────────────────────────────────────────


def test_cond_04_passes_on_production_codebase():
    mod = _load_audit_module()
    f = mod.cond_04_precanonical_seed_scope("2026-05-17")
    assert f.status == "pass", f"evidence={f.evidence}"
    assert f.evidence["derek_builder_rejects_seed_source"] is True
    assert f.evidence["canonical_builder_rejects_seed_source"] is True


# ── artifact upload contract ─────────────────────────────────────────────


def test_cond_14_artifact_upload_contract_passes_on_production_yaml():
    mod = _load_audit_module()
    f = mod.cond_14_artifact_upload("2026-05-17")
    assert f.status == "pass", f"evidence={f.evidence}"
    assert "CORE_DELIVERY_ARTIFACT_UPLOAD_PASS" in (f.marker or "")
    assert "DELIVERY_ARTIFACT_UPLOAD_PASS" in (f.marker or "")


# ── pending_pipeline_execution semantics ─────────────────────────────────


def test_cond_05_feature_snapshot_pending_when_no_artifacts(tmp_path, monkeypatch):
    """When the audit runs against a tmp REPO_ROOT with no
    pipeline outputs, condition 05 reports
    pending_pipeline_execution (non-blocking) instead of False."""
    mod = _load_audit_module()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    (tmp_path / "data" / "features").mkdir(parents=True)
    f = mod.cond_05_feature_snapshot("2026-05-17")
    assert f.status == "pending_pipeline_execution"
    assert f.blocking is False


def test_cond_07_stat_grid_pending_when_no_artifacts(tmp_path, monkeypatch):
    mod = _load_audit_module()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    (tmp_path / "predictions").mkdir(parents=True)
    f = mod.cond_07_stat_grid("2026-05-17")
    assert f.status == "pending_pipeline_execution"
    assert f.blocking is False


def test_cond_08_canonical_pending_when_no_artifacts(tmp_path, monkeypatch):
    mod = _load_audit_module()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    f = mod.cond_08_canonical_model_only("2026-05-17")
    assert f.status == "pending_pipeline_execution"
    assert f.blocking is False


def test_cond_10_derek_pending_when_no_artifacts(tmp_path, monkeypatch):
    mod = _load_audit_module()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    f = mod.cond_10_derek_forward_feed("2026-05-17")
    assert f.status == "pending_pipeline_execution"
    assert f.blocking is False


# ── games-exist slate with no-games manifest (forbidden) ──────────────────


def test_cond_13_m86_fails_when_no_games_manifest_on_games_exist_slate(
    tmp_path, monkeypatch
):
    """If a deliveries/<date>/manifest.json carries the no-games
    flag on a games-exist slate, M8.6 readiness must hard-fail."""
    mod = _load_audit_module()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    base = tmp_path / "deliveries" / "2026-05-19"
    for d in ("canonical_source", "wizard_of_odds", "derek_forward_feed",
              "pmf_model_review_package"):
        (base / d).mkdir(parents=True, exist_ok=True)
    (base / "manifest.json").write_text(json.dumps({
        "no_games_slate": True,
        "confirmed_no_games_slate": True,
        "reason": "no_games_slate",
    }), encoding="utf-8")
    f = mod.cond_13_m86_verifiers("2026-05-19")
    assert f.status == "fail"
    assert f.blocking is True
    assert "SOFT_SKIP_ON_GAMES_SLATE" in (f.marker or "")


def test_cond_13_m86_fails_on_missing_subdirs_for_games_exist_slate(
    tmp_path, monkeypatch
):
    mod = _load_audit_module()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path, raising=True)
    (tmp_path / "deliveries" / "2026-05-19").mkdir(parents=True)
    f = mod.cond_13_m86_verifiers("2026-05-19")
    assert f.status == "fail"
    assert f.blocking is True
    assert "MISSING_SUBDIRS" in (f.marker or "")


# ── warning classifier ────────────────────────────────────────────────────


def test_cond_15_warning_classification_not_applicable_without_log(tmp_path):
    mod = _load_audit_module()
    f = mod.cond_15_warning_classification("2026-05-19", None)
    assert f.status == "not_applicable"
    assert f.blocking is False


def test_cond_15_warning_classification_passes_on_operational_only(tmp_path):
    mod = _load_audit_module()
    p = tmp_path / "log.txt"
    p.write_text(
        "WARNING: Node.js 16 actions are deprecated\n"
        "WARNING: SFTP_HOST not set; skipping SFTP delivery\n"
        "WARNING: DUNKS_AND_THREES_API_KEY optional; continuing\n",
        encoding="utf-8",
    )
    f = mod.cond_15_warning_classification("2026-05-19", p)
    assert f.status == "pass", f"evidence={f.evidence}"


def test_cond_15_warning_classification_fails_on_forbidden(tmp_path):
    mod = _load_audit_module()
    p = tmp_path / "log.txt"
    p.write_text(
        "WARNING: missing feature snapshot for 2026-05-19\n",
        encoding="utf-8",
    )
    f = mod.cond_15_warning_classification("2026-05-19", p)
    assert f.status == "fail"
    assert f.blocking is True
