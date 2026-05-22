# Delivery CSV size contract — 2026-05-22

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 337415 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1493964 | split_and_previewed | 523883 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5730 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6974554 | split_and_previewed | 519696 |
| `derek_forward_feed/lineup_snapshot.csv` | 6974554 | split_and_previewed | 519696 |
| `derek_game_snapshots/21713530/lineup/full_pmf_wide.csv` | 385366 | ok |  |
| `derek_game_snapshots/21713530/lineup/market_comparison.csv` | 2020842 | split_and_previewed | 523694 |
| `derek_game_snapshots/21713530/lineup/outcome_level_probabilities.csv` | 666210 | split_and_previewed | 524236 |
| `derek_game_snapshots/21713530/lineup/prop_summary.csv` | 22235 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 112061 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 385366 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4808723 | split_and_previewed | 523689 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 385366 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2963050 | split_and_previewed | 524264 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4808723 | split_and_previewed | 523689 |
| `wizard_of_odds/full_pmfs_wide.csv` | 385366 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2020842 | split_and_previewed | 523694 |
| `wizard_of_odds/publishable_edges.csv` | 1564984 | split_and_previewed | 523672 |
