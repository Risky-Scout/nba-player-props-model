# Delivery CSV size contract — 2026-06-10

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 339384 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1470222 | split_and_previewed | 523809 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6278 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 7106972 | split_and_previewed | 523052 |
| `derek_forward_feed/morning_snapshot.csv` | 7106972 | split_and_previewed | 523052 |
| `derek_game_snapshots/21716137/morning/full_pmf_wide.csv` | 362823 | ok |  |
| `derek_game_snapshots/21716137/morning/market_comparison.csv` | 2510386 | split_and_previewed | 524271 |
| `derek_game_snapshots/21716137/morning/outcome_level_probabilities.csv` | 533785 | split_and_previewed | 524251 |
| `derek_game_snapshots/21716137/morning/prop_summary.csv` | 25667 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 124469 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 362823 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5482328 | split_and_previewed | 524049 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 362823 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3355434 | split_and_previewed | 523903 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5482328 | split_and_previewed | 524049 |
| `wizard_of_odds/full_pmfs_wide.csv` | 362823 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2510386 | split_and_previewed | 524271 |
| `wizard_of_odds/publishable_edges.csv` | 1957704 | split_and_previewed | 523888 |
