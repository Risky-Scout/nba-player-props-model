# Delivery CSV size contract — 2026-05-30

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 362274 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1548190 | split_and_previewed | 523953 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 6995 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 6856032 | split_and_previewed | 523590 |
| `derek_forward_feed/morning_snapshot.csv` | 6856032 | split_and_previewed | 523590 |
| `derek_game_snapshots/21713534/morning/full_pmf_wide.csv` | 383159 | ok |  |
| `derek_game_snapshots/21713534/morning/market_comparison.csv` | 2554618 | split_and_previewed | 524177 |
| `derek_game_snapshots/21713534/morning/outcome_level_probabilities.csv` | 579322 | split_and_previewed | 524281 |
| `derek_game_snapshots/21713534/morning/prop_summary.csv` | 27866 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 133616 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 383159 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 5939549 | split_and_previewed | 523801 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 383159 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3594505 | split_and_previewed | 524051 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 5939549 | split_and_previewed | 523801 |
| `wizard_of_odds/full_pmfs_wide.csv` | 383159 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2554618 | split_and_previewed | 524177 |
| `wizard_of_odds/publishable_edges.csv` | 2265730 | split_and_previewed | 523751 |
