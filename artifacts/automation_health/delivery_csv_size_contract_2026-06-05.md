# Delivery CSV size contract — 2026-06-05

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 352236 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1522517 | split_and_previewed | 523828 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6510 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6735369 | split_and_previewed | 522004 |
| `derek_forward_feed/morning_snapshot.csv` | 6735369 | split_and_previewed | 522004 |
| `derek_game_snapshots/21716135/morning/full_pmf_wide.csv` | 371059 | ok |  |
| `derek_game_snapshots/21716135/morning/market_comparison.csv` | 2509818 | split_and_previewed | 523624 |
| `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv` | 527542 | split_and_previewed | 520163 |
| `derek_game_snapshots/21716135/morning/prop_summary.csv` | 27275 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 132841 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 371059 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5821103 | split_and_previewed | 524258 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 371059 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3577261 | split_and_previewed | 523975 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5821103 | split_and_previewed | 524258 |
| `wizard_of_odds/full_pmfs_wide.csv` | 371059 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2509818 | split_and_previewed | 523623 |
| `wizard_of_odds/publishable_edges.csv` | 1978026 | split_and_previewed | 524277 |
