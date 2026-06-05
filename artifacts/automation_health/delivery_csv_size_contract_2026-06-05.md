# Delivery CSV size contract — 2026-06-05

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 358683 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1607285 | split_and_previewed | 524052 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6520 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6985293 | split_and_previewed | 523145 |
| `derek_forward_feed/morning_snapshot.csv` | 6985293 | split_and_previewed | 523145 |
| `derek_game_snapshots/21716135/current_live/contextual_feature_audit.csv` | 4825 | ok |  |
| `derek_game_snapshots/21716135/current_live/full_pmf_wide.csv` | 47434 | ok |  |
| `derek_game_snapshots/21716135/current_live/game_context.csv` | 605 | ok |  |
| `derek_game_snapshots/21716135/current_live/injury_availability_context.csv` | 594 | ok |  |
| `derek_game_snapshots/21716135/current_live/lineup_context.csv` | 1623 | ok |  |
| `derek_game_snapshots/21716135/current_live/market_comparison.csv` | 58817 | ok |  |
| `derek_game_snapshots/21716135/current_live/outcome_level_probabilities.csv` | 104924 | ok |  |
| `derek_game_snapshots/21716135/current_live/pmf_driver_decomposition.csv` | 3163 | ok |  |
| `derek_game_snapshots/21716135/current_live/prediction_input_audit.csv` | 2944 | ok |  |
| `derek_game_snapshots/21716135/current_live/prop_summary.csv` | 2158 | ok |  |
| `derek_game_snapshots/21716135/morning/full_pmf_wide.csv` | 378362 | ok |  |
| `derek_game_snapshots/21716135/morning/market_comparison.csv` | 2607886 | split_and_previewed | 523843 |
| `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv` | 537055 | split_and_previewed | 524224 |
| `derek_game_snapshots/21716135/morning/prop_summary.csv` | 27235 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 136897 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 378362 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5848737 | split_and_previewed | 523751 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 378362 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3663718 | split_and_previewed | 524032 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5848737 | split_and_previewed | 523751 |
| `wizard_of_odds/full_pmfs_wide.csv` | 378362 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2607886 | split_and_previewed | 523843 |
| `wizard_of_odds/publishable_edges.csv` | 2075711 | split_and_previewed | 524143 |
