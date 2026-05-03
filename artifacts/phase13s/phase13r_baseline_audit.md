# Phase 13R Baseline Audit (Phase 13S Part A)

- generated_at_utc: 2026-05-03T12:04:15+00:00Z
- pointer.feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- pointer.contextual_pmf_engine: **True**
- contextual_challenger_dir: `artifacts/models/challengers/2026-04-30_direct_lineup_contextual`

## Answers

- **1_contextual_champion_active** — True
- **2_active_feature_set_id** — phase13s_direct_lineup_injury_pmf_driver_v1
- **3_contextual_features_currently_trained** — ['is_actionable', 'is_confirmed_out', 'is_inactive', 'is_doubtful', 'is_questionable', 'is_probable', 'injury_status_encoded', 'availability_status_encoded', 'injury_features_missing', 'num_teammates_out_total', 'num_teammates_out_guard', 'num_teammates_out_wing', 'num_teammates_out_big', 'vacated_minutes_total', 'vacated_minutes_guard', 'vacated_minutes_wing', 'vacated_minutes_big', 'vacated_fga_total', 'vacated_features_missing', 'starter_proxy_lagged', 'is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']
- **4_contextual_features_in_lists** — ['lineup_confirmed', 'current_starter', 'confirmed_starter', 'confirmed_bench', 'starter_changed_from_projection', 'bench_changed_from_projection', 'role_source_confirmed_lineup', 'lineup_position_encoded', 'minutes_projection_conflict', 'confirmed_starter_low_minutes_flag', 'confirmed_bench_high_minutes_flag', 'consecutive_starter_streak', 'recent_starter_rate_5', 'lineup_features_missing', 'team_confirmed_starters_count', 'team_confirmed_bench_count', 'team_lineup_num_guards', 'team_lineup_num_wings', 'team_lineup_num_bigs', 'team_lineup_num_high_usage_players', 'team_lineup_num_primary_ballhandlers', 'team_lineup_num_shooters', 'team_lineup_num_rebounders', 'team_lineup_usage_competition_proxy', 'team_lineup_rebound_competition_proxy', 'team_lineup_assist_creation_proxy', 'team_lineup_spacing_proxy', 'team_lineup_turnover_pressure_proxy', 'player_confirmed_with_high_usage_count', 'player_confirmed_with_primary_ballhandler_count', 'player_confirmed_with_big_count', 'player_confirmed_with_shooter_count', 'player_usage_competition_proxy', 'player_rebound_competition_proxy', 'player_assist_target_quality_proxy', 'player_spacing_support_proxy', 'player_onball_burden_proxy', 'is_actionable', 'is_confirmed_out', 'is_inactive', 'is_doubtful', 'is_questionable', 'is_probable', 'injury_status_encoded', 'availability_status_encoded', 'injury_features_missing', 'num_teammates_out_total', 'num_teammates_out_guard', 'num_teammates_out_wing', 'num_teammates_out_big', 'vacated_minutes_total', 'vacated_minutes_guard', 'vacated_minutes_wing', 'vacated_minutes_big', 'vacated_fga_total', 'vacated_features_missing', 'starter_proxy_lagged', 'is_home', 'rest_days', 'is_back_to_back', 'is_three_in_four', 'season_game_number', 'season_game_number_norm', 'opponent_team_id_hash']
- **5_direct_lineup_affects_pmf_today** — False
- **5_note** — In Phase 13R the trained model was given starter_proxy_lagged but NOT direct lineup_confirmed/current_starter/confirmed_starter as inputs. Live BDL flips changed feature_vector_hash but did not move the trained Ridge model's deltas. Phase 13S adds current_starter / confirmed_starter / consecutive_starter_streak / recent_starter_rate_5 etc. as direct trained features.
- **6_injury_actionability_affects_today** — True
- **7_vacated_opportunity_affects_today** — True
- **8_market_only_leaves_pmf_unchanged_today** — True
- **9_missing_for_direct_lineup** — ['current_starter not in saved feature lists', 'confirmed_starter not in saved feature lists', 'team_lineup_*_competition_proxy not in saved feature lists', 'player_*_competition_proxy not in saved feature lists', 'consecutive_starter_streak not in saved feature lists']
