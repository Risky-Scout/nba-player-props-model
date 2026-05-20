# Delivery CSV size contract — 2026-05-20

- max_bytes: `524288`
- pass: `True`

| path | before bytes | action | after bytes |
|---|---:|---|---:|
| `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.csv` | 345242 | ok |  |
| `derek_forward_feed/derek_forward_feed.csv` | 1499795 | split_and_previewed | 524180 |
| `derek_forward_feed/derek_unique_props_summary.csv` | 5778 | ok |  |
| `derek_forward_feed/latest_available_snapshot.csv` | 8259230 | split_and_previewed | 524057 |
| `derek_forward_feed/morning_snapshot.csv` | 8259230 | split_and_previewed | 524057 |
| `derek_game_snapshots/21713529/morning/full_pmf_wide.csv` | 430446 | ok |  |
| `derek_game_snapshots/21713529/morning/market_comparison.csv` | 2910260 | split_and_previewed | 523942 |
| `derek_game_snapshots/21713529/morning/outcome_level_probabilities.csv` | 757478 | split_and_previewed | 524250 |
| `derek_game_snapshots/21713529/morning/prop_summary.csv` | 25912 | ok |  |
| `pmf_model_review_package/04_PROP_SUMMARY.csv` | 109938 | ok |  |
| `pmf_model_review_package/05_FULL_PMF_WIDE.csv` | 398443 | ok |  |
| `pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv` | 4799439 | split_and_previewed | 524042 |
| `pmf_model_review_package/machine_readable/model_only.csv` | 398443 | ok |  |
| `wizard_of_odds/fair_odds_board.csv` | 3298559 | split_and_previewed | 524001 |
| `wizard_of_odds/full_pmfs_outcome_level.csv` | 4799439 | split_and_previewed | 524042 |
| `wizard_of_odds/full_pmfs_wide.csv` | 398443 | ok |  |
| `wizard_of_odds/market_comparison.csv` | 2509459 | split_and_previewed | 523399 |
| `wizard_of_odds/publishable_edges.csv` | 2043685 | split_and_previewed | 523686 |
