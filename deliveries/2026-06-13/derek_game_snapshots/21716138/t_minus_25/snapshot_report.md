# Knicks @ Spurs — Current-live PMF snapshot

## Summary

- Matchup: **Knicks @ Spurs** (Away: Knicks, Home: Spurs)
- Snapshot: T-minus-25
- Snapshot mode: `production_live`
- Props emitted: **42**
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
| Victor Wembanyama | blk | UNDER | 3.500 | 0.836 | 0.524 | +0.312 | +0.563 | PUBLISH_BLOCKER | CALIBRATION_SAMPLE_THIN | 17 |
| Keldon Johnson | fg3m | OVER | 0.500 | 0.789 | 0.488 | +0.301 | +0.578 | PUBLISH_BLOCKER | CALIBRATION_SAMPLE_LIMITED | 30 |
| Victor Wembanyama | reb | UNDER | 11.500 | 0.769 | 0.497 | +0.273 | +0.501 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Miles McBride | fg3m | OVER | 0.500 | 0.790 | 0.517 | +0.273 | +0.459 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Victor Wembanyama | pts | UNDER | 28.500 | 0.749 | 0.501 | +0.251 | +0.477 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 297 |
| Dylan Harper | pts | UNDER | 15.500 | 0.727 | 0.508 | +0.222 | +0.389 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 297 |
| Jose Alvarado | stl | UNDER | 0.500 | 0.781 | 0.579 | +0.202 | +0.279 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 66 |
| Dylan Harper | reb | UNDER | 5.500 | 0.638 | 0.456 | +0.184 | +0.327 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 443 |
| Devin Vassell | pts | UNDER | 13.500 | 0.676 | 0.494 | +0.184 | +0.352 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 1071 |
| Devin Vassell | fg3m | UNDER | 2.500 | 0.679 | 0.508 | +0.171 | +0.326 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 328 |
| OG Anunoby | stl | UNDER | 1.500 | 0.780 | 0.614 | +0.167 | +0.253 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 86 |
| OG Anunoby | pts | UNDER | 17.500 | 0.658 | 0.494 | +0.167 | +0.285 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 1071 |
| Karl-Anthony Towns | pts | UNDER | 16.500 | 0.675 | 0.512 | +0.165 | +0.288 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 1071 |
| Stephon Castle | ast | UNDER | 6.500 | 0.694 | 0.532 | +0.163 | +0.314 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 197 |
| Dylan Harper | ast | UNDER | 3.500 | 0.729 | 0.569 | +0.161 | +0.239 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 235 |
| Landry Shamet | fg3m | OVER | 1.500 | 0.637 | 0.479 | +0.158 | +0.300 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 328 |
| De'Aaron Fox | reb | OVER | 3.500 | 0.612 | 0.459 | +0.153 | +0.298 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 443 |
| Josh Hart | stl | UNDER | 1.500 | 0.759 | 0.625 | +0.134 | +0.206 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 86 |
| OG Anunoby | fg3m | UNDER | 2.500 | 0.661 | 0.527 | +0.134 | +0.245 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 328 |
| Jalen Brunson | reb | OVER | 3.500 | 0.555 | 0.423 | +0.132 | +0.299 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 443 |

## Technical audit details

- Game ID: `21716138`
- Away Team: Knicks
- Home Team: Spurs
- Game start time UTC: `2026-06-14T00:40:00Z`
- Snapshot target time UTC: `2026-06-14T00:15:00Z`
- Actual run started at UTC: `2026-06-14T00:20:17Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-06-12`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-06-12`
- Calibrated through date: `2026-06-12`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
