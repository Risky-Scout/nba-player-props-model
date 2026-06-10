# Delivery CSV size contract — 2026-06-10

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 335104 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 547618 | split_and_previewed | 524253 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6334 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 531103 | split_and_previewed | 521939 |
| `derek_forward_feed/morning_snapshot.csv` | 531103 | split_and_previewed | 521939 |
| `derek_game_snapshots/21716137/morning/full_pmf_wide.csv` | 354761 | ok |  |
| `derek_game_snapshots/21716137/morning/market_comparison.csv` | 541988 | split_and_previewed | 523402 |
| `derek_game_snapshots/21716137/morning/outcome_level_probabilities.csv` | 512206 | ok |  |
| `derek_game_snapshots/21716137/morning/prop_summary.csv` | 25748 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 124830 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 356386 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5485896 | split_and_previewed | 524090 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 356386 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3362730 | split_and_previewed | 523671 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5485896 | split_and_previewed | 524090 |
| `wizard_of_odds/full_pmfs_wide.csv` | 356386 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2534306 | split_and_previewed | 524140 |
| `wizard_of_odds/publishable_edges.csv` | 1967301 | split_and_previewed | 524158 |
