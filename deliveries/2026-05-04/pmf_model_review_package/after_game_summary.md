# After-game scoring — 2026-05-04

## Aggregate PMF metrics

- n = 48
- NLL mean = 2.3346
- RPS mean = 0.0799
- mean error = -0.4689
- |mean error| = 2.6373
- outcome prob assigned mean = 0.1141

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 9 | 2.1932 | 0.0606 | +0.2896 | 1.8235 | 0.1240 |
| fg3m | 10 | 1.8356 | 0.0428 | -0.1751 | 1.1852 | 0.1920 |
| pts | 12 | 2.8778 | 0.1290 | -2.1433 | 4.8995 | 0.0329 |
| reb | 17 | 2.3196 | 0.0773 | +0.1385 | 2.3253 | 0.1203 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 6 | 1.7982 | 0.0464 | +1.0578 | 1.6760 |
| rotation | 14 | 2.7682 | 0.1143 | -2.0484 | 3.1040 |
| starter | 28 | 2.2327 | 0.0699 | -0.0063 | 2.6099 |
## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
