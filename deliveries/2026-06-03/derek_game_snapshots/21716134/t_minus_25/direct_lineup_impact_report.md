# Direct lineup impact — 2026-06-03 game 21716134 (t_minus_25)

- feature_set_id: `phase13s_direct_lineup_injury_pmf_driver_v1`
- direct_lineup_pmf_driver: **True**
- direct_lineup_features_consumed: **True**
- lineup_confirmed: **False**

This is a best-available pre-tip baseline. BDL did not return confirmed lineup rows at this timestamp, so official lineup status did not directly affect this PMF. The snapshot still reflects the active champion's lagged-proxy starter signal (`starter_proxy_lagged`) and all injury / availability / vacated-opportunity / game-context features.

## Direct lineup metrics

- confirmed_starters: **0**
- confirmed_benches: **31**
- starter_changed_from_projection: **0**
- bench_changed_from_projection: **31**
- minutes_projection_conflicts: **0**
- minutes_delta_abs_mean: **14.4470**
- minutes_delta_abs_max: **14.4470**

## Edge reasonability / publishability

Edges below were re-derived from the PMF (push-excluded win-prob convention), recomputed against no-vig market probabilities, and EV is reported both with and without push handling on integer lines.

### Top edges with publishability status

| player_name | stat | side | line | bet_vendor | model_prob | market_prob | raw_edge | ev | edge_publish_status | root_cause_label | calibration_support_status | edge_reasonability_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Victor Wembanyama | reb | UNDER | 11.500 | fanduel | 0.778 | 0.477 | +0.302 | +0.595 | PUBLISH_BLOCKER | line_vs_median_gap | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_30pp_unjustified; calibration sample limited (n=53) |
| Karl-Anthony Towns | blk | UNDER | 0.500 | draftkings | 0.686 | 0.409 | +0.277 | +0.680 | REVIEW_LARGE_EDGE | low_line_discrete_stat | CALIBRATION_SAMPLE_THIN | abs_edge_>=_20pp; calibration CALIBRATION_SAMPLE_THIN (n=24) |
| Victor Wembanyama | pts | UNDER | 26.500 | fanatics | 0.736 | 0.486 | +0.252 | +0.457 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SUPPORTED | abs_edge_>=_20pp |
| Stephon Castle | ast | UNDER | 6.500 | draftkings | 0.673 | 0.453 | +0.221 | +0.448 | REVIEW_LARGE_EDGE | line_vs_median_gap | CALIBRATION_SAMPLE_LIMITED | abs_edge_>=_20pp; calibration sample limited (n=97) |
| Mitchell Robinson | blk | UNDER | 0.500 | draftkings | 0.682 | 0.464 | +0.219 | +0.379 | REVIEW_LARGE_EDGE | low_line_discrete_stat | CALIBRATION_SAMPLE_THIN | abs_edge_>=_20pp; calibration CALIBRATION_SAMPLE_THIN (n=24) |
| Luke Kornet | reb | UNDER | 2.500 | draftkings | 0.663 | 0.468 | +0.197 | +0.379 | REVIEW_LARGE_EDGE | market_prob_disagreement | CALIBRATION_SAMPLE_THIN | passes_all_gates; calibration CALIBRATION_SAMPLE_THIN (n=12) |
| Victor Wembanyama | stl | UNDER | 1.500 | draftkings | 0.817 | 0.628 | +0.188 | +0.247 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=62) |
| Julian Champagnie | reb | UNDER | 5.500 | fanduel | 0.697 | 0.512 | +0.186 | +0.330 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Keldon Johnson | reb | UNDER | 3.500 | betparx | 0.758 | 0.580 | +0.179 | +0.291 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Josh Hart | reb | UNDER | 7.500 | fanduel | 0.582 | 0.427 | +0.156 | +0.338 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Karl-Anthony Towns | pts | UNDER | 16.500 | fanduel | 0.653 | 0.505 | +0.150 | +0.268 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Stephon Castle | reb | UNDER | 4.500 | fanduel | 0.600 | 0.452 | +0.149 | +0.295 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Devin Vassell | reb | UNDER | 4.500 | fanduel | 0.707 | 0.563 | +0.145 | +0.230 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Devin Vassell | pts | UNDER | 12.500 | draftkings | 0.606 | 0.467 | +0.141 | +0.242 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Dylan Harper | ast | UNDER | 2.500 | betparx | 0.591 | 0.454 | +0.138 | +0.300 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Victor Wembanyama | ast | UNDER | 2.500 | betway | 0.537 | 0.404 | +0.134 | +0.290 | ACTIONABLE_REVIEWED | market_prob_disagreement | CALIBRATION_SUPPORTED | passes_all_gates |
| Karl-Anthony Towns | reb | UNDER | 11.500 | draftkings | 0.650 | 0.522 | +0.130 | +0.216 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=30) |
| Devin Vassell | blk | UNDER | 0.500 | draftkings | 0.695 | 0.566 | +0.129 | +0.158 | ACTIONABLE_REVIEWED | low_line_discrete_stat | CALIBRATION_SAMPLE_LIMITED | passes_all_gates; calibration sample limited (n=77) |
| Karl-Anthony Towns | ast | OVER | 3.500 | betrivers | 0.703 | 0.575 | +0.127 | +0.194 | ACTIONABLE_REVIEWED | line_vs_median_gap | CALIBRATION_SUPPORTED | passes_all_gates |
| Mikal Bridges | blk | UNDER | 0.500 | betparx | 0.691 | 0.600 | +0.091 | +0.095 | ACTIONABLE_REVIEWED | low_line_discrete_stat | NOT_CHECKED | passes_all_gates |

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

