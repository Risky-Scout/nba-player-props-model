# Phase 13Q State Audit (Phase 13R Part A)

- generated_at_utc: 2026-05-03T00:40:25+00:00Z
- challenger_dir: `artifacts/models/challengers/2026-04-30_contextual`
- challenger_dir_resolution_reason: 'ok'
- expected_feature_set_id: `phase13q_contextual_pmf_engine_v1`
- pointer.feature_set_id: `phase13q_contextual_pmf_engine_v1`
- pointer.contextual_pmf_engine: **True**
- feature_files_on_disk: ['phase13q_ast_adjustment_features.pkl', 'phase13q_ast_adjustment_model.pkl', 'phase13q_blk_adjustment_features.pkl', 'phase13q_blk_adjustment_model.pkl', 'phase13q_fg3m_adjustment_features.pkl', 'phase13q_fg3m_adjustment_model.pkl', 'phase13q_minutes_adjustment_features.pkl', 'phase13q_minutes_adjustment_model.pkl', 'phase13q_pts_adjustment_features.pkl', 'phase13q_pts_adjustment_model.pkl', 'phase13q_reb_adjustment_features.pkl', 'phase13q_reb_adjustment_model.pkl', 'phase13q_stl_adjustment_features.pkl', 'phase13q_stl_adjustment_model.pkl', 'phase13q_tov_adjustment_features.pkl', 'phase13q_tov_adjustment_model.pkl']

## Answers

- **1_phase13q_trained_real_artifacts** — True
- **2_actual_contextual_model_files** — ['phase13q_ast_adjustment_features.pkl', 'phase13q_ast_adjustment_model.pkl', 'phase13q_blk_adjustment_features.pkl', 'phase13q_blk_adjustment_model.pkl', 'phase13q_fg3m_adjustment_features.pkl', 'phase13q_fg3m_adjustment_model.pkl', 'phase13q_minutes_adjustment_features.pkl', 'phase13q_minutes_adjustment_model.pkl', 'phase13q_pts_adjustment_features.pkl', 'phase13q_pts_adjustment_model.pkl', 'phase13q_reb_adjustment_features.pkl', 'phase13q_reb_adjustment_model.pkl', 'phase13q_stl_adjustment_features.pkl', 'phase13q_stl_adjustment_model.pkl', 'phase13q_tov_adjustment_features.pkl', 'phase13q_tov_adjustment_model.pkl']
- **3_saved_feature_lists_present** — ['minutes', 'pts', 'reb', 'ast', 'tov', 'stl', 'blk', 'fg3m']
- **4_contextual_features_in_lists** — ['is_actionable', 'is_confirmed_out', 'is_inactive', 'is_doubtful', 'is_questionable', 'is_probable', 'injury_status_encoded', 'availability_status_encoded', 'injury_features_missing', 'num_teammates_out_total', 'num_teammates_out_guard', 'num_teammates_out_wing', 'num_teammates_out_big', 'vacated_minutes_total', 'vacated_minutes_guard', 'vacated_minutes_wing', 'vacated_minutes_big', 'vacated_fga_total', 'vacated_features_missing', 'starter_proxy_lagged', 'is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']
- **5_phase13o_pending_retraining_meaning** — Phase 13O sensitivity verifier emits PHASE13O_LIVE_CONTEXT_FEATURE_TRAINING_PENDING_RETRAINING when the live-context feature builder is wired but no challenger feature_lists yet contain the new columns. Phase 13Q's contextual challenger now contains those columns (plus 7 game-context columns), so the pending state should not block Phase 13R.
- **6_pmf_sensitivity_based_on_real_artifacts** — True
- **7_contextual_challenger_promoted** — True
- **8_champion_pointer_references_contextual** — True
- **9_champion_pointer_includes_feature_set_id** — True
- **10_production_predict_uses_contextual_default** — False
- **10_note** — scripts/predict.py default (WoO) is preserved byte-for-byte. Contextual scoring runs in the Derek live snapshot path only, where the runner loads the trained Phase 13Q artifacts and writes pmf_driver_decomposition / lineup_injury_impact_report sidecars.
