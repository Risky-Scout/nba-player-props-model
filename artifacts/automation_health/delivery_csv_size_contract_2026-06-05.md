# Delivery CSV size contract — 2026-06-05

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 350445 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1550985 | split_and_previewed | 524276 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6504 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6793114 | split_and_previewed | 523048 |
| `derek_forward_feed/morning_snapshot.csv` | 6793114 | split_and_previewed | 523048 |
| `derek_game_snapshots/21716135/morning/full_pmf_wide.csv` | 368112 | ok |  |
| `derek_game_snapshots/21716135/morning/market_comparison.csv` | 2546340 | split_and_previewed | 523689 |
| `derek_game_snapshots/21716135/morning/outcome_level_probabilities.csv` | 520349 | ok |  |
| `derek_game_snapshots/21716135/morning/prop_summary.csv` | 27232 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 132841 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 368112 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5819139 | split_and_previewed | 524237 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 368112 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3577293 | split_and_previewed | 524221 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5819139 | split_and_previewed | 524237 |
| `wizard_of_odds/full_pmfs_wide.csv` | 368112 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2546340 | split_and_previewed | 523689 |
| `wizard_of_odds/publishable_edges.csv` | 2005618 | split_and_previewed | 524268 |
