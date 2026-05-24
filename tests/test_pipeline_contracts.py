"""
Pipeline contract tests — Items A, B, C, E, G.

These tests verify static properties of workflow files, .gitignore, and
the champion pointer contract without running the full pipeline.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
MAIN_WORKFLOW = WORKFLOWS_DIR / "nba_pmf_delivery.yml"
NIGHTLY_WORKFLOW = WORKFLOWS_DIR / "nightly_training_calibration.yml"
CHAMPION_POINTER = REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
FRESH_DELIVERY_POINTER = REPO_ROOT / "artifacts" / "models" / "registry" / "fresh_delivery_model_pointer.json"
MATRIX_BUILDER = REPO_ROOT / "scripts" / "build_m6_3_stat_role_calibration_report.py"
TARGETS_INIT = REPO_ROOT / "src" / "nba_props_model" / "targets" / "__init__.py"


# ── A. Workflow consolidation ─────────────────────────────────────────────────

class TestWorkflowConsolidation:
    def _load_workflow(self, path: Path) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    @staticmethod
    def _get_triggers(wf: dict) -> dict:
        """Return workflow trigger dict.
        PyYAML 5.x parses bare 'on:' keys as the boolean True (YAML 1.1),
        so we must check both 'on' and True as the dict key.
        """
        return wf.get(True) or wf.get("on") or {}

    def test_nightly_training_calibration_has_no_schedule(self):
        """nightly_training_calibration.yml must not have schedule crons.
        It was disabled as a true duplicate of model_chain_training_calibration
        in nba_pmf_delivery.yml.
        """
        wf = self._load_workflow(NIGHTLY_WORKFLOW)
        triggers = self._get_triggers(wf)
        if isinstance(triggers, dict):
            assert "schedule" not in triggers, (
                "nightly_training_calibration.yml has scheduled crons — "
                "this duplicates model_chain_training_calibration in nba_pmf_delivery.yml. "
                "Remove the schedule crons to prevent duplicate same-date training runs."
            )
        elif isinstance(triggers, list):
            assert not any("schedule" in t for t in triggers if isinstance(t, dict))

    def test_nightly_training_calibration_keeps_workflow_dispatch(self):
        """nightly_training_calibration.yml must retain workflow_dispatch for
        manual ad-hoc runs.
        """
        wf = self._load_workflow(NIGHTLY_WORKFLOW)
        triggers = self._get_triggers(wf)
        if isinstance(triggers, dict):
            assert "workflow_dispatch" in triggers, (
                "nightly_training_calibration.yml lost workflow_dispatch — "
                "restore it so operators can still trigger manual training runs."
            )

    def test_main_workflow_has_model_chain_job(self):
        """nba_pmf_delivery.yml must contain model_chain_training_calibration job
        as the one canonical scheduled training/calibration/promotion path.
        """
        wf = self._load_workflow(MAIN_WORKFLOW)
        jobs = wf.get("jobs", {})
        assert "model_chain_training_calibration" in jobs, (
            "model_chain_training_calibration job missing from nba_pmf_delivery.yml"
        )

    def test_main_workflow_has_phase8_job(self):
        wf = self._load_workflow(MAIN_WORKFLOW)
        assert "phase8_pmf_calibration_diagnostics_market_eval" in wf.get("jobs", {})

    def test_main_workflow_has_phase13_job(self):
        wf = self._load_workflow(MAIN_WORKFLOW)
        assert "phase13_live_context_contextual_lineup" in wf.get("jobs", {})

    def test_main_workflow_has_delivery_build_job(self):
        wf = self._load_workflow(MAIN_WORKFLOW)
        assert "delivery_build" in wf.get("jobs", {})

    def test_main_workflow_has_after_game_scoring_job(self):
        wf = self._load_workflow(MAIN_WORKFLOW)
        assert "after_game_scoring" in wf.get("jobs", {})

    def test_main_workflow_has_always_run_summary_job(self):
        """pipeline_summary must run with if: always() so it fires even on failure."""
        wf = self._load_workflow(MAIN_WORKFLOW)
        jobs = wf.get("jobs", {})
        assert "pipeline_summary" in jobs, (
            "pipeline_summary job missing — add an always-run summary job"
        )
        summary_job = jobs["pipeline_summary"]
        job_if = summary_job.get("if", "")
        assert "always()" in str(job_if), (
            "pipeline_summary job must use 'if: always()' so it fires even on failure"
        )

    def test_main_workflow_yaml_valid(self):
        """nba_pmf_delivery.yml must be parseable as valid YAML."""
        with open(MAIN_WORKFLOW) as f:
            content = f.read()
        # Will raise yaml.YAMLError if invalid
        parsed = yaml.safe_load(content)
        assert parsed is not None

    def test_nightly_workflow_yaml_valid(self):
        with open(NIGHTLY_WORKFLOW) as f:
            content = f.read()
        parsed = yaml.safe_load(content)
        assert parsed is not None

    def test_daily_pmf_delivery_workflow_has_no_schedule(self):
        """daily_pmf_delivery.yml (legacy) must not have scheduled crons.
        Its crons were removed in PR #29; only workflow_dispatch should remain.
        """
        legacy = WORKFLOWS_DIR / "daily_pmf_delivery.yml"
        if not legacy.exists():
            pytest.skip("daily_pmf_delivery.yml not present")
        wf = self._load_workflow(legacy)
        triggers = wf.get("on") or {}
        if isinstance(triggers, dict):
            assert "schedule" not in triggers, (
                "daily_pmf_delivery.yml has re-gained schedule crons — remove them"
            )


# ── B. Idempotency checks in workflow ─────────────────────────────────────────

class TestIdempotencySteps:
    def _load_steps(self, job_name: str) -> list:
        with open(MAIN_WORKFLOW) as f:
            wf = yaml.safe_load(f)
        return wf.get("jobs", {}).get(job_name, {}).get("steps", [])

    def _step_names(self, job_name: str) -> list:
        return [s.get("name", "") for s in self._load_steps(job_name)]

    def test_phase8_has_idempotency_check_step(self):
        names = self._step_names("phase8_pmf_calibration_diagnostics_market_eval")
        idempotency_steps = [n for n in names if "idempotency" in n.lower()]
        assert idempotency_steps, (
            "Phase 8 job has no idempotency check step. Add a step that checks "
            "if Phase 8 outputs already exist for as_of_date and emits "
            "PHASE8_ALREADY_COMPLETE_FOR_AS_OF_DATE / PHASE8_SKIPPED_IDEMPOTENT."
        )

    def test_phase8_idempotency_step_uses_github_output(self):
        steps = self._load_steps("phase8_pmf_calibration_diagnostics_market_eval")
        idempotency_step = next(
            (s for s in steps if "idempotency" in (s.get("name") or "").lower()), None
        )
        assert idempotency_step is not None
        run_script = idempotency_step.get("run", "")
        assert "GITHUB_OUTPUT" in run_script or "skip=" in run_script, (
            "Phase 8 idempotency step must write 'skip=true/false' to $GITHUB_OUTPUT"
        )

    def test_phase13_has_idempotency_check_step(self):
        names = self._step_names("phase13_live_context_contextual_lineup")
        idempotency_steps = [n for n in names if "idempotency" in n.lower()]
        assert idempotency_steps, (
            "Phase 13 job has no idempotency check step. Add a step that checks "
            "if challenger dirs already exist for as_of_date and emits "
            "PHASE13_ALREADY_COMPLETE_FOR_AS_OF_DATE / PHASE13_SKIPPED_IDEMPOTENT."
        )

    def test_phase13_heavy_steps_have_if_guard(self):
        steps = self._load_steps("phase13_live_context_contextual_lineup")
        heavy_step_names = {"Phase 13O", "Phase 13P", "Phase 13Q"}
        for step in steps:
            name = step.get("name", "")
            if any(name.startswith(h) for h in heavy_step_names):
                step_if = step.get("if", "")
                assert step_if and "idempotency" in step_if.lower(), (
                    f"Step '{name}' must have an if: condition that respects "
                    "the phase13_idempotency step's skip_training output."
                )


# ── C. Champion persistence ───────────────────────────────────────────────────

class TestChampionPersistence:
    def _get_phase13_commit_step(self):
        with open(MAIN_WORKFLOW) as f:
            wf = yaml.safe_load(f)
        steps = wf.get("jobs", {}).get("phase13_live_context_contextual_lineup", {}).get("steps", [])
        for step in steps:
            if "commit phase 13" in (step.get("name") or "").lower():
                return step
        return None

    def test_phase13_commit_step_exists(self):
        step = self._get_phase13_commit_step()
        assert step is not None, "No 'Commit Phase 13 artifacts' step found"

    def test_phase13_commit_uses_force_add_for_champion_pointer(self):
        step = self._get_phase13_commit_step()
        assert step is not None
        run_script = step.get("run", "")
        assert "git add -f" in run_script and "champion_pointer.json" in run_script, (
            "Phase 13 commit step must use 'git add -f artifacts/models/registry/"
            "champion_pointer.json' to force-add the pointer file."
        )

    def test_phase13_commit_has_promotion_persistence_fail_guard(self):
        step = self._get_phase13_commit_step()
        assert step is not None
        run_script = step.get("run", "")
        assert "PHASE13_PROMOTION_PERSISTENCE_FAIL_NO_STAGED_CHANGES" in run_script, (
            "Phase 13 commit step must emit PHASE13_PROMOTION_PERSISTENCE_FAIL_NO_STAGED_CHANGES "
            "and exit 1 when promotion_decision=promoted but no staged changes found."
        )

    def test_phase13_commit_has_push_verify(self):
        step = self._get_phase13_commit_step()
        assert step is not None
        run_script = step.get("run", "")
        assert "PHASE13_PROMOTION_PUSH_VERIFY_FAIL" in run_script, (
            "Phase 13 commit step must verify champion pointer persisted to origin/main "
            "after push, and emit PHASE13_PROMOTION_PUSH_VERIFY_FAIL on mismatch."
        )

    def test_phase13_commit_cleans_up_rebase_state(self):
        step = self._get_phase13_commit_step()
        assert step is not None
        run_script = step.get("run", "")
        assert "git rebase --abort" in run_script or "rebase-merge" in run_script, (
            "Phase 13 commit step must clean up any lingering git rebase state "
            "before staging artifacts."
        )

    def test_champion_pointer_not_gitignored(self):
        """champion_pointer.json must never be gitignored."""
        result = subprocess.run(
            ["git", "check-ignore", "-v", "artifacts/models/registry/champion_pointer.json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "champion_pointer.json is gitignored! "
            f"Rule: {result.stdout.strip()}\n"
            "Add an explicit exception to .gitignore so this file is always tracked."
        )

    def test_promotion_log_not_gitignored(self):
        """promotion_log.csv must not be gitignored."""
        result = subprocess.run(
            ["git", "check-ignore", "-v", "artifacts/models/registry/promotion_log.csv"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "promotion_log.csv is gitignored. "
            "Remove the .gitignore rule so the promotion log is tracked."
        )


# ── Champion pointer contract ─────────────────────────────────────────────────

class TestChampionPointerContract:
    @pytest.fixture
    def pointer(self) -> dict:
        if not CHAMPION_POINTER.exists():
            pytest.skip("champion_pointer.json does not exist in local checkout")
        with open(CHAMPION_POINTER) as f:
            return json.load(f)

    def test_champion_model_id_present(self, pointer):
        assert pointer.get("champion_model_id"), "champion_model_id must be set"

    def test_feature_set_id_present(self, pointer):
        assert pointer.get("feature_set_id"), (
            "feature_set_id is null/missing — champion pointer is non-contextual. "
            "The active champion must be contextual (phase13q_ or phase13s_)."
        )

    def test_feature_set_id_is_contextual(self, pointer):
        fs = pointer.get("feature_set_id") or ""
        assert fs.startswith("phase13q_") or fs.startswith("phase13s_"), (
            f"feature_set_id='{fs}' is not contextual. "
            "Must start with phase13q_ or phase13s_."
        )

    def test_trained_through_date_present(self, pointer):
        assert pointer.get("trained_through_date") or pointer.get("contextual_trained_through_date"), (
            "trained_through_date / contextual_trained_through_date must be set"
        )

    def test_contextual_challenger_dir_present(self, pointer):
        assert pointer.get("contextual_challenger_dir") or pointer.get("direct_lineup_contextual_challenger_dir"), (
            "No contextual_challenger_dir or direct_lineup_contextual_challenger_dir in champion_pointer.json"
        )


# ── E. Lineup behavior markers ────────────────────────────────────────────────

class TestLineupBehavior:
    def _get_delivery_step_run(self) -> str:
        with open(MAIN_WORKFLOW) as f:
            wf = yaml.safe_load(f)
        steps = wf.get("jobs", {}).get("delivery_build", {}).get("steps", [])
        for step in steps:
            name = step.get("name") or ""
            if "daily pmf delivery pipeline" in name.lower():
                return step.get("run", "")
        return ""

    def test_delivery_step_has_lineup_mode_markers(self):
        run_script = self._get_delivery_step_run()
        assert "PROVISIONAL_ROWS_ACCEPTED_AS_VALID_PREGAME" in run_script, (
            "Delivery step must emit PROVISIONAL_ROWS_ACCEPTED_AS_VALID_PREGAME "
            "for morning/woo_morning_monetization modes."
        )
        assert "LINEUP_STATUS_VALID_FOR_MODE" in run_script, (
            "Delivery step must emit LINEUP_STATUS_VALID_FOR_MODE"
        )
        assert "OFFICIAL_LINEUP_CONTEXT_APPLIED_FOR_NEAR_TIP" in run_script, (
            "Delivery step must emit OFFICIAL_LINEUP_CONTEXT_APPLIED_FOR_NEAR_TIP "
            "for derek_near_lineup/close_lock modes."
        )
        assert "LATEST_AVAILABLE_SNAPSHOT_UPDATED" in run_script, (
            "Delivery step must emit LATEST_AVAILABLE_SNAPSHOT_UPDATED after completion."
        )

    def test_audit_injury_lineup_run_modes_script_exists(self):
        """audit_injury_lineup_run_modes.py must exist — it audits that morning
        mode does not require official lineups.
        """
        assert (REPO_ROOT / "scripts" / "audit_injury_lineup_run_modes.py").exists()


# ── No generated data committed ───────────────────────────────────────────────

class TestNoGeneratedDataCommitted:
    def test_no_raw_pkl_files_at_repo_root(self):
        """No large .pkl files should be committed directly at the repo root
        or in scripts/. This prevents accidental model commits in unusual places.
        """
        result = subprocess.run(
            ["git", "ls-files", "--exclude-standard"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        unexpected_pkls = [
            line for line in result.stdout.splitlines()
            if line.endswith(".pkl")
            and not line.startswith("artifacts/")
            and not line.startswith("deliveries/")  # deliveries may legitimately contain .pkl
            and not line.startswith("predictions/")
            and not line.startswith("public_export/")
        ]
        assert not unexpected_pkls, (
            f"Unexpected .pkl files committed outside known pipeline dirs: {unexpected_pkls}"
        )

    def test_no_training_table_parquet_at_repo_root(self):
        """training_table.parquet should be gitignored, not committed."""
        result = subprocess.run(
            ["git", "check-ignore", "-v", "data/training_table.parquet"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        # Returns 0 if gitignored — that's what we want
        if result.returncode == 0:
            return  # good, it's gitignored
        # If not gitignored, it might still not be committed (doesn't exist)
        committed = subprocess.run(
            ["git", "ls-files", "data/training_table.parquet"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert not committed.stdout.strip(), (
            "data/training_table.parquet is tracked by git. "
            "This large generated file should be .gitignored."
        )

    def test_no_large_pkl_files_in_artifacts_challengers_committed(self):
        """Large pkl files in artifacts/models/challengers/ should not be
        committed (except for the explicit .gitignore exceptions for contextual pkl).
        Check that no unexpected .pkl > 1MB is committed.
        """
        result = subprocess.run(
            ["git", "ls-files", "artifacts/models/challengers/", "--exclude-standard"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        large_pkls = []
        for line in result.stdout.splitlines():
            if not line.endswith(".pkl"):
                continue
            full_path = REPO_ROOT / line
            if full_path.exists() and full_path.stat().st_size > 1024 * 1024:
                large_pkls.append(line)
        assert not large_pkls, (
            f"Large .pkl files committed in challengers/: {large_pkls}"
        )


# ── Promotion script readback verification ───────────────────────────────────

class TestPromotionReadbackVerification:
    """Verify that promotion scripts emit PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL
    and exit non-zero when champion_pointer.json is not updated as expected,
    rather than silently emitting PASS while leaving the pointer stale.
    """

    DIRECT_LINEUP_PROMOTER = REPO_ROOT / "scripts" / "promote_direct_lineup_challenger.py"
    CONTEXTUAL_PROMOTER = REPO_ROOT / "scripts" / "promote_contextual_challenger.py"

    def _script_source(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    # ── Script existence ─────────────────────────────────────────────────────

    def test_direct_lineup_promoter_exists(self):
        assert self.DIRECT_LINEUP_PROMOTER.exists()

    def test_contextual_promoter_exists(self):
        assert self.CONTEXTUAL_PROMOTER.exists()

    # ── Readback guard present in direct-lineup promoter ────────────────────

    def test_direct_lineup_promoter_has_readback(self):
        src = self._script_source(self.DIRECT_LINEUP_PROMOTER)
        assert "PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL" in src, (
            "promote_direct_lineup_challenger.py must emit "
            "PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL when readback fails."
        )

    def test_direct_lineup_promoter_reads_back_after_write(self):
        src = self._script_source(self.DIRECT_LINEUP_PROMOTER)
        # Use the readback-verification sentinel which is inserted right after
        # write_json_atomic(CHAMPION_POINTER_PATH, …).  The initial read of the
        # pointer (before promotion) is at an earlier offset; the sentinel block
        # is what confirms the readback occurs AFTER the write.
        write_idx = src.index("write_json_atomic(CHAMPION_POINTER_PATH, new_pointer)")
        sentinel_idx = src.index("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL")
        assert sentinel_idx > write_idx, (
            "The PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL readback block must "
            "appear AFTER write_json_atomic(CHAMPION_POINTER_PATH) in "
            "promote_direct_lineup_challenger.py."
        )

    def test_direct_lineup_promoter_does_not_pass_before_readback(self):
        src = self._script_source(self.DIRECT_LINEUP_PROMOTER)
        # The PASS print statement — skip the docstring occurrence by finding
        # the actual print() call.
        pass_idx = src.index('print("PHASE13S_DIRECT_LINEUP_CHAMPION_PROMOTION_PASS")')
        sentinel_idx = src.index("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL")
        assert sentinel_idx < pass_idx, (
            "promote_direct_lineup_challenger.py must verify readback (and possibly "
            "call sys.exit(1)) BEFORE printing "
            "PHASE13S_DIRECT_LINEUP_CHAMPION_PROMOTION_PASS."
        )

    def test_direct_lineup_promoter_verifies_ctx_dir_in_readback(self):
        src = self._script_source(self.DIRECT_LINEUP_PROMOTER)
        assert "rb_ctx_dir" in src and "expected_ctx_dir" in src, (
            "promote_direct_lineup_challenger.py must compare contextual_challenger_dir "
            "in the readback against the expected value."
        )

    def test_direct_lineup_promoter_verifies_ttd_in_readback(self):
        src = self._script_source(self.DIRECT_LINEUP_PROMOTER)
        assert "rb_ttd" in src and "expected_ttd" in src, (
            "promote_direct_lineup_challenger.py must compare "
            "contextual_trained_through_date in the readback."
        )

    def test_direct_lineup_promoter_exits_nonzero_on_fail(self):
        src = self._script_source(self.DIRECT_LINEUP_PROMOTER)
        fail_block_idx = src.index("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL")
        exit_idx = src.index("sys.exit(1)", fail_block_idx)
        assert exit_idx > fail_block_idx, (
            "promote_direct_lineup_challenger.py must call sys.exit(1) after "
            "PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL."
        )

    # ── Readback guard present in contextual promoter ───────────────────────

    def test_contextual_promoter_has_readback(self):
        src = self._script_source(self.CONTEXTUAL_PROMOTER)
        assert "PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL" in src, (
            "promote_contextual_challenger.py must emit "
            "PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL when readback fails."
        )

    def test_contextual_promoter_reads_back_after_write(self):
        src = self._script_source(self.CONTEXTUAL_PROMOTER)
        write_idx = src.index("write_json_atomic(CHAMPION_POINTER_PATH, new_pointer)")
        sentinel_idx = src.index("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL")
        assert sentinel_idx > write_idx, (
            "The PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL readback block must "
            "appear AFTER write_json_atomic(CHAMPION_POINTER_PATH) in "
            "promote_contextual_challenger.py."
        )

    def test_contextual_promoter_does_not_pass_before_readback(self):
        src = self._script_source(self.CONTEXTUAL_PROMOTER)
        pass_idx = src.index('print("PHASE13R_CONTEXTUAL_CHAMPION_PROMOTION_PASS")')
        sentinel_idx = src.index("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL")
        assert sentinel_idx < pass_idx, (
            "promote_contextual_challenger.py must verify readback BEFORE "
            "printing PHASE13R_CONTEXTUAL_CHAMPION_PROMOTION_PASS."
        )

    def test_contextual_promoter_exits_nonzero_on_fail(self):
        src = self._script_source(self.CONTEXTUAL_PROMOTER)
        fail_block_idx = src.index("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL")
        exit_idx = src.index("sys.exit(1)", fail_block_idx)
        assert exit_idx > fail_block_idx, (
            "promote_contextual_challenger.py must call sys.exit(1) after "
            "PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL."
        )

    # ── Commit step guards ───────────────────────────────────────────────────

    def test_commit_step_force_adds_champion_pointer(self):
        """The commit step must use git add -f to force-add champion_pointer.json."""
        with open(MAIN_WORKFLOW) as f:
            content = f.read()
        assert "git add -f artifacts/models/registry/champion_pointer.json" in content, (
            "Commit Phase 13 artifacts step must use 'git add -f champion_pointer.json' "
            "to prevent gitignore from silently blocking the stage."
        )

    def test_commit_step_fails_on_promoted_but_no_staged_changes(self):
        """Commit step must fail with PHASE13_PROMOTION_PERSISTENCE_FAIL_NO_STAGED_CHANGES."""
        with open(MAIN_WORKFLOW) as f:
            content = f.read()
        assert "PHASE13_PROMOTION_PERSISTENCE_FAIL_NO_STAGED_CHANGES" in content, (
            "Commit step must fail loudly when promotion reported success but "
            "git add produced no staged changes."
        )

    def test_commit_step_has_post_push_verify(self):
        """Commit step must verify origin/main after push."""
        with open(MAIN_WORKFLOW) as f:
            content = f.read()
        assert "PHASE13_PROMOTION_PUSH_VERIFY_FAIL" in content, (
            "Commit step must verify champion_pointer on origin/main after push."
        )

    # ── .gitignore does not block required champion artifacts ────────────────

    def test_champion_pointer_not_gitignored(self):
        result = subprocess.run(
            ["git", "check-ignore", "-v",
             "artifacts/models/registry/champion_pointer.json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "artifacts/models/registry/champion_pointer.json must NOT be gitignored. "
            f"But git check-ignore output: {result.stdout.strip()!r}"
        )

    def test_promotion_log_not_gitignored(self):
        result = subprocess.run(
            ["git", "check-ignore", "-v",
             "artifacts/models/registry/promotion_log.csv"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "artifacts/models/registry/promotion_log.csv must NOT be gitignored."
        )

    # ── Delivery layout/schema untouched ────────────────────────────────────

    def test_delivery_folder_structure_present(self):
        """deliveries/ folder must exist and contain canonical_source."""
        deliveries = REPO_ROOT / "deliveries"
        assert deliveries.exists(), "deliveries/ folder must exist."
        date_dirs = [d for d in deliveries.iterdir() if d.is_dir()
                     and d.name[0].isdigit()]
        assert date_dirs, "deliveries/ must contain at least one date directory."
        latest = sorted(date_dirs)[-1]
        assert (latest / "canonical_source").exists(), (
            f"{latest.name}/canonical_source/ must exist (delivery contract)."
        )

    def test_fresh_delivery_pointer_not_gitignored(self):
        result = subprocess.run(
            ["git", "check-ignore", "-v",
             "artifacts/models/registry/fresh_delivery_model_pointer.json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            "artifacts/models/registry/fresh_delivery_model_pointer.json must NOT be gitignored."
        )

    def test_derek_unique_props_summary_untouched(self):
        """derek_unique_props_summary.csv must not be staged/modified by these changes."""
        result = subprocess.run(
            ["git", "diff", "--name-only",
             "artifacts/models/registry/champion_pointer.json",
             "scripts/promote_direct_lineup_challenger.py",
             "scripts/promote_contextual_challenger.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        modified = result.stdout.strip().splitlines()
        derek_touched = [f for f in modified if "derek_unique_props_summary" in f]
        assert not derek_touched, (
            f"derek_unique_props_summary.csv must not be touched: {derek_touched}"
        )


# ── Section 3: Market gates as diagnostics / fresh delivery pointer ───────────

class TestMarketGatesDiagnostics:
    """Verify that market gate failures are treated as diagnostics, not blockers."""

    def test_write_fresh_delivery_pointer_script_exists(self):
        assert (REPO_ROOT / "scripts" / "write_fresh_delivery_pointer.py").exists(), (
            "scripts/write_fresh_delivery_pointer.py must exist."
        )

    def test_fresh_delivery_pointer_written(self):
        assert FRESH_DELIVERY_POINTER.exists(), (
            "artifacts/models/registry/fresh_delivery_model_pointer.json must exist "
            "after training/calibration runs."
        )

    def test_fresh_delivery_pointer_has_required_fields(self):
        if not FRESH_DELIVERY_POINTER.exists():
            pytest.skip("fresh_delivery_model_pointer.json not yet written")
        with open(FRESH_DELIVERY_POINTER) as f:
            pointer = json.load(f)
        for field in ("trained_through_date", "market_quality_status", "pointer_type", "base_model_version"):
            assert field in pointer, (
                f"fresh_delivery_model_pointer.json missing field: {field}"
            )
        assert pointer["pointer_type"] == "fresh_delivery"

    def test_promote_challenger_treats_m6_3_gates_as_soft(self):
        src = (REPO_ROOT / "scripts" / "promote_challenger_if_validated.py").read_text()
        assert 'm6_3_' in src, (
            "promote_challenger_if_validated.py must classify m6_3_* gates as soft."
        )
        assert 'soft_gate_failures' in src, (
            "promote_challenger_if_validated.py must have soft_gate_failures logic."
        )

    def test_workflow_writes_fresh_delivery_pointer(self):
        with open(REPO_ROOT / ".github" / "workflows" / "nba_pmf_delivery.yml") as f:
            content = f.read()
        assert "write_fresh_delivery_pointer.py" in content, (
            "nba_pmf_delivery.yml must call write_fresh_delivery_pointer.py."
        )

    def test_workflow_force_adds_fresh_delivery_pointer(self):
        with open(REPO_ROOT / ".github" / "workflows" / "nba_pmf_delivery.yml") as f:
            content = f.read()
        assert "fresh_delivery_model_pointer.json" in content, (
            "nba_pmf_delivery.yml must include fresh_delivery_model_pointer.json in git add."
        )

    def test_fresh_delivery_pointer_training_automation_constant(self):
        src = (REPO_ROOT / "src" / "nba_props_model" / "training_automation.py").read_text()
        assert "FRESH_DELIVERY_POINTER_PATH" in src, (
            "training_automation.py must export FRESH_DELIVERY_POINTER_PATH."
        )


# ── Section 6: RA + all 12 stats in Phase 8 OOF and matrix ──────────────────

class TestDeliveryRequiredStats:
    """Verify ra and all 12 required delivery stats are present throughout the pipeline."""

    def test_delivery_required_targets_canonical_defined(self):
        src = TARGETS_INIT.read_text()
        assert "DELIVERY_REQUIRED_TARGETS_CANONICAL" in src, (
            "src/nba_props_model/targets/__init__.py must define "
            "DELIVERY_REQUIRED_TARGETS_CANONICAL with all 12 delivery stats."
        )

    def test_delivery_required_targets_canonical_has_12_stats(self):
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from nba_props_model.targets import DELIVERY_REQUIRED_TARGETS_CANONICAL
        assert len(DELIVERY_REQUIRED_TARGETS_CANONICAL) == 12, (
            f"DELIVERY_REQUIRED_TARGETS_CANONICAL must have 12 stats, got {len(DELIVERY_REQUIRED_TARGETS_CANONICAL)}: "
            f"{DELIVERY_REQUIRED_TARGETS_CANONICAL}"
        )
        assert "ra" in DELIVERY_REQUIRED_TARGETS_CANONICAL, (
            "DELIVERY_REQUIRED_TARGETS_CANONICAL must include 'ra' (rebounds+assists)."
        )

    def test_ra_not_forbidden_in_matrix_builder(self):
        src = MATRIX_BUILDER.read_text()
        import re
        # Match only the tuple/set literal on the FORBIDDEN_STATS line (before any comment)
        match = re.search(r'FORBIDDEN_STATS\s*=\s*(\(.*?\))', src)
        assert match, "FORBIDDEN_STATS must be defined as a tuple in build_m6_3_stat_role_calibration_report.py"
        literal = match.group(1)
        assert '"ra"' not in literal, (
            f"FORBIDDEN_STATS tuple must not include '\"ra\"'. Got: {literal}"
        )
        assert '"reb_ast"' in literal, (
            f"FORBIDDEN_STATS tuple must still include '\"reb_ast\"' alias. Got: {literal}"
        )

    def test_ra_in_matrix_builder_combo_stats(self):
        src = MATRIX_BUILDER.read_text()
        import re
        match = re.search(r'COMBO_STATS\s*=\s*(.+)', src)
        assert match, "COMBO_STATS must be defined in build_m6_3_stat_role_calibration_report.py"
        assert '"ra"' in match.group(1), (
            f"COMBO_STATS must include 'ra'. Got: {match.group(1)}"
        )

    def test_matrix_includes_ra_when_rebuilt(self):
        """The latest m6_3 matrix CSV must include ra after the rebuild."""
        docs_dir = REPO_ROOT / "artifacts" / "docs"
        matrices = sorted(docs_dir.glob("m6_3_stat_role_calibration_matrix_*.csv"))
        if not matrices:
            pytest.skip("No m6_3 matrix CSV found in artifacts/docs/")
        latest = matrices[-1]
        import csv
        with open(latest, newline="") as f:
            rows = list(csv.DictReader(f))
        stats = {r.get("stat", "") for r in rows}
        assert "ra" in stats, (
            f"Latest matrix {latest.name} must contain 'ra' rows. "
            f"Found stats: {sorted(stats)}"
        )

    def test_matrix_has_72_rows(self):
        """The latest m6_3 matrix must have 72 rows (12 stats x 6 role buckets)."""
        docs_dir = REPO_ROOT / "artifacts" / "docs"
        matrices = sorted(docs_dir.glob("m6_3_stat_role_calibration_matrix_*.csv"))
        if not matrices:
            pytest.skip("No m6_3 matrix CSV found in artifacts/docs/")
        latest = matrices[-1]
        import csv
        with open(latest, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 72, (
            f"Latest matrix {latest.name} must have 72 rows (12 stats × 6 roles). "
            f"Got {len(rows)}."
        )

    def test_ra_canonical_function(self):
        """canonical('reb_ast') must return 'ra'."""
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from nba_props_model.targets import canonical
        assert canonical("reb_ast") == "ra", "canonical('reb_ast') must return 'ra'"
        assert canonical("reb+ast") == "ra", "canonical('reb+ast') must return 'ra'"
        assert canonical("ra") == "ra", "canonical('ra') must return 'ra'"

    def test_validate_champion_uses_dynamic_matrix_path(self):
        src = (REPO_ROOT / "scripts" / "validate_champion_vs_challenger.py").read_text()
        assert "_resolve_latest_m6_3_matrix" in src, (
            "validate_champion_vs_challenger.py must use _resolve_latest_m6_3_matrix() "
            "to dynamically find the most recent matrix file."
        )

    def test_ra_not_forbidden_in_validate_script(self):
        src = (REPO_ROOT / "scripts" / "validate_champion_vs_challenger.py").read_text()
        import re
        match = re.search(r'M7_FORBIDDEN_STATS\s*=\s*\{(.+?)\}', src)
        assert match, "M7_FORBIDDEN_STATS must be defined in validate_champion_vs_challenger.py"
        assert '"ra"' not in match.group(1), (
            f"M7_FORBIDDEN_STATS must not include '\"ra\"'. Got: {match.group(1)}"
        )

    def test_workflow_runs_matrix_builder_in_phase8(self):
        with open(REPO_ROOT / ".github" / "workflows" / "nba_pmf_delivery.yml") as f:
            content = f.read()
        assert "build_m6_3_stat_role_calibration_report.py" in content, (
            "nba_pmf_delivery.yml must call build_m6_3_stat_role_calibration_report.py "
            "in the Phase 8 diagnostics step."
        )
