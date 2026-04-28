# Odds API NBA Player Props — Phase 9 capture foundation

This document is the contract for how the project pulls NBA player-prop
odds from [The Odds API](https://the-odds-api.com/) for both **live** and
**historical** snapshots, in the exact shape needed to evaluate model
PMFs against the market.

The implementation lives in:

- `scripts/oddsapi_nba_props.py`     — capture / flatten / pair
- `scripts/validate_oddsapi_props.py` — schema + range validator

## 1. Endpoints used

For NBA player props, the Odds API requires the **event-odds** endpoint
(one game at a time). The general `/odds` endpoint does not return player
props.

### Live

```
GET /v4/sports/basketball_nba/events
GET /v4/sports/basketball_nba/events/{eventId}/odds
    ?regions=us
    &markets=player_points,player_rebounds,...
    &oddsFormat=american
```

### Historical

```
GET /v4/historical/sports/basketball_nba/events?date={snapshot_iso}
GET /v4/historical/sports/basketball_nba/events/{eventId}/odds
    ?date={snapshot_iso}
    &regions=us
    &markets=player_points,player_rebounds,...
    &oddsFormat=american
```

`{snapshot_iso}` is an ISO-8601 UTC timestamp (e.g. `2026-04-27T11:00:00Z`).
The historical endpoint snaps to the closest stored snapshot at or
before that time.

## 2. Why the event-odds endpoint is mandatory

Player props are *additional markets* under the Odds API taxonomy. The
general `/v4/sports/basketball_nba/odds` endpoint enumerates events with
core markets only (h2h / spreads / totals). To retrieve `player_points`,
`player_threes`, etc. — including their alternate-line ladders — the
**only** supported path is per-event:

1. List events (live or historical) → resolve each `event_id`.
2. Call `/events/{event_id}/odds` with the player-prop market keys.

Cost: each event-odds request is billed per `(market × region)`. With 10
target markets and 1 region, that's 10 quota units per event for live,
and ~10× more for historical.

## 3. Markets fetched

| Group | Market keys |
|---|---|
| Main lines | `player_points`, `player_rebounds`, `player_assists`, `player_turnovers`, `player_threes` |
| Alternate ladders | `player_points_alternate`, `player_rebounds_alternate`, `player_assists_alternate`, `player_turnovers_alternate`, `player_threes_alternate` |

Stat mapping into the model's universe:

| Market key | `market_stat` |
|---|---|
| `player_points`, `player_points_alternate` | `pts` |
| `player_rebounds`, `player_rebounds_alternate` | `reb` |
| `player_assists`, `player_assists_alternate` | `ast` |
| `player_turnovers`, `player_turnovers_alternate` | `tov` |
| `player_threes`, `player_threes_alternate` | `fg3m` |

## 4. Live snapshot procedure

Two fixed-time snapshots per game day:

| Tag | Time | Purpose |
|---|---|---|
| `morning_7am` | ≈ 07:00 ET (11:00 UTC) | early-day baseline; before injury report |
| `close_or_lock` | ≈ 5–10 min before each individual tip-off | closing line; CLV reference |

For each snapshot:

```
python3 scripts/oddsapi_nba_props.py live-snapshot \
    --snapshot-type morning_7am \
    --max-events 20
```

The script:

1. `GET /sports/basketball_nba/events` — list today's events.
2. For each event: `GET /sports/basketball_nba/events/{id}/odds` with all 10 target markets.
3. Save raw JSON to `data/odds_api/raw/YYYY-MM-DD/`.
4. Flatten quotes → `data/odds_api/processed/YYYY-MM-DD/odds_quotes_*.parquet`.
5. Pair Over/Under and de-vig → `data/odds_api/processed/YYYY-MM-DD/odds_pairs_*.parquet`.

## 5. Historical snapshot procedure

For historical OOF backfill (Phase 8 OOF date range: 2024-10-23 →
2026-03-31), use the historical endpoint at fixed snapshots per game
day:

```
python3 scripts/oddsapi_nba_props.py historical-snapshot \
    --snapshot-time-utc 2026-04-27T11:00:00Z \
    --snapshot-type historical_7am \
    --commence-after 2026-04-27T00:00:00Z \
    --commence-before 2026-04-28T06:00:00Z
```

Steps mirror the live flow:

1. `GET /historical/sports/basketball_nba/events?date={snap}` — list events at that snapshot.
2. Filter to the target game day window.
3. For each event: `GET /historical/sports/basketball_nba/events/{id}/odds?date={snap}` with all 10 markets.
4. Same flatten / pair / save pipeline.

Recommended historical snapshots per game day (UTC):

| Tag | Time | Notes |
|---|---|---|
| `historical_morning` / `historical_7am` | 11:00 UTC (07:00 ET) | morning baseline |
| `historical_close` | 23:00 UTC (19:00 ET) | post-injury-report close, before tip |
| `historical_lock` | game `commence_time` − 5 min | exact closing line (per-event timestamp) |

## 6. Pairing and de-vig method

For each `(event_id, bookmaker_key, market_key, player_name, line, snapshot_time_utc)`,
join the Over and Under quotes into one paired row.

```
implied_over  = american_to_implied(over_odds_american)
implied_under = american_to_implied(under_odds_american)
no_vig_over   = implied_over  / (implied_over + implied_under)
no_vig_under  = implied_under / (implied_over + implied_under)
```

`american_to_implied(am) = 100 / (am + 100)` if `am > 0`, else `|am| / (|am| + 100)`.

The pair is dropped when either side is missing odds. `pair_key` is a
SHA-1 prefix of the join keys for stable deduplication.

## 7. Full-PMF evaluation through alternate lines

The alternate-line ladder is what enables full-PMF comparison rather
than only "main-line over/under". With ladder coverage:

1. For one (player, stat) at one snapshot, collect every offered
   `(line, no_vig_over_prob)` pair.
2. The de-vigged ladder defines a market-implied CDF at integer
   half-points: `P(stat ≤ line) = 1 − no_vig_over_prob` for that line.
3. Difference adjacent CDF values to recover a **market-implied PMF**
   over the same support as the model PMF.
4. Compare full-PMF metrics: NLL, RPS, KS, calibration bins.

Reference helpers:

- `src/nba_props_model/evaluation/market_baseline.py::devigged_main_line`
- `src/nba_props_model/evaluation/market_baseline.py::market_implied_cdf_from_alt_lines`
- `src/nba_props_model/evaluation/market_baseline.py::market_pmf_from_cdf`

## 8. Joining outputs back to model PMFs

Preferred join keys (in priority order):

1. `event_id` + `player_name` + `market_stat`  *(primary)*
2. `commence_time_utc.date()` + normalized `player_name` + `market_stat`
3. `commence_time_utc.date()` + `home_team`/`away_team` + normalized `player_name` + `market_stat`

Notes:

- Odds API does not return BallDontLie player IDs; matching uses
  normalized full name (lowercase, trimmed, diacritic-folded).
- Cross-reference team names via `data/player_game_stats.parquet`
  (`team_id`, `team_abbr`, `home_team_id`, `visitor_team_id`).
- The shared OOF manifest at
  `artifacts/market_manifest/oof_market_match_manifest.parquet`
  carries (game_id, game_date, player_id, player_name, team_abbr,
  opponent_team_abbr) to make the join lossless on the OOF side.

## 9. Leakage safeguards

- Never use a snapshot whose `snapshot_time_utc > commence_time_utc` for
  pre-tip evaluation. Such rows are post-tip and not eligible for
  closing-line / CLV use.
- Do not feed market data back into model training without a strict
  walk-forward partition (snapshots before fold start only).
- `outcome` is excluded from the request to the data vendor; it lives
  on the model side and is joined later for evaluation.

## 10. Cost / usage considerations

| Call | Quota cost (approx) |
|---|---|
| `GET /events` (live) | 1 |
| `GET /events/{id}/odds` (live, 10 markets, 1 region) | 10 |
| `GET /historical/events` | 10 |
| `GET /historical/events/{id}/odds` (10 markets, 1 region) | 100 |

For one full live game day with 12 games × 2 snapshots: ≈ 240 quota units.
For one full historical backfill day with 12 games × 2 snapshots:
≈ 2,420 quota units. Plan budget per the project's Odds API tier; the
script logs `x-requests-used` / `x-requests-remaining` headers after
each call so over-quota runs fail visibly rather than silently.

## 11. Outputs (canonical layout)

```
data/odds_api/
├── raw/
│   └── YYYY-MM-DD/
│       ├── live_events_*.json
│       ├── live_event_{event_id}_*.json
│       ├── hist_events_*.json
│       └── hist_event_{event_id}_*.json
└── processed/
    └── YYYY-MM-DD/
        ├── odds_quotes_*.parquet  (and .csv)
        └── odds_pairs_*.parquet   (and .csv)
```

Schemas are documented in the docstrings of `scripts/oddsapi_nba_props.py`
and re-validated by `scripts/validate_oddsapi_props.py`.
