# After-game scoring — 2026-05-30

## Aggregate PMF metrics

- n = 192
- NLL mean = 2.4735
- RPS mean = 0.0738
- mean error = +0.0988
- |mean error| = 2.8611
- outcome prob assigned mean = 0.1956

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 16 | 1.6613 | 0.0408 | +0.1442 | 1.2548 | 0.2225 |
| blk | 16 | 0.9008 | 0.0573 | +0.0981 | 0.5382 | 0.5621 |
| fg3m | 16 | 3.2601 | 0.1477 | -0.4851 | 1.2710 | 0.2571 |
| pa | 16 | 3.2416 | 0.0509 | +0.0084 | 5.0256 | 0.0469 |
| pr | 16 | 3.4742 | 0.0581 | +0.4911 | 6.2005 | 0.0403 |
| pra | 16 | 3.6819 | 0.0608 | +0.6353 | 7.2288 | 0.0360 |
| pts | 16 | 3.1434 | 0.0589 | -0.1358 | 4.0713 | 0.0502 |
| ra | 16 | 3.1496 | 0.0668 | +0.7712 | 3.4870 | 0.0843 |
| reb | 16 | 2.5700 | 0.0692 | +0.6269 | 2.3763 | 0.1276 |
| stl | 16 | 1.4219 | 0.1222 | -0.4468 | 0.8440 | 0.3246 |
| stocks | 16 | 1.5119 | 0.0748 | -0.3463 | 1.0517 | 0.3013 |
| tov | 16 | 1.6653 | 0.0778 | -0.1757 | 0.9835 | 0.2944 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 12 | 1.4496 | 0.0264 | +2.6543 | 2.6543 |
| core | 24 | 2.8555 | 0.1097 | +1.2980 | 4.6456 |
| rotation | 96 | 2.5505 | 0.0710 | -0.8086 | 2.5860 |
| starter | 60 | 2.4023 | 0.0733 | +0.5599 | 2.6286 |

## Market-line scoring (non-push rows)

- non-push rows = 2,777
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
