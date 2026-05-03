# Direct lineup impact — 2026-05-03 game 21684819 (current_live)

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- direct_lineup_pmf_driver: **True**
- direct_lineup_features_consumed: **True**
- lineup_confirmed: **False**

This is a best-available pre-tip baseline. BDL did not return confirmed lineup rows at this timestamp, so official lineup status did not directly affect this PMF. The snapshot still reflects the active champion's lagged-proxy starter signal (`starter_proxy_lagged`) and all injury / availability / vacated-opportunity / game-context features.

## Direct lineup metrics

- confirmed_starters: **0**
- confirmed_benches: **0**
- starter_changed_from_projection: **0**
- bench_changed_from_projection: **0**
- minutes_projection_conflicts: **0**
- minutes_delta_abs_mean: **15.3781**
- minutes_delta_abs_max: **15.3781**

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

