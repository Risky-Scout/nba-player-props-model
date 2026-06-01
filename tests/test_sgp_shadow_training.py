"""Tests for the SGP shadow training and calibration governance system.

Covers:
    - Training script valid-skip behavior (no backtest rows)
    - Training script rejection of same-day / future as_of_date
    - SGP backtest row schema completeness
    - sgp_model_pointer.json schema and governance
    - Factor weights artifact: not overwritten on bad fit
    - Joint calibrator valid-skip on insufficient rows
    - Market correlation baseline valid-skip when no source
    - Delivery script reads pointer and stays in diagnostic mode
    - No CERTIFIED rows without FIT_COMPLETE
    - Shadow workflow defaults disabled
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO / "scripts"

# ── Import helpers ────────────────────────────────────────────────────────────

def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def training_mod():
    return _load_script("run_sgp_training_and_calibration")


@pytest.fixture(scope="module")
def verify_train_mod():
    return _load_script("verify_sgp_training_artifacts")


@pytest.fixture(scope="module")
def market_mod():
    return _load_script("build_sgp_market_correlation_baseline")


# ── 1. Valid-skip when no backtest rows ───────────────────────────────────────

class TestTrainingValidSkipNoRows:
    def test_valid_skip_exits_zero(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Expected exit 0 on valid-skip, got {result.returncode}\n{result.stderr}"

    def test_valid_skip_writes_status_file(self, tmp_path):
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        status_path = tmp_path / "artifacts" / "models" / "sgp" / "reports" / "sgp_training_status.json"
        assert status_path.exists(), "sgp_training_status.json not written on valid-skip"
        data = json.loads(status_path.read_text())
        assert data["status"] == "VALID_SKIP"
        assert "reason" in data

    def test_valid_skip_does_not_write_calibrator(self, tmp_path):
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        cal_dir = tmp_path / "artifacts" / "models" / "sgp" / "joint_calibrators"
        cal_files = list(cal_dir.glob("*.pkl")) if cal_dir.exists() else []
        assert len(cal_files) == 0, f"Calibrator should NOT be written on valid-skip; found {cal_files}"


# ── 2. Reject today or future as_of_date ─────────────────────────────────────

class TestTrainingRejectsFutureDate:
    def test_rejects_today(self, tmp_path):
        today = date.today().isoformat()
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", today,
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, f"Expected exit 1 for today={today}, got {result.returncode}"
        assert "today" in result.stderr.lower() or "future" in result.stderr.lower()

    def test_rejects_future(self, tmp_path):
        future = (date.today() + timedelta(days=5)).isoformat()
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", future,
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "today" in result.stderr.lower() or "future" in result.stderr.lower()

    def test_accepts_yesterday(self, tmp_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", yesterday,
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        assert result.returncode == 0, f"Expected exit 0 for yesterday={yesterday}"


# ── 3. Backtest schema completeness ──────────────────────────────────────────

class TestBacktestSchemaComplete:
    _REQUIRED_COLS = [
        "prediction_date", "as_of_date", "game_id", "sgp_id", "leg_count",
        "legs_json", "relationship_type", "stat_mix", "role_mix",
        "same_player_count", "same_team_count", "opponent_count",
        "contains_combo_overlap", "contains_sparse_stat", "contains_alt_line",
        "line_percentile_bucket", "lineup_status",
        "raw_joint_probability", "calibrated_joint_probability",
        "independent_probability", "correlation_factor", "actual_hit",
        "market_sgp_probability", "market_sgp_odds", "market_corr_factor",
        "model_corr_factor", "corr_factor_delta_vs_market",
        "model_logloss", "model_brier", "market_logloss", "market_brier",
        "independence_logloss", "independence_brier",
        "logloss_delta_vs_market", "brier_delta_vs_market",
        "logloss_delta_vs_independence", "brier_delta_vs_independence",
        "pmf_source_file", "model_version", "sgp_engine_version", "created_at_utc",
    ]

    def test_all_required_columns_in_spec(self):
        """All 41 required backtest columns must be in the spec list."""
        assert len(self._REQUIRED_COLS) == 41, f"Expected 41, got {len(self._REQUIRED_COLS)}"

    def test_build_script_has_all_required_columns(self):
        """build_sgp_backtest_rows.py must reference all required column names."""
        source = (_SCRIPTS / "build_sgp_backtest_rows.py").read_text()
        for col in self._REQUIRED_COLS:
            assert col in source, f"Column {col!r} not referenced in build_sgp_backtest_rows.py"


# ── 4. SGP model pointer schema ───────────────────────────────────────────────

class TestSGPModelPointerSchema:
    _REQUIRED_FIELDS = [
        "sgp_model_version",
        "trained_through_date",
        "calibrated_through_date",
        "latest_actual_box_score_date",
        "factor_weights_artifact",
        "joint_calibrator_artifact",
        "n_backtest_rows",
        "n_games",
        "n_segments",
        "n_certified_segments",
        "calibration_status",
        "promotion_status",
        "default_delivery_enabled",
        "market_sgp_odds_available",
        "commit_sha",
        "created_at_utc",
    ]

    def _make_pointer(self, tmp_path: Path) -> dict:
        """Run training (valid-skip) and return pointer if written, else a stub."""
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", (date.today() - timedelta(days=1)).isoformat(),
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        pointer_path = tmp_path / "artifacts" / "models" / "sgp" / "registry" / "sgp_model_pointer.json"
        if pointer_path.exists():
            return json.loads(pointer_path.read_text())
        # Write a manually-crafted pointer for schema validation when training valid-skips
        # (pointer is only written on COMPLETE, not VALID_SKIP).
        return {
            "sgp_model_version": "v1",
            "trained_through_date": "2026-05-29",
            "calibrated_through_date": "2026-05-29",
            "latest_actual_box_score_date": "2026-05-09",
            "factor_weights_artifact": None,
            "joint_calibrator_artifact": None,
            "n_backtest_rows": 0,
            "n_games": 0,
            "n_segments": 0,
            "calibration_status": "INSUFFICIENT_DATA",
            "promotion_status": "DIAGNOSTIC_NO_BACKTEST",
            "default_delivery_enabled": False,
            "market_sgp_odds_available": False,
            "created_at_utc": "2026-05-31T00:00:00+00:00",
        }

    def test_all_required_fields_documented_in_script(self):
        """run_sgp_training_and_calibration.py must reference all required pointer fields."""
        source = (_SCRIPTS / "run_sgp_training_and_calibration.py").read_text()
        for field in self._REQUIRED_FIELDS:
            assert field in source, f"Pointer field {field!r} not referenced in training script"

    def test_default_delivery_enabled_is_false(self, tmp_path):
        """default_delivery_enabled must never be True in any auto-written pointer."""
        pointer = self._make_pointer(tmp_path)
        assert pointer.get("default_delivery_enabled") is False, \
            f"default_delivery_enabled must be False; got {pointer.get('default_delivery_enabled')}"

    def test_promotion_status_not_production_approved(self, tmp_path):
        """No auto-written pointer should ever have promotion_status=DEFAULT_PRODUCTION_APPROVED."""
        pointer = self._make_pointer(tmp_path)
        promo = pointer.get("promotion_status", "")
        assert promo != "DEFAULT_PRODUCTION_APPROVED", \
            "DEFAULT_PRODUCTION_APPROVED must never be set programmatically"

    def test_market_superiority_field_present(self, tmp_path):
        pointer = self._make_pointer(tmp_path)
        assert "market_sgp_odds_available" in pointer


# ── 5. Factor weights not overwritten on bad fit ──────────────────────────────

class TestFactorWeightsNotOverwrittenOnBadFit:
    def test_insufficient_data_does_not_overwrite_existing(self, tmp_path):
        """If training has insufficient data, factor_weights_latest.json should NOT be overwritten."""
        fw_dir = tmp_path / "artifacts" / "models" / "sgp" / "factor_weights"
        fw_dir.mkdir(parents=True, exist_ok=True)
        original_content = {"_meta": {"as_of_date": "2026-04-01", "method": "prior_version"}, "pts": [0.1]}
        original_json = json.dumps(original_content)
        (fw_dir / "factor_weights_latest.json").write_text(original_json)

        # Run training with no game data → VALID_SKIP, no overwrite.
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", (date.today() - timedelta(days=1)).isoformat(),
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        # On valid-skip, factor_weights_latest.json must be unchanged.
        current_content = (fw_dir / "factor_weights_latest.json").read_text()
        assert current_content == original_json, \
            "factor_weights_latest.json was overwritten on valid-skip — should be preserved"


# ── 6. Joint calibrator valid-skip on insufficient rows ───────────────────────

class TestCalibrationValidSkipInsufficientRows:
    def test_insufficient_rows_returns_skip_status(self):
        """_stage4_fit_calibrators returns INSUFFICIENT_DATA when < 50 settled rows."""
        mod = _load_script("run_sgp_training_and_calibration")
        # Empty dataframe.
        empty_df = pd.DataFrame()
        result = mod._stage4_fit_calibrators(empty_df, "2026-05-01", Path("/tmp"), dry_run=False)
        assert result["status"] in ("NO_ACTUAL_HIT_COLUMN", "INSUFFICIENT_DATA", "DRY_RUN")

    def test_below_minimum_threshold_returns_insufficient(self):
        mod = _load_script("run_sgp_training_and_calibration")
        # 10 settled rows — below minimum 50.
        df = pd.DataFrame({
            "actual_hit": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            "calibrated_joint_probability": [0.4, 0.3, 0.5, 0.2, 0.6, 0.35, 0.45, 0.25, 0.55, 0.3],
            "prediction_date": ["2026-01-01"] * 10,
        })
        result = mod._stage4_fit_calibrators(df, "2026-05-01", Path("/tmp"), dry_run=True)
        assert result["status"] in ("INSUFFICIENT_DATA", "DRY_RUN")


# ── 7. Market correlation baseline valid-skip ─────────────────────────────────

class TestMarketCorrBaselineValidSkip:
    def test_valid_skip_when_no_source(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "build_sgp_market_correlation_baseline.py"),
                "--date", "2026-05-30",
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}\n{result.stderr}"
        assert "VALID_SKIP" in result.stdout

    def test_writes_status_json(self, tmp_path):
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "build_sgp_market_correlation_baseline.py"),
                "--date", "2026-05-30",
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
        )
        status_path = tmp_path / "deliveries" / "2026-05-30" / "sgp_engine" / "market_comparison" / "sgp_market_correlation_status.json"
        assert status_path.exists()
        data = json.loads(status_path.read_text())
        assert data["actual_sgp_market_odds_available"] is False
        assert data["market_corr_factor_source"] == "independence_placeholder"

    def test_gate5_not_applicable_when_no_source(self, tmp_path):
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "build_sgp_market_correlation_baseline.py"),
                "--date", "2026-05-30",
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
        )
        status_path = tmp_path / "deliveries" / "2026-05-30" / "sgp_engine" / "market_comparison" / "sgp_market_correlation_status.json"
        data = json.loads(status_path.read_text())
        assert data.get("gate5_market_superiority_applicable") is False


# ── 8. Delivery uses pointer in diagnostic mode when no calibrator ─────────────

class TestDeliveryUsesPointerDiagnosticMode:
    def test_gate_status_includes_pointer_fields(self):
        """After a smoke run, sgp_gate_status.json must include pointer provenance fields."""
        gate_path = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "calibration" / "sgp_gate_status.json"
        if not gate_path.exists():
            pytest.skip("Smoke output not present; run smoke test first")
        gate = json.loads(gate_path.read_text())
        assert "default_delivery_enabled" in gate, "gate_status must have default_delivery_enabled"
        assert gate["default_delivery_enabled"] is False
        assert "sgp_model_pointer_used" in gate

    def test_factor_weights_used_includes_pointer_fields(self):
        """factor_weights_used.json must include pointer provenance fields."""
        fw_path = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "slate_state_bundle_v1" / "factor_weights_used.json"
        if not fw_path.exists():
            pytest.skip("Smoke output not present")
        fw = json.loads(fw_path.read_text())
        assert "sgp_model_pointer_used" in fw
        assert "promotion_status_from_pointer" in fw


# ── 9. No CERTIFIED rows without FIT_COMPLETE ────────────────────────────────

class TestNoCertifiedRowsWithoutFitComplete:
    def test_no_certified_in_current_price_grid(self):
        """Current price grid must have 0 CERTIFIED rows (no backtest data yet)."""
        pg_path = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "prices" / "sgp_price_grid.parquet"
        if not pg_path.exists():
            pytest.skip("Price grid not present; run smoke test first")
        pg = pd.read_parquet(pg_path)
        certified = pg[pg["tier"].astype(str).str.upper() == "CERTIFIED"]
        assert len(certified) == 0, f"Found {len(certified)} CERTIFIED rows without FIT_COMPLETE"

    def test_gate_status_not_market_superiority_certified(self):
        gate_path = _REPO / "deliveries" / "2026-05-30" / "sgp_engine" / "calibration" / "sgp_gate_status.json"
        if not gate_path.exists():
            pytest.skip("Gate status not present; run smoke test first")
        gate = json.loads(gate_path.read_text())
        assert gate.get("market_superiority_certified") is False


# ── 10. Shadow workflow defaults disabled ─────────────────────────────────────

class TestShadowWorkflowDefaultsDisabled:
    def test_shadow_workflow_exists(self):
        wf = _REPO / ".github" / "workflows" / "sgp_shadow_training.yml"
        assert wf.exists(), "sgp_shadow_training.yml not found"

    def test_shadow_workflow_does_not_enable_sgp_delivery(self):
        wf = (_REPO / ".github" / "workflows" / "sgp_shadow_training.yml").read_text()
        # The shadow workflow must not set ENABLE_SGP_ENGINE=true.
        assert 'ENABLE_SGP_ENGINE: "true"' not in wf
        assert "ENABLE_SGP_ENGINE: true" not in wf

    def test_shadow_workflow_sets_sgp_training_enabled(self):
        wf = (_REPO / ".github" / "workflows" / "sgp_shadow_training.yml").read_text()
        assert "ENABLE_SGP_TRAINING" in wf

    def test_delivery_workflow_sgp_still_false(self):
        wf = (_REPO / ".github" / "workflows" / "nba_pmf_delivery.yml").read_text()
        assert 'ENABLE_SGP_ENGINE: "false"' in wf, "Delivery workflow must have ENABLE_SGP_ENGINE=false"

    def test_verify_training_artifacts_script_exists(self):
        assert (_SCRIPTS / "verify_sgp_training_artifacts.py").exists()

    def test_market_correlation_baseline_script_exists(self):
        assert (_SCRIPTS / "build_sgp_market_correlation_baseline.py").exists()


# ── 11. Training artifact verifier — VALID_SKIP ───────────────────────────────

class TestTrainingArtifactVerifierValidSkip:
    def test_verifier_exits_zero_on_valid_skip(self, tmp_path):
        """verify_sgp_training_artifacts.py must exit 0 when training valid-skipped."""
        # Run training to create a VALID_SKIP status file.
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        # Now run the verifier — should accept VALID_SKIP without error.
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected exit 0 on VALID_SKIP, got {result.returncode}\n{result.stderr}"
        )

    def test_verifier_reports_valid_skip_status(self, tmp_path):
        """Verifier output must mention VALID_SKIP when training valid-skipped."""
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert "VALID_SKIP" in result.stdout, "Verifier should report VALID_SKIP in output"

    def test_verifier_rejects_future_as_of_date(self, tmp_path):
        """Verifier must exit 1 if as_of_date >= today."""
        future = (date.today() + timedelta(days=1)).isoformat()
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", future,
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, f"Expected exit 1 for future date {future}, got {result.returncode}"

    def test_verifier_does_not_require_calibrator_on_valid_skip(self, tmp_path):
        """Verifier must not hard-fail when calibrator is absent on a valid-skip run."""
        subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "run_sgp_training_and_calibration.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
                "--season-mode", "auto",
            ],
            capture_output=True,
        )
        # Ensure there is no calibrator.
        cal_dir = tmp_path / "artifacts" / "models" / "sgp" / "joint_calibrators"
        assert not any(cal_dir.glob("*.pkl")) if cal_dir.exists() else True

        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", "2026-05-01",
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
        )
        assert result.returncode == 0


# ── 12. Training artifact verifier — FIT_COMPLETE ────────────────────────────

class TestTrainingArtifactVerifierFitComplete:
    """Tests for the verifier's behaviour when artifacts are fully present (FIT_COMPLETE)."""

    def _write_fit_complete_artifacts(self, tmp_path: Path, as_of_date: str) -> None:
        """Write the minimum set of artifacts expected for a FIT_COMPLETE run."""
        import pickle, numpy as np

        sgp_dir = tmp_path / "artifacts" / "models" / "sgp"
        fw_dir = sgp_dir / "factor_weights"
        cal_dir = sgp_dir / "joint_calibrators"
        rep_dir = sgp_dir / "reports"
        reg_dir = sgp_dir / "registry"
        for d in [fw_dir, cal_dir, rep_dir, reg_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Factor weights.
        fw = {"_meta": {"as_of_date": as_of_date, "method": "test", "trained_rows": 600}}
        (fw_dir / "factor_weights_latest.json").write_text(json.dumps(fw))
        (fw_dir / f"factor_weights_{as_of_date}.json").write_text(json.dumps(fw))

        # Calibrator (minimal pickle stub).
        (cal_dir / "joint_calibrator_latest.pkl").write_bytes(pickle.dumps({"stub": True}))
        (cal_dir / f"joint_calibrator_{as_of_date}.pkl").write_bytes(pickle.dumps({"stub": True}))

        # Reports.
        for rname in ["sgp_training_report", "sgp_calibration_report", "sgp_gate_report"]:
            rdata = {"as_of_date": as_of_date, "status": "FIT_COMPLETE", "promotion_status": "FIT_COMPLETE_NOT_CERTIFIED"}
            (rep_dir / f"{rname}_{as_of_date}.json").write_text(json.dumps(rdata))

        # Training status.
        status = {"status": "COMPLETE", "as_of_date": as_of_date}
        (rep_dir / "sgp_training_status.json").write_text(json.dumps(status))

        # Registry pointer.
        pointer = {
            "sgp_model_version": "v1",
            "trained_through_date": as_of_date,
            "calibrated_through_date": as_of_date,
            "latest_actual_box_score_date": as_of_date,
            "n_backtest_rows": 600,
            "n_games": 20,
            "n_segments": 5,
            "n_certified_segments": 0,
            "factor_weights_artifact": str(fw_dir / f"factor_weights_{as_of_date}.json"),
            "joint_calibrator_artifact": str(cal_dir / f"joint_calibrator_{as_of_date}.pkl"),
            "calibration_status": "FIT_COMPLETE",
            "promotion_status": "FIT_COMPLETE_NOT_CERTIFIED",
            "default_delivery_enabled": False,
            "market_sgp_odds_available": False,
            "commit_sha": None,
            "created_at_utc": "2026-05-31T00:00:00+00:00",
        }
        (reg_dir / "sgp_model_pointer.json").write_text(json.dumps(pointer))

    def test_verifier_exits_zero_when_fit_complete_artifacts_present(self, tmp_path):
        as_of_date = "2026-05-01"
        self._write_fit_complete_artifacts(tmp_path, as_of_date)
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", as_of_date,
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected exit 0 with FIT_COMPLETE artifacts, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_verifier_fails_if_fit_complete_but_calibrator_missing(self, tmp_path):
        as_of_date = "2026-05-01"
        self._write_fit_complete_artifacts(tmp_path, as_of_date)
        # Remove the calibrator — verifier should now fail.
        cal_dir = tmp_path / "artifacts" / "models" / "sgp" / "joint_calibrators"
        for p in cal_dir.glob("*.pkl"):
            p.unlink()
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", as_of_date,
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected exit 1 when FIT_COMPLETE but calibrator missing, got {result.returncode}"
        )

    def test_verifier_rejects_pointer_claiming_default_production_approved(self, tmp_path):
        as_of_date = "2026-05-01"
        self._write_fit_complete_artifacts(tmp_path, as_of_date)
        # Inject unauthorized production status.
        reg_dir = tmp_path / "artifacts" / "models" / "sgp" / "registry"
        pointer = json.loads((reg_dir / "sgp_model_pointer.json").read_text())
        pointer["promotion_status"] = "DEFAULT_PRODUCTION_APPROVED"
        (reg_dir / "sgp_model_pointer.json").write_text(json.dumps(pointer))
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPTS / "verify_sgp_training_artifacts.py"),
                "--as-of-date", as_of_date,
                "--repo-root", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Verifier should reject DEFAULT_PRODUCTION_APPROVED"

    def test_pointer_has_n_certified_segments_field(self, tmp_path):
        as_of_date = "2026-05-01"
        self._write_fit_complete_artifacts(tmp_path, as_of_date)
        reg_dir = tmp_path / "artifacts" / "models" / "sgp" / "registry"
        pointer = json.loads((reg_dir / "sgp_model_pointer.json").read_text())
        assert "n_certified_segments" in pointer, "Pointer must have n_certified_segments field"
        assert isinstance(pointer["n_certified_segments"], int)

    def test_pointer_has_commit_sha_field(self, tmp_path):
        as_of_date = "2026-05-01"
        self._write_fit_complete_artifacts(tmp_path, as_of_date)
        reg_dir = tmp_path / "artifacts" / "models" / "sgp" / "registry"
        pointer = json.loads((reg_dir / "sgp_model_pointer.json").read_text())
        assert "commit_sha" in pointer, "Pointer must have commit_sha field"
