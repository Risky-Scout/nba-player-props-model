# After-game scoring — 2026-05-24

## Aggregate PMF metrics

- n = 168
- NLL mean = 2.2050
- RPS mean = 0.0397
- mean error = +1.9924
- |mean error| = 3.0616
- outcome prob assigned mean = 0.1949

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 14 | 1.5888 | 0.0270 | +0.5298 | 1.0466 | 0.2170 |
| blk | 14 | 1.1493 | 0.0357 | -0.1411 | 0.5050 | 0.4670 |
| fg3m | 14 | 1.0978 | 0.0337 | +0.8762 | 1.0637 | 0.3763 |
| pa | 14 | 3.5026 | 0.0485 | +5.6102 | 7.6723 | 0.0354 |
| pr | 14 | 3.3977 | 0.0386 | +5.3139 | 6.2995 | 0.0417 |
| pra | 14 | 3.5286 | 0.0381 | +5.8437 | 7.1954 | 0.0373 |
| pts | 14 | 3.3762 | 0.0529 | +5.0804 | 6.7764 | 0.0381 |
| ra | 14 | 2.2151 | 0.0256 | +0.7633 | 1.9522 | 0.1230 |
| reb | 14 | 2.1776 | 0.0390 | +0.2335 | 1.5982 | 0.1613 |
| stl | 14 | 1.2150 | 0.0460 | -0.0640 | 0.7368 | 0.3524 |
| stocks | 14 | 1.5217 | 0.0286 | -0.2051 | 0.7815 | 0.2509 |
| tov | 14 | 1.6901 | 0.0626 | +0.0677 | 1.1120 | 0.2379 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| core | 36 | 1.9547 | 0.0298 | +2.1260 | 2.5101 |
| rotation | 60 | 2.0409 | 0.0348 | +2.3026 | 3.0277 |
| starter | 72 | 2.4670 | 0.0487 | +1.6671 | 3.3657 |

## Market-line scoring (non-push rows)

- non-push rows = 1,695
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
