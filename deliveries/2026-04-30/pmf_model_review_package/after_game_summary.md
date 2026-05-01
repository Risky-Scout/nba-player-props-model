# After-game scoring — 2026-04-30

## Aggregate PMF metrics

- n = 68
- NLL mean = 2.2116
- RPS mean = 0.0715
- mean error = -0.1382
- |mean error| = 2.5987
- outcome prob assigned mean = 0.1220

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 12 | 2.1097 | 0.0585 | -0.0021 | 1.7462 | 0.1353 |
| fg3m | 19 | 1.6113 | 0.0367 | +0.5761 | 1.2403 | 0.2244 |
| pts | 17 | 2.5694 | 0.1031 | -2.0299 | 4.9511 | 0.0346 |
| reb | 20 | 2.5388 | 0.0856 | +0.7095 | 2.4010 | 0.0909 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 9 | 2.2000 | 0.0749 | +0.9020 | 2.5539 |
| rotation | 14 | 2.2589 | 0.0776 | +1.2131 | 2.1737 |
| starter | 45 | 2.1992 | 0.0689 | -0.7667 | 2.7399 |

## Market-line scoring (non-push rows)

- non-push rows = 1,265
- model logloss = 0.6249
- model brier  = 0.2185

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
