# Spurs @ Knicks — Current-live PMF snapshot

## Summary

- Matchup: **Spurs @ Knicks** (Away: Spurs, Home: Knicks)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **30**
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
| Victor Wembanyama | blk | UNDER | 3.500 | 0.809 | 0.509 | +0.300 | +0.532 | PUBLISH_BLOCKER | CALIBRATION_SAMPLE_THIN | 17 |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.769 | 0.512 | +0.257 | +0.431 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Victor Wembanyama | pts | UNDER | 27.500 | 0.734 | 0.506 | +0.232 | +0.400 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 297 |
| Victor Wembanyama | reb | UNDER | 11.500 | 0.712 | 0.490 | +0.224 | +0.410 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Dylan Harper | ast | UNDER | 3.500 | 0.777 | 0.578 | +0.201 | +0.279 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 161 |
| Karl-Anthony Towns | pts | UNDER | 17.500 | 0.663 | 0.500 | +0.167 | +0.301 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 1061 |
| Victor Wembanyama | ast | UNDER | 3.500 | 0.774 | 0.609 | +0.166 | +0.211 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |
| Karl-Anthony Towns | stl | UNDER | 0.500 | 0.609 | 0.453 | +0.156 | +0.279 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 83 |
| De'Aaron Fox | reb | OVER | 3.500 | 0.598 | 0.447 | +0.150 | +0.286 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 405 |
| Stephon Castle | ast | UNDER | 6.500 | 0.705 | 0.557 | +0.148 | +0.204 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 193 |
| Mikal Bridges | fg3m | UNDER | 1.500 | 0.700 | 0.552 | +0.148 | +0.239 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 297 |
| De'Aaron Fox | ast | UNDER | 5.500 | 0.616 | 0.482 | +0.135 | +0.264 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |
| Dylan Harper | pts | UNDER | 13.500 | 0.636 | 0.504 | +0.135 | +0.242 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1061 |
| Stephon Castle | stl | OVER | 0.500 | 0.755 | 0.624 | +0.131 | +0.152 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 83 |
| Julian Champagnie | pts | UNDER | 10.500 | 0.630 | 0.514 | +0.119 | +0.193 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 237 |
| Josh Hart | reb | UNDER | 8.500 | 0.646 | 0.529 | +0.118 | +0.185 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 300 |
| Devin Vassell | pts | UNDER | 13.500 | 0.635 | 0.522 | +0.117 | +0.165 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 1061 |
| Devin Vassell | ast | UNDER | 2.500 | 0.650 | 0.535 | +0.115 | +0.157 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 162 |
| Josh Hart | ast | UNDER | 4.500 | 0.605 | 0.497 | +0.109 | +0.181 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |
| Landry Shamet | pts | UNDER | 8.500 | 0.599 | 0.498 | +0.103 | +0.165 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 237 |

## Technical audit details

- Game ID: `21716136`
- Away Team: Spurs
- Home Team: Knicks
- Game start time UTC: `2026-06-09T00:40:00Z`
- Snapshot target time UTC: `2026-06-08T22:52:48Z`
- Actual run started at UTC: `2026-06-08T22:52:48Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-06-06`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-06-06`
- Calibrated through date: `2026-06-06`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
