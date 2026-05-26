# Delivery CSV size contract — 2026-05-26

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 364036 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1881327 | split_and_previewed | 524117 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6983 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6834112 | split_and_previewed | 523284 |
| `derek_forward_feed/lineup_snapshot.csv` | 6834112 | split_and_previewed | 523284 |
| `derek_game_snapshots/21713532/lineup/full_pmf_wide.csv` | 383704 | ok |  |
| `derek_game_snapshots/21713532/lineup/market_comparison.csv` | 2585735 | split_and_previewed | 523600 |
| `derek_game_snapshots/21713532/lineup/outcome_level_probabilities.csv` | 570044 | split_and_previewed | 524243 |
| `derek_game_snapshots/21713532/lineup/prop_summary.csv` | 27909 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 138065 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 383704 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5953992 | split_and_previewed | 523931 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 383704 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3690597 | split_and_previewed | 524111 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5953992 | split_and_previewed | 523931 |
| `wizard_of_odds/full_pmfs_wide.csv` | 383704 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2585735 | split_and_previewed | 523600 |
| `wizard_of_odds/publishable_edges.csv` | 2152447 | split_and_previewed | 523600 |
