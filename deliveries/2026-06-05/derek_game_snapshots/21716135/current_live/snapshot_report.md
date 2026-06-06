# Knicks @ Spurs — Current-live PMF snapshot

## Summary

- Matchup: **Knicks @ Spurs** (Away: Knicks, Home: Spurs)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **43**
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
| Victor Wembanyama | reb | UNDER | 11.500 | 0.759 | 0.472 | +0.288 | +0.526 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Karl-Anthony Towns | blk | UNDER | 0.500 | 0.700 | 0.416 | +0.283 | +0.644 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 24 |
| Victor Wembanyama | pts | UNDER | 27.500 | 0.772 | 0.514 | +0.261 | +0.474 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 296 |
| Stephon Castle | ast | UNDER | 6.500 | 0.714 | 0.488 | +0.228 | +0.401 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 97 |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.785 | 0.557 | +0.227 | +0.371 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Mitchell Robinson | blk | UNDER | 0.500 | 0.734 | 0.510 | +0.224 | +0.401 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 77 |
| Karl-Anthony Towns | stl | UNDER | 0.500 | 0.672 | 0.448 | +0.224 | +0.444 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Victor Wembanyama | ast | UNDER | 3.500 | 0.807 | 0.595 | +0.213 | +0.308 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 161 |
| Victor Wembanyama | stl | UNDER | 1.500 | 0.850 | 0.648 | +0.202 | +0.286 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 62 |
| Dylan Harper | ast | UNDER | 3.500 | 0.774 | 0.586 | +0.189 | +0.290 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 161 |
| OG Anunoby | blk | UNDER | 0.500 | 0.654 | 0.475 | +0.179 | +0.335 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 77 |
| OG Anunoby | fg3m | UNDER | 1.500 | 0.538 | 0.368 | +0.170 | +0.425 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 283 |
| Julian Champagnie | pts | UNDER | 10.500 | 0.648 | 0.481 | +0.169 | +0.309 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 230 |
| De'Aaron Fox | ast | UNDER | 5.500 | 0.631 | 0.462 | +0.169 | +0.324 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 219 |
| Landry Shamet | fg3m | UNDER | 1.500 | 0.679 | 0.514 | +0.165 | +0.297 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 283 |
| Devin Vassell | pts | UNDER | 12.500 | 0.634 | 0.477 | +0.158 | +0.299 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1034 |
| Jalen Brunson | stl | OVER | 0.500 | 0.713 | 0.554 | +0.158 | +0.248 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 83 |
| Josh Hart | reb | UNDER | 8.500 | 0.625 | 0.470 | +0.156 | +0.281 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 297 |
| Julian Champagnie | reb | UNDER | 5.500 | 0.606 | 0.464 | +0.143 | +0.259 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 400 |
| Dylan Harper | pts | UNDER | 12.500 | 0.659 | 0.519 | +0.143 | +0.222 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 1034 |

## Technical audit details

- Game ID: `21716135`
- Away Team: Knicks
- Home Team: Spurs
- Game start time UTC: `2026-06-06T00:40:00Z`
- Snapshot target time UTC: `2026-06-05T21:53:17Z`
- Actual run started at UTC: `2026-06-05T21:53:17Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-06-04`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-06-04`
- Calibrated through date: `2026-06-04`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
