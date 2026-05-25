# Delivery CSV size contract — 2026-05-24

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `after_game_scoring/after_game_clv_and_scoring.csv` | 484422 | ok |  |
| `after_game_scoring/after_game_scoring.csv` | 484422 | ok |  |
| `after_game_scoring/calibration_by_role_bucket.csv` | 405 | ok |  |
| `after_game_scoring/calibration_by_stat.csv` | 1327 | ok |  |
| `after_game_scoring/model_vs_market_scoring.csv` | 32462 | ok |  |
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 361830 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 524271 | ok |  |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5566 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 524286 | ok |  |
| `derek_forward_feed/lineup_snapshot.csv` | 524286 | ok |  |
| `derek_forward_feed/morning_snapshot.csv` | 523150 | ok |  |
| `derek_game_snapshots/21713531/close_lock/after_game_scoring.csv` | 4520 | ok |  |
| `derek_game_snapshots/21713531/close_lock/full_pmf_wide.csv` | 409597 | ok |  |
| `derek_game_snapshots/21713531/close_lock/market_comparison.csv` | 2281715 | split_and_previewed | 523193 |
| `derek_game_snapshots/21713531/close_lock/outcome_level_probabilities.csv` | 524275 | ok |  |
| `derek_game_snapshots/21713531/close_lock/prop_summary.csv` | 26856 | ok |  |
| `derek_game_snapshots/21713531/morning/full_pmf_wide.csv` | 442368 | ok |  |
| `derek_game_snapshots/21713531/morning/market_comparison.csv` | 524183 | ok |  |
| `derek_game_snapshots/21713531/morning/outcome_level_probabilities.csv` | 524241 | ok |  |
| `derek_game_snapshots/21713531/morning/prop_summary.csv` | 26165 | ok |  |
| `derek_game_snapshots/aggregate_snapshot_scoring.csv` | 211 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 117614 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 409597 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 524286 | ok |  |
| `pmf_model_review_package/after_game_scoring.csv` | 484422 | ok |  |
| `pmf_model_review_package/machine_readable/model_only.csv` | 409597 | ok |  |
| `wizard_of_odds/after_game_clv_and_scoring.csv` | 484422 | ok |  |
| `wizard_of_odds/calibration_by_role_bucket.csv` | 405 | ok |  |
| `wizard_of_odds/calibration_by_stat.csv` | 1327 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 524092 | ok |  |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 524286 | ok |  |
| `wizard_of_odds/full_pmfs_wide.csv` | 409597 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 523780 | ok |  |
| `wizard_of_odds/publishable_edges.csv` | 849 | ok |  |
