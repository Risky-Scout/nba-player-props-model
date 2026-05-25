# Delivery CSV size contract — 2026-05-24

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 361830 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 990064 | split_and_previewed | 524271 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5566 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5331889 | split_and_previewed | 524286 |
| `derek_forward_feed/lineup_snapshot.csv` | 5331889 | split_and_previewed | 524286 |
| `derek_forward_feed/morning_snapshot.csv` | 530055 | split_and_previewed | 523150 |
| `derek_game_snapshots/21713531/close_lock/full_pmf_wide.csv` | 409597 | ok |  |
| `derek_game_snapshots/21713531/close_lock/market_comparison.csv` | 1561860 | split_and_previewed | 523780 |
| `derek_game_snapshots/21713531/close_lock/outcome_level_probabilities.csv` | 836154 | split_and_previewed | 524275 |
| `derek_game_snapshots/21713531/close_lock/prop_summary.csv` | 26856 | ok |  |
| `derek_game_snapshots/21713531/morning/full_pmf_wide.csv` | 442368 | ok |  |
| `derek_game_snapshots/21713531/morning/market_comparison.csv` | 544425 | split_and_previewed | 524183 |
| `derek_game_snapshots/21713531/morning/outcome_level_probabilities.csv` | 533979 | split_and_previewed | 524241 |
| `derek_game_snapshots/21713531/morning/prop_summary.csv` | 26165 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 117614 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 409597 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5191845 | split_and_previewed | 524286 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 409597 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3124644 | split_and_previewed | 524092 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5191845 | split_and_previewed | 524286 |
| `wizard_of_odds/full_pmfs_wide.csv` | 409597 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 1561860 | split_and_previewed | 523780 |
| `wizard_of_odds/publishable_edges.csv` | 849 | ok |  |
