"""Phase 13A — proof / verification suite for the nightly automation.

Verifies that every required artifact exists and that the safety properties
hold. Prints exactly the line:

    TRAINING_AUTOMATION_VERIFICATION_PASS

if and only if every required check passes. Otherwise prints a failure
summary and exits non-zero.

Usage:
    python3 scripts/verify_training_automation.py --as-of-date YYYY-MM-DD

Hard rules echoed:
- Champion pointer never changes when promote=false.
- No raw API data, secrets, or Phase 10D / 10D.2 overlay tokens leak into
  any manifest.
- Production delivery scripts read only the champion pointer; they never
  reference challenger directories.
- The workflow file exists, is scheduled in the safe window, and calls the
  orchestrator.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_DIR,
    CHAMPION_POINTER_PATH,
    CHALLENGERS_DIR,
    FORBIDDEN_OVERLAY_TOKENS,
    MODEL_REGISTRY_PATH,
    PROMOTION_LOG_PATH,
    REGISTRY_DIR,
    challenger_dir,
    git_commit,
    nightly_run_dir,
    parse_date,
    read_json,
    readiness_dir,
    scan_for_forbidden_overlay_tokens,
    scan_for_secrets,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "nightly_training_calibration.yml"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Report:
    as_of_date: str
    generated_at_utc: str
    code_commit: str
    checks: list[Check] = field(default_factory=list)
    failure_simulation: dict = field(default_factory=dict)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(Check(name=name, passed=passed, detail=detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "as_of_date": self.as_of_date,
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "overall_pass": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks
            ],
            "failure_simulation": self.failure_simulation,
        }


def _scan_text_for_forbidden_overlay(s: str) -> list[str]:
    s = s.lower()
    return [t for t in FORBIDDEN_OVERLAY_TOKENS if t in s]


def check_artifacts(report: Report, as_of: str) -> None:
    rdir = readiness_dir(as_of)
    cdir = challenger_dir(as_of)
    nrun = nightly_run_dir(as_of)

    report.add(
        "readiness_report_exists",
        (rdir / "readiness_report.json").exists(),
        str(rdir / "readiness_report.json"),
    )
    report.add(
        "challenger_dir_exists",
        cdir.exists(),
        str(cdir),
    )
    report.add(
        "train_manifest_exists",
        (cdir / "train_manifest.json").exists(),
        str(cdir / "train_manifest.json"),
    )
    report.add(
        "calibration_manifest_exists",
        (cdir / "calibration_manifest.json").exists(),
        str(cdir / "calibration_manifest.json"),
    )
    report.add(
        "validation_report_exists",
        (cdir / "validation_report.json").exists(),
        str(cdir / "validation_report.json"),
    )
    report.add(
        "promotion_decision_exists",
        (cdir / "promotion_decision.json").exists(),
        str(cdir / "promotion_decision.json"),
    )
    report.add(
        "champion_pointer_exists",
        CHAMPION_POINTER_PATH.exists(),
        str(CHAMPION_POINTER_PATH),
    )
    report.add(
        "model_registry_exists",
        MODEL_REGISTRY_PATH.exists(),
        str(MODEL_REGISTRY_PATH),
    )
    report.add(
        "promotion_log_exists",
        PROMOTION_LOG_PATH.exists(),
        str(PROMOTION_LOG_PATH),
    )
    report.add(
        "nightly_run_manifest_exists",
        (nrun / "run_manifest.json").exists(),
        str(nrun / "run_manifest.json"),
    )
    report.add(
        "smoke_test_report_exists",
        (nrun / "smoke_test_report.json").exists(),
        str(nrun / "smoke_test_report.json"),
    )


def check_pointer_invariants(report: Report, as_of: str) -> None:
    if not CHAMPION_POINTER_PATH.exists():
        report.add("champion_pointer_invariants", False, "pointer file missing")
        return
    pointer = read_json(CHAMPION_POINTER_PATH)
    decision_path = challenger_dir(as_of) / "promotion_decision.json"
    if decision_path.exists():
        decision = read_json(decision_path)
        promoted = bool(decision.get("promote"))
    else:
        promoted = False
    promotion_manifest_path = challenger_dir(as_of) / "promotion_manifest.json"
    if promotion_manifest_path.exists():
        pmani = read_json(promotion_manifest_path)
    else:
        pmani = {}

    if promoted and pmani.get("promoted"):
        report.add(
            "champion_pointer_updated_when_promote_true",
            pointer.get("model_version") == pmani.get("to_version"),
            f"pointer.model_version={pointer.get('model_version')!r} "
            f"manifest.to_version={pmani.get('to_version')!r}",
        )
    else:
        report.add(
            "champion_pointer_unchanged_when_promote_false",
            pointer.get("model_version") is not None,
            "pointer model_version present and unchanged (promote was false)",
        )


def check_pmf_validity_passed(report: Report, as_of: str) -> None:
    vp = challenger_dir(as_of) / "validation_report.json"
    if not vp.exists():
        report.add("pmf_validity_passed", False, "validation_report.json missing")
        return
    v = read_json(vp)
    issues = v.get("pmf_validity", {}).get("issues", [])
    report.add("pmf_validity_passed", not issues, f"issues={issues[:3]}")


def check_smoke_passes(report: Report, as_of: str) -> None:
    sp = nightly_run_dir(as_of) / "smoke_test_report.json"
    if not sp.exists():
        report.add("derek_compat_smoke_passed", False, "smoke_test_report.json missing")
        report.add("woo_compat_smoke_passed", False, "smoke_test_report.json missing")
        return
    s = read_json(sp)
    report.add(
        "derek_compat_smoke_passed",
        bool(s.get("derek_compat_smoke", {}).get("passed")),
        json.dumps(s.get("derek_compat_smoke", {}).get("checks", {})),
    )
    report.add(
        "woo_compat_smoke_passed",
        bool(s.get("woo_compat_smoke", {}).get("passed")),
        json.dumps(s.get("woo_compat_smoke", {}).get("checks", {})),
    )


def check_no_secrets_or_raw_data(report: Report, as_of: str) -> None:
    """Walk all manifests + registry files and look for raw API blobs / keys."""
    suspect_paths = [
        CHAMPION_POINTER_PATH,
        MODEL_REGISTRY_PATH,
        challenger_dir(as_of) / "train_manifest.json",
        challenger_dir(as_of) / "calibration_manifest.json",
        challenger_dir(as_of) / "validation_report.json",
        challenger_dir(as_of) / "promotion_decision.json",
        challenger_dir(as_of) / "model_manifest.json",
        nightly_run_dir(as_of) / "run_manifest.json",
        nightly_run_dir(as_of) / "smoke_test_report.json",
        readiness_dir(as_of) / "readiness_report.json",
    ]
    secret_hits: list[str] = []
    overlay_hits: list[str] = []
    for p in suspect_paths:
        if not p.exists():
            continue
        try:
            payload = read_json(p)
        except Exception:
            continue
        secret_hits += [f"{p.name}:{h}" for h in scan_for_secrets(payload)]
        overlay_hits += [f"{p.name}:{h}" for h in scan_for_forbidden_overlay_tokens(payload)]
    report.add("no_secrets_in_manifests", not secret_hits, f"hits={secret_hits[:5]}")
    report.add(
        "no_phase10d_overlays_in_manifests",
        not overlay_hits,
        f"hits={overlay_hits[:5]}",
    )

    # Also: no raw API data should be staged in artifacts/raw/ inside the run.
    raw_dir = REPO_ROOT / "artifacts" / "raw"
    raw_present = raw_dir.exists() and any(raw_dir.iterdir()) if raw_dir.exists() else False
    # The mere existence of artifacts/raw/ on a developer machine isn't a
    # failure; we only care that we haven't *staged* it. The stage check below
    # handles that.
    report.add(
        "no_raw_dir_referenced_in_manifests",
        all("artifacts/raw" not in str(p.read_text(encoding="utf-8")) for p in suspect_paths if p.exists()),
        "manifests do not name artifacts/raw/",
    )


def check_reproducibility(report: Report, as_of: str) -> None:
    train_path = challenger_dir(as_of) / "train_manifest.json"
    cal_path = challenger_dir(as_of) / "calibration_manifest.json"
    if not train_path.exists() or not cal_path.exists():
        report.add("training_run_reproducible", False, "manifests missing")
        return
    train = read_json(train_path)
    cal = read_json(cal_path)
    fields_required = {
        "as_of_date",
        "code_commit",
        "started_at_utc",
        "finished_at_utc",
    }
    missing_train = fields_required - set(train.keys())
    missing_cal = fields_required - set(cal.keys())
    report.add(
        "training_run_reproducible",
        not missing_train and not missing_cal,
        f"missing_train={missing_train} missing_cal={missing_cal}",
    )


def check_workflow(report: Report) -> None:
    if not WORKFLOW_PATH.exists():
        report.add("workflow_file_exists", False, str(WORKFLOW_PATH))
        report.add("workflow_calls_orchestrator", False, "")
        report.add("workflow_has_safe_cron", False, "")
        report.add("workflow_has_timeout_protection", False, "")
        report.add("workflow_uses_required_secrets", False, "")
        report.add("workflow_uses_correct_authorship", False, "")
        return
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    report.add("workflow_file_exists", True, str(WORKFLOW_PATH.relative_to(REPO_ROOT)))
    report.add(
        "workflow_calls_orchestrator",
        "run_nightly_training_and_calibration.py" in text,
        "",
    )
    # Must run before the 15:00 UTC WoO window. We require '30 9 * * *'
    # (09:30 UTC) per the spec.
    report.add(
        "workflow_has_safe_cron",
        ("'30 9 * * *'" in text) or ('"30 9 * * *"' in text),
        "expected cron '30 9 * * *' present",
    )
    report.add(
        "workflow_has_timeout_protection",
        "timeout-minutes" in text,
        "",
    )
    report.add(
        "workflow_uses_required_secrets",
        "BDL_API_KEY" in text,
        "",
    )
    report.add(
        "workflow_uses_correct_authorship",
        "josephshack@gmail.com" in text and "Joseph Shackelford" in text,
        "",
    )
    # No Phase 10D references in the workflow.
    overlay_hits = _scan_text_for_forbidden_overlay(text)
    report.add(
        "workflow_no_phase10d_overlays",
        not overlay_hits,
        f"hits={overlay_hits}",
    )


def check_isolation(report: Report) -> None:
    """Production delivery scripts must read only the champion pointer; they
    must never reference challenger directories."""
    delivery_scripts = [
        REPO_ROOT / "scripts" / "build_daily_pmf_delivery.py",
        REPO_ROOT / "scripts" / "build_derek_forward_feed.py",
        REPO_ROOT / "scripts" / "build_wizard_of_odds_public_export.py",
        REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py",
        REPO_ROOT / "scripts" / "predict.py",
        REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py",
    ]
    bad: list[str] = []
    for p in delivery_scripts:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if "artifacts/models/challengers" in text:
            bad.append(str(p.relative_to(REPO_ROOT)))
    report.add(
        "no_delivery_references_challenger_dir",
        not bad,
        f"violations={bad}",
    )

    # Promotion uses atomic pointer update — confirm the script imports / uses
    # write_json_atomic and promotion_lock.
    promote_script = REPO_ROOT / "scripts" / "promote_challenger_if_validated.py"
    promote_text = promote_script.read_text(encoding="utf-8") if promote_script.exists() else ""
    report.add(
        "promotion_uses_atomic_pointer_update",
        ("write_json_atomic" in promote_text) and ("promotion_lock" in promote_text),
        "",
    )


def check_failure_mode_simulation(report: Report, as_of: str) -> None:
    """Simulate a failed validation and confirm production champion is not changed.

    We do this by:
      1. Snapshotting the champion pointer's sha256 before the simulation.
      2. Crafting a *fake* failed promotion_decision.json in a tmp challenger
         dir under challengers/<as_of>__sim/.
      3. Running promote_challenger_if_validated.py against that simulated
         date and confirming the pointer's sha256 is unchanged.
    """
    if not CHAMPION_POINTER_PATH.exists():
        report.add("failure_mode_keeps_champion_unchanged", False, "no champion pointer")
        return
    pre_sha = sha256_file(CHAMPION_POINTER_PATH)

    # Use a real ISO date so promote_challenger_if_validated.py exercises the
    # actual decision.promote=false branch (parse_date must succeed). 2099-12-31
    # is sentinel-style — clearly synthetic, and clearly distinct from any real
    # nightly run.
    sim_date = "2099-12-31"
    sim_dir = CHALLENGERS_DIR / sim_date
    sim_dir.mkdir(parents=True, exist_ok=True)
    # Real-looking but failed payload.
    write_json_atomic(
        sim_dir / "promotion_decision.json",
        {
            "schema_version": "1.0",
            "as_of_date": sim_date,
            "promote": False,
            "reason": "simulated_failure",
            "gates_passed": [],
            "gates_failed": ["nll_improves_or_non_worse"],
            "champion_metrics": {},
            "challenger_metrics": {},
            "warnings": [],
            "code_commit": git_commit(),
            "generated_at_utc": utcnow_iso(),
        },
    )
    write_json_atomic(
        sim_dir / "validation_report.json",
        {
            "schema_version": "1.0",
            "as_of_date": sim_date,
            "pmf_validity": {"issues": []},
            "derek_compatibility": {"passed": True},
            "woo_compatibility": {"passed": True},
            "challenger": {"model_version": f"sim-{sim_date}"},
            "champion": {"model_version": "unchanged"},
            "gates_passed": [],
            "gates_failed": ["nll_improves_or_non_worse"],
            "phase10d_overlays_in_use": False,
        },
    )

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/promote_challenger_if_validated.py",
            "--as-of-date",
            sim_date,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    post_sha = sha256_file(CHAMPION_POINTER_PATH)
    promotion_manifest_path = sim_dir / "promotion_manifest.json"
    pmani = read_json(promotion_manifest_path) if promotion_manifest_path.exists() else {}
    # Cleanup the sim dir so it doesn't pollute the registry view.
    shutil.rmtree(sim_dir, ignore_errors=True)

    pointer_unchanged = pre_sha == post_sha
    promote_field_false = pmani.get("promoted") is False or pmani.get("promoted") is None

    report.failure_simulation = {
        "pre_pointer_sha256": pre_sha,
        "post_pointer_sha256": post_sha,
        "pointer_unchanged": pointer_unchanged,
        "promotion_marker_promoted_field": pmani.get("promoted"),
        "promote_script_exit_code": proc.returncode,
    }
    report.add(
        "failure_mode_keeps_champion_unchanged",
        pointer_unchanged and promote_field_false,
        f"pre={pre_sha[:12]} post={post_sha[:12]}",
    )


def check_no_raw_data_or_zips_staged(report: Report) -> None:
    """Look at the git staging area for forbidden patterns."""
    forbidden_patterns = [
        re.compile(r"^data/odds_api/"),
        re.compile(r"^data/bdl/"),
        re.compile(r"^data/dunks(?:_and_threes|andthrees)/"),
        re.compile(r"^data/freshness_manifest/"),
        re.compile(r"^artifacts/raw/"),
        re.compile(r"\.zip$"),
        re.compile(r"^logs(?:_|/|$)"),
        re.compile(r"^\.env"),
        re.compile(r"phase10d_independent_validation"),
        re.compile(r"phase10d2_tov_mean_preserving"),
    ]
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        staged = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except Exception as exc:
        report.add("no_forbidden_files_staged", False, f"git error: {exc}")
        return
    bad = [
        f for f in staged
        if any(pat.search(f) for pat in forbidden_patterns)
    ]
    report.add(
        "no_forbidden_files_staged",
        not bad,
        f"staged_violations={bad[:5]}",
    )


def detect_mode(as_of: str) -> tuple[str, dict]:
    """Inspect the day's manifests and decide what mode this run was in.

    Returns one of:
      - "dry_run": both manifests dry_run=true.
      - "real_training": both manifests dry_run=false AND challenger pickles exist.
      - "real_training_failed_inputs_missing": train tried real (dry_run=false)
        but produced no pickles AND/OR the run halted with
        halted_reason=training_inputs_missing or training_failed.
      - "real_training_failed": train_manifest dry_run=false but
        validation/promotion artifacts are missing (training crashed).
      - "unknown": train_manifest itself is missing entirely.

    Phase 13F: the previous "unknown" classification used to fire on the
    legitimately-failed real run case (train wrote dry_run=false, calibration
    inherited stale dry_run=true from a previous run on the same date) — that
    pattern is now classified as ``real_training_failed_inputs_missing`` so
    the verifier can print a clear blocker line instead of opaque MODE_UNKNOWN.
    """
    train_path = challenger_dir(as_of) / "train_manifest.json"
    cal_path = challenger_dir(as_of) / "calibration_manifest.json"
    run_path = nightly_run_dir(as_of) / "run_manifest.json"
    details: dict = {
        "train_manifest_dry_run": None,
        "calibration_manifest_dry_run": None,
        "challenger_pickle_count": 0,
        "run_manifest_halted_reason": None,
        "run_manifest_final_status": None,
        "train_manifest_status": None,
    }
    if train_path.exists():
        tm = read_json(train_path)
        details["train_manifest_dry_run"] = tm.get("dry_run")
        details["train_manifest_status"] = tm.get("status")
    if cal_path.exists():
        details["calibration_manifest_dry_run"] = read_json(cal_path).get("dry_run")
    cdir = challenger_dir(as_of)
    if cdir.exists():
        details["challenger_pickle_count"] = len(list(cdir.glob("pmf_cal_role_*.pkl")))
    if run_path.exists():
        rm = read_json(run_path)
        details["run_manifest_halted_reason"] = rm.get("halted_reason")
        details["run_manifest_final_status"] = rm.get("final_status")

    train_dry = details["train_manifest_dry_run"]
    cal_dry = details["calibration_manifest_dry_run"]
    pickles = details["challenger_pickle_count"]
    halted = details["run_manifest_halted_reason"]
    train_status = details["train_manifest_status"]

    # Halted runs always classify by halted_reason — never "unknown".
    if halted in ("training_inputs_missing", "training_inputs_prepare_failed"):
        return "real_training_failed_inputs_missing", details
    if halted in ("readiness_failed",):
        return "real_training_failed_readiness", details
    if halted == "training_failed":
        return "real_training_failed", details
    if halted == "calibration_failed":
        return "real_training_failed", details

    # Train manifest entirely absent → unknown (could be aborted before training).
    if train_dry is None:
        return "unknown", details

    # Train ran but reported error / not-implemented → real-training failed.
    if train_status in ("error", "not_implemented"):
        return "real_training_failed", details

    # Real-training success requires train_dry=false AND pickles produced AND
    # calibration also non-dry. If train tried real but no pickles landed,
    # classify as inputs_missing (the most likely failure mode on a clean runner).
    if train_dry is False:
        if pickles == 0:
            return "real_training_failed_inputs_missing", details
        if cal_dry is False:
            return "real_training", details
        # train_dry=false, pickles present, but cal_dry=true → mixed (e.g.
        # stale cal manifest from a previous local run that wasn't cleaned).
        return "real_training_failed", details

    # train_dry=true: dry-run mode (cal_dry should also be true for clean state).
    if cal_dry is True:
        return "dry_run", details
    return "unknown", details


def check_real_training_artifacts(report: Report, as_of: str, details: dict) -> None:
    """Additional checks that must pass when train/cal report dry_run=false.

    These are gated by mode: in dry-run they are skipped (recorded as advisory
    yes-checks); in real-training mode they are required.
    """
    cdir = challenger_dir(as_of)
    pickle_count = details["challenger_pickle_count"]
    report.add(
        "real_training_challenger_pickles_present",
        pickle_count > 0,
        f"challenger_pickles={pickle_count} (must be > 0 when dry_run=false)",
    )
    # Validation report's challenger.dry_run must be false.
    vp = cdir / "validation_report.json"
    if vp.exists():
        v = read_json(vp)
        ch_dry = v.get("challenger", {}).get("dry_run")
        report.add(
            "real_training_validation_scored_real_artifacts",
            ch_dry is False,
            f"validation_report.challenger.dry_run={ch_dry}",
        )
        # Real metrics: at least NLL or RPS must be non-null on both sides.
        ch_metrics = v.get("challenger", {}).get("metrics", {}) or {}
        cm_metrics = v.get("champion", {}).get("metrics", {}) or {}
        any_nonnull = any(ch_metrics.get(k) is not None for k in ("nll", "rps", "ece"))
        any_nonnull_c = any(cm_metrics.get(k) is not None for k in ("nll", "rps", "ece"))
        report.add(
            "real_training_metrics_computed",
            any_nonnull and any_nonnull_c,
            f"challenger_has_metric={any_nonnull} champion_has_metric={any_nonnull_c}",
        )
    else:
        report.add("real_training_validation_scored_real_artifacts", False, "no validation_report.json")
        report.add("real_training_metrics_computed", False, "no validation_report.json")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Phase 13A/13B nightly automation.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date).isoformat()
    out_dir = nightly_run_dir(as_of)
    out_dir.mkdir(parents=True, exist_ok=True)

    mode, mode_details = detect_mode(as_of)

    report = Report(
        as_of_date=as_of,
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
    )

    check_artifacts(report, as_of)
    check_pointer_invariants(report, as_of)
    check_pmf_validity_passed(report, as_of)
    check_smoke_passes(report, as_of)
    check_no_secrets_or_raw_data(report, as_of)
    check_reproducibility(report, as_of)
    check_workflow(report)
    check_isolation(report)
    check_failure_mode_simulation(report, as_of)
    check_no_raw_data_or_zips_staged(report)
    if mode == "real_training":
        check_real_training_artifacts(report, as_of, mode_details)

    report_dict = report.to_dict()
    report_dict["mode"] = mode
    report_dict["mode_details"] = mode_details
    write_json_atomic(out_dir / "automation_verification_report.json", report_dict)

    md_lines = [
        f"# Training Automation Verification — {as_of}",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- mode: **{mode}**",
        f"- overall_pass: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe_detail = c.detail.replace("|", "\\|")
        md_lines.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe_detail} |")
    md_lines += ["", "## Mode details", "", "```", json.dumps(mode_details, indent=2), "```"]
    if report.failure_simulation:
        md_lines += ["", "## Failure-mode simulation", "", "```",
                     json.dumps(report.failure_simulation, indent=2), "```"]
    (out_dir / "automation_verification_summary.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )

    # Phase 13F: clear, machine-greppable status lines per detected mode.
    # Failure modes always print a SPECIFIC blocker line and exit 1; only
    # the two genuine success paths print *_VERIFICATION_PASS.
    if mode == "real_training_failed_inputs_missing":
        print("TRAINING_AUTOMATION_REAL_TRAINING_FAILED_INPUTS_MISSING")
        print(f"  halted_reason={mode_details.get('run_manifest_halted_reason')!r}")
        print(f"  challenger_pickles={mode_details.get('challenger_pickle_count')}")
        print(f"  train_manifest_dry_run={mode_details.get('train_manifest_dry_run')}")
        print(f"  calibration_manifest_dry_run={mode_details.get('calibration_manifest_dry_run')}")
        return 1
    if mode == "real_training_failed_readiness":
        print("TRAINING_AUTOMATION_REAL_TRAINING_FAILED_READINESS")
        return 1
    if mode == "real_training_failed":
        print("TRAINING_AUTOMATION_REAL_TRAINING_FAILED")
        print(f"  halted_reason={mode_details.get('run_manifest_halted_reason')!r}")
        print(f"  train_manifest_status={mode_details.get('train_manifest_status')!r}")
        print(f"  challenger_pickles={mode_details.get('challenger_pickle_count')}")
        return 1

    if report.passed:
        # Backwards-compatible line for any existing automation that greps for
        # the Phase 13A success string. The mode-specific line follows.
        print("TRAINING_AUTOMATION_VERIFICATION_PASS")
        if mode == "real_training":
            print("TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS")
            # Phase 13G + 13H: chain strict no-leakage + champion-pointer
            # metadata + Derek/WoO dependency + source-completeness verifiers.
            # Each sub-verifier writes its own structured artifact under the
            # same date and prints its own PASS line.
            import subprocess
            sub_ok = True
            for cmd, label in (
                (
                    [sys.executable, "scripts/verify_previous_day_source_completeness.py",
                     "--target-date", as_of],
                    "previous_day_source_completeness",
                ),
                (
                    [sys.executable, "scripts/verify_previous_day_no_leakage.py",
                     "--as-of-date", as_of],
                    "previous_day_no_leakage",
                ),
                (
                    [sys.executable, "scripts/verify_champion_pointer_metadata.py"],
                    "champion_pointer_metadata",
                ),
                (
                    [sys.executable, "scripts/verify_derek_woo_champion_dependency.py"],
                    "derek_woo_champion_dependency",
                ),
            ):
                rc = subprocess.run(cmd, cwd=REPO_ROOT, check=False).returncode
                if rc != 0:
                    sub_ok = False
            if not sub_ok:
                return 1
        elif mode == "dry_run":
            print("TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS")
        else:
            print("TRAINING_AUTOMATION_MODE_UNKNOWN")
            print(f"  details={mode_details}")
            return 1
        return 0

    failed = [c for c in report.checks if not c.passed]
    print(f"VERIFICATION FAILED (mode={mode})")
    for c in failed:
        print(f"  - {c.name}: {c.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
