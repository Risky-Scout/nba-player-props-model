# Delivery CSV size contract — 2026-05-30

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 361796 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547079 | split_and_previewed | 523825 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6987 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 535037 | split_and_previewed | 524137 |
| `derek_forward_feed/morning_snapshot.csv` | 535037 | split_and_previewed | 524137 |
| `derek_game_snapshots/21713534/morning/full_pmf_wide.csv` | 376051 | ok |  |
| `derek_game_snapshots/21713534/morning/market_comparison.csv` | 545644 | split_and_previewed | 523538 |
| `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv` | 530763 | split_and_previewed | 524251 |
| `derek_game_snapshots/21713534/morning/prop_summary.csv` | 27909 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 134002 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 382753 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5958447 | split_and_previewed | 523834 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 382753 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3603017 | split_and_previewed | 524273 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5958447 | split_and_previewed | 523834 |
| `wizard_of_odds/full_pmfs_wide.csv` | 382753 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2602448 | split_and_previewed | 523589 |
| `wizard_of_odds/publishable_edges.csv` | 2313271 | split_and_previewed | 524203 |
