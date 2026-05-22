# Delivery Empty Column Hygiene — 2026-05-22

- files checked: `154`
- files changed: `24`
- columns removed total: `222`
- errors: `0`

## 2026-05-22

### `deliveries/2026-05-22/canonical_source/all_props_model_only.parquet`
- rows: `156`
- cols before: `53`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, lineup_last_updated_utc, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-22/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv`
- rows: `156`
- cols before: `53`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, lineup_last_updated_utc, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-22/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl`
- rows: `156`
- cols before: `53`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, lineup_last_updated_utc, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-22/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- rows: `156`
- cols before: `53`
- cols after: `38`
- preserved columns: ``
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, lineup_last_updated_utc, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

### `deliveries/2026-05-22/pmf_model_review_package/04_PROP_SUMMARY.csv`
- rows: `156`
- cols before: `50`
- cols after: `37`
- preserved columns: ``
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/pmf_model_review_package/04_PROP_SUMMARY.parquet`
- rows: `156`
- cols before: `50`
- cols after: `37`
- preserved columns: ``
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/pmf_model_review_package/05_FULL_PMF_WIDE.csv`
- rows: `156`
- cols before: `84`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/pmf_model_review_package/05_FULL_PMF_WIDE.parquet`
- rows: `156`
- cols before: `84`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv`
- rows: `8446`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-22/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet`
- rows: `8446`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-22/pmf_model_review_package/machine_readable/model_only.csv`
- rows: `156`
- cols before: `84`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/pmf_model_review_package/machine_readable/model_only.jsonl`
- rows: `156`
- cols before: `84`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/pmf_model_review_package/machine_readable/model_only.parquet`
- rows: `156`
- cols before: `84`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/fair_odds_board.csv`
- rows: `3341`
- cols before: `69`
- cols after: `62`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/fair_odds_board.jsonl`
- rows: `3341`
- cols before: `69`
- cols after: `62`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/fair_odds_board.parquet`
- rows: `3341`
- cols before: `69`
- cols after: `62`
- preserved columns: ``
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/full_pmfs_outcome_level.csv`
- rows: `8446`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-22/wizard_of_odds/full_pmfs_outcome_level.parquet`
- rows: `8446`
- cols before: `25`
- cols after: `24`
- preserved columns: ``
- removed columns: `game_start_time`

### `deliveries/2026-05-22/wizard_of_odds/full_pmfs_wide.csv`
- rows: `156`
- cols before: `83`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/full_pmfs_wide.parquet`
- rows: `156`
- cols before: `83`
- cols after: `69`
- preserved columns: ``
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/market_comparison.csv`
- rows: `2224`
- cols before: `69`
- cols after: `67`
- preserved columns: ``
- removed columns: `game_start_time, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/market_comparison.parquet`
- rows: `2224`
- cols before: `69`
- cols after: `67`
- preserved columns: ``
- removed columns: `game_start_time, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/publishable_edges.csv`
- rows: `1744`
- cols before: `69`
- cols after: `67`
- preserved columns: ``
- removed columns: `game_start_time, lineup_last_updated_utc`

### `deliveries/2026-05-22/wizard_of_odds/publishable_edges.parquet`
- rows: `1744`
- cols before: `69`
- cols after: `67`
- preserved columns: ``
- removed columns: `game_start_time, lineup_last_updated_utc`

