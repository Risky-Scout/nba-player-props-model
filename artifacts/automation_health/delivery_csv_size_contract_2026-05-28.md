# Delivery CSV size contract — 2026-05-28

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 313765 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1351100 | split_and_previewed | 523843 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6202 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5910754 | split_and_previewed | 522488 |
| `derek_forward_feed/morning_snapshot.csv` | 5910754 | split_and_previewed | 522488 |
| `derek_game_snapshots/21713533/morning/full_pmf_wide.csv` | 329962 | ok |  |
| `derek_game_snapshots/21713533/morning/market_comparison.csv` | 2280357 | split_and_previewed | 523309 |
| `derek_game_snapshots/21713533/morning/outcome_level_probabilities.csv` | 491487 | ok |  |
| `derek_game_snapshots/21713533/morning/prop_summary.csv` | 24554 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 116757 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 329962 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5182641 | split_and_previewed | 524163 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 329962 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3141053 | split_and_previewed | 524062 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5182641 | split_and_previewed | 524163 |
| `wizard_of_odds/full_pmfs_wide.csv` | 329962 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2280357 | split_and_previewed | 523299 |
| `wizard_of_odds/publishable_edges.csv` | 1907514 | split_and_previewed | 524000 |
