# Delivery CSV size contract — 2026-05-21

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 377787 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1319826 | split_and_previewed | 523793 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5805 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 7823303 | split_and_previewed | 522012 |
| `derek_forward_feed/morning_snapshot.csv` | 7823303 | split_and_previewed | 522012 |
| `derek_game_snapshots/21713897/morning/full_pmf_wide.csv` | 430868 | ok |  |
| `derek_game_snapshots/21713897/morning/market_comparison.csv` | 2231198 | split_and_previewed | 523910 |
| `derek_game_snapshots/21713897/morning/outcome_level_probabilities.csv` | 651476 | split_and_previewed | 524268 |
| `derek_game_snapshots/21713897/morning/prop_summary.csv` | 23717 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 122314 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 430868 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5395415 | split_and_previewed | 523741 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 430868 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3269387 | split_and_previewed | 523762 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5395415 | split_and_previewed | 523741 |
| `wizard_of_odds/full_pmfs_wide.csv` | 430868 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2231198 | split_and_previewed | 523910 |
| `wizard_of_odds/publishable_edges.csv` | 1706703 | split_and_previewed | 524264 |
