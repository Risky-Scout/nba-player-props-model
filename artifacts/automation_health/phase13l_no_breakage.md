# Phase 13L No-Breakage Verification

- generated_at_utc: 2026-07-24T22:49:54+00:00
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
| phase13_correction_token:run_derek_live_game_snapshot.py::snapshot_mode = "backfill_demo" | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::snapshot_mode = "production_live_current" | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::snapshot_mode = "production_live" | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::champion_metadata_verified | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::lineup_feature_blocker | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::--derek-live-snapshot | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::lineup_integration_summary | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::lineup_source_equivalence_verified | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::injury_availability_hash | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::market_snapshot_hash | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::lineup_context.parquet | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::injury_availability_context.parquet | yes | ok |
| phase13_correction_token:run_derek_live_game_snapshot.py::prediction_input_audit.parquet | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::all_production_recomputed | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::DEREK_LINEUP_CONTEXT_DOCUMENTED_PASS | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::DEREK_INJURY_AVAILABILITY_CONTEXT_PASS | yes | ok |
| phase13_correction_token:verify_derek_live_snapshots.py::BDL_LINEUPS_FETCH_PASS | yes | ok |
| phase13_correction_token:predict.py::_derek_live_args | yes | ok |
| phase13_correction_token:predict.py::_join_lineup_context_into_rows | yes | ok |
| phase13_correction_token:predict.py::PREDICT_DEREK_LIVE_ARGS_PASS | yes | ok |
| phase13_correction_token:predict.py::PREDICT_LINEUP_CONTEXT_FEATURE_INTEGRATION_PASS | yes | ok |
| phase13_correction_token:predict.py::derek_live_predictions.parquet | yes | ok |
| phase13_correction_token:verify_derek_live_api_readiness.py::DEREK_LIVE_API_READINESS_PASS | yes | ok |
| phase13_correction_token:verify_derek_live_api_readiness.py::BDL_API_KEY | yes | ok |
| phase13_correction_token:verify_derek_live_api_readiness.py::get_lineups | yes | ok |
| phase13_correction_token:verify_derek_live_api_readiness.py::get_injuries | yes | ok |
| phase13_correction_token:live_context.py::PHASE13O_LIVE_CONTEXT_FEATURES_PASS | yes | ok |
| phase13_correction_token:live_context.py::LINEUP_FEATURE_COLUMNS | yes | ok |
| phase13_correction_token:live_context.py::INJURY_FEATURE_COLUMNS | yes | ok |
| phase13_correction_token:live_context.py::VACATED_OPPORTUNITY_FEATURE_COLUMNS | yes | ok |
| phase13_correction_token:live_context.py::build_live_context_features | yes | ok |
| phase13_correction_token:live_context.py::feature_set_id | yes | ok |
| phase13_correction_token:live_context.py::phase13o_live_context_v1 | yes | ok |
| phase13_correction_token:build_live_context_training_dataset.py::PHASE13O_LIVE_CONTEXT_TRAINING_DATASET_PASS | yes | ok |
| phase13_correction_token:build_live_context_training_dataset.py::PHASE13O_LINEUP_HISTORY_LIMITED | yes | ok |
| phase13_correction_token:build_live_context_training_dataset.py::no_future_leakage_verified | yes | ok |
| phase13_correction_token:build_live_context_training_dataset.py::asof_cutoff_rule | yes | ok |
| phase13_correction_token:verify_live_context_pmf_sensitivity.py::PHASE13O_FEATURE_VECTOR_SENSITIVITY_PASS | yes | ok |
| phase13_correction_token:verify_live_context_pmf_sensitivity.py::PHASE13O_ACTIONABILITY_SENSITIVITY_PASS | yes | ok |
| phase13_correction_token:verify_live_context_pmf_sensitivity.py::PHASE13O_MARKET_ONLY_EDGE_SENSITIVITY_PASS | yes | ok |
| phase13_correction_token:verify_live_context_pmf_sensitivity.py::PHASE13O_PMF_SENSITIVITY_PENDING_RETRAINED_ARTIFAC | yes | ok |
| phase13_correction_token:verify_live_context_pmf_sensitivity.py::PHASE13P_PMF_SENSITIVITY_PASS | yes | ok |
| phase13_correction_token:train_live_context_challenger.py::PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINER_READY_PAS | yes | ok |
| phase13_correction_token:train_live_context_challenger.py::PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_PASS | yes | ok |
| phase13_correction_token:train_live_context_challenger.py::phase13p_lineup_injury_driver_v1 | yes | ok |
| phase13_correction_token:train_live_context_challenger.py::starter_proxy_lagged | yes | ok |
| phase13_correction_token:train_live_context_challenger.py::no_same_game_performance_predictors | yes | ok |
| phase13_correction_token:verify_phase13p_no_leakage.py::PHASE13P_NO_LEAKAGE_PASS | yes | ok |
| phase13_correction_token:verify_phase13p_no_leakage.py::FORBIDDEN_PREDICTOR_COLUMNS | yes | ok |
| phase13_correction_token:verify_phase13p_validation_gates.py::PHASE13P_VALIDATION_GATES_PASS | yes | ok |
| phase13_correction_token:verify_phase13p_validation_gates.py::PHASE13P_VALIDATION_GATES_FAILED | yes | ok |
| phase13_correction_token:verify_phase13p_validation_gates.py::SAFE_NONINFERIORITY_THRESHOLD | yes | ok |
| phase13_correction_token:verify_phase13p_validation_gates.py::PHASE13Q_VALIDATION_GATES_PASS | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINER_READY_PASS | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINING_PASS | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::phase13q_contextual_pmf_engine_v1 | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::GAME_CONTEXT_FEATURES | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::is_back_to_back | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::is_three_in_four | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::season_game_number | yes | ok |
| phase13_correction_token:train_contextual_challenger.py::no_same_game_performance_predictors | yes | ok |
