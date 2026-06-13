# Delivery CSV size contract — 2026-06-13

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 352274 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1516465 | split_and_previewed | 523865 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6804 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6868557 | split_and_previewed | 522424 |
| `derek_forward_feed/morning_snapshot.csv` | 6868557 | split_and_previewed | 522424 |
| `derek_game_snapshots/21716138/morning/full_pmf_wide.csv` | 370511 | ok |  |
| `derek_game_snapshots/21716138/morning/market_comparison.csv` | 2578776 | split_and_previewed | 523360 |
| `derek_game_snapshots/21716138/morning/outcome_level_probabilities.csv` | 528256 | split_and_previewed | 520920 |
| `derek_game_snapshots/21716138/morning/prop_summary.csv` | 27361 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 132849 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 370511 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5838521 | split_and_previewed | 524264 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 370511 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3578965 | split_and_previewed | 523783 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5838521 | split_and_previewed | 524264 |
| `wizard_of_odds/full_pmfs_wide.csv` | 370511 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2578776 | split_and_previewed | 523360 |
| `wizard_of_odds/publishable_edges.csv` | 2105423 | split_and_previewed | 524151 |
