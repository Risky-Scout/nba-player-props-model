# Delivery CSV size contract — 2026-05-28

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 316018 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 546840 | split_and_previewed | 523843 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6202 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 531075 | split_and_previewed | 522488 |
| `derek_forward_feed/morning_snapshot.csv` | 531075 | split_and_previewed | 522488 |
| `derek_game_snapshots/21713533/morning/full_pmf_wide.csv` | 329962 | ok |  |
| `derek_game_snapshots/21713533/morning/market_comparison.csv` | 544145 | split_and_previewed | 523309 |
| `derek_game_snapshots/21713533/morning/outcome_level_probabilities.csv` | 491487 | ok |  |
| `derek_game_snapshots/21713533/morning/prop_summary.csv` | 24554 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 117093 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 334176 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5200891 | split_and_previewed | 524262 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 334176 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3148583 | split_and_previewed | 524242 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5200891 | split_and_previewed | 524262 |
| `wizard_of_odds/full_pmfs_wide.csv` | 334176 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2284523 | split_and_previewed | 523326 |
| `wizard_of_odds/publishable_edges.csv` | 1936098 | split_and_previewed | 523261 |
