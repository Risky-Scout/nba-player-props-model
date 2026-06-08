# Delivery CSV size contract — 2026-06-08

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 269618 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1249040 | split_and_previewed | 524255 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5291 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 5865010 | split_and_previewed | 522203 |
| `derek_forward_feed/morning_snapshot.csv` | 5865010 | split_and_previewed | 522203 |
| `derek_game_snapshots/21716136/morning/full_pmf_wide.csv` | 286811 | ok |  |
| `derek_game_snapshots/21716136/morning/market_comparison.csv` | 2140947 | split_and_previewed | 523686 |
| `derek_game_snapshots/21716136/morning/outcome_level_probabilities.csv` | 420701 | ok |  |
| `derek_game_snapshots/21716136/morning/prop_summary.csv` | 20854 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 99883 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 286811 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4398626 | split_and_previewed | 523920 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 286811 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 2687275 | split_and_previewed | 523726 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4398626 | split_and_previewed | 523920 |
| `wizard_of_odds/full_pmfs_wide.csv` | 286811 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2140947 | split_and_previewed | 523642 |
| `wizard_of_odds/publishable_edges.csv` | 1780333 | split_and_previewed | 523595 |
