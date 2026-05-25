# Knicks @ Cavaliers — Current-live PMF snapshot

## Summary

- Matchup: **Knicks @ Cavaliers** (Away: Knicks, Home: Cavaliers)
- Snapshot: Current-live
- Snapshot mode: `production_live_current`
- Props emitted: **32**
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
| Karl-Anthony Towns | reb | UNDER | 11.500 | 0.710 | 0.470 | +0.240 | +0.455 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 53 |
| Evan Mobley | reb | UNDER | 8.500 | 0.746 | 0.522 | +0.225 | +0.367 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 121 |
| Jalen Brunson | fg3m | UNDER | 2.500 | 0.747 | 0.525 | +0.222 | +0.385 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 174 |
| James Harden | ast | UNDER | 6.500 | 0.764 | 0.562 | +0.203 | +0.298 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 97 |
| Jarrett Allen | reb | UNDER | 7.500 | 0.658 | 0.457 | +0.201 | +0.381 | REVIEW_LARGE_EDGE | CALIBRATION_SUPPORTED | 121 |
| Jarrett Allen | stl | UNDER | 0.500 | 0.607 | 0.406 | +0.201 | +0.444 | REVIEW_LARGE_EDGE | CALIBRATION_SAMPLE_LIMITED | 48 |
| Evan Mobley | ast | UNDER | 3.500 | 0.667 | 0.486 | +0.183 | +0.322 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 200 |
| Max Strus | fg3m | UNDER | 2.500 | 0.750 | 0.572 | +0.178 | +0.250 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 277 |
| Donovan Mitchell | pts | UNDER | 26.500 | 0.648 | 0.478 | +0.173 | +0.296 | PUBLISH_BLOCKER | CALIBRATION_SUPPORTED | 955 |
| Mikal Bridges | fg3m | UNDER | 1.500 | 0.727 | 0.560 | +0.167 | +0.286 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 277 |
| James Harden | blk | UNDER | 0.500 | 0.753 | 0.594 | +0.159 | +0.209 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 70 |
| Max Strus | stl | UNDER | 0.500 | 0.630 | 0.474 | +0.156 | +0.260 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 74 |
| Mikal Bridges | blk | UNDER | 0.500 | 0.718 | 0.565 | +0.153 | +0.242 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 70 |
| Max Strus | pts | UNDER | 9.500 | 0.625 | 0.478 | +0.149 | +0.251 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 205 |
| Donovan Mitchell | reb | UNDER | 4.500 | 0.651 | 0.517 | +0.136 | +0.243 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 376 |
| Karl-Anthony Towns | pts | UNDER | 17.500 | 0.621 | 0.493 | +0.129 | +0.217 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 955 |
| James Harden | reb | UNDER | 4.500 | 0.586 | 0.460 | +0.127 | +0.219 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 376 |
| Donovan Mitchell | ast | UNDER | 4.500 | 0.718 | 0.594 | +0.126 | +0.156 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 200 |
| Donovan Mitchell | blk | UNDER | 0.500 | 0.844 | 0.724 | +0.124 | +0.103 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SAMPLE_LIMITED | 70 |
| Josh Hart | reb | UNDER | 7.500 | 0.654 | 0.534 | +0.121 | +0.177 | WATCHLIST_NOT_CONFIRMED_LINEUP | CALIBRATION_SUPPORTED | 297 |

## Technical audit details

- Game ID: `21713901`
- Away Team: Knicks
- Home Team: Cavaliers
- Game start time UTC: `None`
- Snapshot target time UTC: `2026-05-25T22:01:03Z`
- Actual run started at UTC: `2026-05-25T22:01:03Z`
- Snapshot validity status: `on_time_or_current_live`
- Champion model ID: `challenger-2026-05-24`
- Feature set ID: `phase13s_direct_lineup_injury_pmf_driver_v1`
- Trained through date: `2026-05-24`
- Calibrated through date: `2026-05-24`
- Direct-lineup PMF driver: **True**
- Contextual PMF engine: **True**
- PMFs recomputed: **True**
- PMF source: `live_snapshot_recomputed`
- BDL lineup fetch status: `no_rows_returned` (rows=0)
- BDL injury fetch status: `deferred_to_predict_pipeline` (rows=0)
- market_odds_used_as_features: `False`
- market_odds_used_for_edge_only: `True`
- no_post_tip_data_used: `True`
