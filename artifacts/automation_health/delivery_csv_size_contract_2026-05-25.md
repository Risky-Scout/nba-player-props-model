# Delivery CSV size contract — 2026-05-25

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 303412 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 548599 | split_and_previewed | 523888 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 4998 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 527627 | split_and_previewed | 522266 |
| `derek_forward_feed/morning_snapshot.csv` | 527627 | split_and_previewed | 522266 |
| `derek_game_snapshots/21713901/morning/full_pmf_wide.csv` | 345934 | ok |  |
| `derek_game_snapshots/21713901/morning/market_comparison.csv` | 543095 | split_and_previewed | 523636 |
| `derek_game_snapshots/21713901/morning/outcome_level_probabilities.csv` | 525233 | split_and_previewed | 514071 |
| `derek_game_snapshots/21713901/morning/prop_summary.csv` | 19317 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 98246 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 346107 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4366149 | split_and_previewed | 524265 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 346107 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2622984 | split_and_previewed | 523761 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4366149 | split_and_previewed | 524265 |
| `wizard_of_odds/full_pmfs_wide.csv` | 346107 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2086943 | split_and_previewed | 523237 |
| `wizard_of_odds/publishable_edges.csv` | 1607721 | split_and_previewed | 524089 |
