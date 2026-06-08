# Delivery CSV size contract — 2026-06-08

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 267134 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1304374 | split_and_previewed | 524074 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5289 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5821345 | split_and_previewed | 523462 |
| `derek_forward_feed/morning_snapshot.csv` | 5821345 | split_and_previewed | 523462 |
| `derek_game_snapshots/21716136/morning/full_pmf_wide.csv` | 282522 | ok |  |
| `derek_game_snapshots/21716136/morning/market_comparison.csv` | 2153412 | split_and_previewed | 524253 |
| `derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv` | 410123 | ok |  |
| `derek_game_snapshots/21716136/morning/prop_summary.csv` | 20856 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 99883 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 282522 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4398626 | split_and_previewed | 523857 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 282522 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2686651 | split_and_previewed | 524014 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4398626 | split_and_previewed | 523857 |
| `wizard_of_odds/full_pmfs_wide.csv` | 282522 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2153412 | split_and_previewed | 524253 |
| `wizard_of_odds/publishable_edges.csv` | 1751095 | split_and_previewed | 523867 |
