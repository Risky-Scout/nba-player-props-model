# Phase 9C — controlled multi-day OOF market backfill plan

This plan documents the second leakage-safe evaluation pass: a 14-day
window covering **2026-03-18 → 2026-03-31** (the last two weeks of the
Phase 8 OOF horizon). Goal is diagnostic, not market-beating: identify
where the standalone calibrated model agrees / disagrees with the
de-vigged market across stats, role buckets, line buckets, and
alternate-line ladders.

## 1. Window

| Metric | Value |
|---|---:|
| Dates | 14 (2026-03-18 → 2026-03-31, inclusive) |
| OOF rows | 11,075 |
| Distinct OOF games | 107 |
| Distinct OOF players (sum across dates) | 2,215 |

Per-date OOF coverage (used for cost estimation):

| Date | OOF rows | Games |
|---|---:|---:|
| 2026-03-18 | 965 | 9 |
| 2026-03-19 | 805 | 8 |
| 2026-03-20 | 575 | 6 |
| 2026-03-21 | 995 | 10 |
| 2026-03-22 | 560 | 5 |
| 2026-03-23 | 1,055 | 10 |
| 2026-03-24 | 390 | 4 |
| 2026-03-25 | 1,220 | 12 |
| 2026-03-26 | 320 | 3 |
| 2026-03-27 | 1,050 | 10 |
| 2026-03-28 | 610 | 6 |
| 2026-03-29 | 980 | 9 |
| 2026-03-30 | 765 | 8 |
| **2026-03-31** | 785 | 7 (only 2 already captured) |

## 2. Capture cost estimate

Using observed Phase 9B rates:

| Call | Per-call | × | Total |
|---|---:|---:|---:|
| Historical events list (1 per date) | ≈ 10 credits | 14 dates | ≈ 140 |
| Historical event-odds (10 markets, US region) | ≈ 100 credits | 100 events | ≈ 10,000 |
| Subtotal | | | ≈ 10,140 |
| 20 % safety margin | | | × 1.20 |
| **Estimated total** | | | **≈ 12,170 credits** |

Well under the 25,000-credit confirmation threshold, so the spec
authorizes proceeding once quota allows. The current quota state is
documented under "Status (2026-04-29)" below.

## 3. Capture command (per-date)

```
python3 scripts/oddsapi_nba_props.py historical-lock-day \
    --target-date {YYYY-MM-DD} \
    --max-events 20 \
    --commence-after {YYYY-MM-DD}T00:00:00Z \
    --commence-before {YYYY-MM-DD+1}T06:00:00Z \
    --lock-offset-minutes 5
```

Skip rule: if `data/odds_api/processed/{date}/odds_pairs_hist_lockday_{date}.parquet`
already has > 0 paired rows AND was validated by
`scripts/validate_oddsapi_props.py`, do NOT re-fetch unless the
operator passes `--force` (caller-side; the subcommand itself does not
implement `--force` and the orchestrator should branch on file
existence + non-emptiness). The 2026-03-31 file is non-empty (1,293
pairs from 2 events) and is therefore preserved as-is — partial
coverage on that date is documented in the aggregate output.

## 4. Aggregate evaluator

`scripts/evaluate_oof_vs_oddsapi_market_aggregate.py`

```
python3 scripts/evaluate_oof_vs_oddsapi_market_aggregate.py \
    --from-date 2026-03-18 --to-date 2026-03-31
```

Reuses the leakage-safe match path from `evaluate_oof_vs_oddsapi_market.py`:

- crosswalk `(game_id, player_id) → player_name + team` (deduped before merge — fixes the prior 5× explosion bug)
- explicit join on `(game_date, normalized_player_name, market_stat == stat)`
- leakage filter: `snapshot_time_utc ≤ commence_time_utc`
- hard gates A–F preserved
- aggregates over the entire date window without manufacturing matches

Outputs go to `artifacts/phase9_market_eval/aggregate_2026-03-18_to_2026-03-31/`:

- `aggregate_matches.parquet` / `.csv`
- `aggregate_summary.md` (decision report)
- `by_stat.csv`, `by_book.csv`, `by_main_vs_alternate.csv`,
  `by_line_bucket.csv`, `by_role_bucket.csv`, `by_date.csv`
- `calibration_bins_model.csv`, `calibration_bins_market.csv` (10 bins each + weighted ECE)
- `alternate_ladder_shape_eval.csv` (per ladder group with ≥ 3 lines: monotonicity, mean/median/max abs diff, market-PMF-reconstruction feasibility)
- `date_coverage.csv` (per-date file count, paired-row count, source filenames)

## 5. Validation gates (aggregate)

Hard fail if any of:

| Gate | Threshold |
|---|---|
| matched rows | = 0 |
| matched_rows / pairs | > 1.10 |
| `market_stat != stat` count | > 0 |
| PMF sum-to-1 within 1e-6 | any failure |
| PMF negative or non-finite | any failure |
| `model_p_over_line` ∈ [0,1] | any out-of-range |
| leakage violations (post-filter) | > 0 |

ECE / by-stat / by-book / ladder shape are reported but not gated.

## 6. Decision report (aggregate_summary.md)

The aggregate summary is meant to answer:

1. **Is the standalone model better or worse than no-vig market overall?**
2. Which stats are closest / worst?
3. Is the error mean/center, tail shape, or both?
4. Do alternate lines show systematic full-PMF shape error?
5. Is the FG3M tail correction still reasonable?
6. Is TOV market coverage usable?
7. Is the model overconfident or underconfident by calibration bin?
8. Are errors concentrated by role_bucket or projected minutes?
9. What is the highest-value next improvement?

Recommended next-steps to be ranked in the report (do NOT pre-decide here):
injury / minutes freshness · role / minutes model improvement ·
PMF calibrator retraining · stat-specific tail correction ·
market-aware residual calibration · full historical backfill.

## 7. Honest framing

- A 14-day window is **not** sufficient for a market-beating claim.
  The full-OOF audit (n = 3,818) found the de-vigged closing market
  beating the standalone calibrated model on log-loss in 9 of 11
  cohorts at 95 % CI. A 14-day diagnostic refines that picture by
  stat / role / line bucket / book / date — but does not overturn it.
- The capture is per-event lock at `commence_time − 5 min`; this is
  the closing line, not the opening line. CLV is not reported here
  because opening-line snapshots are not part of this capture set.

## Status (2026-04-29 quota check)

The Odds API monthly quota was at **100,000 / 100,000 used** (`remaining=0`)
when this plan was finalized. The capture in §3 is paused awaiting quota
refresh or a higher-tier key. The aggregate evaluator was built and
validated on the existing single-date capture (2026-03-31, 1,293 pairs)
to confirm gates A–F still pass at the aggregate scale; the genuine
multi-day diagnostic numbers will be produced once the 13 missing dates
are captured.
