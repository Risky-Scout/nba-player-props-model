# After-game scoring — 2026-05-20

## Aggregate PMF metrics

- n = 144
- NLL mean = 2.5290
- RPS mean = 0.0516
- mean error = +0.0210
- |mean error| = 3.1247
- outcome prob assigned mean = 0.1786

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 12 | 2.3295 | 0.0536 | -0.4512 | 1.8078 | 0.1623 |
| blk | 12 | 1.2600 | 0.0472 | +0.0638 | 0.7889 | 0.4681 |
| fg3m | 12 | 1.5202 | 0.0590 | -0.0634 | 1.4179 | 0.2800 |
| pa | 12 | 3.3733 | 0.0393 | -0.2781 | 5.3595 | 0.0460 |
| pr | 12 | 3.4321 | 0.0406 | +0.5508 | 6.1198 | 0.0396 |
| pra | 12 | 3.7534 | 0.0419 | +0.0996 | 7.5334 | 0.0353 |
| pts | 12 | 3.2011 | 0.0402 | +0.1731 | 4.4310 | 0.0495 |
| ra | 12 | 3.3929 | 0.0592 | -0.0735 | 4.0115 | 0.0671 |
| reb | 12 | 2.6643 | 0.0612 | +0.3777 | 2.5358 | 0.1239 |
| stl | 12 | 1.3091 | 0.0472 | +0.1515 | 0.7675 | 0.3719 |
| stocks | 12 | 1.8304 | 0.0440 | +0.2153 | 1.3620 | 0.2306 |
| tov | 12 | 2.2820 | 0.0860 | -0.5136 | 1.3619 | 0.2686 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| core | 48 | 2.8706 | 0.0624 | +3.9353 | 4.3390 |
| rotation | 48 | 2.1053 | 0.0359 | -1.7592 | 2.3173 |
| starter | 48 | 2.6113 | 0.0565 | -2.1132 | 2.7179 |

## Market-line scoring (non-push rows)

- non-push rows = 2,111
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
