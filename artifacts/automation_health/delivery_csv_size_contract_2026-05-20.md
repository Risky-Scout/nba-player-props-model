# Delivery CSV size contract — 2026-05-20

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `after_game_scoring/after_game_clv_and_scoring.csv` | 417970 | ok |  |
| `after_game_scoring/after_game_scoring.csv` | 417970 | ok |  |
| `after_game_scoring/calibration_by_role_bucket.csv` | 407 | ok |  |
| `after_game_scoring/calibration_by_stat.csv` | 1320 | ok |  |
| `after_game_scoring/model_vs_market_scoring.csv` | 368836 | ok |  |
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 323671 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1712455 | split_and_previewed | 524072 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5336 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 7324597 | split_and_previewed | 523054 |
| `derek_forward_feed/lineup_snapshot.csv` | 7324597 | split_and_previewed | 523054 |
| `derek_forward_feed/morning_snapshot.csv` | 456547 | ok |  |
| `derek_game_snapshots/21713529/lineup/full_pmf_wide.csv` | 402022 | ok |  |
| `derek_game_snapshots/21713529/lineup/market_comparison.csv` | 2661579 | split_and_previewed | 523476 |
| `derek_game_snapshots/21713529/lineup/outcome_level_probabilities.csv` | 804654 | split_and_previewed | 524193 |
| `derek_game_snapshots/21713529/lineup/prop_summary.csv` | 26379 | ok |  |
| `derek_game_snapshots/21713529/morning/full_pmf_wide.csv` | 380661 | ok |  |
| `derek_game_snapshots/21713529/morning/market_comparison.csv` | 390551 | ok |  |
| `derek_game_snapshots/21713529/morning/outcome_level_probabilities.csv` | 451536 | ok |  |
| `derek_game_snapshots/21713529/morning/prop_summary.csv` | 22750 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 107045 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 372425 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4561053 | split_and_previewed | 523767 |
| `pmf_model_review_package/after_game_scoring.csv` | 417970 | ok |  |
| `pmf_model_review_package/machine_readable/model_only.csv` | 372425 | ok |  |
| `wizard_of_odds/after_game_clv_and_scoring.csv` | 417970 | ok |  |
| `wizard_of_odds/calibration_by_role_bucket.csv` | 407 | ok |  |
| `wizard_of_odds/calibration_by_stat.csv` | 1320 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3159220 | split_and_previewed | 524134 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4561053 | split_and_previewed | 523767 |
| `wizard_of_odds/full_pmfs_wide.csv` | 372425 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2297146 | split_and_previewed | 523914 |
| `wizard_of_odds/publishable_edges.csv` | 1745988 | split_and_previewed | 523057 |
