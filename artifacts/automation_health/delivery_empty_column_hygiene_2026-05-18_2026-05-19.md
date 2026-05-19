# Delivery Empty Column Hygiene — 2026-05-18_2026-05-19

- write: `True`
- files checked: `93`
- files changed: `91`
- columns removed total: `594`

## `deliveries/2026-05-18/canonical_source/all_props_model_only.parquet`
- rows: `180`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-18/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv`
- rows: `180`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-18/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl`
- rows: `180`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-18/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- rows: `180`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-18/derek_forward_feed/derek_forward_feed.csv`
- rows: `2172`
- cols before: `55`
- cols after: `49`
- removed columns: `event_id, role_mixture_weights_json, role_entropy, role_bucket_confidence, minutes_q10, minutes_q90`

## `deliveries/2026-05-18/derek_forward_feed/derek_forward_feed.jsonl`
- rows: `2172`
- cols before: `55`
- cols after: `49`
- removed columns: `event_id, role_mixture_weights_json, role_entropy, role_bucket_confidence, minutes_q10, minutes_q90`

## `deliveries/2026-05-18/derek_forward_feed/derek_forward_feed.parquet`
- rows: `2172`
- cols before: `55`
- cols after: `49`
- removed columns: `event_id, role_mixture_weights_json, role_entropy, role_bucket_confidence, minutes_q10, minutes_q90`

## `deliveries/2026-05-18/derek_forward_feed/latest_available_snapshot.csv`
- rows: `2172`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/latest_available_snapshot.parquet`
- rows: `2172`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/lineup_snapshot.csv`
- rows: `2172`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/lineup_snapshot.jsonl`
- rows: `2172`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/lineup_snapshot.parquet`
- rows: `2172`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/morning_snapshot.csv`
- rows: `2494`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/morning_snapshot.jsonl`
- rows: `2494`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_forward_feed/morning_snapshot.parquet`
- rows: `2494`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/full_pmf_wide.csv`
- rows: `180`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/full_pmf_wide.parquet`
- rows: `180`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/market_comparison.csv`
- rows: `2207`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/market_comparison.parquet`
- rows: `2207`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/outcome_level_probabilities.csv`
- rows: `8734`
- cols before: `12`
- cols after: `11`
- removed columns: `line`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/outcome_level_probabilities.parquet`
- rows: `8734`
- cols before: `12`
- cols after: `11`
- removed columns: `line`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/prop_summary.csv`
- rows: `180`
- cols before: `20`
- cols after: `19`
- removed columns: `edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/lineup/prop_summary.parquet`
- rows: `180`
- cols before: `20`
- cols after: `19`
- removed columns: `edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/full_pmf_wide.csv`
- rows: `180`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/full_pmf_wide.parquet`
- rows: `180`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/market_comparison.csv`
- rows: `2544`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/market_comparison.parquet`
- rows: `2544`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/outcome_level_probabilities.csv`
- rows: `8824`
- cols before: `12`
- cols after: `11`
- removed columns: `line`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/outcome_level_probabilities.parquet`
- rows: `8824`
- cols before: `12`
- cols after: `11`
- removed columns: `line`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/prop_summary.csv`
- rows: `180`
- cols before: `20`
- cols after: `19`
- removed columns: `edge`

## `deliveries/2026-05-18/derek_game_snapshots/21713528/morning/prop_summary.parquet`
- rows: `180`
- cols before: `20`
- cols after: `19`
- removed columns: `edge`

## `deliveries/2026-05-18/pmf_model_review_package/04_PROP_SUMMARY.csv`
- rows: `180`
- cols before: `50`
- cols after: `38`
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/pmf_model_review_package/04_PROP_SUMMARY.parquet`
- rows: `180`
- cols before: `50`
- cols after: `38`
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/pmf_model_review_package/05_FULL_PMF_WIDE.csv`
- rows: `180`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/pmf_model_review_package/05_FULL_PMF_WIDE.parquet`
- rows: `180`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv`
- rows: `9738`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet`
- rows: `9738`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/pmf_model_review_package/machine_readable/model_only.csv`
- rows: `180`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/pmf_model_review_package/machine_readable/model_only.jsonl`
- rows: `180`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/pmf_model_review_package/machine_readable/model_only.parquet`
- rows: `180`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/wizard_of_odds/fair_odds_board.csv`
- rows: `3855`
- cols before: `69`
- cols after: `63`
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

## `deliveries/2026-05-18/wizard_of_odds/fair_odds_board.jsonl`
- rows: `3855`
- cols before: `69`
- cols after: `63`
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

## `deliveries/2026-05-18/wizard_of_odds/fair_odds_board.parquet`
- rows: `3855`
- cols before: `69`
- cols after: `63`
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

## `deliveries/2026-05-18/wizard_of_odds/full_pmfs_outcome_level.csv`
- rows: `9738`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/wizard_of_odds/full_pmfs_outcome_level.parquet`
- rows: `9738`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/wizard_of_odds/full_pmfs_wide.csv`
- rows: `180`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/wizard_of_odds/full_pmfs_wide.parquet`
- rows: `180`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-18/wizard_of_odds/market_comparison.csv`
- rows: `2207`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/wizard_of_odds/market_comparison.parquet`
- rows: `2207`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/wizard_of_odds/publishable_edges.csv`
- rows: `1766`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-18/wizard_of_odds/publishable_edges.parquet`
- rows: `1766`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/canonical_source/all_props_model_only.parquet`
- rows: `156`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-19/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv`
- rows: `156`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-19/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.jsonl`
- rows: `156`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-19/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- rows: `156`
- cols before: `53`
- cols after: `39`
- removed columns: `game_start_et, role_mixture_enabled, role_mixture_weights_json, role_entropy, role_bucket_confidence, mp_bucket, usage_bucket, projected_minutes, minutes_q10, minutes_q90, line, market_fair_over_prob, market_source, market_offered_odds`

