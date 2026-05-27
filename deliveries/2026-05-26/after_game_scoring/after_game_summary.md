# After-game scoring — 2026-05-26

## Aggregate PMF metrics

- n = 180
- NLL mean = 2.3946
- RPS mean = 0.0809
- mean error = -0.7913
- |mean error| = 3.0799
- outcome prob assigned mean = 0.1806

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 15 | 2.0379 | 0.0610 | -0.4731 | 1.4594 | 0.1752 |
| blk | 15 | 0.8600 | 0.0637 | +0.0004 | 0.4863 | 0.5488 |
| fg3m | 15 | 1.8020 | 0.1709 | -0.1892 | 1.0883 | 0.2152 |
| pa | 15 | 3.4765 | 0.0620 | -1.6736 | 6.0540 | 0.0410 |
| pr | 15 | 3.5504 | 0.0613 | -1.3120 | 6.9004 | 0.0360 |
| pra | 15 | 3.6096 | 0.0583 | -1.7851 | 7.0732 | 0.0362 |
| pts | 15 | 3.3379 | 0.0784 | -1.2005 | 5.9149 | 0.0434 |
| ra | 15 | 2.5078 | 0.0435 | -0.5846 | 2.3903 | 0.1161 |
| reb | 15 | 2.2072 | 0.0519 | -0.1115 | 1.8823 | 0.1499 |
| stl | 15 | 1.7142 | 0.1480 | -0.8095 | 1.1995 | 0.3233 |
| stocks | 15 | 1.7469 | 0.0800 | -0.8154 | 1.3141 | 0.2503 |
| tov | 15 | 1.8847 | 0.0920 | -0.5409 | 1.1963 | 0.2316 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 12 | 1.7491 | 0.0332 | +1.0190 | 1.2187 |
| core | 12 | 2.2668 | 0.0721 | -1.4453 | 1.7124 |
| rotation | 84 | 2.3189 | 0.0795 | -1.7614 | 2.9777 |
| starter | 72 | 2.6118 | 0.0920 | +0.1479 | 3.7374 |

## Market-line scoring (non-push rows)

- non-push rows = 2,512
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
