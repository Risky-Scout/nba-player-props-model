# Delivery CSV size contract — 2026-05-28

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 314077 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1295208 | split_and_previewed | 524140 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6192 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5906379 | split_and_previewed | 524284 |
| `derek_forward_feed/morning_snapshot.csv` | 5906379 | split_and_previewed | 524284 |
| `derek_game_snapshots/21713533/morning/full_pmf_wide.csv` | 330452 | ok |  |
| `derek_game_snapshots/21713533/morning/market_comparison.csv` | 2267802 | split_and_previewed | 523743 |
| `derek_game_snapshots/21713533/morning/outcome_level_probabilities.csv` | 492738 | ok |  |
| `derek_game_snapshots/21713533/morning/prop_summary.csv` | 24459 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 116758 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 330452 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5182641 | split_and_previewed | 524142 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 330452 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3141386 | split_and_previewed | 523669 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5182641 | split_and_previewed | 524142 |
| `wizard_of_odds/full_pmfs_wide.csv` | 330452 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2267802 | split_and_previewed | 523743 |
| `wizard_of_odds/publishable_edges.csv` | 1936137 | split_and_previewed | 523511 |
