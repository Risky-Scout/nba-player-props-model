# Phase 2 — Availability Signal Coverage

Metrics generated from `data/player_availability_asof.parquet` produced by
`python scripts/build_availability_table.py` on 2026-04-18 against the
full history in `data/player_game_stats.parquet`.

## 1. Core coverage numbers

| Metric | Before (pre-rebuild) | After (Phase 2) |
|---|---|---|
| Training rows with a populated injury map | 6.5% (snapshot table only, 2026-03-11+) | **99.0% HIGH confidence** |
| Training rows with a teammate-OUT signal | 0% of pre-snapshot rows (77,285) | **64.6% of the same rows (49,892)** |
| Overall rows with ≥1 teammate OUT | — | **63.3% (52,266 / 82,627)** |
| Overall rows with `is_returning_from_absence` | — | 11.8% (9,783) |
| Overall rows with `minutes_restriction_flag` | — | 8.6% (7,088) |

The pre-rebuild row is the defect headlined in `docs/PHASE1_AUDIT.md`:
`data/injury_snapshots.parquet` only started accumulating on 2026-03-11
so 93.5% of training rows received an empty `injury_map` at training
time. Inference always had a populated map. Phase 2 sources from
`data/nba_injury_reports.parquet` (which spans 2023-10-25 → 2026-03-31)
and collapses the gap.

## 2. Confidence tier by month

HIGH means an injury report was available for that date; LOW means we
fell back to recent play history.

| Month | HIGH | MEDIUM | LOW | % HIGH |
|---|---:|---:|---:|---:|
| 2023-10 | 773 | 0 | 415 | 65.1% |
| 2023-11 | 4,619 | 0 | 71 | 98.5% |
| 2023-12 | 4,387 | 0 | 33 | 99.3% |
| 2024-01 | 4,965 | 0 | 16 | 99.7% |
| 2024-02 | 3,715 | 0 | 14 | 99.6% |
| 2024-03 | 4,859 | 0 | 18 | 99.6% |
| 2024-04 | 3,318 | 0 | 5 | 99.8% |
| 2024-05 | 846 | 0 | 0 | 100.0% |
| 2024-06 | 114 | 0 | 0 | 100.0% |
| 2024-10 | 1,526 | 0 | 62 | 96.1% |
| 2024-11 | 4,753 | 0 | 21 | 99.6% |
| 2024-12 | 4,060 | 0 | 7 | 99.8% |
| 2025-01 | 4,870 | 0 | 7 | 99.9% |
| 2025-02 | 3,707 | 0 | 7 | 99.8% |
| 2025-03 | 4,992 | 0 | 15 | 99.7% |
| 2025-04 | 3,131 | 0 | 3 | 99.9% |
| 2025-05 | 835 | 0 | 0 | 100.0% |
| 2025-06 | 158 | 0 | 0 | 100.0% |
| 2025-10 | 1,724 | 0 | 57 | 96.8% |
| 2025-11 | 4,751 | 0 | 11 | 99.8% |
| 2025-12 | 4,268 | 0 | 5 | 99.9% |
| 2026-01 | 4,987 | 0 | 1 | 99.98% |
| 2026-02 | 3,530 | 0 | 12 | 99.7% |
| 2026-03 | 5,034 | 0 | 17 | 99.7% |
| 2026-04 | 1,903 | 0 | 5 | 99.7% |
| **Total** | **81,825** | **0** | **802** | **99.0%** |

2023-10 is the only month below 95% — the injury-report feed started
2023-10-25, so the first few days have no report and fall back to
play-history inference.

## 3. Status distribution by NBA season

| Season | ACTIVE | PROBABLE | QUESTIONABLE | DOUBTFUL | OUT | UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|
| 2023-2024 | 26,005 | 540 | 993 | 7 | 51 | 572 |
| 2024-2025 | 26,389 | 621 | 932 | 15 | 75 | 122 |
| 2025-2026 | 24,885 | 390 | 877 | 15 | 30 | 108 |

OUT counts are modest here because the table is keyed on
(player_id, game_date) pairs that appear in `player_game_stats`; a
player who sat does not generate a row. The OUT signal flows through
the team-level teammate-absence features, not the subject-row status.

## 4. Teammate-absence signal distribution

Distribution across the full 82,627 rows (medians and upper tails):

| Feature | mean | 50% | 75% | 90% | 95% | max |
|---|---:|---:|---:|---:|---:|---:|
| num_teammates_out_total | 1.46 | 1.0 | 2.0 | 4.0 | 4.0 | 9.0 |
| vacated_minutes_guard | 10.6 | 0.0 | 18.5 | 35.3 | 47.8 | 139.1 |
| vacated_minutes_wing | 10.7 | 0.0 | 18.0 | 34.1 | 46.3 | 152.6 |
| vacated_minutes_big | 4.2 | 0.0 | 0.0 | 20.8 | 30.1 | 76.6 |
| vacated_fga_total | 9.6 | 4.1 | 15.5 | 26.8 | 34.9 | 93.8 |

The 90th percentile of vacated_minutes across guard and wing archetypes
sits above 34 — these are games the model must treat materially
differently from the "no absences" baseline. Under the old pipeline the
feature was identically zero for all pre-snapshot rows, so the model
learned to ignore it.

## 5. Source provenance

| Source | Rows | Share |
|---|---:|---:|
| implicit_active (no report row for the player; covered window) | 76,620 | 92.7% |
| injury_report (explicit status present) | 5,205 | 6.3% |
| no_history (LOW confidence fallback) | 802 | 1.0% |

## 6. What this enables

The rebuilt pipeline makes the following training-time features real
instead of silently zero:

- `teammate_out_count_{guard,wing,big}`
- `teammate_questionable_count_{guard,wing,big}`
- `vacated_minutes_{guard,wing,big}`
- `vacated_fga_total`, `num_teammates_out_total`
- `availability_status`, `prob_active`, `availability_confidence`
- `games_since_last_played`, `days_since_last_played`,
  `is_returning_from_absence`, `minutes_restriction_flag`

These replace the NaN-propagating, forward-only `injury_snapshots` +
`injury_map = {}` flow described in the Phase 1 audit. No feature silently
encodes "no signal"; every row carries an explicit confidence tier and
an explicit source tag.

## 7. What Phase 2 does not yet change

Per the phase scope, the pipeline is built, backfilled, tested, and
integration-ready but **no model's feature whitelist has changed yet**.
Phase 3 is the first consumer: the rebuilt minutes model subscribes to
these features via
`nba_props_model.features.availability_asof.attach_from_table`. Today
the quantile models and `feature_engineering.py` still read the
legacy `injury_map`. The handoff is intentional — we keep the Phase 2
commit isolated from training-behavior changes so its correctness can
be verified independently of a retrain.

## 8. Reproducibility

```
python scripts/build_availability_table.py
pytest tests/test_availability_asof.py -v
```

Runtime: ~9 minutes single-threaded for the full history (82,627 rows).
Tests: 35 pass, ~1s wall clock.
