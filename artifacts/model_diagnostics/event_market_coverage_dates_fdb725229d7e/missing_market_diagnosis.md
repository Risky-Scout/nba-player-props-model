# Event-market coverage audit — `dates_fdb725229d7e`

- Dates: 2026-05-06
- Snapshot filter: `*auto*`
- `min_scored_rows` threshold for `covered`: 100

## Summary

| stat | processed | two_way | eml | matched | scored | final_missing_reason | raw_presence |
|---|---:|---:|---:|---:|---:|---|---|
| pts | 1063 | 1063 | 1063 | 669 | 669 | `no_offered_market` | `expected_keys_absent_in_raw` |
| reb | 526 | 526 | 526 | 333 | 333 | `no_offered_market` | `expected_keys_absent_in_raw` |
| ast | 352 | 352 | 352 | 226 | 226 | `no_offered_market` | `expected_keys_absent_in_raw` |
| fg3m | 336 | 336 | 336 | 225 | 225 | `no_offered_market` | `expected_keys_absent_in_raw` |
| tov | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| stl | 81 | 81 | 81 | 51 | 51 | `no_offered_market` | `expected_keys_absent_in_raw` |
| blk | 107 | 107 | 107 | 67 | 67 | `no_offered_market` | `expected_keys_absent_in_raw` |
| stocks | 9 | 9 | 9 | 9 | 9 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pa | 499 | 499 | 499 | 330 | 330 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pr | 708 | 708 | 708 | 463 | 463 | `no_offered_market` | `expected_keys_absent_in_raw` |
| ra | 344 | 344 | 344 | 229 | 229 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pra | 859 | 859 | 859 | 525 | 525 | `no_offered_market` | `expected_keys_absent_in_raw` |

## Rules

- **`no_offered_market`** only when requested registry keys are **absent** from raw JSON and at least one raw JSON file was scanned.
- **`not_requested_from_odds_api`** when expected keys are missing from the default registry.
- **`event_market_join_failed`** includes missing raw files (cannot prove offer) or join gaps.

