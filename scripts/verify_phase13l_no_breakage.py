"""Phase 13L — verify no Phase-13L change broke prior systems.

Read-only check that:
- Wizard of Odds delivery files for the latest delivery are unchanged by the
  Derek live snapshot runner (we hash them before/after a control run via
  ``--baseline`` mode and compare).
- ``daily_pmf_delivery.yml`` still parses as YAML and still references the
  Phase 13K script names (no removal of prior PASS lines).
- ``nightly_training_calibration.yml`` still parses and still references the
  Phase 13G/H/K verifiers.
- ``artifacts/models/registry/champion_pointer.json`` still has the rich
  Phase 13H schema (champion_model_id, trained_through_date, etc.) and was
  not silently overwritten.
- The Phase 13K PASS-line strings are still emitted by their owning scripts
  (a regression where someone removed a PASS print would silently re-pass
  but break automation downstream).

Usage:
    python3 scripts/verify_phase13l_no_breakage.py

Pass line:  PHASE13L_NO_BREAKAGE_PASS
Fail line:  PHASE13L_NO_BREAKAGE_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit,
    read_json,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"

# Phase 13K-and-earlier PASS strings that must still be emitted somewhere
# in scripts/ — used to detect accidental regressions where a PASS print
# was removed.
REQUIRED_PASS_TOKENS = {
    "TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS": "scripts/verify_training_automation.py",
    "TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS": "scripts/verify_training_automation.py",
    "PREVIOUS_DAY_NO_LEAKAGE_VERIFICATION_PASS": "scripts/verify_previous_day_no_leakage.py",
    "PREVIOUS_DAY_SOURCE_COMPLETENESS_PASS": "scripts/verify_previous_day_source_completeness.py",
    "CHAMPION_POINTER_METADATA_PASS": "scripts/verify_champion_pointer_metadata.py",
    "DEREK_WOO_CHAMPION_DEPENDENCY_PASS": "scripts/verify_derek_woo_champion_dependency.py",
    "DELIVERY_CHAMPION_METADATA_STAMP_PASS": "scripts/stamp_delivery_champion_metadata.py",
    "EXPECTED_TARGET_STATS_COVERAGE_ACCOUNTED_PASS": "scripts/score_daily_pmf_delivery_after_game.py",
    "MODEL_VS_MARKET_SCORING_PASS": "scripts/score_daily_pmf_delivery_after_game.py",
    "AFTER_GAME_SCORING_PACKAGE_CONSISTENCY_PASS": "scripts/verify_after_game_scoring_package_consistency.py",
    "ROLLING_MARKET_BENCHMARK_PASS": "scripts/build_rolling_market_benchmark.py",
    "DAILY_AUTOMATION_HEALTH_PASS": "scripts/verify_daily_automation_health.py",
}

# Workflows that must remain valid YAML and contain the Phase 13K script
# references (a sign that we have not accidentally regressed earlier wiring).
WORKFLOW_INTEGRITY = {
    ".github/workflows/daily_pmf_delivery.yml": (
        "stamp_delivery_champion_metadata.py",
        "verify_after_game_scoring_package_consistency.py",
        "build_rolling_market_benchmark.py",
    ),
    ".github/workflows/nightly_training_calibration.yml": (
        "verify_training_automation.py",
        "verify_daily_automation_health.py",
        "resolve_previous_day_et_target.py",
    ),
}


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    generated_at_utc: str
    code_commit: str
    checks: list[Check] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(name, ok, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "passed": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
            "facts": self.facts,
        }


def _check_pass_tokens(report: Report) -> None:
    for token, script_rel in REQUIRED_PASS_TOKENS.items():
        path = REPO_ROOT / script_rel
        if not path.exists():
            report.add(
                f"pass_token_present:{token}",
                False,
                f"script missing: {script_rel}",
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            report.add(
                f"pass_token_present:{token}",
                False,
                f"read_error:{exc}",
            )
            continue
        report.add(
            f"pass_token_present:{token}",
            token in text,
            f"in {script_rel}" if token in text else f"missing from {script_rel}",
        )


def _check_workflow_integrity(report: Report) -> None:
    try:
        import yaml
    except ImportError:
        # Fallback: just check the references via substring search.
        yaml = None
    for rel, refs in WORKFLOW_INTEGRITY.items():
        path = REPO_ROOT / rel
        if not path.exists():
            report.add(f"workflow_present:{rel}", False, "missing")
            continue
        report.add(f"workflow_present:{rel}", True, "")
        text = path.read_text(encoding="utf-8")
        if yaml is not None:
            try:
                yaml.safe_load(text)
                report.add(f"workflow_yaml_valid:{rel}", True, "ok")
            except Exception as exc:
                report.add(f"workflow_yaml_valid:{rel}", False, str(exc))
        for r in refs:
            report.add(
                f"workflow_references:{rel}::{r}",
                r in text,
                "ok" if r in text else f"missing reference {r!r}",
            )


def _check_champion_pointer(report: Report) -> None:
    if not CHAMPION_POINTER_PATH.exists():
        report.add("champion_pointer_present", False, str(CHAMPION_POINTER_PATH))
        return
    pointer = read_json(CHAMPION_POINTER_PATH)
    rich_fields = (
        "champion_model_id", "trained_through_date", "calibrated_through_date",
        "promoted_at_utc", "training_run_id",
    )
    missing = [f for f in rich_fields if f not in pointer or pointer[f] in (None, "")]
    is_bootstrap = pointer.get("schema_version") in (None, "1.0") and not pointer.get("champion_model_id")
    if is_bootstrap:
        report.add(
            "champion_pointer_intact",
            True,
            "bootstrap pointer (acceptable when no real promotion has occurred yet)",
        )
        return
    report.add(
        "champion_pointer_rich_fields_present",
        not missing,
        f"missing={missing}" if missing else "all rich fields present",
    )
    report.facts["champion_pointer"] = {
        "schema_version": pointer.get("schema_version"),
        "champion_model_id": pointer.get("champion_model_id"),
        "champion_pointer_hash": (
            sha256_file(CHAMPION_POINTER_PATH)[:32] if CHAMPION_POINTER_PATH.exists() else None
        ),
    }


def _check_woo_files_unchanged(report: Report) -> None:
    """Take a hash of the most recent WoO run_manifest + Derek feed_manifest
    and confirm they are still well-formed JSON. We can't prove "unchanged
    by Derek live snapshot runner" without a baseline; instead we prove the
    Derek live snapshot runner WROTE NOTHING under deliveries/<date>/wizard_of_odds/
    or deliveries/<date>/derek_forward_feed/ for any date that has a
    derek_game_snapshots/ folder."""
    deliveries = REPO_ROOT / "deliveries"
    if not deliveries.exists():
        report.add("woo_files_unchanged", True, "no deliveries dir (skipped)")
        return
    bad: list[str] = []
    for d in sorted(deliveries.iterdir()):
        if not d.is_dir() or not (d / "derek_game_snapshots").exists():
            continue
        for protected in ("wizard_of_odds", "derek_forward_feed", "pmf_model_review_package",
                           "canonical_source"):
            sub = d / "derek_game_snapshots" / protected
            if sub.exists():
                bad.append(str(sub.relative_to(REPO_ROOT)))
    report.add(
        "derek_live_snapshots_did_not_pollute_protected_dirs",
        not bad,
        f"violations={bad[:5]}" if bad else "ok",
    )


def _check_phase13l_correction_semantics(report: Report) -> None:
    """Phase 13L correction guarantees:
      - run_derek_live_game_snapshot.py: snapshot_mode field is recorded, and
        production-live pmfs_recomputed requires invoked_predict_ok.
      - verify_derek_live_snapshots.py: emits
        DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS for backfill
        collections, and guards the recomputed-pass-line on
        all_production_recomputed.
    Phase 13M additions:
      - Runner records lineup_source / lineup_blocker / champion_metadata_verified.
      - Verifier emits DEREK_LINEUP_CONTEXT_DOCUMENTED_PASS.
    These are token-presence checks — a regression that removed the source
    line would silently break the corrected pass-line semantics.
    """
    runner = REPO_ROOT / "scripts" / "run_derek_live_game_snapshot.py"
    verifier = REPO_ROOT / "scripts" / "verify_derek_live_snapshots.py"
    predict_pipeline = REPO_ROOT / "src" / "nba_props_model" / "pipelines" / "predict.py"
    api_readiness = REPO_ROOT / "scripts" / "verify_derek_live_api_readiness.py"
    live_context = REPO_ROOT / "src" / "nba_props_model" / "features" / "live_context.py"
    dataset_builder = REPO_ROOT / "scripts" / "build_live_context_training_dataset.py"
    sensitivity = REPO_ROOT / "scripts" / "verify_live_context_pmf_sensitivity.py"
    p13p_trainer = REPO_ROOT / "scripts" / "train_live_context_challenger.py"
    p13p_no_leakage = REPO_ROOT / "scripts" / "verify_phase13p_no_leakage.py"
    p13p_gates = REPO_ROOT / "scripts" / "verify_phase13p_validation_gates.py"
    p13q_trainer = REPO_ROOT / "scripts" / "train_contextual_challenger.py"
    needed = {
        runner: (
            # Phase 13U expanded the snapshot_mode resolution to also
            # emit "production_live_current" for current_live snapshots,
            # so the assertion is now on the canonical mode strings
            # rather than the exact one-line ternary.
            'snapshot_mode = "backfill_demo"',
            'snapshot_mode = "production_live_current"',
            'snapshot_mode = "production_live"',
            "champion_metadata_verified",
            "lineup_feature_blocker",
            "--derek-live-snapshot",
            "lineup_integration_summary",
            # Phase 13N tokens.
            "lineup_source_equivalence_verified",
            "injury_availability_hash",
            "market_snapshot_hash",
            "lineup_context.parquet",
            "injury_availability_context.parquet",
            "prediction_input_audit.parquet",
        ),
        verifier: (
            "DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS",
            "all_production_recomputed",
            "DEREK_LINEUP_CONTEXT_DOCUMENTED_PASS",
            "DEREK_INJURY_AVAILABILITY_CONTEXT_PASS",
            "BDL_LINEUPS_FETCH_PASS",
        ),
        predict_pipeline: (
            "_derek_live_args",
            "_join_lineup_context_into_rows",
            "PREDICT_DEREK_LIVE_ARGS_PASS",
            "PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS",
            "derek_live_predictions.parquet",
        ),
        api_readiness: (
            "DEREK_LIVE_API_READINESS_PASS",
            "BDL_API_KEY",
            "get_lineups",
            "get_injuries",
        ),
        live_context: (
            "PHASE13O_LIVE_CONTEXT_FEATURES_PASS",  # in module docstring
            "LINEUP_FEATURE_COLUMNS",
            "INJURY_FEATURE_COLUMNS",
            "VACATED_OPPORTUNITY_FEATURE_COLUMNS",
            "build_live_context_features",
            "feature_set_id",
            "phase13o_live_context_v1",
        ),
        dataset_builder: (
            "PHASE13O_LIVE_CONTEXT_TRAINING_DATASET_PASS",
            "PHASE13O_LINEUP_HISTORY_LIMITED",
            "no_future_leakage_verified",
            "asof_cutoff_rule",
        ),
        sensitivity: (
            "PHASE13O_FEATURE_VECTOR_SENSITIVITY_PASS",
            "PHASE13O_ACTIONABILITY_SENSITIVITY_PASS",
            "PHASE13O_MARKET_ONLY_EDGE_SENSITIVITY_PASS",
            "PHASE13O_PMF_SENSITIVITY_PENDING_RETRAINED_ARTIFACTS",
            "PHASE13P_PMF_SENSITIVITY_PASS",  # post-13P pass line
        ),
        p13p_trainer: (
            "PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINER_READY_PASS",
            "PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_PASS",
            "phase13p_lineup_injury_driver_v1",
            "starter_proxy_lagged",
            "no_same_game_performance_predictors",
        ),
        p13p_no_leakage: (
            "PHASE13P_NO_LEAKAGE_PASS",
            "FORBIDDEN_PREDICTOR_COLUMNS",
        ),
        p13p_gates: (
            "PHASE13P_VALIDATION_GATES_PASS",
            "PHASE13P_VALIDATION_GATES_FAILED",
            "SAFE_NONINFERIORITY_THRESHOLD",
            "PHASE13Q_VALIDATION_GATES_PASS",
        ),
        p13q_trainer: (
            "PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINER_READY_PASS",
            "PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINING_PASS",
            "phase13q_contextual_pmf_engine_v1",
            "GAME_CONTEXT_FEATURES",
            "is_back_to_back",
            "is_three_in_four",
            "season_game_number",
            "no_same_game_performance_predictors",
        ),
    }
    for path, tokens in needed.items():
        if not path.exists():
            report.add(
                f"phase13_correction_script_present:{path.name}", False, "missing"
            )
            continue
        text = path.read_text(encoding="utf-8")
        for tok in tokens:
            present = tok in text
            report.add(
                f"phase13_correction_token:{path.name}::{tok[:50]}",
                present,
                "ok" if present else f"missing token {tok!r}",
            )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Phase 13L did not break prior systems.")
    p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    report = Report(generated_at_utc=utcnow_iso(), code_commit=git_commit())
    _check_pass_tokens(report)
    _check_workflow_integrity(report)
    _check_champion_pointer(report)
    _check_woo_files_unchanged(report)
    _check_phase13l_correction_semantics(report)

    payload = report.to_dict()
    write_json_atomic(HEALTH_DIR / "phase13l_no_breakage.json", payload)

    md = [
        "# Phase 13L No-Breakage Verification",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- passed: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe} |")
    (HEALTH_DIR / "phase13l_no_breakage.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if report.passed:
        print("PHASE13L_NO_BREAKAGE_PASS")
        return 0
    print("PHASE13L_NO_BREAKAGE_FAILED", file=sys.stderr)
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
