# Delivery CSV size contract — 2026-06-10

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 329530 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1542125 | split_and_previewed | 524080 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6330 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6814648 | split_and_previewed | 522984 |
| `derek_forward_feed/morning_snapshot.csv` | 6814648 | split_and_previewed | 522984 |
| `derek_game_snapshots/21716137/morning/full_pmf_wide.csv` | 346457 | ok |  |
| `derek_game_snapshots/21716137/morning/market_comparison.csv` | 2534400 | split_and_previewed | 523451 |
| `derek_game_snapshots/21716137/morning/outcome_level_probabilities.csv` | 490190 | ok |  |
| `derek_game_snapshots/21716137/morning/prop_summary.csv` | 25753 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 124470 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 346457 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5466504 | split_and_previewed | 523999 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 346457 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3353611 | split_and_previewed | 523694 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5466504 | split_and_previewed | 523999 |
| `wizard_of_odds/full_pmfs_wide.csv` | 346457 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2534400 | split_and_previewed | 523451 |
| `wizard_of_odds/publishable_edges.csv` | 1930896 | split_and_previewed | 524287 |
