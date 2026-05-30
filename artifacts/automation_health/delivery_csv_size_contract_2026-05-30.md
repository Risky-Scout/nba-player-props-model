# Delivery CSV size contract — 2026-05-30

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 361069 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1494474 | split_and_previewed | 523900 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6881 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6875038 | split_and_previewed | 524122 |
| `derek_forward_feed/morning_snapshot.csv` | 6875038 | split_and_previewed | 524122 |
| `derek_game_snapshots/21713534/morning/full_pmf_wide.csv` | 381126 | ok |  |
| `derek_game_snapshots/21713534/morning/market_comparison.csv` | 2627868 | split_and_previewed | 523634 |
| `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv` | 574586 | split_and_previewed | 524216 |
| `derek_game_snapshots/21713534/morning/prop_summary.csv` | 27784 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133617 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 381126 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5933541 | split_and_previewed | 523826 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 381126 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3594280 | split_and_previewed | 524092 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5933541 | split_and_previewed | 523826 |
| `wizard_of_odds/full_pmfs_wide.csv` | 381126 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2627868 | split_and_previewed | 523634 |
| `wizard_of_odds/publishable_edges.csv` | 2304879 | split_and_previewed | 523635 |
