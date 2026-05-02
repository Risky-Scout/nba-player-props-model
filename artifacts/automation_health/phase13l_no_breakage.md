# Phase 13L No-Breakage Verification

- generated_at_utc: 2026-05-02T13:12:55+00:00
- passed: **True**

## Checks

| Check | Pass | Detail |
| --- | --- | --- |
| pass_token_present:TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS | yes | in scripts/verify_training_automation.py |
| pass_token_present:TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS | yes | in scripts/verify_training_automation.py |
| pass_token_present:PREVIOUS_DAY_NO_LEAKAGE_VERIFICATION_PASS | yes | in scripts/verify_previous_day_no_leakage.py |
| pass_token_present:PREVIOUS_DAY_SOURCE_COMPLETENESS_PASS | yes | in scripts/verify_previous_day_source_completeness.py |
| pass_token_present:CHAMPION_POINTER_METADATA_PASS | yes | in scripts/verify_champion_pointer_metadata.py |
| pass_token_present:DEREK_WOO_CHAMPION_DEPENDENCY_PASS | yes | in scripts/verify_derek_woo_champion_dependency.py |
| pass_token_present:DELIVERY_CHAMPION_METADATA_STAMP_PASS | yes | in scripts/stamp_delivery_champion_metadata.py |
| pass_token_present:EXPECTED_TARGET_STATS_COVERAGE_ACCOUNTED_PASS | yes | in scripts/score_daily_pmf_delivery_after_game.py |
| pass_token_present:MODEL_VS_MARKET_SCORING_PASS | yes | in scripts/score_daily_pmf_delivery_after_game.py |
| pass_token_present:AFTER_GAME_SCORING_PACKAGE_CONSISTENCY_PASS | yes | in scripts/verify_after_game_scoring_package_consistency.py |
| pass_token_present:ROLLING_MARKET_BENCHMARK_PASS | yes | in scripts/build_rolling_market_benchmark.py |
| pass_token_present:DAILY_AUTOMATION_HEALTH_PASS | yes | in scripts/verify_daily_automation_health.py |
| workflow_present:.github/workflows/daily_pmf_delivery.yml | yes |  |
| workflow_references:.github/workflows/daily_pmf_delivery.yml::stamp_delivery_champion_metadata.py | yes | ok |
| workflow_references:.github/workflows/daily_pmf_delivery.yml::verify_after_game_scoring_package_consistency.py | yes | ok |
| workflow_references:.github/workflows/daily_pmf_delivery.yml::build_rolling_market_benchmark.py | yes | ok |
| workflow_present:.github/workflows/nightly_training_calibration.yml | yes |  |
| workflow_references:.github/workflows/nightly_training_calibration.yml::verify_training_automation.py | yes | ok |
| workflow_references:.github/workflows/nightly_training_calibration.yml::verify_daily_automation_health.py | yes | ok |
| workflow_references:.github/workflows/nightly_training_calibration.yml::resolve_previous_day_et_target.py | yes | ok |
| champion_pointer_rich_fields_present | yes | all rich fields present |
| derek_live_snapshots_did_not_pollute_protected_dirs | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::snapshot_mode = "backfill_demo" if allow_backfill  | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::champion_metadata_verified | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::lineup_feature_blocker | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::all_production_recomputed | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::DEREK_LINEUP_CONTEXT_DOCUMENTED_PASS | yes | ok |
