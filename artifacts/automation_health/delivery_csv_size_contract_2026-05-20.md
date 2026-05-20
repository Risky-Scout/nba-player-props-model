# Delivery CSV size contract — 2026-05-20

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 337922 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1557581 | split_and_previewed | 523955 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5772 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6603286 | split_and_previewed | 521100 |
| `derek_forward_feed/lineup_snapshot.csv` | 6603286 | split_and_previewed | 521100 |
| `derek_forward_feed/morning_snapshot.csv` | 456547 | ok |  |
| `derek_game_snapshots/21713529/lineup/full_pmf_wide.csv` | 384229 | ok |  |
| `derek_game_snapshots/21713529/lineup/market_comparison.csv` | 2040383 | split_and_previewed | 524076 |
| `derek_game_snapshots/21713529/lineup/outcome_level_probabilities.csv` | 768648 | split_and_previewed | 524209 |
| `derek_game_snapshots/21713529/lineup/prop_summary.csv` | 25127 | ok |  |
| `derek_game_snapshots/21713529/morning/full_pmf_wide.csv` | 380661 | ok |  |
| `derek_game_snapshots/21713529/morning/market_comparison.csv` | 390551 | ok |  |
| `derek_game_snapshots/21713529/morning/outcome_level_probabilities.csv` | 451536 | ok |  |
| `derek_game_snapshots/21713529/morning/prop_summary.csv` | 22750 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 114304 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 384229 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4942451 | split_and_previewed | 523845 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 384229 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3009545 | split_and_previewed | 523684 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4942451 | split_and_previewed | 523845 |
| `wizard_of_odds/full_pmfs_wide.csv` | 384229 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2040383 | split_and_previewed | 524074 |
| `wizard_of_odds/publishable_edges.csv` | 1616826 | split_and_previewed | 524271 |
