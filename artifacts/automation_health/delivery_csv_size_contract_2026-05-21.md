# Delivery CSV size contract — 2026-05-21

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 379004 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 912021 | split_and_previewed | 523637 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 149 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 3857002 | split_and_previewed | 524088 |
| `derek_forward_feed/lineup_snapshot.csv` | 3857002 | split_and_previewed | 524088 |
| `derek_forward_feed/morning_snapshot.csv` | 528076 | split_and_previewed | 522012 |
| `derek_game_snapshots/21713897/lineup/full_pmf_wide.csv` | 428204 | ok |  |
| `derek_game_snapshots/21713897/lineup/market_comparison.csv` | 1058512 | split_and_previewed | 523710 |
| `derek_game_snapshots/21713897/lineup/outcome_level_probabilities.csv` | 654812 | split_and_previewed | 524253 |
| `derek_game_snapshots/21713897/lineup/prop_summary.csv` | 22327 | ok |  |
| `derek_game_snapshots/21713897/morning/full_pmf_wide.csv` | 430868 | ok |  |
| `derek_game_snapshots/21713897/morning/market_comparison.csv` | 538733 | split_and_previewed | 523910 |
| `derek_game_snapshots/21713897/morning/outcome_level_probabilities.csv` | 535472 | split_and_previewed | 524268 |
| `derek_game_snapshots/21713897/morning/prop_summary.csv` | 23717 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 119102 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 428204 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5218328 | split_and_previewed | 524258 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 428204 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3200158 | split_and_previewed | 524192 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5218328 | split_and_previewed | 524258 |
| `wizard_of_odds/full_pmfs_wide.csv` | 428204 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 1058512 | split_and_previewed | 523710 |
| `wizard_of_odds/publishable_edges.csv` | 818301 | split_and_previewed | 524074 |
