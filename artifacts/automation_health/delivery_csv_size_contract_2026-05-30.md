# Delivery CSV size contract — 2026-05-30

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 361171 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547113 | split_and_previewed | 523935 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6988 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 533510 | split_and_previewed | 524076 |
| `derek_forward_feed/morning_snapshot.csv` | 533510 | split_and_previewed | 524076 |
| `derek_game_snapshots/21713534/morning/full_pmf_wide.csv` | 380880 | ok |  |
| `derek_game_snapshots/21713534/morning/market_comparison.csv` | 545686 | split_and_previewed | 523617 |
| `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv` | 530942 | split_and_previewed | 524250 |
| `derek_game_snapshots/21713534/morning/prop_summary.csv` | 27939 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 134001 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 381842 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5954394 | split_and_previewed | 523917 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 381842 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3602396 | split_and_previewed | 523715 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5954394 | split_and_previewed | 523917 |
| `wizard_of_odds/full_pmfs_wide.csv` | 381842 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2584305 | split_and_previewed | 523570 |
| `wizard_of_odds/publishable_edges.csv` | 2266815 | split_and_previewed | 524282 |
