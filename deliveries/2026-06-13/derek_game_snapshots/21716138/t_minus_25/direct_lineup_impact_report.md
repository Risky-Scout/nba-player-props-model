# Direct lineup impact — 2026-06-13 game 21716138 (t_minus_25)

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- direct_lineup_pmf_driver: **True**
- direct_lineup_features_consumed: **True**
- lineup_confirmed: **False**

This is a best-available pre-tip baseline. BDL did not return confirmed lineup rows at this timestamp, so official lineup status did not directly affect this PMF. The snapshot still reflects the active champion's lagged-proxy starter signal (`starter_proxy_lagged`) and all injury / availability / vacated-opportunity / game-context features.

## Direct lineup metrics

- confirmed_starters: **0**
- confirmed_benches: **42**
- starter_changed_from_projection: **0**
- bench_changed_from_projection: **42**
- minutes_projection_conflicts: **0**
- minutes_delta_abs_mean: **14.4424**
- minutes_delta_abs_max: **14.4424**

## Edge reasonability / publishability

Edges below were re-derived from the PMF (push-excluded win-prob convention), recomputed against no-vig market probabilities, and EV is reported both with and without push handling on integer lines.

### Top edges with publishability status

| player_name | stat | side | line | bet_vendor | model_prob | market_prob | raw_edge | ev | edge_publish_status | root_cause_label | calibration_support_status | edge_reasonability_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | blk | UNDER | 3.500 | draftkings | 0.836 | 0.524 | +0.312 | +0.563 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SAMPLE_THIN | abs_edge_>=_30pp_unjustified; calibration CALIBRATION_SAMPLE_THIN (n=17) |
| Keldon Johnson | fg3m | OVER | 0.500 | draftkings | 0.789 | 0.488 | +0.301 | +0.578 | PUBLISH_BLOCKER | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_30pp_unjustified; calibration sample limited (n=30) |
| Victor Wembanyama | reb | UNDER | 11.500 | fanduel | 0.769 | 0.497 | +0.273 | +0.501 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=53) |
| Miles McBride | fg3m | OVER | 0.500 | fanduel | 0.790 | 0.517 | +0.273 | +0.459 | REVIEW_LARGE_EDGE | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=48) |
| Victor Wembanyama | pts | UNDER | 28.500 | fanduel | 0.749 | 0.501 | +0.251 | +0.477 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SUPPORTED | calculation_bug |
| Dylan Harper | pts | UNDER | 15.500 | betparx | 0.727 | 0.508 | +0.222 | +0.389 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SUPPORTED | calculation_bug |
| Jose Alvarado | stl | UNDER | 0.500 | betparx | 0.781 | 0.579 | +0.202 | +0.279 | REVIEW_LARGE_EDGE | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=66) |
| Dylan Harper | reb | UNDER | 5.500 | betmgm | 0.638 | 0.456 | +0.184 | +0.327 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Devin Vassell | pts | UNDER | 13.500 | betway | 0.676 | 0.494 | +0.184 | +0.352 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Devin Vassell | fg3m | UNDER | 2.500 | draftkings | 0.679 | 0.508 | +0.171 | +0.326 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| OG Anunoby | stl | UNDER | 1.500 | betway | 0.780 | 0.614 | +0.167 | +0.253 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=86) |
| OG Anunoby | pts | UNDER | 17.500 | betmgm | 0.658 | 0.494 | +0.167 | +0.285 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Karl-Anthony Towns | pts | UNDER | 16.500 | fanduel | 0.675 | 0.512 | +0.165 | +0.288 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Stephon Castle | ast | UNDER | 6.500 | betway | 0.694 | 0.532 | +0.163 | +0.314 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Dylan Harper | ast | UNDER | 3.500 | fanduel | 0.729 | 0.569 | +0.161 | +0.239 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Landry Shamet | fg3m | OVER | 1.500 | fanduel | 0.637 | 0.479 | +0.158 | +0.300 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SUPPORTED | passes_all_gates |
| De'Aaron Fox | reb | OVER | 3.500 | draftkings | 0.612 | 0.459 | +0.153 | +0.298 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Josh Hart | stl | UNDER | 1.500 | betparx | 0.759 | 0.625 | +0.134 | +0.206 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=86) |
| OG Anunoby | fg3m | UNDER | 2.500 | betmgm | 0.661 | 0.527 | +0.134 | +0.245 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Jalen Brunson | reb | OVER | 3.500 | draftkings | 0.555 | 0.423 | +0.132 | +0.299 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |

### Calibration bucket summary (historical corpus)

| stat/side | n | model_logloss | market_logloss | Δll |
| --- | ---: | ---: | ---: | ---: |
| ast/OVER | 1634 | nan | nan | +nan |
| ast/UNDER | 1634 | nan | nan | +nan |
| blk/OVER | 259 | nan | nan | +nan |
| blk/UNDER | 259 | nan | nan | +nan |
| fg3m/OVER | 1643 | nan | nan | +nan |
| fg3m/UNDER | 1643 | nan | nan | +nan |
| pa/OVER | 745 | nan | nan | +nan |
| pa/UNDER | 745 | nan | nan | +nan |
| pr/OVER | 805 | nan | nan | +nan |
| pr/UNDER | 805 | nan | nan | +nan |
| pra/OVER | 821 | nan | nan | +nan |
| pra/UNDER | 821 | nan | nan | +nan |
| pts/OVER | 3315 | nan | nan | +nan |
| pts/UNDER | 3315 | nan | nan | +nan |
| ra/OVER | 436 | nan | nan | +nan |
| ra/UNDER | 436 | nan | nan | +nan |
| reb/OVER | 2365 | nan | nan | +nan |
| reb/UNDER | 2365 | nan | nan | +nan |
| stl/OVER | 300 | nan | nan | +nan |
| stl/UNDER | 300 | nan | nan | +nan |
| stocks/OVER | 139 | nan | nan | +nan |
| stocks/UNDER | 139 | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan |

