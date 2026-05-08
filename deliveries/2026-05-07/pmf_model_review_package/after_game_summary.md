# After-game scoring — 2026-05-07

## Aggregate PMF metrics

- n = 220
- NLL mean = 1.7230
- RPS mean = 0.0612
- mean error = -0.0119
- |mean error| = 1.6479
- outcome prob assigned mean = 0.2672

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 44 | 1.6135 | 0.0419 | +0.0109 | 1.2209 | 0.2714 |
| fg3m | 44 | 1.1116 | 0.1329 | -0.0081 | 0.7813 | 0.4288 |
| pts | 44 | 2.8229 | 0.0564 | -0.6715 | 4.1618 | 0.0901 |
| reb | 44 | 1.8567 | 0.0388 | +0.5088 | 1.4187 | 0.1887 |
| tov | 44 | 1.2105 | 0.0360 | +0.1005 | 0.6569 | 0.3571 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 55 | 1.4907 | 0.0666 | +0.2843 | 1.5693 |
| core | 45 | 1.9690 | 0.0706 | -0.4218 | 2.0666 |
| fringe | 20 | 0.9189 | 0.0387 | +0.7955 | 0.8696 |
| inactive_risk | 15 | 1.0868 | 0.0292 | +0.3965 | 0.7635 |
| rotation | 30 | 1.8347 | 0.0568 | -0.7112 | 1.3421 |
| starter | 55 | 2.1591 | 0.0674 | +0.0037 | 2.0751 |

## Market-line scoring (non-push rows)

- non-push rows = 400
- model logloss = 0.7774
- model brier  = 0.2832

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
