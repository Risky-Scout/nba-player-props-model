# Spurs @ Knicks — Current-live PMF snapshot

## Summary

- Matchup: **Spurs @ Knicks** (Away: Spurs, Home: Knicks)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **35**
- PMFs recomputed: **True**
- Lineup status: BDL did not return confirmed starters at this timestamp; this is a baseline snapshot
- Injury status: Injury / availability inherited from the canonical predictions slate
- Edge status: See `market_comparison.csv` `edge_publish_status` column. Current-live without confirmed lineups is at most `WATCHLIST_NOT_CONFIRMED_LINEUP`.

## How to read this

- `model_prob` is the model's **win probability** under the sportsbook push-excluded convention. For decimal lines (e.g. `UNDER 8.5`), `model_prob = P(stat < 8.5)`. For integer lines (e.g. `UNDER 1.0`), `model_prob = P(stat < 1) / (1 − P(stat = 1))`.
- `market_prob` is the no-vig probability implied by the same side's American odds, after stripping the vig.
- `raw_edge = model_prob − market_prob`. `ev` uses the same push-excluded convention; integer-line rows also report a push-aware EV in the audit JSON.
- `edge_publish_status` filters which rows are eligible to show Derek as actionable: `PUBLISH_BLOCKER` > `REVIEW_LARGE_EDGE` > `REVIEW_PUSH_LINE` > `WATCHLIST_NOT_CONFIRMED_LINEUP` > `ACTIONABLE_REVIEWED`. Current-live without confirmed lineups is never higher than `WATCHLIST_NOT_CONFIRMED_LINEUP`.
- `calibration_support_status` reports whether the historical scoring corpus has enough settled rows in the same (stat, side, line bucket, edge bucket) to trust the edge: `CALIBRATION_SUPPORTED` (n ≥ 100) > `CALIBRATION_SAMPLE_LIMITED` (30 ≤ n < 100) > `CALIBRATION_SAMPLE_THIN` (n < 30) > `CALIBRATION_REVIEW_REQUIRED` (model worse than market by ≥ 0.05 logloss).
- `p0` is the modeled probability the player records exactly zero of this stat. PMF tail mass is summarized in `pmf_mean` / `pmf_variance`.

## Important caveats

- **BDL did not return confirmed lineup rows at this timestamp.** This snapshot is a best-available baseline; it does not directly reflect official starter status. The dispatcher will produce confirmed-lineup snapshots in the T-minus-25 and close-lock windows.
- Market odds are used for **edge only**, never as model features (`market_odds_used_as_features=False`).
- No post-tip data was used in any prediction (`no_post_tip_data_used=True`).

## Top edges (subject to publishability gates)

Sort: largest |raw_edge| first. `edge_publish_status` is the gate that determines whether a row is showable; rows without `ACTIONABLE_REVIEWED` are not for action.

| player_name | stat | side | line | model_prob | market_prob | raw_edge | ev | edge_publish_status | calibration_support_status | calibration_bucket_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.794 | 0.497 | +0.298 | +0.536 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Victor Wembanyama | reb | UNDER | 11.500 | 0.784 | 0.534 | +0.251 | +0.416 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Miles McBride | fg3m | OVER | 0.500 | 0.835 | 0.608 | +0.227 | +0.303 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Victor Wembanyama | pts | UNDER | 27.500 | 0.726 | 0.514 | +0.215 | +0.357 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 297 |
| Stephon Castle | ast | UNDER | 6.500 | 0.712 | 0.516 | +0.197 | +0.370 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 197 |
| Dylan Harper | reb | UNDER | 5.500 | 0.626 | 0.437 | +0.191 | +0.347 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 421 |
| Karl-Anthony Towns | pts | UNDER | 17.500 | 0.688 | 0.524 | +0.167 | +0.252 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1061 |
| Jalen Brunson | fg3m | UNDER | 2.500 | 0.722 | 0.560 | +0.162 | +0.249 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 313 |
| Josh Hart | reb | UNDER | 8.500 | 0.649 | 0.496 | +0.155 | +0.256 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 300 |
| Devin Vassell | pts | UNDER | 12.500 | 0.660 | 0.511 | +0.150 | +0.249 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1061 |
| De'Aaron Fox | reb | OVER | 3.500 | 0.588 | 0.446 | +0.142 | +0.317 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 421 |
| Mikal Bridges | fg3m | UNDER | 1.500 | 0.694 | 0.554 | +0.140 | +0.190 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 313 |
| Mitchell Robinson | stl | UNDER | 0.500 | 0.728 | 0.589 | +0.139 | +0.192 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 83 |
| Keldon Johnson | stl | UNDER | 0.500 | 0.774 | 0.637 | +0.137 | +0.182 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 83 |
| Dylan Harper | ast | UNDER | 3.500 | 0.704 | 0.571 | +0.133 | +0.185 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 235 |
| OG Anunoby | stl | UNDER | 1.500 | 0.747 | 0.615 | +0.132 | +0.192 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 85 |
| Victor Wembanyama | ast | UNDER | 3.500 | 0.702 | 0.575 | +0.128 | +0.170 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 235 |
| Keldon Johnson | reb | UNDER | 2.500 | 0.583 | 0.456 | +0.128 | +0.252 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 90 |
| Dylan Harper | pts | UNDER | 13.500 | 0.601 | 0.497 | +0.106 | +0.141 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1061 |
| Josh Hart | stl | UNDER | 1.500 | 0.673 | 0.575 | +0.099 | +0.117 | WATCHLIST_NOT_CONFIRMED_LINEUP | NOT_CHECKED | 0 |

## Technical audit details

- Game ID: `21716137`
- Away Team: Spurs
- Home Team: Knicks
- Game start time UTC: `2026-06-11T00:40:00Z`
- Snapshot target time UTC: `2026-06-10T23:04:20Z`
- Actual run started at UTC: `2026-06-10T23:04:20Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-06-09`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-06-09`
- Calibrated through date: `2026-06-09`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
