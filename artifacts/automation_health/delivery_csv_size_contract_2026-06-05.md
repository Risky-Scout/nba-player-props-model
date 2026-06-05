# Delivery CSV size contract — 2026-06-05

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 356145 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547876 | split_and_previewed | 524276 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6504 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 532321 | split_and_previewed | 523048 |
| `derek_forward_feed/morning_snapshot.csv` | 532321 | split_and_previewed | 523048 |
| `derek_game_snapshots/21716135/morning/full_pmf_wide.csv` | 368112 | ok |  |
| `derek_game_snapshots/21716135/morning/market_comparison.csv` | 543108 | split_and_previewed | 523689 |
| `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv` | 520349 | ok |  |
| `derek_game_snapshots/21716135/morning/prop_summary.csv` | 27232 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133224 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 378090 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5843736 | split_and_previewed | 523699 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 378090 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3586816 | split_and_previewed | 523961 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5843736 | split_and_previewed | 523699 |
| `wizard_of_odds/full_pmfs_wide.csv` | 378090 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2544157 | split_and_previewed | 523527 |
| `wizard_of_odds/publishable_edges.csv` | 1998178 | split_and_previewed | 523731 |
