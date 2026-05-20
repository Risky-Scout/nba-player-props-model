# Delivery CSV size contract — 2026-05-20

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 350278 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1480320 | split_and_previewed | 524229 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5664 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 8047514 | split_and_previewed | 522156 |
| `derek_forward_feed/morning_snapshot.csv` | 8047514 | split_and_previewed | 522156 |
| `derek_game_snapshots/21713529/morning/full_pmf_wide.csv` | 436386 | ok |  |
| `derek_game_snapshots/21713529/morning/market_comparison.csv` | 2836951 | split_and_previewed | 523526 |
| `derek_game_snapshots/21713529/morning/outcome_level_probabilities.csv` | 765444 | split_and_previewed | 524251 |
| `derek_game_snapshots/21713529/morning/prop_summary.csv` | 25644 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 113233 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 404417 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4802504 | split_and_previewed | 524041 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 404417 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3368732 | split_and_previewed | 523363 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4802504 | split_and_previewed | 524041 |
| `wizard_of_odds/full_pmfs_wide.csv` | 404417 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2445181 | split_and_previewed | 524134 |
| `wizard_of_odds/publishable_edges.csv` | 1990792 | split_and_previewed | 523559 |
