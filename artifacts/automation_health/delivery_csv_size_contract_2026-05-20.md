# Delivery CSV size contract — 2026-05-20

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 349420 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1829108 | split_and_previewed | 523991 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5764 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 8058488 | split_and_previewed | 523516 |
| `derek_forward_feed/lineup_snapshot.csv` | 8058488 | split_and_previewed | 523516 |
| `derek_forward_feed/morning_snapshot.csv` | 524057 | ok |  |
| `derek_game_snapshots/21713529/lineup/full_pmf_wide.csv` | 435373 | ok |  |
| `derek_game_snapshots/21713529/lineup/market_comparison.csv` | 2862246 | split_and_previewed | 523313 |
| `derek_game_snapshots/21713529/lineup/outcome_level_probabilities.csv` | 762049 | split_and_previewed | 524270 |
| `derek_game_snapshots/21713529/lineup/prop_summary.csv` | 25936 | ok |  |
| `derek_game_snapshots/21713529/morning/full_pmf_wide.csv` | 430446 | ok |  |
| `derek_game_snapshots/21713529/morning/market_comparison.csv` | 523942 | ok |  |
| `derek_game_snapshots/21713529/morning/outcome_level_probabilities.csv` | 524250 | ok |  |
| `derek_game_snapshots/21713529/morning/prop_summary.csv` | 25912 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 113534 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 403575 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4812693 | split_and_previewed | 524011 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 403575 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3376205 | split_and_previewed | 523953 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4812693 | split_and_previewed | 524011 |
| `wizard_of_odds/full_pmfs_wide.csv` | 403575 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2475607 | split_and_previewed | 523426 |
| `wizard_of_odds/publishable_edges.csv` | 2024314 | split_and_previewed | 523938 |
