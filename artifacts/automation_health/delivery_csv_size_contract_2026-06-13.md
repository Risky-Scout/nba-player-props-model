# Delivery CSV size contract — 2026-06-13

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 353071 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1574612 | split_and_previewed | 524014 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6810 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6917013 | split_and_previewed | 522275 |
| `derek_forward_feed/morning_snapshot.csv` | 6917013 | split_and_previewed | 522275 |
| `derek_game_snapshots/21716138/morning/full_pmf_wide.csv` | 371750 | ok |  |
| `derek_game_snapshots/21716138/morning/market_comparison.csv` | 2578808 | split_and_previewed | 523651 |
| `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv` | 531230 | split_and_previewed | 523817 |
| `derek_game_snapshots/21716138/morning/prop_summary.csv` | 27359 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 132851 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 371750 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5844482 | split_and_previewed | 523760 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 371750 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3579378 | split_and_previewed | 523913 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5844482 | split_and_previewed | 523760 |
| `wizard_of_odds/full_pmfs_wide.csv` | 371750 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2578808 | split_and_previewed | 523651 |
| `wizard_of_odds/publishable_edges.csv` | 2102219 | split_and_previewed | 524062 |
