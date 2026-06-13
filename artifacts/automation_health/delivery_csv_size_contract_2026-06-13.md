# Delivery CSV size contract — 2026-06-13

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 355169 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1640051 | split_and_previewed | 523830 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6801 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6964552 | split_and_previewed | 522843 |
| `derek_forward_feed/morning_snapshot.csv` | 6964552 | split_and_previewed | 522843 |
| `derek_game_snapshots/21716138/current_live/contextual_feature_audit.csv` | 4828 | ok |  |
| `derek_game_snapshots/21716138/current_live/full_pmf_wide.csv` | 45581 | ok |  |
| `derek_game_snapshots/21716138/current_live/game_context.csv` | 608 | ok |  |
| `derek_game_snapshots/21716138/current_live/injury_availability_context.csv` | 597 | ok |  |
| `derek_game_snapshots/21716138/current_live/lineup_context.csv` | 1627 | ok |  |
| `derek_game_snapshots/21716138/current_live/market_comparison.csv` | 56637 | ok |  |
| `derek_game_snapshots/21716138/current_live/outcome_level_probabilities.csv` | 103141 | ok |  |
| `derek_game_snapshots/21716138/current_live/pmf_driver_decomposition.csv` | 3166 | ok |  |
| `derek_game_snapshots/21716138/current_live/prediction_input_audit.csv` | 2804 | ok |  |
| `derek_game_snapshots/21716138/current_live/prop_summary.csv` | 2054 | ok |  |
| `derek_game_snapshots/21716138/morning/full_pmf_wide.csv` | 372709 | ok |  |
| `derek_game_snapshots/21716138/morning/market_comparison.csv` | 2653138 | split_and_previewed | 524009 |
| `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv` | 524114 | ok |  |
| `derek_game_snapshots/21716138/morning/prop_summary.csv` | 27355 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 136905 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 372709 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5838486 | split_and_previewed | 523692 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 372709 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3664942 | split_and_previewed | 523778 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5838486 | split_and_previewed | 523692 |
| `wizard_of_odds/full_pmfs_wide.csv` | 372709 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2653138 | split_and_previewed | 524005 |
| `wizard_of_odds/publishable_edges.csv` | 2135527 | split_and_previewed | 523547 |
