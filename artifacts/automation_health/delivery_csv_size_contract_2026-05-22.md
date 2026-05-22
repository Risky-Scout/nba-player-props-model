# Delivery CSV size contract — 2026-05-22

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 331982 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547216 | split_and_previewed | 524200 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5720 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 527566 | split_and_previewed | 520842 |
| `derek_forward_feed/lineup_snapshot.csv` | 531265 | split_and_previewed | 524168 |
| `derek_forward_feed/morning_snapshot.csv` | 527566 | split_and_previewed | 520842 |
| `derek_game_snapshots/21713530/lineup/full_pmf_wide.csv` | 382487 | ok |  |
| `derek_game_snapshots/21713530/lineup/market_comparison.csv` | 543614 | split_and_previewed | 523650 |
| `derek_game_snapshots/21713530/lineup/outcome_level_probabilities.csv` | 533522 | split_and_previewed | 524220 |
| `derek_game_snapshots/21713530/lineup/prop_summary.csv` | 22350 | ok |  |
| `derek_game_snapshots/21713530/morning/full_pmf_wide.csv` | 381493 | ok |  |
| `derek_game_snapshots/21713530/morning/market_comparison.csv` | 544699 | split_and_previewed | 523612 |
| `derek_game_snapshots/21713530/morning/outcome_level_probabilities.csv` | 533679 | split_and_previewed | 524269 |
| `derek_game_snapshots/21713530/morning/prop_summary.csv` | 22511 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 108763 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 378474 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4808747 | split_and_previewed | 523671 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 378474 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2891660 | split_and_previewed | 524052 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4808747 | split_and_previewed | 523671 |
| `wizard_of_odds/full_pmfs_wide.csv` | 378474 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2003969 | split_and_previewed | 523815 |
| `wizard_of_odds/publishable_edges.csv` | 1588262 | split_and_previewed | 524264 |
