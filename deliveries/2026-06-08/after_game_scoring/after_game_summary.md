# After-game scoring — 2026-06-08

## Aggregate PMF metrics

- n = 144
- NLL mean = 2.2942
- RPS mean = 0.0797
- mean error = +0.1188
- |mean error| = 2.6370
- outcome prob assigned mean = 0.1896

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 12 | 2.4223 | 0.0717 | -0.0900 | 1.7340 | 0.1532 |
| blk | 12 | 1.3317 | 0.1517 | -0.4487 | 0.8344 | 0.4378 |
| fg3m | 12 | 1.5213 | 0.1620 | -0.1722 | 0.9145 | 0.2679 |
| pa | 12 | 3.3439 | 0.0490 | +0.3511 | 5.4490 | 0.0437 |
| pr | 12 | 3.1727 | 0.0409 | +0.8280 | 5.2664 | 0.0461 |
| pra | 12 | 3.3324 | 0.0426 | +0.7379 | 5.8160 | 0.0427 |
| pts | 12 | 3.1709 | 0.0533 | +0.4411 | 4.6219 | 0.0488 |
| ra | 12 | 2.4505 | 0.0457 | +0.2968 | 2.2768 | 0.1100 |
| reb | 12 | 2.1704 | 0.0492 | +0.3869 | 1.7211 | 0.1415 |
| stl | 12 | 1.2315 | 0.1139 | -0.1522 | 0.7861 | 0.3968 |
| stocks | 12 | 1.7616 | 0.1140 | -0.5822 | 1.3091 | 0.2608 |
| tov | 12 | 1.6207 | 0.0627 | -0.1704 | 0.9151 | 0.3260 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 12 | 1.6655 | 0.0341 | +0.4890 | 0.8704 |
| core | 24 | 2.0246 | 0.0662 | -1.8000 | 2.2523 |
| rotation | 12 | 2.0206 | 0.0662 | +1.2161 | 2.1165 |
| starter | 96 | 2.4743 | 0.0905 | +0.4151 | 3.0191 |

## Market-line scoring (non-push rows)

- non-push rows = 2,352
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
