# Delivery CSV size contract — 2026-06-05

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 354142 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1464544 | split_and_previewed | 524197 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6512 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6899002 | split_and_previewed | 523652 |
| `derek_forward_feed/morning_snapshot.csv` | 6899002 | split_and_previewed | 523652 |
| `derek_game_snapshots/21716135/morning/full_pmf_wide.csv` | 374368 | ok |  |
| `derek_game_snapshots/21716135/morning/market_comparison.csv` | 2506131 | split_and_previewed | 523679 |
| `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv` | 536901 | split_and_previewed | 524224 |
| `derek_game_snapshots/21716135/morning/prop_summary.csv` | 27280 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 132839 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 374368 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5819138 | split_and_previewed | 523661 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 374368 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3578305 | split_and_previewed | 523904 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5819138 | split_and_previewed | 523661 |
| `wizard_of_odds/full_pmfs_wide.csv` | 374368 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2506131 | split_and_previewed | 523679 |
| `wizard_of_odds/publishable_edges.csv` | 1992832 | split_and_previewed | 524142 |
