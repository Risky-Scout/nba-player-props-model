# Event-market coverage audit — `dates_e77f109a685a`

- Dates: 2026-05-07, 2026-05-12
- Snapshot filter: `*close_or_lock*`
- `min_scored_rows` threshold for `covered`: 100

## Summary

| stat | processed | two_way | eml | matched | scored | final_missing_reason | raw_presence |
|---|---:|---:|---:|---:|---:|---|---|
| pts | 733 | 733 | 733 | 422 | 422 | `covered` | `expected_keys_present_in_raw` |
| reb | 576 | 576 | 576 | 345 | 345 | `covered` | `expected_keys_present_in_raw` |
| ast | 471 | 471 | 471 | 280 | 280 | `covered` | `expected_keys_present_in_raw` |
| fg3m | 491 | 491 | 491 | 282 | 282 | `covered` | `expected_keys_present_in_raw` |
| tov | 5 | 5 | 5 | 1 | 1 | `insufficient_scored_rows` | `expected_keys_present_in_raw` |
| stl | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| blk | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| stocks | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pa | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pr | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| ra | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pra | 0 | 0 | 0 | 0 | 0 | `no_offered_market` | `expected_keys_absent_in_raw` |

## Rules

- **`no_offered_market`** only when requested registry keys are **absent** from raw JSON and at least one raw JSON file was scanned.
- **`not_requested_from_odds_api`** when expected keys are missing from the default registry.
- **`event_market_join_failed`** includes missing raw files (cannot prove offer) or join gaps.

