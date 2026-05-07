# After-game scoring — 2026-05-06

## Aggregate PMF metrics

- n = 86
- NLL mean = 1.9547
- RPS mean = 0.0621
- mean error = -0.4885
- |mean error| = 2.0275
- outcome prob assigned mean = 0.1743

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 13 | 1.9667 | 0.0435 | -0.5173 | 1.2028 | 0.1456 |
| fg3m | 14 | 1.6418 | 0.0387 | +0.4514 | 1.3063 | 0.2238 |
| pts | 16 | 2.6963 | 0.1467 | -2.2487 | 5.4724 | 0.0505 |
| reb | 15 | 2.1650 | 0.0571 | +0.1453 | 1.5117 | 0.1284 |
| tov | 28 | 1.5692 | 0.0368 | -0.2788 | 1.0787 | 0.2582 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 6 | 1.9771 | 0.0492 | +0.0185 | 1.3485 |
| rotation | 18 | 2.1736 | 0.0704 | -0.9889 | 2.1385 |
| starter | 34 | 2.1524 | 0.0808 | -0.4858 | 2.8699 |
## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
