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
- BDL_lineup_fetched_at_utc: `2026-05-03T19:28:50Z`
- BDL_injury_fetch_attempted: **True**
- BDL_injury_fetch_status: `deferred_to_predict_pipeline`
- BDL_injury_rows: **0**
- BDL_injury_endpoint: `data/nba_injury_reports.parquet (downstream of predict.py)`
- lineup_blocker: `no rows returned by BDL lineups endpoint (lineups not posted yet)`
- injury_blocker: `no rows returned by BDL lineups endpoint (lineups not posted yet)`

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
| Daniss Jenkins | pts | +0.0331 |
| Daniss Jenkins | pts | +0.0331 |
| Ausar Thompson | pts | +0.0331 |
| Anthony Black | pts | +0.0331 |
| Anthony Black | pts | +0.0331 |
| Isaiah Stewart | pts | +0.0331 |
| Jamal Cain | pts | +0.0331 |
| Tobias Harris | pts | +0.0331 |
| Tobias Harris | pts | +0.0331 |
| Tobias Harris | pts | +0.0331 |
| Tobias Harris | pts | +0.0331 |
| Jalen Suggs | pts | +0.0331 |
| Jalen Suggs | pts | +0.0331 |
| Jalen Suggs | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |
| Cade Cunningham | pts | +0.0331 |

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
| prop_summary.parquet | 33 | `0aa0fc1947f59f7b` |
| full_pmf_wide.parquet | 33 | `ca0892f1ea46f93c` |
| outcome_level_probabilities.parquet | 33 | `d9002f7c2f93cfce` |
| market_comparison.parquet | 33 | `f23f89039160ecbf` |
| lineup_context.parquet | 14 | `c40ca398f48a41a2` |
| injury_availability_context.parquet | 14 | `f703cdf64a4f65ba` |
| prediction_input_audit.parquet | 33 | `0aa0fc1947f59f7b` |
| direct_lineup_impact_report.json | 1 | `1641f1cdcba64f05` |
| game_context.parquet | 14 | `57d2af0e891852ca` |
| pmf_driver_decomposition.parquet | 33 | `49e98a311e447118` |
| lineup_injury_impact_report.json | 1 | `394015348926e904` |
| contextual_feature_audit.parquet | 14 | `6b05e5a6859d70e7` |

## Edge reasonability / publishability

Current-live edges are **model-vs-market disagreements** from the best-available baseline. BDL did not return confirmed lineup rows at this timestamp, so these rows are **watchlist / review signals**, not confirmed-lineup recommendations. Large edges are flagged for review. Push / integer lines are audited separately. Calibration support is checked by stat / side / edge bucket where settled samples exist. **T-minus-25 and close-lock are the more important near-tip confirmed-lineup snapshots.**

### Top edges with publishability status

| player_name | stat | side | line | bet_vendor | model_prob | market_prob | raw_edge | ev | edge_publish_status | root_cause_label | calibration_support_status | edge_reasonability_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jamal Cain | reb | UNDER | 3.500 | betmgm | 0.754 | 0.557 | +0.197 | +0.348 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Jalen Suggs | blk | UNDER | 0.500 | draftkings | 0.621 | 0.426 | +0.194 | +0.384 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Isaiah Stewart | reb | OVER | 3.500 | fanduel | 0.617 | 0.423 | +0.194 | +0.443 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Desmond Bane | fg3m | UNDER | 2.500 | betmgm | 0.699 | 0.506 | +0.193 | +0.398 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup; calibration sample limited (n=78) |
| Tobias Harris | pts | UNDER | 17.500 | betmgm | 0.673 | 0.483 | +0.190 | +0.346 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Cade Cunningham | pts | UNDER | 28.500 | betmgm | 0.675 | 0.490 | +0.185 | +0.336 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Ausar Thompson | blk | OVER | 1.500 | draftkings | 0.625 | 0.442 | +0.182 | +0.393 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Tobias Harris | blk | OVER | 0.500 | draftkings | 0.647 | 0.468 | +0.180 | +0.347 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Anthony Black | pts | UNDER | 11.500 | fanatics | 0.690 | 0.517 | +0.173 | +0.289 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Daniss Jenkins | ast | UNDER | 2.500 | fanduel | 0.733 | 0.585 | +0.148 | +0.238 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup; calibration sample limited (n=33) |
| Tobias Harris | stl | UNDER | 1.500 | betparx | 0.786 | 0.641 | +0.145 | +0.189 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Duncan Robinson | fg3m | UNDER | 2.500 | betparx | 0.686 | 0.544 | +0.142 | +0.198 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup; calibration sample limited (n=78) |
| Jalen Suggs | ast | UNDER | 4.500 | betrivers | 0.575 | 0.441 | +0.134 | +0.254 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup; calibration sample limited (n=82) |
| Cade Cunningham | reb | OVER | 5.500 | betmgm | 0.666 | 0.536 | +0.130 | +0.198 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Jalen Duren | stl | UNDER | 0.500 | draftkings | 0.629 | 0.503 | +0.126 | +0.176 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Anthony Black | blk | UNDER | 0.500 | betparx | 0.635 | 0.512 | +0.123 | +0.187 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Cade Cunningham | ast | UNDER | 8.500 | betmgm | 0.621 | 0.499 | +0.122 | +0.185 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Daniss Jenkins | fg3m | OVER | 0.500 | betway | 0.612 | 0.495 | +0.117 | +0.143 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=11) |
| Daniss Jenkins | stl | UNDER | 0.500 | betparx | 0.647 | 0.544 | +0.104 | +0.113 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Tristan Da Silva | reb | UNDER | 2.500 | betway | 0.584 | 0.483 | +0.101 | +0.169 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=23) |

### Calibration bucket summary (historical corpus)

| stat/side | n | model_logloss | market_logloss | Δll |
| --- | ---: | ---: | ---: | ---: |
| ast/OVER | 496 | 0.647 | 0.669 | -0.021 |
| ast/UNDER | 496 | 0.647 | 0.669 | -0.021 |
| fg3m/OVER | 484 | 0.616 | 0.641 | -0.025 |
| fg3m/UNDER | 484 | 0.616 | 0.641 | -0.025 |
| pts/OVER | 1012 | 0.687 | 0.657 | +0.030 |
| pts/UNDER | 1012 | 0.687 | 0.657 | +0.030 |
| reb/OVER | 881 | 0.720 | 0.665 | +0.055 |
| reb/UNDER | 881 | 0.720 | 0.665 | +0.055 |

