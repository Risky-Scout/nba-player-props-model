# Event-market coverage audit — `dates_24c1750e26ad`

- Dates: 2026-04-27, 2026-04-28, 2026-04-29, 2026-04-30, 2026-05-01, 2026-05-02, 2026-05-03, 2026-05-04, 2026-05-05, 2026-05-06, 2026-05-07, 2026-05-08, 2026-05-09, 2026-05-10, 2026-05-11, 2026-05-12
- Snapshot filter: `*auto*`
- `min_scored_rows` threshold for `covered`: 100

## Summary

| stat | processed | two_way | eml | matched | scored | final_missing_reason | raw_presence |
|---|---:|---:|---:|---:|---:|---|---|
| pts | 30412 | 30412 | 30412 | 14189 | 14180 | `covered` | `expected_keys_present_in_raw` |
| reb | 18081 | 18081 | 18081 | 8397 | 8397 | `covered` | `expected_keys_present_in_raw` |
| ast | 12139 | 12139 | 12139 | 5745 | 5745 | `covered` | `expected_keys_present_in_raw` |
| fg3m | 12686 | 12686 | 12686 | 5933 | 5928 | `covered` | `expected_keys_present_in_raw` |
| tov | 94 | 94 | 94 | 40 | 40 | `insufficient_scored_rows` | `expected_keys_present_in_raw` |
| stl | 4045 | 4045 | 4045 | 1923 | 1923 | `no_offered_market` | `expected_keys_absent_in_raw` |
| blk | 3945 | 3945 | 3945 | 1831 | 1831 | `no_offered_market` | `expected_keys_absent_in_raw` |
| stocks | 1910 | 1910 | 1910 | 914 | 914 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pa | 13604 | 13604 | 13604 | 6417 | 6417 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pr | 18452 | 18452 | 18452 | 8648 | 8648 | `no_offered_market` | `expected_keys_absent_in_raw` |
| ra | 10228 | 10228 | 10228 | 4793 | 4793 | `no_offered_market` | `expected_keys_absent_in_raw` |
| pra | 21546 | 21546 | 21546 | 10234 | 10233 | `no_offered_market` | `expected_keys_absent_in_raw` |

## Rules

- **`no_offered_market`** only when requested registry keys are **absent** from raw JSON and at least one raw JSON file was scanned.
- **`not_requested_from_odds_api`** when expected keys are missing from the default registry.
- **`event_market_join_failed`** includes missing raw files (cannot prove offer) or join gaps.

