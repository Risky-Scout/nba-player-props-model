# Event-market coverage audit — `2026-05-12`

- Dates: 2026-05-12
- Snapshot filter: `*close_or_lock*`
- `min_scored_rows` threshold for `covered`: 100

## Summary

| stat | processed_rows | two_way | eml_rows | matched | scored | missing_reason |
|---|---:|---:|---:|---:|---:|---|
| pts | 248 | 248 | 248 | 142 | 142 | `covered` |
| reb | 187 | 187 | 187 | 118 | 118 | `covered` |
| ast | 180 | 180 | 180 | 109 | 109 | `covered` |
| fg3m | 159 | 159 | 159 | 97 | 97 | `insufficient_scored_rows` |
| tov | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| stl | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| blk | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| stocks | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| pa | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| pr | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| ra | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |
| pra | 0 | 0 | 0 | 0 | 0 | `no_offered_market` |

## Interpretation

- **no_offered_market**: Odds API responses for this slate did not include any registered market key for the stat (books did not offer / API omitted).
- **processed_parser_dropped_market**: Raw JSON contained the market key but processed `odds_pairs` did not — investigate `oddsapi_nba_props.py` pairing/filtering.
- **not_requested_from_odds_api**: A registered market key for this stat is missing from `ODDSAPI_NBA_DEFAULT_MARKETS` (fetch/registry bug).
- **insufficient_scored_rows**: End-to-end rows exist but scored count is below the audit threshold (100); use multi-date aggregation for superiority.

