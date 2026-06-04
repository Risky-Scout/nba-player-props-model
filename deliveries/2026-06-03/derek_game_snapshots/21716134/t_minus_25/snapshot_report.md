# Knicks @ Spurs — Current-live PMF snapshot

## Summary

- Matchup: **Knicks @ Spurs** (Away: Knicks, Home: Spurs)
- Snapshot: T-minus-25 (late but pre-tip)
- Snapshot mode: `production_live`
- Props emitted: **31**
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
| Victor Wembanyama | reb | UNDER | 11.500 | 0.778 | 0.477 | +0.302 | +0.595 | PUBLISH_BLOCKER | CALIBRATION_SAMPLE_LIMITED | 53 |
| Karl-Anthony Towns | blk | UNDER | 0.500 | 0.686 | 0.409 | +0.277 | +0.680 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 24 |
| Victor Wembanyama | pts | UNDER | 26.500 | 0.736 | 0.486 | +0.252 | +0.457 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 296 |
| Stephon Castle | ast | UNDER | 6.500 | 0.673 | 0.453 | +0.221 | +0.448 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 97 |
| Mitchell Robinson | blk | UNDER | 0.500 | 0.682 | 0.464 | +0.219 | +0.379 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 24 |
| Luke Kornet | reb | UNDER | 2.500 | 0.663 | 0.468 | +0.197 | +0.379 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_THIN | 12 |
| Victor Wembanyama | stl | UNDER | 1.500 | 0.817 | 0.628 | +0.188 | +0.247 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 62 |
| Julian Champagnie | reb | UNDER | 5.500 | 0.697 | 0.512 | +0.186 | +0.330 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 400 |
| Keldon Johnson | reb | UNDER | 3.500 | 0.758 | 0.580 | +0.179 | +0.291 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 400 |
| Josh Hart | reb | UNDER | 7.500 | 0.582 | 0.427 | +0.156 | +0.338 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 297 |
| Karl-Anthony Towns | pts | UNDER | 16.500 | 0.653 | 0.505 | +0.150 | +0.268 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 1034 |
| Stephon Castle | reb | UNDER | 4.500 | 0.600 | 0.452 | +0.149 | +0.295 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 400 |
| Devin Vassell | reb | UNDER | 4.500 | 0.707 | 0.563 | +0.145 | +0.230 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 400 |
| Devin Vassell | pts | UNDER | 12.500 | 0.606 | 0.467 | +0.141 | +0.242 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 1034 |
| Dylan Harper | ast | UNDER | 2.500 | 0.591 | 0.454 | +0.138 | +0.300 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 148 |
| Victor Wembanyama | ast | UNDER | 2.500 | 0.537 | 0.404 | +0.134 | +0.290 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 148 |
| Karl-Anthony Towns | reb | UNDER | 11.500 | 0.650 | 0.522 | +0.130 | +0.216 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 30 |
| Devin Vassell | blk | UNDER | 0.500 | 0.695 | 0.566 | +0.129 | +0.158 | ACTIONABLE_REVIEWED | CALIBRATION_SAMPLE_LIMITED | 77 |
| Karl-Anthony Towns | ast | OVER | 3.500 | 0.703 | 0.575 | +0.127 | +0.194 | ACTIONABLE_REVIEWED | CALIBRATION_SUPPORTED | 219 |
| Mikal Bridges | blk | UNDER | 0.500 | 0.691 | 0.600 | +0.091 | +0.095 | ACTIONABLE_REVIEWED | NOT_CHECKED | 0 |

## Technical audit details

- Game ID: `21716134`
- Away Team: Knicks
- Home Team: Spurs
- Game start time UTC: `2026-06-04T00:30:00Z`
- Snapshot target time UTC: `2026-06-04T00:05:00Z`
- Actual run started at UTC: `2026-06-04T00:23:15Z`
- Snapshot validity status: `late_but_pre_tip`
- Champion model ID: `challenger-2026-06-02`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-06-02`
- Calibrated through date: `2026-06-02`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
