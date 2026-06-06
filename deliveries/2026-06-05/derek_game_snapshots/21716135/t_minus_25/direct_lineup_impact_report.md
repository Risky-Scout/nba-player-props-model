# Direct lineup impact — 2026-06-05 game 21716135 (t_minus_25)

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- direct_lineup_pmf_driver: **True**
- direct_lineup_features_consumed: **True**
- lineup_confirmed: **False**

This is a best-available pre-tip baseline. BDL did not return confirmed lineup rows at this timestamp, so official lineup status did not directly affect this PMF. The snapshot still reflects the active champion's lagged-proxy starter signal (`starter_proxy_lagged`) and all injury / availability / vacated-opportunity / game-context features.

## Direct lineup metrics

- confirmed_starters: **0**
- confirmed_benches: **35**
- starter_changed_from_projection: **0**
- bench_changed_from_projection: **35**
- minutes_projection_conflicts: **0**
- minutes_delta_abs_mean: **14.4474**
- minutes_delta_abs_max: **14.4474**

## Edge reasonability / publishability

Edges below were re-derived from the PMF (push-excluded win-prob convention), recomputed against no-vig market probabilities, and EV is reported both with and without push handling on integer lines.

### Top edges with publishability status

| player_name | stat | side | line | bet_vendor | model_prob | market_prob | raw_edge | ev | edge_publish_status | root_cause_label | calibration_support_status | edge_reasonability_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.500 | betmgm | 0.733 | 0.451 | +0.284 | +0.554 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=53) |
| Victor Wembanyama | pts | UNDER | 27.500 | betway | 0.760 | 0.509 | +0.255 | +0.464 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SUPPORTED | calculation_bug |
| Stephon Castle | ast | UNDER | 6.500 | betway | 0.729 | 0.493 | +0.237 | +0.430 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=97) |
| Dylan Harper | ast | UNDER | 3.500 | fanduel | 0.801 | 0.588 | +0.215 | +0.336 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SUPPORTED | abs_edge_>=_20pp |
| Victor Wembanyama | ast | UNDER | 3.500 | betmgm | 0.809 | 0.597 | +0.213 | +0.302 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SUPPORTED | abs_edge_>=_20pp |
| Keldon Johnson | fg3m | OVER | 0.500 | betmgm | 0.767 | 0.554 | +0.213 | +0.357 | REVIEW_LARGE_EDGE | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=48) |
| De'Aaron Fox | ast | UNDER | 5.500 | draftkings | 0.649 | 0.462 | +0.187 | +0.363 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Josh Hart | ast | UNDER | 4.500 | betrivers | 0.639 | 0.466 | +0.175 | +0.310 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Josh Hart | reb | UNDER | 8.500 | draftkings | 0.623 | 0.459 | +0.165 | +0.340 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Landry Shamet | fg3m | UNDER | 1.500 | fanduel | 0.659 | 0.514 | +0.145 | +0.259 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SUPPORTED | passes_all_gates |
| Jalen Brunson | fg3m | UNDER | 2.500 | fanduel | 0.740 | 0.596 | +0.144 | +0.203 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Dylan Harper | pts | UNDER | 11.500 | fanduel | 0.596 | 0.454 | +0.144 | +0.276 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Julian Champagnie | pts | UNDER | 10.500 | fanduel | 0.625 | 0.485 | +0.143 | +0.250 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SUPPORTED | calculation_bug |
| Julian Champagnie | reb | UNDER | 5.500 | draftkings | 0.612 | 0.470 | +0.143 | +0.273 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Keldon Johnson | reb | UNDER | 2.500 | betmgm | 0.609 | 0.481 | +0.129 | +0.230 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=88) |
| Mitchell Robinson | blk | UNDER | 0.500 | draftkings | 0.641 | 0.513 | +0.128 | +0.224 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=77) |
| Devin Vassell | pts | UNDER | 12.500 | betway | 0.610 | 0.486 | +0.127 | +0.232 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SUPPORTED | calculation_bug |
| Julian Champagnie | fg3m | UNDER | 2.500 | betmgm | 0.630 | 0.512 | +0.118 | +0.203 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Victor Wembanyama | stl | UNDER | 1.500 | draftkings | 0.761 | 0.646 | +0.115 | +0.161 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=62) |
| Devin Vassell | ast | UNDER | 2.500 | fanduel | 0.678 | 0.569 | +0.111 | +0.163 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |

### Calibration bucket summary (historical corpus)

| stat/side | n | model_logloss | market_logloss | Δll |
| --- | ---: | ---: | ---: | ---: |
| ast/OVER | 1534 | nan | nan | +nan |
| ast/UNDER | 1534 | nan | nan | +nan |
| blk/OVER | 215 | nan | nan | +nan |
| blk/UNDER | 215 | nan | nan | +nan |
| fg3m/OVER | 1538 | nan | nan | +nan |
| fg3m/UNDER | 1538 | nan | nan | +nan |
| pa/OVER | 610 | nan | nan | +nan |
| pa/UNDER | 610 | nan | nan | +nan |
| pr/OVER | 704 | nan | nan | +nan |
| pr/UNDER | 704 | nan | nan | +nan |
| pra/OVER | 722 | nan | nan | +nan |
| pra/UNDER | 722 | nan | nan | +nan |
| pts/OVER | 3094 | nan | nan | +nan |
| pts/UNDER | 3094 | nan | nan | +nan |
| ra/OVER | 391 | nan | nan | +nan |
| ra/UNDER | 391 | nan | nan | +nan |
| reb/OVER | 2251 | nan | nan | +nan |
| reb/UNDER | 2251 | nan | nan | +nan |
| stl/OVER | 251 | nan | nan | +nan |
| stl/UNDER | 251 | nan | nan | +nan |
| stocks/OVER | 115 | nan | nan | +nan |
| stocks/UNDER | 115 | nan | nan | +nan |
| tov/OVER | 1 | nan | nan | +nan |
| tov/UNDER | 1 | nan | nan | +nan |

