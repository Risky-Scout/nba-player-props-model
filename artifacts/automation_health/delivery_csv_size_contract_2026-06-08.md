# Delivery CSV size contract — 2026-06-08

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 271950 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1389307 | split_and_previewed | 524153 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5286 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5950989 | split_and_previewed | 524134 |
| `derek_forward_feed/morning_snapshot.csv` | 5950989 | split_and_previewed | 524134 |
| `derek_game_snapshots/21716136/current_live/contextual_feature_audit.csv` | 4092 | ok |  |
| `derek_game_snapshots/21716136/current_live/full_pmf_wide.csv` | 35964 | ok |  |
| `derek_game_snapshots/21716136/current_live/game_context.csv` | 502 | ok |  |
| `derek_game_snapshots/21716136/current_live/injury_availability_context.csv` | 497 | ok |  |
| `derek_game_snapshots/21716136/current_live/lineup_context.csv` | 1344 | ok |  |
| `derek_game_snapshots/21716136/current_live/market_comparison.csv` | 43741 | ok |  |
| `derek_game_snapshots/21716136/current_live/outcome_level_probabilities.csv` | 99489 | ok |  |
| `derek_game_snapshots/21716136/current_live/pmf_driver_decomposition.csv` | 2619 | ok |  |
| `derek_game_snapshots/21716136/current_live/prediction_input_audit.csv` | 2134 | ok |  |
| `derek_game_snapshots/21716136/current_live/prop_summary.csv` | 1582 | ok |  |
| `derek_game_snapshots/21716136/morning/full_pmf_wide.csv` | 287086 | ok |  |
| `derek_game_snapshots/21716136/morning/market_comparison.csv` | 2247810 | split_and_previewed | 523878 |
| `derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv` | 481011 | ok |  |
| `derek_game_snapshots/21716136/morning/prop_summary.csv` | 23015 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 105090 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 287086 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4515311 | split_and_previewed | 523972 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 287086 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2797395 | split_and_previewed | 524245 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4515311 | split_and_previewed | 523972 |
| `wizard_of_odds/full_pmfs_wide.csv` | 287086 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2247810 | split_and_previewed | 523878 |
| `wizard_of_odds/publishable_edges.csv` | 1847941 | split_and_previewed | 524143 |
