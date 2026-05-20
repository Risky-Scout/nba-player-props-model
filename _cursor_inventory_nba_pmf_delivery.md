# NBA PMF Delivery — Workflow & Script Inventory

> **Phase 0 deliverable** for the consolidation work described in
> `CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md`. This file is the
> source of truth for what currently runs, in what order, with what
> exact flags. Subsequent phases (resolver, workflow rewrite,
> calibration contract) read from this file — they MUST NOT invent
> flags or commands that contradict what is recorded here.
>
> Generated 2026-05-20 ET. Branch
> `fix/nba-pmf-delivery-production-timing-and-calibration` (forked off
> `origin/main` per the brief). Read-only inventory — no production
> behavior was changed to produce it.

## Table of contents

- [Section A — Workflow inventory (12 files)](#section-a--workflow-inventory)
- [Section B — Key-script argparse](#section-b--key-script-argparse)
- [Section C — Referenced-script existence map](#section-c--referenced-script-existence-map)
- [Section D — Comparison: `daily_pmf_delivery.yml` (production) vs `nba_pmf_delivery.yml` (consolidation target)](#section-d--comparison-daily_pmf_deliveryyml-production-vs-nba_pmf_deliveryyml-consolidation-target)
- [Section E — Brief-mandated gaps & observations](#section-e--brief-mandated-gaps--observations)

---

## Section A — Workflow inventory

### `daily_pmf_delivery.yml`

- **Trigger**:
  - `workflow_run`:
    - `workflows`: `["NBA Props Model — Daily Pipeline"]`
    - `types`: `[completed]`
    - `branches`: `[main]`
  - `schedule`:
    - `- cron: '0 15 * * *'`  # WoO monetization (early/afternoon).
    - `- cron: '0 18 * * *'`
    - `- cron: '0 20 * * *'`
    - `- cron: '25 22 * * *'`  # Derek near-lineup window — first publishable evaluation snapshot at 22:25 UTC, then every 15 min through 03:10 UTC.
    - `- cron: '40,55 22 * * *'`
    - `- cron: '10,25,40,55 23,0,1,2 * * *'`
    - `- cron: '10 3 * * *'`
    - `- cron: '25 3 * * *'`  # Late close lock.
    - `- cron: '30 6 * * *'`  # After-game scoring (yesterday's slate).
  - `workflow_dispatch`:
    - `mode`: type `choice`, required `true`, default `derek_near_lineup`, options: `woo_morning_monetization`, `woo_afternoon_refresh`, `derek_near_lineup`, `close_lock`, `after_game`, `full_day`, `morning`
    - `delivery_date`: default `""`, "Delivery date (YYYY-MM-DD); blank = today (UTC)"
    - `run_predict`: choice, default `"false"`, "Run scripts/predict.py before refresh (woo_morning_monetization / morning / full_day only). Requires BDL_API_KEY."
    - `force_run`: choice, default `"false"`, "Bypass the tipoff-window gate (used for manual backfills outside the lineup window)"
- **Top-level env**: `PYTHON_VERSION`, `PYTHONPATH`, `STAT_GRID_RECALIBRATION_MODEL_DIR`, `SOURCE_RECALIBRATION_MODEL_DIR`, `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`, `DUNKS_AND_THREES_API_KEY`, `DUNKS_API_KEY`, `DNT_API_KEY`, `DUNKS_THREES_API_KEY`, `REQUIRE_DUNKS_AND_THREES`
- **Concurrency**: group `daily-pmf-delivery-${{ github.ref }}`, cancel-in-progress `false`
- **Permissions**: none
- **Jobs** (all `runs-on: ubuntu-latest`, no `needs:`):
  - `morning` — `if: github.event_name == 'workflow_dispatch' && github.event.inputs.mode == 'morning'`
    - `Secrets preflight` → `python3 scripts/verify_secrets_preflight.py --mode daily`
    - `Verify critical delivery sources` → `python scripts/verify_critical_delivery_sources.py`
    - `Predictions readiness gate (Phase 13AM)` → `python3 scripts/predictions_readiness_gate.py --date "${{ steps.d.outputs.date }}" --predict-cron-hour-utc 13 --mode "morning"`
    - `Run delivery pipeline` → `python scripts/run_daily_delivery_pipeline.py --date ${{ steps.d.outputs.date }} --mode morning --regions us us2 --rebuild-canonical --verify --fail-on-missing-delivery $PREDICT_FLAG $FORCE_FLAG`
    - `Write delivery previews` → `python scripts/write_delivery_review_previews.py --date ${{ steps.d.outputs.date }}`
    - `Stamp champion metadata` → `python scripts/stamp_delivery_champion_metadata.py --delivery-date ${{ steps.d.outputs.date }}`
    - `Verify champion dependency` → `python scripts/verify_derek_woo_champion_dependency.py --delivery-date ${{ steps.d.outputs.date }} --require-both-sides false`
    - `Strip empty columns` → `python3 scripts/strip_empty_delivery_columns.py --date ${{ steps.d.outputs.date }} --write`
    - `Stage and commit` → `git config ...`, `git add deliveries/${{ steps.d.outputs.date }} artifacts/delivery_metadata/${{ steps.d.outputs.date }} deliveries/README.md deliveries/index.html public_export/wizard_of_odds`, `git commit --author=... -m "daily delivery champion metadata ${{ steps.d.outputs.date }} (morning)"`, `git pull --rebase origin main && git push origin main`
  - `woo_morning_monetization` — `if: (workflow_run.success) || (dispatch mode == 'woo_morning_monetization') || (schedule == '0 15 * * *')`
    - same preflight + readiness gate (mode `woo_morning_monetization`)
    - `Run delivery pipeline` → `python scripts/run_daily_delivery_pipeline.py --date ${{ steps.d.outputs.date }} --mode woo_morning_monetization --regions us us2 --rebuild-canonical --verify --fail-on-missing-delivery $PREDICT_FLAG $FORCE_FLAG`
    - WoO publish/build/verify (4 calls): `publish_woo_public_export.py --date`, `build_woo_dashboard.py --date`, `verify_woo_dashboard_render_contract.py --date`, `verify_woo_public_export_contract.py --date`
    - M8.6 verifiers: `verify_oddsapi_market_registry_contract.py`, `verify_no_legacy_prediction_artifacts.py`, `verify_daily_delivery_folder_contract.py --date "$D" --allow-missing after_game_scoring derek_forward_feed`, `verify_woo_public_artifacts_target_allowlist.py --date`, `verify_availability_freshness.py --date "$D" --mode close_lock`
    - Morning-completeness: `verify_morning_delivery_completeness.py --date`, `verify_oddsapi_bdl_full_prop_coverage.py --date "$D" --snapshot-substr auto --ensure-audit`
    - Previews + champion stamp + strip + stage/commit (same pattern as `morning`)
  - `woo_afternoon_refresh` — `if: (dispatch mode == 'woo_afternoon_refresh') || schedule == '0 18 * * *' || schedule == '0 20 * * *'`
    - Same flow as `woo_morning_monetization` but without `--predict` and without morning-completeness verifiers
  - `derek_near_lineup` — `if: (dispatch mode == 'derek_near_lineup') || schedule == '25 22' || '40,55 22' || '10,25,40,55 23,0,1,2' || '10 3 * * *'`
    - Preflight + readiness gate (mode `derek_near_lineup`)
    - `Run delivery pipeline` → `python scripts/run_daily_delivery_pipeline.py --date $DATE --mode derek_near_lineup --regions us us2 --rebuild-canonical --verify --fail-on-missing-delivery $FORCE_FLAG`
    - WoO publish/build/verify (4 calls) — same as above
    - M8.6 verifiers — same 5 calls
    - **M8.8 strict t25 audits** (4 calls): `audit_daily_delivery_completeness.py --start-date "$D" --end-date "$D" --include-current-if-present --out-dir artifacts/model_diagnostics/daily_delivery_completeness --run-mode t25`, `verify_derek_forward_feed_contract.py --date`, `audit_injury_lineup_run_modes.py --date "$D" --latest-completed-date "$PREV"`, `audit_github_delivery_automation.py`
    - `Verify near-lineup contract` → `verify_derek_near_lineup_contract.py --date`
    - Previews + champion stamp + strip + stage/commit
  - `close_lock` — `if: (dispatch mode == 'close_lock') || schedule == '25 3 * * *'`
    - Same as `derek_near_lineup` but **M8.8 strict t5 audits** (`--run-mode t5`)
  - `after_game` — `if: (dispatch mode == 'after_game') || schedule == '30 6 * * *'`
    - Preflight + readiness gate with `--no-run-predict`
    - `Run complete after-game scoring` → `python scripts/run_after_game_complete_scoring.py --date ${{ steps.d.outputs.date }}`
    - `Stamp champion metadata` → `stamp_delivery_champion_metadata.py --delivery-date`
    - `After-game package consistency` → `verify_after_game_scoring_package_consistency.py --delivery-date`
    - M8.6 verifiers (5 calls — strict, no `--allow-missing`)
    - Phase 13K rolling market benchmark → `build_rolling_market_benchmark.py --as-of-date $D --window-days 28 || echo "::notice::..."`
    - Phase 13AA PMF variance experience → `build_pmf_variance_experience_study.py`, `verify_pmf_variance_experience_study.py` (non-blocking via `|| echo`)
    - Previews + champion stamp + strip + stage/commit (commit also adds `artifacts/market_benchmark/$D`, `artifacts/experience_studies`)
  - `derek_schedule_bridge` — `if: (schedule in derek windows) || (dispatch mode in derek_near_lineup, close_lock)`, job-level `permissions: actions: write, contents: read`
    - `Trigger Derek due-snapshot workflow` → `gh workflow run derek_live_game_snapshots.yml --repo "${{ github.repository }}" --ref main -f delivery_date="$DATE" -f snapshot_type=all -f allow_backfill_test=false -f force=false`
- **Notes**:
  - **Phase 13AM**: `workflow_run` is ACTIVE (auto-fires `woo_morning_monetization` after Daily Pipeline completes).
  - `morning` job is manual-dispatch only since Phase 12D.
  - `full_day` is a dispatch option but has no dedicated job in this file.
  - Hard rules in file header: never log secrets, never stage raw API data/artifacts/logs, never wire Phase 10D/10D.2 TOV overlays, never fabricate affiliate URLs.

### `nba_pmf_delivery.yml` (consolidation target)

- **Trigger**:
  - `schedule` (14 entries):
    - `- cron: "30 6 * * *"`   # After-game scoring.
    - `- cron: "30 9 * * *"`   # Nightly training / calibration deferred retries.
    - `- cron: "30 12 * * *"`
    - `- cron: "30 15 * * *"`
    - `- cron: "30 18 * * *"`
    - `- cron: "30 21 * * *"`
    - `- cron: "0 15 * * *"`   # WoO / delivery refresh windows.
    - `- cron: "0 18 * * *"`
    - `- cron: "0 20 * * *"`
    - `- cron: "25 22 * * *"`  # Derek near-lineup / close-lock windows.
    - `- cron: "40,55 22 * * *"`
    - `- cron: "10,25,40,55 23,0,1,2 * * *"`
    - `- cron: "10 3 * * *"`
    - `- cron: "25 3 * * *"`
  - `workflow_dispatch`:
    - `stage`: choice, default `"auto"`, options: `auto`, `full_cycle`, `training`, `phase8`, `phase13_context`, `delivery`, `after_game`, `verifiers`
    - `mode`: choice, default `"derek_near_lineup"`, options: `morning`, `woo_morning_monetization`, `woo_afternoon_refresh`, `derek_near_lineup`, `close_lock`, `after_game`, `full_day`
    - `delivery_date`: default `""`, "YYYY-MM-DD. Blank = America/New_York today."
    - `as_of_date`: default `""`, "YYYY-MM-DD. Blank = America/New_York yesterday."
    - `no_promote`: choice, default `"true"`, "Block champion promotion during manual testing"
    - `run_predict`: choice, default `"false"`, "Run prediction inside delivery stage"
- **Top-level env**: same as `daily_pmf_delivery.yml`
- **Concurrency**: group `nba-pmf-delivery-${{ github.ref }}`, cancel-in-progress `false` *(brief asks to remove this — see Section E)*
- **Permissions**: `contents: write`, `actions: read`
- **Jobs**:
  - `resolve_context` — no scripts; pure shell routing
  - `readiness` — `python3 scripts/verify_real_champion_pointer.py`. `needs: [resolve_context]`
  - `training_role_stat_calibration` — `if: needs.resolve_context.outputs.run_training == 'true'`, `needs: [resolve_context, readiness]`
    - `python3 scripts/refresh_bdl_player_game_stats.py --start-date "$ASOF" --end-date "$ASOF" --force-rewrite`
    - `python3 scripts/run_nightly_training_and_calibration.py --as-of-date "$ASOF" [--no-promote]`
    - Commits `artifacts/models`, `artifacts/model_diagnostics`, `artifacts/docs`, `artifacts/automation_health`, `data/oof_pmfs.parquet`, `data/oof_combo_pmfs.parquet`, `data/oof_combo_pmfs.manifest.json`
  - `phase8_pmf_calibration_diagnostics_market_eval` — `if: always() && run_phase8=='true'`, `needs: [resolve_context, readiness, training_role_stat_calibration]`
    - `python3 scripts/train.py --build-table-only`
    - For each FOLD in 1..4: `python3 scripts/calibrate_pmf.py --fold-index $FOLD --max-folds 4 --emit-fold-oof artifacts/folds/fold_${FOLD}.parquet --skip-final-fit --core-props-only`
    - `python3 scripts/calibrate_pmf.py --aggregate-mode --aggregate-oofs artifacts/folds/`
    - `python3 scripts/build_combo_oof_pmfs_from_base_oof.py --in data/oof_pmfs.parquet --out data/oof_combo_pmfs.parquet --manifest data/oof_combo_pmfs.manifest.json --as-of-date "$ASOF" --n-draws 20000`
    - `PYTHONPATH=src python3 scripts/fit_combo_pmf_calibrators.py --oof data/oof_combo_pmfs.parquet`
    - `python3 scripts/run_diagnostics.py --run-date "$D" --require-market-eval --allow-provisional-block --start-date 2026-04-01 --end-date "$D" --snapshot-substr close_or_lock`
    - `python3 scripts/verify_no_unexplained_calibration_nans.py --meta "artifacts/docs/diagnostics_${D}.meta.json"`
    - `python3 scripts/verify_role_bucket_contract.py`
    - `python3 scripts/verify_combo_role_calibration_contract.py || true`
  - `phase13_live_context_contextual_lineup` — `if: always() && run_phase13=='true'`, `needs: [resolve_context, readiness, phase8_*]`
    - Phase 13O: `build_live_context_training_dataset.py --as-of-date "$ASOF" --start-date 2023-10-24`, `verify_live_context_feature_training.py`, `verify_live_context_pmf_sensitivity.py`, `_phase13o_check_no_leakage.py`, `_phase13o_record_derek_readiness.py`
    - Phase 13P: `train_live_context_challenger.py --as-of-date "$ASOF" [--dry-run]`, `verify_live_context_feature_training.py --feature-set-id phase13p_lineup_injury_driver_v1`, `verify_live_context_pmf_sensitivity.py`, `verify_phase13p_no_leakage.py`, `verify_phase13p_validation_gates.py`, `verify_phase13l_no_breakage.py`
    - Phase 13Q: `train_contextual_challenger.py --as-of-date "$ASOF" [--dry-run]`, `verify_live_context_feature_training.py --feature-set-id phase13q_contextual_pmf_engine_v1`, then same 4 verifiers as 13P
    - Phase 13R: `_phase13r_write_state_audit.py`, `verify_contextual_feature_lists.py`, `verify_contextual_predict_path.py`, `verify_contextual_pmf_sensitivity.py`, `verify_phase13q_no_leakage.py`, `verify_phase13l_no_breakage.py`, then (when `no_promote != 'true'`) `promote_contextual_challenger.py`, `verify_phase13r_deployment.py`
    - Phase 13S: `_phase13s_write_baseline_audit.py`, `build_direct_lineup_training_dataset.py --as-of-date "$ASOF"`, `train_direct_lineup_contextual_challenger.py --as-of-date "$ASOF"`, `verify_direct_lineup_feature_lists.py`, `verify_direct_lineup_pmf_sensitivity.py`, `verify_phase13s_validation_gates.py`, `verify_phase13s_no_leakage.py`, `verify_phase13l_no_breakage.py`, then (when `no_promote != 'true'`) `promote_direct_lineup_challenger.py`, `verify_phase13s_deployment.py`, then regression verifiers (`verify_contextual_*`, `verify_phase13q_no_leakage.py`), then `run_phase13s_after_game_scoring.py --delivery-date "$ASOF" || true`
  - `delivery_build` — `if: run_delivery == 'true'`, `needs: [resolve_context, readiness]` *(brief Phase 7 — delivery must not depend on training/phase8/phase13)*
    - `python3 scripts/run_daily_delivery_pipeline.py --date "$D" --mode "$MODE" --regions us us2 --rebuild-canonical --verify --fail-on-missing-delivery [--predict]`
    - `stamp_delivery_champion_metadata.py --delivery-date "$D" || true`
    - `strip_empty_delivery_columns.py --date "$D" --write`
    - `write_delivery_review_previews.py --date "$D"`
    - `enforce_delivery_csv_size_contract.py --date "$D" --max-bytes 524288 --preserve derek_forward_feed/derek_unique_props_summary.csv --write`
    - Delivery verifiers: `verify_daily_delivery_folder_contract.py --date "$D"`, `verify_model_only_parquet_selection.py --date "$D" || true`, `validate_production_pmf_math.py || true`, `validate_daily_pmf_delivery.py --date "$D" --train-through-date "$TRAIN_THROUGH" --pipeline-mode "$MODE" || true`, `verify_derek_forward_feed.py --delivery-date "$D" --mode production --allow-pending-lineup || true`
    - `build_deliveries_index.py || true`, then commit
  - `after_game_scoring` — `if: run_after_game == 'true'`, `needs: [resolve_context, readiness]`
    - `python3 scripts/run_after_game_complete_scoring.py --date "$D"`
    - `verify_after_game_scoring_package_consistency.py --delivery-date "$D"`
    - `strip_empty_delivery_columns.py`, `write_delivery_review_previews.py`, `enforce_delivery_csv_size_contract.py` (same flags as `delivery_build`)
    - `build_deliveries_index.py || true`, then commit
  - `final_contract_verifiers` — `if: always() && run_verifiers == 'true'`, `needs: [resolve_context, readiness, delivery_build, after_game_scoring]`
    - `verify_real_champion_pointer.py`
    - `verify_daily_delivery_folder_contract.py --date "$D" || true`
    - `verify_morning_delivery_completeness.py --date "$D" || true`
    - `verify_model_only_parquet_selection.py --date "$D" || true`
    - `validate_production_pmf_math.py || true`
    - `validate_daily_pmf_delivery.py --date "$D" --train-through-date "$TRAIN_THROUGH" --pipeline-mode "$MODE" || true`
    - `verify_derek_forward_feed.py --delivery-date "$D" --mode production --allow-pending-lineup || true`
    - `verify_after_game_scoring_package_consistency.py --delivery-date "$D" || true` (only when after_game_scoring dir exists)
    - `enforce_delivery_csv_size_contract.py --date "$D" --max-bytes 524288 --preserve derek_forward_feed/derek_unique_props_summary.csv`
- **Notes**:
  - Name: `NBA PMF Delivery`. New consolidated workflow added in commit `92dddf53` (2026-05-19 ET).
  - `delivery_build` already correctly does **not** depend on training/phase8/phase13.
  - Manual `no_promote` default is `"true"` — matches brief rule 01.
  - Workflow-level concurrency present — brief asks to remove and use job-level (Section E).
  - **Missing**: schedule resolver (`scripts/resolve_nba_pmf_schedule.py`) — `resolve_context` job is shell routing only today. Brief Phase 1 requires a Python script.

### `nightly_training_calibration.yml`

- **Trigger**:
  - `schedule`:
    - `- cron: '30 9 * * *'`   # 09:30 UTC early morning (post-after_game)
    - `- cron: '30 12 * * *'`  # 12:30 UTC late morning retry
    - `- cron: '30 15 * * *'`  # 15:30 UTC early afternoon retry
    - `- cron: '30 18 * * *'`  # 18:30 UTC late afternoon retry
    - `- cron: '30 21 * * *'`  # 21:30 UTC evening retry (before WoO close)
  - `workflow_dispatch`: `as_of_date`, `dry` (default `"false"`), `no_promote` (manual default `"true"`), `allow_stale_safe_date`
- **Concurrency**: none (job-level: `phase13a-nightly-training`, cancel-in-progress `false`)
- **Jobs**:
  - `nightly_training`:
    - `verify_secrets_preflight.py --mode training`
    - `_bootstrap_champion_registry.py`
    - **Pre-resolver BDL backfill** (Phase 13AE): `backfill_player_game_stats_from_bdl.py --from-date "$FROM_DATE" --to-date "$PREV_DAY_ET"` then `verify_player_game_stats_freshness.py --required-through-date "$PREV_DAY_ET"`
    - Commit `data/player_game_stats.parquet` (Phase 13AF auto-refresh)
    - `resolve_previous_day_et_target.py [--allow-stale-safe-date]`
    - `check_training_inputs.py --as-of-date $D`, `prepare_training_inputs.py --as-of-date $D`
    - `run_nightly_training_and_calibration.py --as-of-date $D $DRY_FLAG $NO_PROMOTE_FLAG $STALE_FLAG`
    - `write_aggregate_input_audit.py --as-of-date $D`
    - `verify_training_automation.py --as-of-date $D`
    - `verify_daily_automation_health.py`
    - `build_daily_model_training_report.py --as-of-date $D`
    - Commit
- **Notes**:
  - Phase 13A — daily champion/challenger training. Promotion forbidden at or after 14:30 UTC.
  - Deferred-retry pattern (Phase 13AJ): resolver halt = valid skip, not failure.
  - Comment notes H4 TODO on backfill exit codes; H13: scoped `rm -rf` instead of `git clean -fd`.

### `phase8.yml`

- **Trigger**: `workflow_run: ["NBA Props Model — Retrain"] [completed] [main]`, `workflow_dispatch` (inputs: `note`, `max_folds=4`, `core_props_only=true`, `allow_local_build_fallback=false`, `val_rows_limit=""`, `pmf_draws=3000`)
- **Concurrency**: none
- **Jobs** (5):
  - `build-table` — `python scripts/train.py --build-table-only`
  - `setup-matrix` — inline Python generates fold list
  - `calibrate-fold` (matrix, `fail-fast: false`, `max-parallel: 5`) — `python scripts/calibrate_pmf.py --fold-index ${{ matrix.fold }} --max-folds $MAX_FOLDS --emit-fold-oof artifacts/fold_${{ matrix.fold }}.parquet --skip-final-fit [--core-props-only] [--val-rows-limit] [--pmf-draws]`
  - `aggregate-calibration` — `calibrate_pmf.py --aggregate-mode --aggregate-oofs artifacts/folds/`, then `build_combo_oof_pmfs_from_base_oof.py --in data/oof_pmfs.parquet --out data/oof_combo_pmfs.parquet --manifest data/oof_combo_pmfs.manifest.json --as-of-date "$(date -u +%F)" --n-draws 20000`, then `fit_combo_pmf_calibrators.py --oof data/oof_combo_pmfs.parquet`
  - `diagnostics` — `run_diagnostics.py --run-date $RUN_DATE --require-market-eval --allow-provisional-block --start-date 2026-04-01 --end-date $RUN_DATE --snapshot-substr close_or_lock [--core-props-only]`, `verify_phase8_market_eval_contract.py`, `verify_no_unexplained_calibration_nans.py`, then commit
- **Notes**: H1B chain — auto-fires after `retrain.yml` succeeds. Only the final job pushes to origin/main. H17: refuses to commit empty calibrators.

### `phase13o_live_context_training.yml`

- **Trigger**: `workflow_run: ["NBA Props Model — Phase 8 ..."] [completed] [main]`, `workflow_dispatch` (inputs: `as_of_date`, `start_date=2023-10-24`, `dry_run=false`)
- **Concurrency**: job-level `phase13o-live-context-${{ as_of_date || 'today' }}`, cancel-in-progress `false`
- **Jobs**: `phase13o_live_context_training` — `build_live_context_training_dataset.py --as-of-date $D --start-date $START [--dry-run]`, `verify_live_context_feature_training.py`, `verify_live_context_pmf_sensitivity.py`, `_phase13o_check_no_leakage.py`, `_phase13o_record_derek_readiness.py`, then commit `data/live_context_features.parquet` and `artifacts/phase13o`
- **Notes**: Does NOT call `run_nightly_training_and_calibration.py`. Read-only verification of champion (no promotion).

### `phase13p_live_context_challenger.yml`

- **Trigger**: `workflow_run: ["Phase 13O ..."] [completed] [main]`, `workflow_dispatch` (`as_of_date`, `dry_run=false`)
- **Concurrency**: job-level `phase13p-live-context-${{ as_of_date || 'today' }}`
- **Jobs**: `build_live_context_training_dataset.py --as-of-date $D`, `train_live_context_challenger.py --as-of-date $D [--dry-run]`, `verify_live_context_feature_training.py --feature-set-id phase13p_lineup_injury_driver_v1`, `verify_live_context_pmf_sensitivity.py`, `verify_phase13p_no_leakage.py`, `verify_phase13p_validation_gates.py`, `verify_phase13l_no_breakage.py`, then commit
- **Notes**: Does NOT auto-promote. H1B chain — auto-fires after phase13o.

### `phase13q_contextual_challenger.yml`

- **Trigger**: `workflow_run: ["Phase 13P ..."] [completed] [main]`, `workflow_dispatch` (`as_of_date`, `dry_run=false`)
- **Concurrency**: job-level `phase13q-contextual-${{ as_of_date || 'today' }}`
- **Jobs**: `build_live_context_training_dataset.py --as-of-date $D`, `train_contextual_challenger.py --as-of-date $D [--dry-run]`, `verify_live_context_feature_training.py --feature-set-id phase13q_contextual_pmf_engine_v1`, then same verifiers as 13P, then commit including `artifacts/phase13q`
- **Notes**: Does NOT auto-promote. H1B chain — auto-fires after phase13p.

### `phase13r_contextual_deployment_verification.yml`

- **Trigger**: `workflow_run: ["Phase 13Q ..."] [completed] [main]`, `workflow_dispatch` (`challenger_dir`, `force_promote=false`, `allow_future_trained_through=false`)
- **Concurrency**: job-level `phase13r-contextual-deployment`
- **Jobs**: `_phase13r_write_state_audit.py`, `verify_contextual_feature_lists.py`, `verify_contextual_predict_path.py`, `verify_contextual_pmf_sensitivity.py`, `verify_phase13q_no_leakage.py`, `verify_phase13l_no_breakage.py`, `promote_contextual_challenger.py [--challenger-dir] [--force] [--allow-future-trained-through]`, `verify_phase13r_deployment.py`, then commit `champion_pointer.json` etc.
- **Notes**: H1B chain — auto-fires after phase13q (parallel with phase13s). **Touches `champion_pointer.json`**.

### `phase13s_direct_lineup_contextual_pmf.yml`

- **Trigger**: `workflow_run: ["Phase 13Q ..."] [completed] [main]`, `workflow_dispatch` (`as_of_date`, `dry_run=false`, `promote_if_pass=true`, `allow_future_trained_through=false`, `force_promote=false`)
- **Concurrency**: job-level `phase13s-direct-lineup-contextual`
- **Jobs**: `_phase13s_write_baseline_audit.py`, `build_direct_lineup_training_dataset.py --as-of-date $D`, `train_direct_lineup_contextual_challenger.py --as-of-date $D [--dry-run]`, `verify_direct_lineup_feature_lists.py`, `verify_direct_lineup_pmf_sensitivity.py`, `verify_phase13s_validation_gates.py`, `verify_phase13s_no_leakage.py`, `verify_phase13l_no_breakage.py`, `promote_direct_lineup_challenger.py [--allow-future-trained-through] [--force]`, `verify_phase13s_deployment.py`, regression: `verify_contextual_*` + `verify_phase13q_no_leakage.py`, `run_phase13s_after_game_scoring.py --delivery-date $D || true`, then commit
- **Notes**: H1B chain — auto-fires after phase13q (parallel with phase13r). **Touches `champion_pointer.json`**.

### `derek_live_game_snapshots.yml`

- **Trigger**:
  - `schedule`: `- cron: '0,10,20,30,40,50 16,17,18,19,20,21,22,23,0,1,2,3,4 * * *'`
  - `workflow_dispatch`: `delivery_date`, `snapshot_type=all` (`current_live | t_minus_25 | close_lock | both | all`), `allow_backfill_test=false`, `max_games`, `force=false`
- **Concurrency**: job-level `derek-live-snapshots-${{ delivery_date || 'today' }}-${{ snapshot_type || 't_minus_25' }}`
- **Jobs** (~28 steps; abbreviated): `verify_secrets_preflight.py --mode daily`, `resolve_game_start_times.py`, `enrich_predictions_game_start_times.py`, `verify_derek_slate_completeness.py`, three `dispatch_derek_live_game_snapshots.py --snapshot-type <current_live|t_minus_25|close_lock>` calls, `verify_corrected_pmf_delivery.py --date $D --skip-derek-snapshots`, `verify_derek_live_api_readiness.py`, `verify_predict_lineup_context.py`, `verify_derek_live_champion_ready.py --delivery-date $D`, `build_derek_snapshot_comparison.py`, legacy diagnostics (`verify_derek_live_snapshots.py`, `verify_bdl_fetch_proof_for_derek.py`, `audit_contextual_delta_variation.py`), `build_derek_delivery_readme.py`, Phase 13X edge audits (`audit_derek_edge_root_cause.py`, `audit_derek_calibration_for_edge_buckets.py --as-of-date "$AS_OF"`, `apply_derek_edge_publishability.py`, `append_phase13x_edge_section_to_reports.py`), `render_derek_human_reports.py`, `verify_derek_outcome_level_probabilities.py`, `verify_phase13x_woo_unchanged.py`, `verify_derek_production_live_e2e.py`, `verify_phase13l_no_breakage.py`, `verify_daily_retrain_recalibration.py --as-of-date "$AS_OF"`, `build_daily_model_training_report.py --as-of-date "$AS_OF"`, `score_derek_live_snapshots_after_game.py`, `build_rolling_derek_snapshot_benchmark.py --as-of-date $D --window-days 28`, then commit
- **Notes**: "restored schedule-proven Derek workflow path". Phase 13L: Derek-only — never modifies WoO or pmf_model_review_package. Also triggered by `derek_schedule_bridge` job in `daily_pmf_delivery.yml`. Legacy diagnostic steps marked non-authoritative.

### `m86_delivery_contract_verifiers.yml`

- **Trigger**: `pull_request` and `push` on `main`
- **Concurrency**: `m86-contract-verifiers-${{ github.ref }}`, cancel-in-progress `true`
- **Jobs**: `static_contracts` — `verify_oddsapi_market_registry_contract.py`, `verify_no_legacy_prediction_artifacts.py`
- **Notes**: Static contract checks (no API keys, no dated delivery artifacts).

### `wizard_of_odds_ftp_deploy.yml`

- **Trigger**: `workflow_dispatch` (`check_only`, `allow_plain=true`, `walk_only`), `workflow_run: ["NBA PMF Delivery — Daily Pipeline"] [completed]`
- **Concurrency**: `${{ github.workflow }}-${{ github.ref }}`, cancel-in-progress `false`
- **Jobs**: `deploy` — `predictions_readiness_gate.py --date $D --predict-cron-hour-utc 13 --mode "ftp_deploy" --no-run-predict`, four WoO build/verify calls (`publish_woo_public_export.py`, `build_woo_dashboard.py`, `verify_woo_dashboard_render_contract.py`, `verify_woo_public_export_contract.py`), `verify_woo_deploy_workflow_contract.py`, `verify_corrected_pmf_delivery.py --date $D --skip-derek-snapshots`, `deploy_wizard_of_odds_ftp.py [--check-connection] [--dry-run] [--allow-plain]`
- **Notes**: Phase 12B/12D/12E/12F/13AM. Triggers on `workflow_run` of `"NBA PMF Delivery — Daily Pipeline"`. Hard rules: credentials from secrets only, FTPS-first with plain-FTP fallback, never stages outside `public_export/wizard_of_odds/`.

### Workflow summary table

| Workflow | Triggers | Job count | Live? |
| --- | --- | --- | --- |
| `daily_pmf_delivery.yml` | cron (9) + workflow_run + dispatch | 7 | yes (current production) |
| `nba_pmf_delivery.yml` | cron (14) + dispatch | 8 | being built (consolidation target) |
| `nightly_training_calibration.yml` | cron (5) + dispatch | 1 | yes |
| `phase8.yml` | workflow_run + dispatch | 5 | yes (H1B chain) |
| `phase13o_live_context_training.yml` | workflow_run + dispatch | 1 | yes (H1B chain) |
| `phase13p_live_context_challenger.yml` | workflow_run + dispatch | 1 | yes (H1B chain) |
| `phase13q_contextual_challenger.yml` | workflow_run + dispatch | 1 | yes (H1B chain) |
| `phase13r_contextual_deployment_verification.yml` | workflow_run + dispatch | 1 | yes (H1B chain) |
| `phase13s_direct_lineup_contextual_pmf.yml` | workflow_run + dispatch | 1 | yes (H1B chain) |
| `derek_live_game_snapshots.yml` | cron (1, every 10 min) + dispatch | 1 | yes ("restored schedule-proven") |
| `m86_delivery_contract_verifiers.yml` | push + pull_request | 1 | yes (CI gate) |
| `wizard_of_odds_ftp_deploy.yml` | workflow_run + dispatch | 1 | yes |

---

## Section B — Key-script argparse

Captured by running `python3 <script> --help` in the repo with the
production interpreter. These are the **canonical flag names** —
later phases must not invent flags that don't appear here.

### `scripts/run_daily_delivery_pipeline.py`

```
usage: run_daily_delivery_pipeline.py [-h] --date DATE
                                      (--mode {woo_morning_monetization,woo_afternoon_refresh,derek_pre_tipoff_refresh,derek_near_lineup,close_lock,after_game,full_day,morning,pre_close} | --run-mode {morning_expected,t25,t5,final_after_game,backtest})
                                      [--regions REGIONS [REGIONS ...]]
                                      [--rebuild-canonical] [--predict]
                                      [--force-run] [--verify]
                                      [--fail-on-missing-delivery]
```

- `--date DATE` (required) — delivery calendar date YYYY-MM-DD (US/Eastern).
- `--mode` XOR `--run-mode` (one required):
  - `--mode`: legacy pipeline mode (Phase 12D). `derek_near_lineup` is a legacy alias for `derek_pre_tipoff_refresh`.
  - `--run-mode`: M8.8 consumer run mode (preferred). Maps to internal `--mode`.
- `--regions us us2` — pass-through.
- `--rebuild-canonical` — pass-through to `build_daily_pmf_delivery.py`.
- `--predict` — run `scripts/predict.py` before refresh in `morning` / `full_day` modes.
- `--force-run` — bypass tipoff-window gate (Phase 12D).
- `--verify` — run M8.8 delivery completeness + Derek contract + audits after pipeline.
- `--fail-on-missing-delivery` — non-zero exit if any verifier fails (implies `--verify`).

### `scripts/predictions_readiness_gate.py`

```
usage: predictions_readiness_gate.py [-h] --date DATE
                                     [--predict-cron-hour-utc PREDICT_CRON_HOUR_UTC]
                                     --mode MODE [--no-run-predict]
                                     [--force-run-predict]
```

- `--date` (required) — slate date YYYY-MM-DD.
- `--mode` (required) — delivery mode (`morning`, `derek_pre_tipoff_refresh`, `after_game`, ...). `derek_near_lineup` accepted as legacy alias.
- `--predict-cron-hour-utc N` — hour (UTC) at which the daily predict cron is scheduled.
- `--no-run-predict` — do NOT invoke `predict.py` when predictions are missing (after-game uses this — past slates can't regenerate).
- `--force-run-predict` — allow `predict.py` invocation even before the scheduled predict cron hour (same-day manual backfills).

**Output contract** (exactly one token on stdout): `PREDICTIONS_READY`, `WAITING_FOR_PREDICTIONS_VALID_SKIP`, `PREDICT_PY_FAILED`, or `PREDICT_OUTPUTS_MISSING`. Also writes `should_proceed=true|false` to `$GITHUB_OUTPUT`.

### `scripts/run_nightly_training_and_calibration.py`

```
usage: run_nightly_training_and_calibration.py [-h] [--as-of-date AS_OF_DATE]
                                               [--dry-run] [--no-dry-run]
                                               [--no-promote]
                                               [--skip-outcome-refresh]
                                               [--allow-stale-safe-date]
                                               [--use-legacy-resolver]
```

- `--as-of-date YYYY-MM-DD` — if omitted, runs `scripts/resolve_latest_safe_training_date.py`.
- `--dry-run` (default) / `--no-dry-run` — Phase 13D: real challenger calibration runs by default; pass `--no-dry-run` to actually retrain.
- `--no-promote` — run all stages but never promote, even if validation passes.
- `--skip-outcome-refresh` — skip BDL outcome refresh step.
- `--allow-stale-safe-date` — Phase 13G opt-in fallback. Scheduled workflow does NOT pass this flag — it halts cleanly with `halted_reason=previous_day_data_not_ready` instead.
- `--use-legacy-resolver` — backwards compat only.

> **Important for Phase 1**: the brief asks for `allow_promote=true` on morning crons and `no_promote=true` on afternoon retries. This script accepts `--no-promote` only (no `--allow-promote`). The Phase 1 schedule resolver must surface `no_promote` (not `allow_promote`) when invoking this script.

### `scripts/run_after_game_complete_scoring.py`

```
usage: run_after_game_complete_scoring.py [-h] --date DATE
```

Only `--date`. No other flags.

### `scripts/enforce_delivery_csv_size_contract.py`

```
usage: enforce_delivery_csv_size_contract.py [-h] --date DATE
                                             [--max-bytes MAX_BYTES] [--write]
                                             [--preserve PRESERVE]
```

- `--date` (required).
- `--max-bytes N` — default budget.
- `--write` — actually rewrite (default: dry-run report).
- `--preserve PATH` — path relative to `deliveries/<date>` that must never be modified (used to protect `derek_unique_props_summary.csv`).

### `scripts/build_derek_forward_feed.py`

```
usage: build_derek_forward_feed.py [-h] --date DATE [--run-mode RUN_MODE]
                                   [--snapshot {morning,lineup,both}]
```

- `--date` (required).
- `--run-mode` — M8.8 stamp for unified Derek feed (`morning_expected|t25|t5|final_after_game|backtest|unspecified`).
- `--snapshot {morning,lineup,both}` — which snapshot to build.

---

## Section C — Referenced-script existence map

All scripts referenced in Section A workflow invocations exist on
disk and are non-empty. None of the workflow invocations is calling a
phantom file.

| Script | Lines | Used by |
| --- | --- | --- |
| `scripts/run_daily_delivery_pipeline.py` | 1886 | `daily_pmf_delivery.yml` (all delivery jobs), `nba_pmf_delivery.yml` (`delivery_build`) |
| `scripts/predictions_readiness_gate.py` | 464 | `daily_pmf_delivery.yml`, `wizard_of_odds_ftp_deploy.yml` |
| `scripts/run_nightly_training_and_calibration.py` | 663 | `nightly_training_calibration.yml`, `nba_pmf_delivery.yml` (`training_role_stat_calibration`) |
| `scripts/run_after_game_complete_scoring.py` | 233 | `daily_pmf_delivery.yml` (`after_game`), `nba_pmf_delivery.yml` (`after_game_scoring`) |
| `scripts/enforce_delivery_csv_size_contract.py` | 335 | `nba_pmf_delivery.yml` (delivery_build + after_game + final_verifiers) |
| `scripts/build_derek_forward_feed.py` | 2153 | invoked indirectly via `run_daily_delivery_pipeline.py` |
| `scripts/train.py` | 33 | `phase8.yml`, `nba_pmf_delivery.yml` (`phase8`) |
| `scripts/calibrate_pmf.py` | 1476 | `phase8.yml`, `nba_pmf_delivery.yml` |
| `scripts/build_combo_oof_pmfs_from_base_oof.py` | 532 | `phase8.yml`, `nba_pmf_delivery.yml` |
| `scripts/fit_combo_pmf_calibrators.py` | 408 | `phase8.yml`, `nba_pmf_delivery.yml` |
| `scripts/run_diagnostics.py` | 880 | `phase8.yml`, `nba_pmf_delivery.yml` |
| `scripts/verify_phase8_market_eval_contract.py` | 113 | `phase8.yml` |
| `scripts/verify_no_unexplained_calibration_nans.py` | 83 | `phase8.yml`, `nba_pmf_delivery.yml` |
| `scripts/build_live_context_training_dataset.py` | 301 | Phase 13O/P/Q, `nba_pmf_delivery.yml` |
| `scripts/train_live_context_challenger.py` | 428 | `phase13p_live_context_challenger.yml`, `nba_pmf_delivery.yml` |
| `scripts/train_contextual_challenger.py` | 398 | `phase13q_contextual_challenger.yml`, `nba_pmf_delivery.yml` |
| `scripts/promote_contextual_challenger.py` | 353 | `phase13r_*.yml`, `nba_pmf_delivery.yml` |
| `scripts/promote_direct_lineup_challenger.py` | 298 | `phase13s_*.yml`, `nba_pmf_delivery.yml` |
| `scripts/verify_phase13r_deployment.py` | 337 | `phase13r_*.yml`, `nba_pmf_delivery.yml` |
| `scripts/verify_phase13s_deployment.py` | 312 | `phase13s_*.yml`, `nba_pmf_delivery.yml` |
| `scripts/resolve_previous_day_et_target.py` | 226 | `nightly_training_calibration.yml` |
| `scripts/resolve_latest_safe_training_date.py` | 118 | `run_nightly_training_and_calibration.py` (called when `--as-of-date` omitted) |
| `scripts/verify_derek_forward_feed_contract.py` | 104 | `daily_pmf_delivery.yml` (M8.8 audits) |
| `scripts/audit_daily_delivery_completeness.py` | 486 | `daily_pmf_delivery.yml` (M8.8 audits) |
| `scripts/audit_github_delivery_automation.py` | 54 | `daily_pmf_delivery.yml` (M8.8 audits) |
| `scripts/audit_injury_lineup_run_modes.py` | 297 | `daily_pmf_delivery.yml` (M8.8 audits) |
| `scripts/verify_corrected_pmf_delivery.py` | 217 | `derek_live_game_snapshots.yml`, `wizard_of_odds_ftp_deploy.yml` |
| `scripts/publish_woo_public_export.py` | 1336 | `daily_pmf_delivery.yml`, `wizard_of_odds_ftp_deploy.yml` |
| `scripts/build_woo_dashboard.py` | 253 | `daily_pmf_delivery.yml`, `wizard_of_odds_ftp_deploy.yml` |
| `scripts/verify_woo_dashboard_render_contract.py` | 312 | `daily_pmf_delivery.yml`, `wizard_of_odds_ftp_deploy.yml` |
| `scripts/verify_woo_public_export_contract.py` | 602 | `daily_pmf_delivery.yml`, `wizard_of_odds_ftp_deploy.yml` |

---

## Section D — Comparison: `daily_pmf_delivery.yml` (production) vs `nba_pmf_delivery.yml` (consolidation target)

| Aspect | `daily_pmf_delivery.yml` (live) | `nba_pmf_delivery.yml` (target) | Brief expectation |
| --- | --- | --- | --- |
| Triggers | 9 crons + `workflow_run` + dispatch (`mode` only) | 14 crons + dispatch (`stage` + `mode`) | 15 crons + dispatch (`force_run`, stage options) |
| Schedule routing | Inline `if:` per job, hard-coded cron strings | Inline shell `resolve_context` job | **Python script** `scripts/resolve_nba_pmf_schedule.py` (Phase 1 — missing) |
| Concurrency | Workflow-level group, `cancel: false` | Workflow-level group, `cancel: false` | **Job-level only** (training by `as_of_date`, delivery by `delivery_date+mode`, after_game by `delivery_date`) — brief Phase 2 |
| Training in delivery flow | Not present (separate workflow) | `training_role_stat_calibration` job present | Training must not block delivery; delivery reads latest champion |
| Phase 8 in delivery flow | Not present (separate `phase8.yml`) | `phase8_pmf_calibration_diagnostics_market_eval` job present | Same as above — must not block delivery |
| Phase 13 chain in delivery flow | Not present (separate `phase13o-s.yml`) | `phase13_live_context_contextual_lineup` job present | Same as above |
| Delivery → predict gate | Yes (`predictions_readiness_gate.py --mode <mode>` per job) | Implicit in `delivery_build` step — uses pipeline's own gate | Brief Phase 6: dedicated `predict_daily` job at 14:00 UTC |
| `--force-run-predict` plumbing | Not in `daily_pmf_delivery.yml` (added via PR #11/#13 in `predictions_readiness_gate.py` itself) | Not surfaced as workflow input | Brief: `force_run=true` should propagate to resolver and downstream `--force-run` flags |
| CSV size contract | Not enforced in this workflow (added in `92dddf53` only in `nba_pmf_delivery.yml`) | Enforced via `enforce_delivery_csv_size_contract.py --preserve derek_forward_feed/derek_unique_props_summary.csv --max-bytes 524288 --write` | Required by brief rule 04 |
| Derek unique summary protection | None at workflow level (relied on writer code) | `--preserve` flag in CSV contract; `verify_derek_woo_champion_dependency.py` re-checks out modifications | **Mandatory**: rule 00 forbids modifying this file |
| Calibration/market-superiority gate | Lives in `phase8.yml` + nightly + Phase 13R/S; not invoked in delivery | Lives in same separate path (no consolidated gate yet) | Brief Phase 3: create `scripts/verify_calibration_market_superiority_contract.py` (missing) |
| Promotion timing | Nightly cron handles it; Phase 13R/S have `--force-promote` opt-in | `no_promote` flag default `"true"` on manual dispatch | Brief: promotion only before 14:30 UTC and only when gates pass; no-promote at 15:30/18:30/21:30 UTC |
| After-game workflow | `after_game` job inside `daily_pmf_delivery.yml` (cron `30 6 * * *`) | `after_game_scoring` job inside `nba_pmf_delivery.yml` | Brief Phase 8 — preserved |
| Old workflows | Still enabled | Still enabled (in parallel) | Brief: do not disable old workflows until the new one passes a full production day |

---

## Section E — Brief-mandated gaps & observations

Items the brief requires that DO NOT yet exist on disk (these are the
backlog for Phase 1+):

1. **Missing — `scripts/resolve_nba_pmf_schedule.py`** (Phase 1).
   The brief specifies 14 input flags and 13 outputs. Today `nba_pmf_delivery.yml::resolve_context` is shell routing only.

2. **Missing — `scripts/verify_calibration_market_superiority_contract.py`** (Phase 3).
   Brief rule 02 spells out 6 mathematical gates (proper scoring, bootstrap, calibration, reliability, no-hidden-regression, PMF validity) with explicit thresholds. The existing repo has `scripts/verify_stat_role_ucb_contract.py` (referenced by existing rule `.cursor/rules/nba-pmf-market-superiority.mdc`) but no unified contract script.

3. **Missing — 4 brief-required test files**:
   - `tests/test_nba_pmf_delivery_schedule_resolver.py` (Phase 1 cases)
   - `tests/test_nba_pmf_delivery_workflow_shape.py`
   - `tests/test_calibration_market_superiority_contract.py` (if Phase 3 script is created)
   - `tests/test_derek_bdl_empty_props_valid_skip.py` (if BDL empty-props behavior is changed)

4. **`nba_pmf_delivery.yml` currently violates brief Phase 2 in two ways**:
   - Workflow-level concurrency present (brief says remove and use job-level).
   - No dedicated `predict_daily` job at 14:00 UTC (brief Phase 6 requires it).

5. **Argparse drift risk for the resolver→pipeline contract**:
   - `run_daily_delivery_pipeline.py` accepts `--mode` XOR `--run-mode`. The resolver must commit to ONE (the brief implies `--mode` since it lists pipeline-mode names like `derek_near_lineup`).
   - `run_daily_delivery_pipeline.py` uses `--force-run` (singular) not `--force` or `--force-run-predict`. The resolver must surface this distinction:
     - `--force-run-predict` → passed to `predictions_readiness_gate.py`.
     - `--force-run` → passed to `run_daily_delivery_pipeline.py`.
   - `run_nightly_training_and_calibration.py` accepts `--no-promote` but NOT `--allow-promote`. The resolver must emit `allow_promote=true|false` semantically, but the script invocation only conditionally adds `--no-promote`.
   - `predictions_readiness_gate.py --mode <X>` accepts free-form mode strings (the script accepts `derek_near_lineup` as legacy alias for `derek_pre_tipoff_refresh`). The resolver's `mode` output is what the workflow passes here verbatim.

6. **Production-schedule alignment** (`.cursor/rules/01_production_schedule.mdc`):
   - 06:30 UTC `after_game` — `daily_pmf_delivery.yml` already has this (`30 6 * * *`).
   - 09:30/12:30 UTC `model_chain` with `allow_promote=true` — currently in `nightly_training_calibration.yml` at `30 9` / `30 12`. ✓
   - 14:00 UTC `predict` — currently inside delivery gates via `predictions_readiness_gate.py`, no standalone cron.
   - 14:30 UTC promotion cutoff — enforced inside `run_nightly_training_and_calibration.py` / Phase 13R/S? **Needs verification in Phase 3.**
   - 15:00 UTC `WoO morning` — `daily_pmf_delivery.yml` has `0 15 * * *`. ✓
   - 15:30/18:30/21:30 UTC `model_chain_no_promote` — `nightly_training_calibration.yml` has `30 15` / `30 18` / `30 21`, BUT all five crons today use the same job spec. The job must be parameterized so post-14:30 runs pass `--no-promote` and the early runs do not.
   - 22:25→03:25 UTC Derek windows — `daily_pmf_delivery.yml` has them. ✓

7. **Non-negotiables already in force**:
   - `derek_unique_props_summary.csv` is never overwritten by the existing `daily_pmf_delivery.yml` flow (delivery pipeline writes it; `verify_derek_woo_champion_dependency.py` checks it; `enforce_delivery_csv_size_contract.py --preserve` excludes it). ✓
   - Old workflows still on disk and enabled. ✓
   - Job-level `no_promote` default `"true"` in `nba_pmf_delivery.yml` workflow_dispatch. ✓

8. **Open question for Phase 1**: the brief says Derek snapshot routing should be "35 to 11 minutes pre-tip → `derek_near_lineup`; 10 to 0 minutes pre-tip → `close_lock`; otherwise `valid_skip_reason=outside_slate_delivery_window`". Today `derek_live_game_snapshots.yml` runs every 10 minutes between 16:00 and 04:00 UTC and dispatches all three snapshot types. The resolver must replicate this window logic in Python so the new workflow can valid-skip outside the lineup window.

9. **Pre-existing PyYAML strict-mode parse failure** in `.github/workflows/derek_live_game_snapshots.yml` around line 199-200. The workflow contains a bash heredoc (`python3 - <<'PY' ... PY`) inside a `run:` block where the Python code starts at column 0 (`import pandas as pd`). PyYAML 6.0.3's `safe_load` rejects this with `while scanning a simple key ... could not find expected ':'`. GitHub Actions' own YAML parser appears to accept it (the workflow does run; it's not failing at YAML parse), but this means `tests/test_nba_pmf_delivery_workflow_shape.py` (Phase 1+) and any local lint that uses PyYAML cannot include this file in its shape checks until either:
   - The brief Phase 9 verifier explicitly skips this file, or
   - The heredoc content is re-indented to live under the literal block scalar (10-space leading indent matching the rest of the `run:` block).
   We do not change this file in Phase 0 (scope: docs only). Note it so Phase 1 tests don't break.

10. **Pre-existing runtime failures on `derek_live_game_snapshots.yml`**. Last 5 scheduled runs on 2026-05-20 ET (between 02:00 and 03:55 UTC) all `completed/failure`. This is unrelated to the YAML parse issue above and unrelated to the consolidation work — but it's a live production hot-spot the operator should be aware of. Phase 0 does NOT investigate or fix this. It is a candidate for a separate hot-fix branch.

---

*End of inventory. Next phase: build `scripts/resolve_nba_pmf_schedule.py` plus `tests/test_nba_pmf_delivery_schedule_resolver.py` using ONLY the canonical flags and modes recorded above.*
