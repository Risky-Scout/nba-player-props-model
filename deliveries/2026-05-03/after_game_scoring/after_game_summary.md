# After-game scoring — 2026-05-03

## Aggregate PMF metrics

- n = 46
- NLL mean = 3.2537
- RPS mean = 0.0820
- mean error = -1.5611
- |mean error| = 3.1144
- outcome prob assigned mean = 0.1010

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 8 | 2.5153 | 0.0800 | -1.4119 | 2.1808 | 0.0926 |
| fg3m | 12 | 5.9621 | 0.0541 | -0.4503 | 1.3267 | 0.1840 |
| pts | 13 | 2.0599 | 0.1076 | -5.5823 | 5.8749 | 0.0294 |
| reb | 13 | 2.4020 | 0.0833 | +1.3430 | 2.5786 | 0.1011 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 8 | 5.5231 | 0.0905 | +0.3430 | 2.6930 |
| rotation | 16 | 3.9044 | 0.1009 | -2.4702 | 3.3656 |
| starter | 22 | 1.9553 | 0.0651 | -1.5924 | 3.0849 |

## Market-line scoring (non-push rows)

- non-push rows = 489
- model logloss = 0.6400
- model brier  = 0.2273

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
