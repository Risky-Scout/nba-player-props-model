# Thunder @ Spurs — Current-live PMF snapshot

## Summary

- Matchup: **Thunder @ Spurs** (Away: Thunder, Home: Spurs)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **39**
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
| Victor Wembanyama | pts | UNDER | 27.500 | 0.685 | 0.474 | +0.214 | +0.404 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 285 |
| Victor Wembanyama | blk | UNDER | 3.500 | 0.719 | 0.514 | +0.206 | +0.356 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 0 |
| Chet Holmgren | blk | UNDER | 1.500 | 0.724 | 0.542 | +0.182 | +0.256 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_THIN | 2 |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.760 | 0.580 | +0.180 | +0.266 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 44 |
| Devin Vassell | stl | OVER | 1.000 | 0.667 | 0.488 | +0.178 | +0.900 | REVIEW_PUSH_LINE | CALIBRATION_SAMPLE_LIMITED | 82 |
| Alex Caruso | pts | UNDER | 10.500 | 0.677 | 0.516 | +0.163 | +0.250 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 208 |
| Shai Gilgeous-Alexander | fg3m | UNDER | 1.500 | 0.723 | 0.562 | +0.161 | +0.240 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 280 |
| Jared McCain | pts | UNDER | 13.500 | 0.639 | 0.501 | +0.142 | +0.243 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 957 |
| Jalen Williams | reb | OVER | 3.500 | 0.620 | 0.479 | +0.140 | +0.270 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 378 |
| Shai Gilgeous-Alexander | pts | UNDER | 29.500 | 0.635 | 0.509 | +0.131 | +0.197 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 957 |
| Cason Wallace | ast | UNDER | 2.500 | 0.640 | 0.513 | +0.128 | +0.216 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 136 |
| Devin Vassell | fg3m | UNDER | 2.500 | 0.623 | 0.495 | +0.127 | +0.210 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 280 |
| Cason Wallace | fg3m | UNDER | 1.500 | 0.690 | 0.565 | +0.125 | +0.220 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 280 |
| Dylan Harper | ast | UNDER | 2.500 | 0.617 | 0.497 | +0.122 | +0.178 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 136 |
| Dylan Harper | stl | OVER | 0.500 | 0.707 | 0.591 | +0.116 | +0.175 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 82 |
| Jalen Williams | ast | OVER | 3.500 | 0.570 | 0.456 | +0.114 | +0.226 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 202 |
| Luguentz Dort | fg3m | UNDER | 1.500 | 0.743 | 0.632 | +0.111 | +0.140 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 280 |
| Victor Wembanyama | reb | UNDER | 12.500 | 0.586 | 0.476 | +0.110 | +0.207 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 30 |
| Stephon Castle | ast | UNDER | 6.500 | 0.542 | 0.437 | +0.105 | +0.192 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 191 |
| Alex Caruso | blk | UNDER | 0.500 | 0.683 | 0.579 | +0.104 | +0.193 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 76 |

## Push-line audit rows

Integer lines where the model's probability of exact-line outcomes is non-trivial. The displayed `ev` uses the sportsbook push-excluded convention; `ev_recomputed_pushinc` is the honest dollar-EV with push paid as $0.

| player_name | stat | side | line | push_prob | ev | ev_recomputed | ev_recomputed_pushinc | edge_publish_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Devin Vassell | stl | OVER | 1.000 | 0.285 | +0.900 | +0.900 | +0.643 | REVIEW_PUSH_LINE |

## Technical audit details

- Game ID: `21713533`
- Away Team: Thunder
- Home Team: Spurs
- Game start time UTC: `2026-05-29T00:40:00Z`
- Snapshot target time UTC: `2026-05-28T22:48:40Z`
- Actual run started at UTC: `2026-05-28T22:48:40Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-05-27`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-05-27`
- Calibrated through date: `2026-05-27`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
