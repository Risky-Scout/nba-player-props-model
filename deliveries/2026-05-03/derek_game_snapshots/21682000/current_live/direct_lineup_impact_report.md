# Direct lineup impact — 2026-05-03 game 21682000 (current_live)

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

