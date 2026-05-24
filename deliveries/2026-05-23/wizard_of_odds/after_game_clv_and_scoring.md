# After-game scoring — 2026-05-23

## Aggregate PMF metrics

- n = 180
- NLL mean = 2.2561
- RPS mean = 0.0417
- mean error = +0.0074
- |mean error| = 2.4827
- outcome prob assigned mean = 0.1972

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 15 | 1.7101 | 0.0311 | -0.0847 | 1.0929 | 0.2303 |
| blk | 15 | 0.7943 | 0.0290 | +0.2139 | 0.5705 | 0.5763 |
| fg3m | 15 | 1.3694 | 0.0368 | +0.1413 | 0.9083 | 0.3301 |
| pa | 15 | 3.0775 | 0.0296 | -0.3024 | 4.3146 | 0.0495 |
| pr | 15 | 3.2574 | 0.0337 | +0.2968 | 5.2458 | 0.0430 |
| pra | 15 | 3.3146 | 0.0312 | +0.2121 | 5.5003 | 0.0407 |
| pts | 15 | 3.1340 | 0.0350 | -0.2177 | 4.1783 | 0.0488 |
| ra | 15 | 2.5442 | 0.0334 | +0.4298 | 2.5008 | 0.0984 |
| reb | 15 | 2.2100 | 0.0405 | +0.5145 | 1.8224 | 0.1297 |
| stl | 15 | 1.8451 | 0.0741 | -0.5301 | 1.0162 | 0.3416 |
| stocks | 15 | 1.9245 | 0.0461 | -0.3162 | 1.2307 | 0.2453 |
| tov | 15 | 1.8920 | 0.0803 | -0.2686 | 1.4111 | 0.2329 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 12 | 1.7366 | 0.0248 | +2.9020 | 2.9020 |
| core | 36 | 2.4255 | 0.0469 | -0.6502 | 2.7514 |
| rotation | 48 | 1.9398 | 0.0290 | +2.1490 | 2.3856 |
| starter | 84 | 2.4385 | 0.0492 | -1.3480 | 2.3631 |

## Market-line scoring (non-push rows)

- non-push rows = 2,474
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
