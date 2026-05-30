# Delivery CSV size contract — 2026-05-30

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 361870 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1613244 | split_and_previewed | 524286 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6991 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6863377 | split_and_previewed | 523644 |
| `derek_forward_feed/morning_snapshot.csv` | 6863377 | split_and_previewed | 523644 |
| `derek_game_snapshots/21713534/current_live/contextual_feature_audit.csv` | 5360 | ok |  |
| `derek_game_snapshots/21713534/current_live/full_pmf_wide.csv` | 46581 | ok |  |
| `derek_game_snapshots/21713534/current_live/game_context.csv` | 720 | ok |  |
| `derek_game_snapshots/21713534/current_live/injury_availability_context.csv` | 705 | ok |  |
| `derek_game_snapshots/21713534/current_live/lineup_context.csv` | 1857 | ok |  |
| `derek_game_snapshots/21713534/current_live/market_comparison.csv` | 57427 | ok |  |
| `derek_game_snapshots/21713534/current_live/outcome_level_probabilities.csv` | 114950 | ok |  |
| `derek_game_snapshots/21713534/current_live/pmf_driver_decomposition.csv` | 3574 | ok |  |
| `derek_game_snapshots/21713534/current_live/prediction_input_audit.csv` | 2914 | ok |  |
| `derek_game_snapshots/21713534/current_live/prop_summary.csv` | 2164 | ok |  |
| `derek_game_snapshots/21713534/morning/full_pmf_wide.csv` | 379569 | ok |  |
| `derek_game_snapshots/21713534/morning/market_comparison.csv` | 2636212 | split_and_previewed | 523480 |
| `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv` | 558526 | split_and_previewed | 524240 |
| `derek_game_snapshots/21713534/morning/prop_summary.csv` | 27926 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 137672 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 379569 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5935535 | split_and_previewed | 523811 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 379569 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3680524 | split_and_previewed | 523697 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5935535 | split_and_previewed | 523811 |
| `wizard_of_odds/full_pmfs_wide.csv` | 379569 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2636212 | split_and_previewed | 523480 |
| `wizard_of_odds/publishable_edges.csv` | 2325587 | split_and_previewed | 523940 |
