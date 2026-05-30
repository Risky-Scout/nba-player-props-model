# Delivery CSV size contract — 2026-05-30

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 358183 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1553425 | split_and_previewed | 523825 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6987 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6768391 | split_and_previewed | 524137 |
| `derek_forward_feed/morning_snapshot.csv` | 6768391 | split_and_previewed | 524137 |
| `derek_game_snapshots/21713534/morning/full_pmf_wide.csv` | 376051 | ok |  |
| `derek_game_snapshots/21713534/morning/market_comparison.csv` | 2564863 | split_and_previewed | 523538 |
| `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv` | 560335 | split_and_previewed | 524251 |
| `derek_game_snapshots/21713534/morning/prop_summary.csv` | 27909 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133616 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 376051 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5937640 | split_and_previewed | 523789 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 376051 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3594329 | split_and_previewed | 524219 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5937640 | split_and_previewed | 523789 |
| `wizard_of_odds/full_pmfs_wide.csv` | 376051 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2564863 | split_and_previewed | 523538 |
| `wizard_of_odds/publishable_edges.csv` | 2262857 | split_and_previewed | 523742 |
