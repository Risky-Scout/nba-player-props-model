# After-game scoring — 2026-04-29

## Aggregate PMF metrics

- n = 32
- NLL mean = 2.9684
- RPS mean = 0.0748
- mean error = -1.2708
- |mean error| = 2.1096
- outcome prob assigned mean = 0.1432

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 4 | 2.2234 | 0.0603 | -0.5367 | 1.5712 | 0.1196 |
| fg3m | 4 | 7.9401 | 0.0696 | -1.1789 | 1.5407 | 0.1963 |
| pts | 5 | 2.7707 | 0.1279 | -2.9892 | 4.1692 | 0.0457 |
| reb | 8 | 2.6250 | 0.0984 | -1.8621 | 2.5769 | 0.1166 |
| tov | 11 | 1.7710 | 0.0407 | -0.3602 | 1.2362 | 0.1960 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 2 | 2.0598 | 0.0467 | -1.2885 | 1.2885 |
| rotation | 17 | 2.4170 | 0.0909 | -1.5622 | 2.5742 |
| starter | 2 | 15.1494 | 0.1536 | -3.7851 | 3.7851 |

## Market-line scoring (non-push rows)

- non-push rows = 448
- model logloss = 0.7499
- model brier  = 0.2678

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
