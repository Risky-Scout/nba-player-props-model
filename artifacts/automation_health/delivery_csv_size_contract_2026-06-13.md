# Delivery CSV size contract — 2026-06-13

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 355760 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1579188 | split_and_previewed | 523904 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6801 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 7091267 | split_and_previewed | 522038 |
| `derek_forward_feed/morning_snapshot.csv` | 7091267 | split_and_previewed | 522038 |
| `derek_game_snapshots/21716138/morning/full_pmf_wide.csv` | 376620 | ok |  |
| `derek_game_snapshots/21716138/morning/market_comparison.csv` | 2588256 | split_and_previewed | 523473 |
| `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv` | 544097 | split_and_previewed | 524281 |
| `derek_game_snapshots/21716138/morning/prop_summary.csv` | 27355 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 132849 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 376620 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5840535 | split_and_previewed | 524277 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 376620 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3580160 | split_and_previewed | 523879 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5840535 | split_and_previewed | 524277 |
| `wizard_of_odds/full_pmfs_wide.csv` | 376620 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2588256 | split_and_previewed | 523473 |
| `wizard_of_odds/publishable_edges.csv` | 2124272 | split_and_previewed | 523820 |
