# Delivery Empty Column Hygiene — 2026-06-05

- files checked: `204`
- files changed: `14`
- columns removed total: `56`
- errors: `0`

## 2026-06-05

### `deliveries/2026-06-05/derek_game_snapshots/21716135/current_live/after_game_scoring.csv`
- rows: `43`
- cols before: `10`
- cols after: `8`
- preserved columns: ``
- removed columns: `model_p_over, market_no_vig_over_prob`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/after_game_scoring.csv`
- rows: `35`
- cols before: `10`
- cols after: `8`
- preserved columns: ``
- removed columns: `model_p_over, market_no_vig_over_prob`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/derek_live_predictions.parquet`
- rows: `35`
- cols before: `52`
- cols after: `47`
- preserved columns: ``
- removed columns: `current_starter, lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/full_pmf_wide.csv`
- rows: `35`
- cols before: `100`
- cols after: `93`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/full_pmf_wide.parquet`
- rows: `35`
- cols before: `100`
- cols after: `93`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/lineup_context.csv`
- rows: `14`
- cols before: `17`
- cols after: `13`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/lineup_context.parquet`
- rows: `14`
- cols before: `17`
- cols after: `13`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/market_comparison.csv`
- rows: `35`
- cols before: `120`
- cols after: `111`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker, model_over_prob, model_under_prob`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/market_comparison.parquet`
- rows: `35`
- cols before: `120`
- cols after: `111`
- preserved columns: ``
- removed columns: `lineup_position, lineup_source, role_bucket_pre_lineup, role_bucket_post_lineup, contextual_pmf_mean_baseline, contextual_pmf_mean_post, contextual_blocker, model_over_prob, model_under_prob`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/pmf_driver_decomposition.csv`
- rows: `14`
- cols before: `23`
- cols after: `21`
- preserved columns: ``
- removed columns: `contextual_pmf_mean_baseline, contextual_pmf_mean_post`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/pmf_driver_decomposition.parquet`
- rows: `14`
- cols before: `23`
- cols after: `21`
- preserved columns: ``
- removed columns: `contextual_pmf_mean_baseline, contextual_pmf_mean_post`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/prediction_input_audit.csv`
- rows: `35`
- cols before: `9`
- cols after: `8`
- preserved columns: ``
- removed columns: `role_bucket_post_lineup`

### `deliveries/2026-06-05/derek_game_snapshots/21716135/t_minus_25/prediction_input_audit.parquet`
- rows: `35`
- cols before: `9`
- cols after: `8`
- preserved columns: ``
- removed columns: `role_bucket_post_lineup`

### `deliveries/2026-06-05/derek_game_snapshots/aggregate_snapshot_scoring.csv`
- rows: `2`
- cols before: `8`
- cols after: `7`
- preserved columns: ``
- removed columns: `blocker`

