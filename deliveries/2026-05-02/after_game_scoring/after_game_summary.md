# After-game scoring — 2026-05-02

## Aggregate PMF metrics

- n = 18
- NLL mean = 2.3281
- RPS mean = 0.0829
- mean error = -2.7700
- |mean error| = 3.2378
- outcome prob assigned mean = 0.1025

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 2 | 2.2750 | 0.0629 | -1.9682 | 1.9682 | 0.1039 |
| fg3m | 7 | 1.9794 | 0.0440 | -0.5738 | 1.0562 | 0.1694 |
| pts | 3 | 1.6412 | 0.1002 | -8.1419 | 8.6837 | 0.0155 |
| reb | 6 | 3.0959 | 0.1262 | -2.9135 | 3.4833 | 0.0675 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 1 | 3.7564 | 0.1575 | -4.0076 | 4.0076 |
| rotation | 2 | 1.4891 | 0.0238 | +0.6465 | 0.6465 |
| starter | 15 | 2.3447 | 0.0858 | -3.1430 | 3.5320 |

## Market-line scoring (non-push rows)

- non-push rows = 406
- model logloss = 0.8029
- model brier  = 0.2926

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
