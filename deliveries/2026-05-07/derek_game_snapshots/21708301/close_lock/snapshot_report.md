# Lakers @ Thunder — Current-live PMF snapshot

## Summary

- Matchup: **Lakers @ Thunder** (Away: Lakers, Home: Thunder)
- Snapshot: Close-lock
- Snapshot mode: `None`
- Props emitted: **None**
- PMFs recomputed: **None**
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

_Edge tables unavailable: 'raw_edge'_

## Technical audit details

- Game ID: `21708301`
- Away Team: Lakers
- Home Team: Thunder
- Game start time UTC: `None`
- Snapshot target time UTC: `None`
- Actual run started at UTC: `None`
- Snapshot validity status: `None`
- Champion model ID: `None`
- Feature set ID: `None`
- Trained through date: `None`
- Calibrated through date: `None`
- Direct-lineup PMF driver: **None**
- Contextual PMF engine: **None**
- PMFs recomputed: **None**
- PMF source: `corrected_wizard_of_odds_full_pmfs_wide`
- BDL lineup fetch status: `None` (rows=None)
- BDL injury fetch status: `None` (rows=None)
- market_odds_used_as_features: `None`
- market_odds_used_for_edge_only: `None`
- no_post_tip_data_used: `None`
