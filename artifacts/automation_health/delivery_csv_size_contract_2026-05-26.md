# Delivery CSV size contract — 2026-05-26

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 363062 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1574524 | split_and_previewed | 524279 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6988 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6845116 | split_and_previewed | 523916 |
| `derek_forward_feed/lineup_snapshot.csv` | 534742 | split_and_previewed | 523284 |
| `derek_forward_feed/morning_snapshot.csv` | 6845116 | split_and_previewed | 523916 |
| `derek_game_snapshots/21713532/lineup/full_pmf_wide.csv` | 383704 | ok |  |
| `derek_game_snapshots/21713532/lineup/market_comparison.csv` | 544731 | split_and_previewed | 523600 |
| `derek_game_snapshots/21713532/lineup/outcome_level_probabilities.csv` | 530681 | split_and_previewed | 524243 |
| `derek_game_snapshots/21713532/lineup/prop_summary.csv` | 27909 | ok |  |
| `derek_game_snapshots/21713532/morning/full_pmf_wide.csv` | 382848 | ok |  |
| `derek_game_snapshots/21713532/morning/market_comparison.csv` | 2555739 | split_and_previewed | 523904 |
| `derek_game_snapshots/21713532/morning/outcome_level_probabilities.csv` | 671333 | split_and_previewed | 524234 |
| `derek_game_snapshots/21713532/morning/prop_summary.csv` | 30786 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 136504 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 382848 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 6089413 | split_and_previewed | 523835 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 382848 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3657410 | split_and_previewed | 523843 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 6089413 | split_and_previewed | 523835 |
| `wizard_of_odds/full_pmfs_wide.csv` | 382848 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2555739 | split_and_previewed | 523904 |
| `wizard_of_odds/publishable_edges.csv` | 2146514 | split_and_previewed | 524105 |
