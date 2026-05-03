# Derek live snapshot — 2026-05-03 game 21682000 (current_live)

## Executive summary

- snapshot_type: **current_live  (best-available pre-tip baseline)**
- snapshot_mode: **production_live_current**
- game_start_time_utc: `2026-05-03T23:40:00Z`
- game_start_time_source: `predictions_parquet_game_start_time`
- props_emitted: **36**
- market_rows: **36**
- active_players_projected: **14**

This is a best-available pre-tip baseline. BDL did not return confirmed lineup rows at this timestamp, so official lineup status did not directly affect this PMF. The snapshot still reflects the active champion's lagged-proxy starter signal (`starter_proxy_lagged`) and all injury / availability / vacated-opportunity / game-context features.

## BDL fetch status

- BDL_lineup_fetch_attempted: **True**
- BDL_lineup_fetch_status: `no_rows_returned`
- BDL_lineup_rows: **0**
- BDL_lineup_endpoint: `balldontlie_v1_lineups`
- BDL_lineup_fetched_at_utc: `2026-05-03T18:14:16Z`
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
| James Harden | 15.378 | 15.378 |
| Donovan Mitchell | 15.378 | 15.378 |
| Sam Merrill | 15.378 | 15.378 |
| Brandon Ingram | 15.378 | 15.378 |
| Ja'Kobe Walter | 15.378 | 15.378 |
| Jarrett Allen | 15.378 | 15.378 |
| Evan Mobley | 15.378 | 15.378 |
| RJ Barrett | 15.378 | 15.378 |
| Collin Murray-Boyles | 15.378 | 15.378 |
| Jakob Poeltl | 15.378 | 15.378 |
| Scottie Barnes | 15.378 | 15.378 |
| Dennis Schroder | 15.378 | 15.378 |
| Jamal Shead | 15.378 | 15.378 |
| Sandro Mamukelashvili | 15.378 | 15.378 |

## Top 20 stat-rate deltas (any stat)

| player_name | stat | rate_delta |
| --- | --- | ---: |
| James Harden | pts | +0.0331 |
| RJ Barrett | pts | +0.0331 |
| RJ Barrett | pts | +0.0331 |
| Collin Murray-Boyles | pts | +0.0331 |
| Collin Murray-Boyles | pts | +0.0331 |
| Jakob Poeltl | pts | +0.0331 |
| Scottie Barnes | pts | +0.0331 |
| Scottie Barnes | pts | +0.0331 |
| Scottie Barnes | pts | +0.0331 |
| Scottie Barnes | pts | +0.0331 |
| Dennis Schroder | pts | +0.0331 |
| Jamal Shead | pts | +0.0331 |
| Jamal Shead | pts | +0.0331 |
| Jamal Shead | pts | +0.0331 |
| Jamal Shead | pts | +0.0331 |
| Sandro Mamukelashvili | pts | +0.0331 |
| James Harden | pts | +0.0331 |
| RJ Barrett | pts | +0.0331 |
| Scottie Barnes | pts | +0.0331 |
| RJ Barrett | pts | +0.0331 |

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
| prop_summary.parquet | 36 | `30e53c10184e77f3` |
| full_pmf_wide.parquet | 36 | `be0cd7064081a1d1` |
| outcome_level_probabilities.parquet | 36 | `a0725ddea472ff90` |
| market_comparison.parquet | 36 | `6181299bafd7adc9` |
| lineup_context.parquet | 14 | `309684be346dbb08` |
| injury_availability_context.parquet | 14 | `7ed829ff6ceedeac` |
| prediction_input_audit.parquet | 36 | `30e53c10184e77f3` |
| direct_lineup_impact_report.json | 1 | `07b92a094f379a10` |
| game_context.parquet | 14 | `84ba364948262ee2` |
| pmf_driver_decomposition.parquet | 36 | `c8da310d3048bc73` |
| lineup_injury_impact_report.json | 1 | `f23ae18c69b7e9bb` |
| contextual_feature_audit.parquet | 14 | `f4adadd72437a2ab` |
