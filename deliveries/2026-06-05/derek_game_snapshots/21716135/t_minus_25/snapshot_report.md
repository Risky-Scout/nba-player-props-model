# Knicks @ Spurs — Current-live PMF snapshot

## Summary

- Matchup: **Knicks @ Spurs** (Away: Knicks, Home: Spurs)
- Snapshot: T-minus-25 (late but pre-tip)
- Snapshot mode: `production_live`
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
| Victor Wembanyama | reb | UNDER | 11.500 | 0.733 | 0.451 | +0.284 | +0.554 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Victor Wembanyama | pts | UNDER | 27.500 | 0.760 | 0.509 | +0.255 | +0.464 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 296 |
| Stephon Castle | ast | UNDER | 6.500 | 0.729 | 0.493 | +0.237 | +0.430 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 97 |
| Dylan Harper | ast | UNDER | 3.500 | 0.801 | 0.588 | +0.215 | +0.336 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 161 |
| Victor Wembanyama | ast | UNDER | 3.500 | 0.809 | 0.597 | +0.213 | +0.302 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 161 |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.767 | 0.554 | +0.213 | +0.357 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| De'Aaron Fox | ast | UNDER | 5.500 | 0.649 | 0.462 | +0.187 | +0.363 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 219 |
| Josh Hart | ast | UNDER | 4.500 | 0.639 | 0.466 | +0.175 | +0.310 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 219 |
| Josh Hart | reb | UNDER | 8.500 | 0.623 | 0.459 | +0.165 | +0.340 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 297 |
| Landry Shamet | fg3m | UNDER | 1.500 | 0.659 | 0.514 | +0.145 | +0.259 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 283 |
| Jalen Brunson | fg3m | UNDER | 2.500 | 0.740 | 0.596 | +0.144 | +0.203 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 283 |
| Dylan Harper | pts | UNDER | 11.500 | 0.596 | 0.454 | +0.144 | +0.276 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 1034 |
| Julian Champagnie | pts | UNDER | 10.500 | 0.625 | 0.485 | +0.143 | +0.250 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 230 |
| Julian Champagnie | reb | UNDER | 5.500 | 0.612 | 0.470 | +0.143 | +0.273 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 400 |
| Keldon Johnson | reb | UNDER | 2.500 | 0.609 | 0.481 | +0.129 | +0.230 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 88 |
| Mitchell Robinson | blk | UNDER | 0.500 | 0.641 | 0.513 | +0.128 | +0.224 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 77 |
| Devin Vassell | pts | UNDER | 12.500 | 0.610 | 0.486 | +0.127 | +0.232 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 1034 |
| Julian Champagnie | fg3m | UNDER | 2.500 | 0.630 | 0.512 | +0.118 | +0.203 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 283 |
| Victor Wembanyama | stl | UNDER | 1.500 | 0.761 | 0.646 | +0.115 | +0.161 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 62 |
| Devin Vassell | ast | UNDER | 2.500 | 0.678 | 0.569 | +0.111 | +0.163 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 148 |

## Technical audit details

- Game ID: `21716135`
- Away Team: Knicks
- Home Team: Spurs
- Game start time UTC: `2026-06-06T00:40:00Z`
- Snapshot target time UTC: `2026-06-06T00:15:00Z`
- Actual run started at UTC: `2026-06-06T00:22:19Z`
- Snapshot validity status: `late_but_pre_tip`
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