## `deliveries/2026-05-19/derek_forward_feed/derek_forward_feed.csv`
- rows: `2219`
- cols before: `55`
- cols after: `47`
- removed columns: `model_artifact_hash, event_id, role_mixture_weights_json, role_entropy, role_bucket_confidence, minutes_q10, minutes_q90, unavailable_reason`

## `deliveries/2026-05-19/derek_forward_feed/derek_forward_feed.jsonl`
- rows: `2219`
- cols before: `55`
- cols after: `47`
- removed columns: `model_artifact_hash, event_id, role_mixture_weights_json, role_entropy, role_bucket_confidence, minutes_q10, minutes_q90, unavailable_reason`

## `deliveries/2026-05-19/derek_forward_feed/derek_forward_feed.parquet`
- rows: `2219`
- cols before: `55`
- cols after: `47`
- removed columns: `model_artifact_hash, event_id, role_mixture_weights_json, role_entropy, role_bucket_confidence, minutes_q10, minutes_q90, unavailable_reason`

## `deliveries/2026-05-19/derek_forward_feed/latest_available_snapshot.csv`
- rows: `2219`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-19/derek_forward_feed/latest_available_snapshot.parquet`
- rows: `2219`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-19/derek_forward_feed/morning_snapshot.csv`
- rows: `2219`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-19/derek_forward_feed/morning_snapshot.jsonl`
- rows: `2219`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-19/derek_forward_feed/morning_snapshot.parquet`
- rows: `2219`
- cols before: `93`
- cols after: `89`
- removed columns: `game_start_time_utc, minutes_source, minutes_model_version, availability_freshness_status`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/full_pmf_wide.csv`
- rows: `156`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/full_pmf_wide.parquet`
- rows: `156`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/market_comparison.csv`
- rows: `2254`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/market_comparison.parquet`
- rows: `2254`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/outcome_level_probabilities.csv`
- rows: `7565`
- cols before: `12`
- cols after: `11`
- removed columns: `line`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/outcome_level_probabilities.parquet`
- rows: `7565`
- cols before: `12`
- cols after: `11`
- removed columns: `line`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/prop_summary.csv`
- rows: `156`
- cols before: `20`
- cols after: `19`
- removed columns: `edge`

## `deliveries/2026-05-19/derek_game_snapshots/21713895/morning/prop_summary.parquet`
- rows: `156`
- cols before: `20`
- cols after: `19`
- removed columns: `edge`

## `deliveries/2026-05-19/pmf_model_review_package/04_PROP_SUMMARY.csv`
- rows: `156`
- cols before: `50`
- cols after: `38`
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/pmf_model_review_package/04_PROP_SUMMARY.parquet`
- rows: `156`
- cols before: `50`
- cols after: `38`
- removed columns: `game_start_time, line, market_line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, model_p_over, p_over, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/pmf_model_review_package/05_FULL_PMF_WIDE.csv`
- rows: `156`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/pmf_model_review_package/05_FULL_PMF_WIDE.parquet`
- rows: `156`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv`
- rows: `8419`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.parquet`
- rows: `8419`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/pmf_model_review_package/machine_readable/model_only.csv`
- rows: `156`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/pmf_model_review_package/machine_readable/model_only.jsonl`
- rows: `156`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/pmf_model_review_package/machine_readable/model_only.parquet`
- rows: `156`
- cols before: `84`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, model_p_over, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/wizard_of_odds/fair_odds_board.csv`
- rows: `3341`
- cols before: `69`
- cols after: `63`
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

## `deliveries/2026-05-19/wizard_of_odds/fair_odds_board.jsonl`
- rows: `3341`
- cols before: `69`
- cols after: `63`
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

## `deliveries/2026-05-19/wizard_of_odds/fair_odds_board.parquet`
- rows: `3341`
- cols before: `69`
- cols after: `63`
- removed columns: `game_start_time, book, market_over_odds, market_under_odds, market_no_vig_over_prob, edge`

## `deliveries/2026-05-19/wizard_of_odds/full_pmfs_outcome_level.csv`
- rows: `8419`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/wizard_of_odds/full_pmfs_outcome_level.parquet`
- rows: `8419`
- cols before: `25`
- cols after: `24`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/wizard_of_odds/full_pmfs_wide.csv`
- rows: `156`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/wizard_of_odds/full_pmfs_wide.parquet`
- rows: `156`
- cols before: `83`
- cols after: `70`
- removed columns: `game_start_time, line, book, market_over_odds, market_under_odds, market_no_vig_over_prob, minutes_source, minutes_model_version, p_over, market_line, fair_over_odds_american, fair_under_odds_american, edge`

## `deliveries/2026-05-19/wizard_of_odds/market_comparison.csv`
- rows: `2254`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/wizard_of_odds/market_comparison.parquet`
- rows: `2254`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/wizard_of_odds/publishable_edges.csv`
- rows: `1803`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

## `deliveries/2026-05-19/wizard_of_odds/publishable_edges.parquet`
- rows: `1803`
- cols before: `69`
- cols after: `68`
- removed columns: `game_start_time`

