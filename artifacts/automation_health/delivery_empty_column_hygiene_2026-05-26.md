# Delivery Empty Column Hygiene — 2026-05-26

- files checked: `41`
- files changed: `37`
- columns removed total: `254`
- errors: `0`

## 2026-05-26

### `deliveries/2026-05-26/canonical_source/all_props_model_only.parquet`
- rows: `192`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-26/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv`
- rows: `192`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-26/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl`
- rows: `192`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-26/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- rows: `192`
- cols before: `53`
- cols after: `39`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-26/derek_forward_feed/latest_available_snapshot.csv`
- rows: `2690`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-05-26/derek_forward_feed/latest_available_snapshot.parquet`
- rows: `2690`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-05-26/derek_forward_feed/lineup_snapshot.csv`
- rows: `2690`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-05-26/derek_forward_feed/lineup_snapshot.jsonl`
- rows: `2690`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-05-26/derek_forward_feed/lineup_snapshot.parquet`
- rows: `2690`
- cols before: `93`
- cols after: `89`
- preserved columns: ``
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/full_pmf_wide.csv`
- rows: `192`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/full_pmf_wide.parquet`
- rows: `192`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/market_comparison.csv`
- rows: `2736`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/market_comparison.parquet`
- rows: `2736`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/outcome_level_probabilities.csv`
- rows: `6622`
- cols before: `12`
- cols after: `11`
- preserved columns: ``
- removed columns: `line`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/outcome_level_probabilities.parquet`
- rows: `6622`
- cols before: `12`
- cols after: `11`
- preserved columns: ``
- removed columns: `line`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/prop_summary.csv`
- rows: `192`
- cols before: `20`
- cols after: `19`
- preserved columns: ``
- removed columns: `edge`

### `deliveries/2026-05-26/derek_game_snapshots/21713532/lineup/prop_summary.parquet`
- rows: `192`
- cols before: `20`
- cols after: `19`
- preserved columns: ``
- removed columns: `edge`

### `deliveries/2026-05-26/pmf_model_review_package/04_PROP_SUMMARY.csv`
- rows: `192`
- cols before: `50`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/pmf_model_review_package/04_PROP_SUMMARY.parquet`
- rows: `192`
- cols before: `50`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/pmf_model_review_package/05_FULL_PMF_WIDE.csv`
- rows: `192`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/pmf_model_review_package/05_FULL_PMF_WIDE.parquet`
- rows: `192`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv`
- rows: `10417`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet`
- rows: `10417`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/pmf_model_review_package/machine_readable/model_only.csv`
- rows: `192`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/pmf_model_review_package/machine_readable/model_only.jsonl`
- rows: `192`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/pmf_model_review_package/machine_readable/model_only.parquet`
- rows: `192`
- cols before: `84`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/wizard_of_odds/fair_odds_board.csv`
- rows: `4112`
- cols before: `70`
- cols after: `64`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

### `deliveries/2026-05-26/wizard_of_odds/fair_odds_board.jsonl`
- rows: `4112`
- cols before: `70`
- cols after: `64`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

### `deliveries/2026-05-26/wizard_of_odds/fair_odds_board.parquet`
- rows: `4112`
- cols before: `70`
- cols after: `64`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

### `deliveries/2026-05-26/wizard_of_odds/full_pmfs_outcome_level.csv`
- rows: `10417`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/wizard_of_odds/full_pmfs_outcome_level.parquet`
- rows: `10417`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/wizard_of_odds/full_pmfs_wide.csv`
- rows: `192`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/wizard_of_odds/full_pmfs_wide.parquet`
- rows: `192`
- cols before: `83`
- cols after: `70`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

### `deliveries/2026-05-26/wizard_of_odds/market_comparison.csv`
- rows: `2736`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/wizard_of_odds/market_comparison.parquet`
- rows: `2736`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/wizard_of_odds/publishable_edges.csv`
- rows: `2281`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-26/wizard_of_odds/publishable_edges.parquet`
- rows: `2281`
- cols before: `70`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time`

