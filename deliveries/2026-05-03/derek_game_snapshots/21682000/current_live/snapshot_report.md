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
- BDL_lineup_fetched_at_utc: `2026-05-03T20:54:09Z`
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
| James Harden | pts | +0.0331 |
| James Harden | pts | +0.0331 |
| James Harden | pts | +0.0331 |
| Donovan Mitchell | pts | +0.0331 |
| Donovan Mitchell | pts | +0.0331 |
| Donovan Mitchell | pts | +0.0331 |
| Donovan Mitchell | pts | +0.0331 |
| Sam Merrill | pts | +0.0331 |
| Brandon Ingram | pts | +0.0331 |
| Ja'Kobe Walter | pts | +0.0331 |
| Ja'Kobe Walter | pts | +0.0331 |
| Ja'Kobe Walter | pts | +0.0331 |
| Jarrett Allen | pts | +0.0331 |
| Jarrett Allen | pts | +0.0331 |
| Evan Mobley | pts | +0.0331 |
| Evan Mobley | pts | +0.0331 |
| Evan Mobley | pts | +0.0331 |
| RJ Barrett | pts | +0.0331 |
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
| prop_summary.parquet | 36 | `f0b547c75bb698b0` |
| full_pmf_wide.parquet | 36 | `0cfe3f67e070543b` |
| outcome_level_probabilities.parquet | 36 | `328ee7f0e7c3d738` |
| market_comparison.parquet | 36 | `3b06a6f3cd8cfc94` |
| lineup_context.parquet | 14 | `68e4c3809924ed02` |
| injury_availability_context.parquet | 14 | `4c93951bcceb0d23` |
| prediction_input_audit.parquet | 36 | `f0b547c75bb698b0` |
| direct_lineup_impact_report.json | 1 | `07b92a094f379a10` |
| game_context.parquet | 14 | `69985a512b327691` |
| pmf_driver_decomposition.parquet | 36 | `e71a00e9a26a76d0` |
| lineup_injury_impact_report.json | 1 | `f23ae18c69b7e9bb` |
| contextual_feature_audit.parquet | 14 | `9687d78ecd426743` |
## Edge reasonability / publishability

Current-live edges are **model-vs-market disagreements** from the best-available baseline. BDL did not return confirmed lineup rows at this timestamp, so these rows are **watchlist / review signals**, not confirmed-lineup recommendations. Large edges are flagged for review. Push / integer lines are audited separately. Calibration support is checked by stat / side / edge bucket where settled samples exist. **T-minus-25 and close-lock are the more important near-tip confirmed-lineup snapshots.**

### Top edges with publishability status

| player_name | stat | side | line | bet_vendor | model_prob | market_prob | raw_edge | ev | edge_publish_status | root_cause_label | calibration_support_status | edge_reasonability_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evan Mobley | blk | UNDER | 1.500 | draftkings | 0.789 | 0.473 | +0.316 | +0.617 | PUBLISH_BLOCKER | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | abs_edge_>=_30pp_unjustified; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Donovan Mitchell | fg3m | UNDER | 2.500 | betway | 0.735 | 0.479 | +0.257 | +0.529 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup_with_large_edge; calibration sample limited (n=69) |
| Scottie Barnes | ast | UNDER | 7.500 | betrivers | 0.668 | 0.440 | +0.228 | +0.482 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup_with_large_edge; calibration sample limited (n=62) |
| Collin Murray-Boyles | pts | UNDER | 12.500 | betmgm | 0.693 | 0.469 | +0.225 | +0.442 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup_with_large_edge |
| Scottie Barnes | fg3m | UNDER | 1.000 | fanduel | 0.746 | 0.526 | +0.220 | +0.978 | REVIEW_PUSH_LINE | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup_with_large_edge; push_prob=0.326; push-aware EV may differ from displayed EV; calibration CALIBRATION_SAMPLE_THIN (n=7) |
| Jamal Shead | ast | UNDER | 5.500 | fanduel | 0.668 | 0.467 | +0.201 | +0.430 | REVIEW_LARGE_EDGE | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup_with_large_edge; calibration sample limited (n=67) |
| RJ Barrett | pts | UNDER | 23.500 | fanduel | 0.708 | 0.508 | +0.200 | +0.334 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| James Harden | blk | UNDER | 0.500 | betway | 0.755 | 0.561 | +0.194 | +0.269 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Sandro Mamukelashvili | reb | OVER | 3.500 | draftkings | 0.627 | 0.435 | +0.192 | +0.373 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Jamal Shead | pts | UNDER | 8.500 | fanduel | 0.676 | 0.488 | +0.189 | +0.333 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=28) |
| Ja'Kobe Walter | reb | UNDER | 3.500 | caesars | 0.654 | 0.472 | +0.182 | +0.340 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| Scottie Barnes | reb | UNDER | 6.500 | betway | 0.624 | 0.446 | +0.178 | +0.310 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_REVIEW_REQUIRED | current_live_unconfirmed_lineup; calibration CALIBRATION_REVIEW_REQUIRED (n=147) |
| Donovan Mitchell | stl | UNDER | 1.500 | draftkings | 0.789 | 0.612 | +0.178 | +0.283 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| James Harden | stl | UNDER | 1.500 | draftkings | 0.790 | 0.615 | +0.175 | +0.284 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| James Harden | fg3m | UNDER | 2.500 | betparx | 0.624 | 0.451 | +0.173 | +0.342 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup; calibration sample limited (n=78) |
| Donovan Mitchell | pts | UNDER | 25.500 | betparx | 0.676 | 0.505 | +0.171 | +0.264 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SUPPORTED | current_live_unconfirmed_lineup |
| RJ Barrett | ast | UNDER | 3.500 | betmgm | 0.655 | 0.486 | +0.170 | +0.297 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_LIMITED | current_live_unconfirmed_lineup; calibration sample limited (n=82) |
| Sam Merrill | stl | UNDER | 0.500 | betparx | 0.701 | 0.556 | +0.145 | +0.175 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Scottie Barnes | blk | UNDER | 1.500 | betparx | 0.733 | 0.589 | +0.144 | +0.177 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=0) |
| Dennis Schroder | fg3m | OVER | 0.500 | betway | 0.624 | 0.485 | +0.138 | +0.191 | WATCHLIST_NOT_CONFIRMED_LINEUP | unconfirmed_lineup_baseline | CALIBRATION_SAMPLE_THIN | current_live_unconfirmed_lineup; calibration CALIBRATION_SAMPLE_THIN (n=11) |

### Push-line audit rows

| player | stat | side | line | push_prob | ev | ev_recomputed | ev_recomputed_pushinc | edge_publish_status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Scottie Barnes | fg3m | UNDER | 1.0 | 0.326 | +0.978 | +0.978 | +0.659 | REVIEW_PUSH_LINE |

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

