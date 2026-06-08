# Delivery CSV size contract — 2026-06-08

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 265018 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547473 | split_and_previewed | 523821 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5275 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 533187 | split_and_previewed | 524201 |
| `derek_forward_feed/morning_snapshot.csv` | 533187 | split_and_previewed | 524201 |
| `derek_game_snapshots/21716136/morning/full_pmf_wide.csv` | 279321 | ok |  |
| `derek_game_snapshots/21716136/morning/market_comparison.csv` | 542363 | split_and_previewed | 523395 |
| `derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv` | 400659 | ok |  |
| `derek_game_snapshots/21716136/morning/prop_summary.csv` | 20856 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 100168 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 279087 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4414184 | split_and_previewed | 523959 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 279087 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2692623 | split_and_previewed | 524125 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4414184 | split_and_previewed | 523959 |
| `wizard_of_odds/full_pmfs_wide.csv` | 279087 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2165875 | split_and_previewed | 523855 |
| `wizard_of_odds/publishable_edges.csv` | 1781064 | split_and_previewed | 523558 |
