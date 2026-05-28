# Delivery CSV size contract — 2026-05-28

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 316699 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1354549 | split_and_previewed | 523974 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6221 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6045430 | split_and_previewed | 522052 |
| `derek_forward_feed/morning_snapshot.csv` | 6045430 | split_and_previewed | 522052 |
| `derek_game_snapshots/21713533/morning/full_pmf_wide.csv` | 335043 | ok |  |
| `derek_game_snapshots/21713533/morning/market_comparison.csv` | 2287511 | split_and_previewed | 523887 |
| `derek_game_snapshots/21713533/morning/outcome_level_probabilities.csv` | 505471 | ok |  |
| `derek_game_snapshots/21713533/morning/prop_summary.csv` | 24546 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 116758 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 335043 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5182641 | split_and_previewed | 524165 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 335043 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3141652 | split_and_previewed | 523766 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5182641 | split_and_previewed | 524165 |
| `wizard_of_odds/full_pmfs_wide.csv` | 335043 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2287511 | split_and_previewed | 523877 |
| `wizard_of_odds/publishable_edges.csv` | 1932942 | split_and_previewed | 524004 |
