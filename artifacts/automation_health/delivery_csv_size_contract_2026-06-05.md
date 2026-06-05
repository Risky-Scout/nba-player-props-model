# Delivery CSV size contract — 2026-06-05

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 351868 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547382 | split_and_previewed | 523751 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6510 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 531491 | split_and_previewed | 522552 |
| `derek_forward_feed/morning_snapshot.csv` | 531491 | split_and_previewed | 522552 |
| `derek_game_snapshots/21716135/morning/full_pmf_wide.csv` | 372332 | ok |  |
| `derek_game_snapshots/21716135/morning/market_comparison.csv` | 542973 | split_and_previewed | 524086 |
| `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv` | 531730 | split_and_previewed | 524280 |
| `derek_game_snapshots/21716135/morning/prop_summary.csv` | 27276 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133223 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 370802 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5841720 | split_and_previewed | 523690 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 370802 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3586585 | split_and_previewed | 523834 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5841720 | split_and_previewed | 523690 |
| `wizard_of_odds/full_pmfs_wide.csv` | 370802 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2533745 | split_and_previewed | 523355 |
| `wizard_of_odds/publishable_edges.csv` | 1985490 | split_and_previewed | 524152 |
