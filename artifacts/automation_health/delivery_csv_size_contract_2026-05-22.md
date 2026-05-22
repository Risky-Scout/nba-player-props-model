# Delivery CSV size contract — 2026-05-22

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 335651 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1574194 | split_and_previewed | 524194 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5731 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 7036138 | split_and_previewed | 524168 |
| `derek_forward_feed/lineup_snapshot.csv` | 7036138 | split_and_previewed | 524168 |
| `derek_game_snapshots/21713530/lineup/full_pmf_wide.csv` | 382487 | ok |  |
| `derek_game_snapshots/21713530/lineup/market_comparison.csv` | 2071201 | split_and_previewed | 523650 |
| `derek_game_snapshots/21713530/lineup/outcome_level_probabilities.csv` | 659367 | split_and_previewed | 524220 |
| `derek_game_snapshots/21713530/lineup/prop_summary.csv` | 22350 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 112061 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 382487 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4810726 | split_and_previewed | 523695 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 382487 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2962498 | split_and_previewed | 523840 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4810726 | split_and_previewed | 523695 |
| `wizard_of_odds/full_pmfs_wide.csv` | 382487 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2071201 | split_and_previewed | 523652 |
| `wizard_of_odds/publishable_edges.csv` | 1599423 | split_and_previewed | 523741 |
