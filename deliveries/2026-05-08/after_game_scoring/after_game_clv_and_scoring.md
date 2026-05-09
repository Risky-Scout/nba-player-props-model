# After-game scoring — 2026-05-08

## Aggregate PMF metrics

- n = 230
- NLL mean = 1.6869
- RPS mean = 0.0617
- mean error = +0.0056
- |mean error| = 1.8004
- outcome prob assigned mean = 0.2987

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 46 | 1.5257 | 0.0435 | -0.0915 | 1.3289 | 0.3154 |
| fg3m | 46 | 1.0057 | 0.1166 | +0.0325 | 0.6953 | 0.4942 |
| pts | 46 | 2.6608 | 0.0549 | +0.2565 | 4.2659 | 0.1164 |
| reb | 46 | 2.0720 | 0.0558 | -0.4030 | 1.9606 | 0.1796 |
| tov | 46 | 1.1701 | 0.0380 | +0.2337 | 0.7514 | 0.3879 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 55 | 1.2458 | 0.0473 | +0.5098 | 1.4668 |
| core | 50 | 2.4642 | 0.1027 | -1.5732 | 3.0474 |
| fringe | 30 | 0.7814 | 0.0133 | +0.9004 | 0.9459 |
| inactive_risk | 15 | 0.8880 | 0.0278 | +0.9375 | 1.1022 |
| rotation | 25 | 1.6874 | 0.0741 | +0.8789 | 1.3185 |
| starter | 55 | 2.1328 | 0.0690 | -0.2024 | 1.8760 |

## Market-line scoring (non-push rows)

- non-push rows = 578
- model logloss = 0.9083
- model brier  = 0.3079

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
