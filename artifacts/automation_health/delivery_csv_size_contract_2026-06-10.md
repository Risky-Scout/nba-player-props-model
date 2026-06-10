# Delivery CSV size contract — 2026-06-10

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 331142 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 548223 | split_and_previewed | 523809 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6278 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 531807 | split_and_previewed | 523052 |
| `derek_forward_feed/morning_snapshot.csv` | 531807 | split_and_previewed | 523052 |
| `derek_game_snapshots/21716137/morning/full_pmf_wide.csv` | 362823 | ok |  |
| `derek_game_snapshots/21716137/morning/market_comparison.csv` | 543040 | split_and_previewed | 524271 |
| `derek_game_snapshots/21716137/morning/outcome_level_probabilities.csv` | 532074 | split_and_previewed | 524251 |
| `derek_game_snapshots/21716137/morning/prop_summary.csv` | 25667 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 124829 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 349406 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5487878 | split_and_previewed | 524061 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 349406 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3361810 | split_and_previewed | 523607 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5487878 | split_and_previewed | 524061 |
| `wizard_of_odds/full_pmfs_wide.csv` | 349406 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2532976 | split_and_previewed | 524071 |
| `wizard_of_odds/publishable_edges.csv` | 1924722 | split_and_previewed | 523545 |
