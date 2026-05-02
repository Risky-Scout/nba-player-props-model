# After-game scoring — 2026-05-01

## Aggregate PMF metrics

- n = 69
- NLL mean = 2.2529
- RPS mean = 0.0909
- mean error = -1.7566
- |mean error| = 3.4146
- outcome prob assigned mean = 0.1078

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 16 | 2.4780 | 0.0850 | -0.0518 | 2.4794 | 0.1037 |
| fg3m | 11 | 1.4112 | 0.0297 | +0.4621 | 1.0660 | 0.2688 |
| pts | 18 | 2.2090 | 0.1358 | -5.0003 | 6.9905 | 0.0233 |
| reb | 24 | 2.5215 | 0.0894 | -1.4771 | 2.4327 | 0.1001 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 6 | 2.1231 | 0.0597 | +0.7209 | 1.7851 |
| rotation | 21 | 2.5952 | 0.1304 | -2.5262 | 4.3610 |
| starter | 42 | 2.1003 | 0.0757 | -1.7257 | 3.1742 |

## Market-line scoring (non-push rows)

- non-push rows = 1,202
- model logloss = 0.6928
- model brier  = 0.2492

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
