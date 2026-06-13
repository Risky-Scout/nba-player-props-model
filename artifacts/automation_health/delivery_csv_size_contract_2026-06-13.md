# Delivery CSV size contract — 2026-06-13

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 356641 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547415 | split_and_previewed | 523799 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6804 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 532128 | split_and_previewed | 522280 |
| `derek_forward_feed/morning_snapshot.csv` | 532128 | split_and_previewed | 522280 |
| `derek_game_snapshots/21716138/morning/full_pmf_wide.csv` | 370868 | ok |  |
| `derek_game_snapshots/21716138/morning/market_comparison.csv` | 542690 | split_and_previewed | 523729 |
| `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv` | 529432 | split_and_previewed | 522142 |
| `derek_game_snapshots/21716138/morning/prop_summary.csv` | 27357 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133235 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 378353 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5865184 | split_and_previewed | 523768 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 378353 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3587640 | split_and_previewed | 524104 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5865184 | split_and_previewed | 523768 |
| `wizard_of_odds/full_pmfs_wide.csv` | 378353 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2591222 | split_and_previewed | 523654 |
| `wizard_of_odds/publishable_edges.csv` | 2129792 | split_and_previewed | 524036 |
