# Delivery CSV size contract — 2026-05-23

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 381205 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 548631 | split_and_previewed | 523991 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5713 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 525006 | split_and_previewed | 519385 |
| `derek_forward_feed/morning_snapshot.csv` | 525006 | split_and_previewed | 519385 |
| `derek_game_snapshots/21713899/morning/full_pmf_wide.csv` | 432769 | ok |  |
| `derek_game_snapshots/21713899/morning/market_comparison.csv` | 539781 | split_and_previewed | 523836 |
| `derek_game_snapshots/21713899/morning/outcome_level_probabilities.csv` | 535466 | split_and_previewed | 524223 |
| `derek_game_snapshots/21713899/morning/prop_summary.csv` | 23568 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 122821 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 435880 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5460459 | split_and_previewed | 524284 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 435880 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3279639 | split_and_previewed | 523659 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5460459 | split_and_previewed | 524284 |
| `wizard_of_odds/full_pmfs_wide.csv` | 435880 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2190932 | split_and_previewed | 523651 |
| `wizard_of_odds/publishable_edges.csv` | 1475421 | split_and_previewed | 523661 |
