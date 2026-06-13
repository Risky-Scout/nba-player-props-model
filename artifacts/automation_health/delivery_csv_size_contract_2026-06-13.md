# Delivery CSV size contract — 2026-06-13

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 349918 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547949 | split_and_previewed | 524180 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6799 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 529695 | split_and_previewed | 520413 |
| `derek_forward_feed/morning_snapshot.csv` | 529695 | split_and_previewed | 520413 |
| `derek_game_snapshots/21716138/morning/full_pmf_wide.csv` | 365106 | ok |  |
| `derek_game_snapshots/21716138/morning/market_comparison.csv` | 543424 | split_and_previewed | 524206 |
| `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv` | 513502 | ok |  |
| `derek_game_snapshots/21716138/morning/prop_summary.csv` | 27359 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133235 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 366586 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5865149 | split_and_previewed | 523774 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 366586 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3586764 | split_and_previewed | 523925 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5865149 | split_and_previewed | 523774 |
| `wizard_of_odds/full_pmfs_wide.csv` | 366586 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2587437 | split_and_previewed | 523761 |
| `wizard_of_odds/publishable_edges.csv` | 2095658 | split_and_previewed | 523684 |
