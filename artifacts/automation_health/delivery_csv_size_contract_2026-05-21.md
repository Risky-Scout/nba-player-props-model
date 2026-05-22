# Delivery CSV size contract — 2026-05-21

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 380357 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 838879 | split_and_previewed | 524089 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 149 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 3593702 | split_and_previewed | 522117 |
| `derek_forward_feed/lineup_snapshot.csv` | 3593702 | split_and_previewed | 522117 |
| `derek_forward_feed/morning_snapshot.csv` | 528076 | split_and_previewed | 522012 |
| `derek_game_snapshots/21713897/lineup/full_pmf_wide.csv` | 430315 | ok |  |
| `derek_game_snapshots/21713897/lineup/market_comparison.csv` | 975713 | split_and_previewed | 523983 |
| `derek_game_snapshots/21713897/lineup/outcome_level_probabilities.csv` | 658949 | split_and_previewed | 524271 |
| `derek_game_snapshots/21713897/lineup/prop_summary.csv` | 22314 | ok |  |
| `derek_game_snapshots/21713897/morning/full_pmf_wide.csv` | 430868 | ok |  |
| `derek_game_snapshots/21713897/morning/market_comparison.csv` | 538733 | split_and_previewed | 523910 |
| `derek_game_snapshots/21713897/morning/outcome_level_probabilities.csv` | 535472 | split_and_previewed | 524268 |
| `derek_game_snapshots/21713897/morning/prop_summary.csv` | 23717 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 119102 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 430315 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5220229 | split_and_previewed | 524213 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 430315 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3199931 | split_and_previewed | 523322 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5220229 | split_and_previewed | 524213 |
| `wizard_of_odds/full_pmfs_wide.csv` | 430315 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 975713 | split_and_previewed | 523983 |
| `wizard_of_odds/publishable_edges.csv` | 739029 | split_and_previewed | 523383 |
