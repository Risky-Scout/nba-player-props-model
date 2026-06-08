# Delivery CSV size contract — 2026-06-08

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 266451 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1309392 | split_and_previewed | 523888 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5283 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5867537 | split_and_previewed | 523078 |
| `derek_forward_feed/morning_snapshot.csv` | 5867537 | split_and_previewed | 523078 |
| `derek_game_snapshots/21716136/morning/full_pmf_wide.csv` | 281396 | ok |  |
| `derek_game_snapshots/21716136/morning/market_comparison.csv` | 2162675 | split_and_previewed | 523759 |
| `derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv` | 406093 | ok |  |
| `derek_game_snapshots/21716136/morning/prop_summary.csv` | 20855 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 99881 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 281396 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4398626 | split_and_previewed | 523886 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 281396 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2686356 | split_and_previewed | 523769 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4398626 | split_and_previewed | 523886 |
| `wizard_of_odds/full_pmfs_wide.csv` | 281396 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2162675 | split_and_previewed | 523759 |
| `wizard_of_odds/publishable_edges.csv` | 1751299 | split_and_previewed | 523886 |
