# Delivery CSV size contract — 2026-06-10

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 337164 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1640811 | split_and_previewed | 523834 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6334 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6914171 | split_and_previewed | 522592 |
| `derek_forward_feed/morning_snapshot.csv` | 6914171 | split_and_previewed | 522592 |
| `derek_game_snapshots/21716137/current_live/contextual_feature_audit.csv` | 4832 | ok |  |
| `derek_game_snapshots/21716137/current_live/full_pmf_wide.csv` | 41966 | ok |  |
| `derek_game_snapshots/21716137/current_live/game_context.csv` | 612 | ok |  |
| `derek_game_snapshots/21716137/current_live/injury_availability_context.csv` | 601 | ok |  |
| `derek_game_snapshots/21716137/current_live/lineup_context.csv` | 1629 | ok |  |
| `derek_game_snapshots/21716137/current_live/market_comparison.csv` | 51079 | ok |  |
| `derek_game_snapshots/21716137/current_live/outcome_level_probabilities.csv` | 119943 | ok |  |
| `derek_game_snapshots/21716137/current_live/pmf_driver_decomposition.csv` | 3171 | ok |  |
| `derek_game_snapshots/21716137/current_live/prediction_input_audit.csv` | 2410 | ok |  |
| `derek_game_snapshots/21716137/current_live/prop_summary.csv` | 1768 | ok |  |
| `derek_game_snapshots/21716137/morning/full_pmf_wide.csv` | 354837 | ok |  |
| `derek_game_snapshots/21716137/morning/market_comparison.csv` | 2639921 | split_and_previewed | 523392 |
| `derek_game_snapshots/21716137/morning/outcome_level_probabilities.csv` | 586082 | split_and_previewed | 524231 |
| `derek_game_snapshots/21716137/morning/prop_summary.csv` | 28449 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 130972 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 354837 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5611944 | split_and_previewed | 524081 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 354837 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3492585 | split_and_previewed | 524027 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5611944 | split_and_previewed | 524081 |
| `wizard_of_odds/full_pmfs_wide.csv` | 354837 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2639921 | split_and_previewed | 523392 |
| `wizard_of_odds/publishable_edges.csv` | 2054259 | split_and_previewed | 523429 |
