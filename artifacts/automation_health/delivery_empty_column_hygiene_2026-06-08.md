# Delivery Empty Column Hygiene — 2026-06-08

- files checked: `142`
- files changed: `48`
- columns removed total: `305`
- errors: `0`

## 2026-06-08

### `deliveries/2026-06-08/canonical_source/all_props_model_only.parquet`
- rows: `144`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-06-08/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv`
- rows: `144`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-06-08/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl`
- rows: `144`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-06-08/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- rows: `144`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-06-08/derek_forward_feed/latest_available_snapshot.csv`
- rows: `2299`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-06-08/derek_forward_feed/latest_available_snapshot.parquet`
- rows: `2299`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-06-08/derek_forward_feed/morning_snapshot.csv`
- rows: `2299`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-06-08/derek_forward_feed/morning_snapshot.jsonl`
- rows: `2299`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-06-08/derek_forward_feed/morning_snapshot.parquet`
- rows: `2299`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/derek_live_predictions.parquet`
- rows: `30`
- cols before: `52`
- cols after: `47`
- preserved columns: ``
- removed columns: `current_starter, lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/full_pmf_wide.csv`
- rows: `30`
- cols before: `100`
- cols after: `93`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/full_pmf_wide.parquet`
- rows: `30`
- cols before: `100`
- cols after: `93`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/lineup_context.csv`
- rows: `12`
- cols before: `17`
- cols after: `13`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/lineup_context.parquet`
- rows: `12`
- cols before: `17`
- cols after: `13`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/market_comparison.csv`
- rows: `30`
- cols before: `120`
- cols after: `111`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker, model_over_prob, model_under_prob`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/market_comparison.parquet`
- rows: `30`
- cols before: `120`
- cols after: `111`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker, model_over_prob, model_under_prob`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/pmf_driver_decomposition.csv`
- rows: `12`
- cols before: `23`
- cols after: `21`
- preserved columns: ``
- removed columns: `contextual_pmf_mean_baseline, contextual_pmf_mean_post`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/pmf_driver_decomposition.parquet`
- rows: `12`
- cols before: `23`
- cols after: `21`
- preserved columns: ``
- removed columns: `contextual_pmf_mean_baseline, contextual_pmf_mean_post`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/prediction_input_audit.csv`
- rows: `30`
- cols before: `9`
- cols after: `8`
- preserved columns: ``
- removed columns: `role_bucket_post_lineup`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/current_live/prediction_input_audit.parquet`
- rows: `30`
- cols before: `9`
- cols after: `8`
- preserved columns: ``
- removed columns: `role_bucket_post_lineup`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/full_pmf_wide.csv`
- rows: `144`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/full_pmf_wide.parquet`
- rows: `144`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/market_comparison.csv`
- rows: `2352`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/market_comparison.parquet`
- rows: `2352`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv`
- rows: `4893`
- cols before: `12`
- cols after: `11`
- preserved columns: ``
- removed columns: `line`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/outcome_level_probabilities.parquet`
- rows: `4893`
- cols before: `12`
- cols after: `11`
- preserved columns: ``
- removed columns: `line`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/prop_summary.csv`
- rows: `144`
- cols before: `20`
- cols after: `19`
- preserved columns: ``
- removed columns: `edge`

### `deliveries/2026-06-08/derek_game_snapshots/21716136/morning/prop_summary.parquet`
- rows: `144`
- cols before: `20`
- cols after: `19`
- preserved columns: ``
- removed columns: `edge`

### `deliveries/2026-06-08/pmf_model_review_package/04_PROP_SUMMARY.csv`
- rows: `144`
- cols before: `50`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/pmf_model_review_package/04_PROP_SUMMARY.parquet`
- rows: `144`
- cols before: `50`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/pmf_model_review_package/05_FULL_PMF_WIDE.csv`
- rows: `144`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/pmf_model_review_package/05_FULL_PMF_WIDE.parquet`
- rows: `144`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv`
- rows: `7779`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet`
- rows: `7779`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/pmf_model_review_package/machine_readable/model_only.csv`
- rows: `144`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/pmf_model_review_package/machine_readable/model_only.jsonl`
- rows: `144`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/pmf_model_review_package/machine_readable/model_only.parquet`
- rows: `144`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/wizard_of_odds/fair_odds_board.csv`
- rows: `3084`
- cols before: `70`
- cols after: `64`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

### `deliveries/2026-06-08/wizard_of_odds/fair_odds_board.jsonl`
- rows: `3084`
- cols before: `70`
- cols after: `64`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

### `deliveries/2026-06-08/wizard_of_odds/fair_odds_board.parquet`
- rows: `3084`
- cols before: `70`
- cols after: `64`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

### `deliveries/2026-06-08/wizard_of_odds/full_pmfs_outcome_level.csv`
- rows: `7779`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/wizard_of_odds/full_pmfs_outcome_level.parquet`
- rows: `7779`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/wizard_of_odds/full_pmfs_wide.csv`
- rows: `144`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/wizard_of_odds/full_pmfs_wide.parquet`
- rows: `144`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-06-08/wizard_of_odds/market_comparison.csv`
- rows: `2352`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/wizard_of_odds/market_comparison.parquet`
- rows: `2352`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/wizard_of_odds/publishable_edges.csv`
- rows: `1918`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-06-08/wizard_of_odds/publishable_edges.parquet`
- rows: `1918`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

