# After-game scoring — 2026-05-12

## Aggregate PMF metrics

- n = 135
- NLL mean = 1.6202
- RPS mean = 0.0323
- mean error = +0.7088
- |mean error| = 1.5514
- outcome prob assigned mean = 0.2918

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 27 | 1.3443 | 0.0234 | +0.2419 | 0.9175 | 0.3192 |
| fg3m | 27 | 1.0229 | 0.0244 | +0.3614 | 0.7316 | 0.4753 |
| pts | 27 | 2.4187 | 0.0240 | +1.9488 | 3.0770 | 0.1218 |
| reb | 27 | 2.1440 | 0.0481 | +0.8715 | 2.1993 | 0.1692 |
| tov | 27 | 1.1713 | 0.0415 | +0.1205 | 0.8317 | 0.3735 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 50 | 1.2306 | 0.0215 | +1.0312 | 1.3121 |
| core | 25 | 2.2318 | 0.0514 | +0.2776 | 2.0559 |
| fringe | 15 | 0.8445 | 0.0102 | +0.9135 | 0.9717 |
| rotation | 15 | 2.0895 | 0.0478 | -0.1218 | 2.5491 |
| starter | 30 | 1.9133 | 0.0376 | +0.8437 | 1.3208 |

## Market-line scoring (non-push rows)

- non-push rows = 1,285
- model logloss = 0.6361
- model brier  = 0.2228

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
