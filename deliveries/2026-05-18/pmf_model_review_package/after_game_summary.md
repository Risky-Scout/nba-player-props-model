# After-game scoring — 2026-05-18

## Aggregate PMF metrics

- n = 168
- NLL mean = 3.5364
- RPS mean = 0.0772
- mean error = -2.1244
- |mean error| = 4.4000
- outcome prob assigned mean = 0.1559

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 14 | 2.1728 | 0.0520 | -0.6630 | 1.7711 | 0.2025 |
| blk | 14 | 1.6690 | 0.0663 | -0.5466 | 0.8355 | 0.4008 |
| fg3m | 14 | 5.2433 | 0.0703 | -0.7452 | 1.3313 | 0.2298 |
| pa | 14 | 3.9398 | 0.0619 | -3.5008 | 7.7437 | 0.0399 |
| pr | 14 | 4.6769 | 0.0794 | -4.4808 | 10.2251 | 0.0335 |
| pra | 14 | 4.7070 | 0.0695 | -5.1438 | 10.4990 | 0.0345 |
| pts | 14 | 3.9545 | 0.0738 | -2.8378 | 7.5205 | 0.0404 |
| ra | 14 | 4.3280 | 0.0755 | -2.3059 | 4.8188 | 0.0744 |
| reb | 14 | 3.7919 | 0.0977 | -1.6430 | 3.6326 | 0.1114 |
| stl | 14 | 2.0374 | 0.1096 | -1.0601 | 1.2233 | 0.2438 |
| stocks | 14 | 2.7295 | 0.0793 | -1.6067 | 1.8827 | 0.1567 |
| tov | 14 | 3.1869 | 0.0907 | -0.9595 | 1.3166 | 0.3032 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| core | 84 | 3.4738 | 0.0777 | -1.4983 | 5.0842 |
| rotation | 60 | 3.8955 | 0.0787 | -3.3303 | 4.3682 |
| starter | 24 | 2.8578 | 0.0716 | -1.3011 | 2.0848 |

## Market-line scoring (non-push rows)

- non-push rows = 2,185
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
