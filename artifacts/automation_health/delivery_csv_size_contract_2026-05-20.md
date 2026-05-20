# Delivery CSV size contract — 2026-05-20

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 346801 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1500759 | split_and_previewed | 524133 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5728 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 8346670 | split_and_previewed | 522647 |
| `derek_forward_feed/lineup_snapshot.csv` | 523516 | ok |  |
| `derek_forward_feed/morning_snapshot.csv` | 8346670 | split_and_previewed | 522647 |
| `derek_game_snapshots/21713529/lineup/full_pmf_wide.csv` | 435373 | ok |  |
| `derek_game_snapshots/21713529/lineup/market_comparison.csv` | 523313 | ok |  |
| `derek_game_snapshots/21713529/lineup/outcome_level_probabilities.csv` | 524270 | ok |  |
| `derek_game_snapshots/21713529/lineup/prop_summary.csv` | 25936 | ok |  |
| `derek_game_snapshots/21713529/morning/full_pmf_wide.csv` | 432583 | ok |  |
| `derek_game_snapshots/21713529/morning/market_comparison.csv` | 2918636 | split_and_previewed | 523742 |
| `derek_game_snapshots/21713529/morning/outcome_level_probabilities.csv` | 764073 | split_and_previewed | 524238 |
| `derek_game_snapshots/21713529/morning/prop_summary.csv` | 25984 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 109926 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 400791 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4800562 | split_and_previewed | 523954 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 400791 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3297852 | split_and_previewed | 524172 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4800562 | split_and_previewed | 523954 |
| `wizard_of_odds/full_pmfs_wide.csv` | 400791 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2519287 | split_and_previewed | 523799 |
| `wizard_of_odds/publishable_edges.csv` | 2052968 | split_and_previewed | 524110 |
