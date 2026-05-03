# Derek live snapshot — 2026-05-03 game 21684819 (current_live)

## Executive summary

- snapshot_type: **current_live  (best-available pre-tip baseline)**
- snapshot_mode: **production_live_current**
- game_start_time_utc: `2026-05-03T19:40:00Z`
- game_start_time_source: `predictions_parquet_game_start_time`
- props_emitted: **33**
- market_rows: **33**
- active_players_projected: **14**

This is a best-available pre-tip baseline. BDL did not return confirmed lineup rows at this timestamp, so official lineup status did not directly affect this PMF. The snapshot still reflects the active champion's lagged-proxy starter signal (`starter_proxy_lagged`) and all injury / availability / vacated-opportunity / game-context features.

## BDL fetch status

- BDL_lineup_fetch_attempted: **True**
- BDL_lineup_fetch_status: `no_rows_returned`
- BDL_lineup_rows: **0**
- BDL_lineup_endpoint: `balldontlie_v1_lineups`
- BDL_lineup_fetched_at_utc: `2026-05-03T18:14:14Z`
- BDL_injury_fetch_attempted: **True**
- BDL_injury_fetch_status: `deferred_to_predict_pipeline`
- BDL_injury_rows: **0**
- BDL_injury_endpoint: `data/nba_injury_reports.parquet (downstream of predict.py)`
- lineup_blocker: `BDL_API_KEY not set in runner environment`
- injury_blocker: `BDL_API_KEY not set in runner environment`

## Champion model

- champion_model_id: `challenger-2026-04-30`
- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- direct_lineup_pmf_driver: **True**
- contextual_pmf_engine: **True**
- contextual_pmf_applied: **True**
- pmfs_recomputed: **True**
- pmf_source: `live_snapshot_recomputed_canonical_current`
- trained_through_date: `2026-04-30`
- calibrated_through_date: `2026-04-30`

## Market odds invariant

Market odds were used **for edge only**, never as model features.
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`

## Top 20 contextual minutes deltas

| player_name | exp_mp_contextual | contextual_minutes_delta |
| --- | --- | --- |
| Daniss Jenkins | 15.378 | 15.378 |
| Ausar Thompson | 15.378 | 15.378 |
| Anthony Black | 15.378 | 15.378 |
| Isaiah Stewart | 15.378 | 15.378 |
| Jamal Cain | 15.378 | 15.378 |
| Tobias Harris | 15.378 | 15.378 |
| Jalen Suggs | 15.378 | 15.378 |
| Cade Cunningham | 15.378 | 15.378 |
| Duncan Robinson | 15.378 | 15.378 |
| Paolo Banchero | 15.378 | 15.378 |
| Wendell Carter Jr. | 15.378 | 15.378 |
| Desmond Bane | 15.378 | 15.378 |
| Tristan Da Silva | 15.378 | 15.378 |
| Jalen Duren | 15.378 | 15.378 |

## Top 20 stat-rate deltas (any stat)

| player_name | stat | rate_delta |
| --- | --- | ---: |
| Daniss Jenkins | pts | +0.0331 |
| Wendell Carter Jr. | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Duncan Robinson | pts | +0.0331 |
| Duncan Robinson | pts | +0.0331 |
| Paolo Banchero | pts | +0.0331 |
| Paolo Banchero | pts | +0.0331 |
| Paolo Banchero | pts | +0.0331 |
| Desmond Bane | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Desmond Bane | pts | +0.0331 |
| Desmond Bane | pts | +0.0331 |
| Tristan Da Silva | pts | +0.0331 |
| Jalen Duren | pts | +0.0331 |
| Jalen Duren | pts | +0.0331 |
| Daniss Jenkins | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Paolo Banchero | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Tobias Harris | pts | +0.0331 |

## What Derek should inspect first

1. `snapshot_manifest.json` — full provenance + truth fields.
2. `prop_summary.csv` — slim per-prop view.
3. `direct_lineup_impact_report.md` — Phase 13S driver attribution.
4. `lineup_injury_impact_report.md` — lineup + injury impact summary.
5. `pmf_driver_decomposition.md` — per-row contextual deltas.
6. `market_comparison.csv` — model probs vs market probs (edge only).

## Files in this snapshot

| File | rows | sha256 |
| --- | ---: | --- |
| prop_summary.parquet | 33 | `7eccf72a0c200c25` |
| full_pmf_wide.parquet | 33 | `ec3ba1c9bcfba624` |
| outcome_level_probabilities.parquet | 33 | `f1e9defa598f1d0c` |
| market_comparison.parquet | 33 | `fc636ef87feac491` |
| lineup_context.parquet | 14 | `fca957c3620ea87f` |
| injury_availability_context.parquet | 14 | `0e6c746d82e02043` |
| prediction_input_audit.parquet | 33 | `7eccf72a0c200c25` |
| direct_lineup_impact_report.json | 1 | `1641f1cdcba64f05` |
| game_context.parquet | 14 | `cef478ea358e1e88` |
| pmf_driver_decomposition.parquet | 33 | `34f40c4de5767254` |
| lineup_injury_impact_report.json | 1 | `394015348926e904` |
| contextual_feature_audit.parquet | 14 | `ff215e9da25d99c2` |
