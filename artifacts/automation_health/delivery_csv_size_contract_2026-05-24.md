# Delivery CSV size contract — 2026-05-24

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 384804 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 548270 | split_and_previewed | 524235 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6685 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 530055 | split_and_previewed | 523150 |
| `derek_forward_feed/morning_snapshot.csv` | 530055 | split_and_previewed | 523150 |
| `derek_game_snapshots/21713531/morning/full_pmf_wide.csv` | 442368 | ok |  |
| `derek_game_snapshots/21713531/morning/market_comparison.csv` | 544425 | split_and_previewed | 524183 |
| `derek_game_snapshots/21713531/morning/outcome_level_probabilities.csv` | 533979 | split_and_previewed | 524241 |
| `derek_game_snapshots/21713531/morning/prop_summary.csv` | 26165 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 125438 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 438961 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5561921 | split_and_previewed | 523695 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 438961 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3337342 | split_and_previewed | 524105 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5561921 | split_and_previewed | 523695 |
| `wizard_of_odds/full_pmfs_wide.csv` | 438961 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2357026 | split_and_previewed | 524154 |
| `wizard_of_odds/publishable_edges.csv` | 2010706 | split_and_previewed | 523873 |
