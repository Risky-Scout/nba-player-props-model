# After-game scoring — 2026-06-13

## Aggregate PMF metrics

- n = 192
- NLL mean = 2.3587
- RPS mean = 0.0749
- mean error = +0.5481
- |mean error| = 3.0337
- outcome prob assigned mean = 0.2109

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 16 | 1.8553 | 0.0535 | +0.8759 | 1.3914 | 0.2095 |
| blk | 16 | 1.0477 | 0.1033 | -0.3147 | 0.6524 | 0.5351 |
| fg3m | 16 | 1.6417 | 0.1351 | -0.0542 | 1.0502 | 0.2871 |
| pa | 16 | 3.5017 | 0.0611 | +2.5717 | 6.3998 | 0.0500 |
| pr | 16 | 3.5267 | 0.0589 | +1.1229 | 6.5203 | 0.0425 |
| pra | 16 | 3.6735 | 0.0567 | +1.9988 | 6.8600 | 0.0393 |
| pts | 16 | 3.2994 | 0.0726 | +1.6958 | 6.0061 | 0.0669 |
| ra | 16 | 2.4572 | 0.0480 | +0.3030 | 2.3902 | 0.1145 |
| reb | 16 | 2.3602 | 0.0624 | -0.5729 | 2.1247 | 0.1338 |
| stl | 16 | 1.2373 | 0.0915 | -0.2894 | 0.8299 | 0.4105 |
| stocks | 16 | 1.5871 | 0.0769 | -0.6061 | 1.1195 | 0.3078 |
| tov | 16 | 2.1169 | 0.0794 | -0.1529 | 1.0603 | 0.3341 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 48 | 1.6340 | 0.0453 | +0.9376 | 2.1125 |
| core | 24 | 2.6234 | 0.0862 | -2.8917 | 3.1479 |
| rotation | 12 | 1.6628 | 0.0393 | +1.8227 | 1.8227 |
| starter | 108 | 2.6994 | 0.0896 | +0.9978 | 3.5524 |

## Market-line scoring (non-push rows)

- non-push rows = 2,837
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
