# Phase 13Q State Audit (Phase 13R Part A)

- generated_at_utc: 2026-05-23T12:04:05+00:00Z
- challenger_dir: `artifacts/models/challengers/2026-04-30_direct_lineup_contextual`
- challenger_dir_resolution_reason: 'ok'
- expected_feature_set_id: `phase13q_contextual_pmf_engine_v1`
- pointer.feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- pointer.contextual_pmf_engine: **True**
- feature_files_on_disk: ['phase13s_ast_adjustment.pkl', 'phase13s_ast_features.pkl', 'phase13s_blk_adjustment.pkl', 'phase13s_blk_features.pkl', 'phase13s_fg3m_adjustment.pkl', 'phase13s_fg3m_features.pkl', 'phase13s_minutes_adjustment.pkl', 'phase13s_minutes_features.pkl', 'phase13s_pts_adjustment.pkl', 'phase13s_pts_features.pkl', 'phase13s_reb_adjustment.pkl', 'phase13s_reb_features.pkl', 'phase13s_stl_adjustment.pkl', 'phase13s_stl_features.pkl', 'phase13s_tov_adjustment.pkl', 'phase13s_tov_features.pkl']

## Answers

- **1_phase13q_trained_real_artifacts** — True
- **2_actual_contextual_model_files** — ['phase13s_ast_adjustment.pkl', 'phase13s_ast_features.pkl', 'phase13s_blk_adjustment.pkl', 'phase13s_blk_features.pkl', 'phase13s_fg3m_adjustment.pkl', 'phase13s_fg3m_features.pkl', 'phase13s_minutes_adjustment.pkl', 'phase13s_minutes_features.pkl', 'phase13s_pts_adjustment.pkl', 'phase13s_pts_features.pkl', 'phase13s_reb_adjustment.pkl', 'phase13s_reb_features.pkl', 'phase13s_stl_adjustment.pkl', 'phase13s_stl_features.pkl', 'phase13s_tov_adjustment.pkl', 'phase13s_tov_features.pkl']
- **3_saved_feature_lists_present** — ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- **4_contextual_features_in_lists** — ['lineup_confirmed', 'current_starter', 'confirmed_starter', 'confirmed_bench', 'starter_changed_from_projection', 'bench_changed_from_projection', 'role_source_confirmed_lineup', 'lineup_position_encoded', 'minutes_projection_conflict', 'confirmed_starter_low_minutes_flag', 'confirmed_bench_high_minutes_flag', 'consecutive_starter_streak', 'recent_starter_rate_5', 'lineup_features_missing', 'team_confirmed_starters_count', 'team_confirmed_bench_count', 'team_lineup_num_guards', 'team_lineup_num_wings', 'team_lineup_num_bigs', 'team_lineup_num_high_usage_players', 'team_lineup_num_primary_ballhandlers', 'team_lineup_num_shooters', 'team_lineup_num_rebounders', 'team_lineup_usage_competition_proxy', 'team_lineup_rebound_competition_proxy', 'team_lineup_assist_creation_proxy', 'team_lineup_spacing_proxy', 'team_lineup_turnover_pressure_proxy', 'player_confirmed_with_high_usage_count', 'player_confirmed_with_primary_ballhandler_count', 'player_confirmed_with_big_count', 'player_confirmed_with_shooter_count', 'player_usage_competition_proxy', 'player_rebound_competition_proxy', 'player_assist_target_quality_proxy', 'player_spacing_support_proxy', 'player_onball_burden_proxy', 'is_actionable', 'is_confirmed_out', 'is_inactive', 'is_doubtful', 'is_questionable', 'is_probable', 'injury_status_encoded', 'availability_status_encoded', 'injury_features_missing', 'num_teammates_out_total', 'num_teammates_out_guard', 'num_teammates_out_wing', 'num_teammates_out_big', 'vacated_minutes_total', 'vacated_minutes_guard', 'vacated_minutes_wing', 'vacated_minutes_big', 'vacated_fga_total', 'vacated_features_missing', 'starter_proxy_lagged', 'is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']
- **5_phase13o_pending_retraining_meaning** — Phase 13O sensitivity verifier emits PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PENDING_RETRAINING when the live-context feature builder is wired but no challenger feature_lists yet contain the new columns. Phase 13Q's contextual challenger now contains those columns (plus 7 game-context columns), so the pending state should not block Phase 13R.
- **6_pmf_sensitivity_based_on_real_artifacts** — True
- **7_contextual_challenger_promoted** — True
- **8_champion_pointer_references_contextual** — True
- **9_champion_pointer_includes_feature_set_id** — True
- **10_production_predict_uses_contextual_default** — False
- **10_note** — scripts/predict.py default (WoO) is preserved byte-for-byte. Contextual scoring runs in the Derek live snapshot path only, where the runner loads the trained Phase 13Q artifacts and writes pmf_driver_decomposition / lineup_injury_impact_report sidecars.
