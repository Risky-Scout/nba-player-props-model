# Delivery CSV size contract — 2026-05-28

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 323306 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1446595 | split_and_previewed | 523770 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6218 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6158554 | split_and_previewed | 522551 |
| `derek_forward_feed/morning_snapshot.csv` | 6158554 | split_and_previewed | 522551 |
| `derek_game_snapshots/21713533/current_live/contextual_feature_audit.csv` | 5117 | ok |  |
| `derek_game_snapshots/21713533/current_live/full_pmf_wide.csv` | 46097 | ok |  |
| `derek_game_snapshots/21713533/current_live/game_context.csv` | 687 | ok |  |
| `derek_game_snapshots/21713533/current_live/injury_availability_context.csv` | 674 | ok |  |
| `derek_game_snapshots/21713533/current_live/lineup_context.csv` | 1763 | ok |  |
| `derek_game_snapshots/21713533/current_live/market_comparison.csv` | 56180 | ok |  |
| `derek_game_snapshots/21713533/current_live/outcome_level_probabilities.csv` | 130040 | ok |  |
| `derek_game_snapshots/21713533/current_live/pmf_driver_decomposition.csv` | 3391 | ok |  |
| `derek_game_snapshots/21713533/current_live/prediction_input_audit.csv` | 2776 | ok |  |
| `derek_game_snapshots/21713533/current_live/prop_summary.csv` | 2062 | ok |  |
| `derek_game_snapshots/21713533/morning/full_pmf_wide.csv` | 342022 | ok |  |
| `derek_game_snapshots/21713533/morning/market_comparison.csv` | 2387905 | split_and_previewed | 524283 |
| `derek_game_snapshots/21713533/morning/outcome_level_probabilities.csv` | 596791 | split_and_previewed | 524198 |
| `derek_game_snapshots/21713533/morning/prop_summary.csv` | 27061 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 122830 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 342022 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5321558 | split_and_previewed | 524143 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 342022 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3270905 | split_and_previewed | 523786 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5321558 | split_and_previewed | 524143 |
| `wizard_of_odds/full_pmfs_wide.csv` | 342022 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2387905 | split_and_previewed | 524271 |
| `wizard_of_odds/publishable_edges.csv` | 2061535 | split_and_previewed | 524198 |
