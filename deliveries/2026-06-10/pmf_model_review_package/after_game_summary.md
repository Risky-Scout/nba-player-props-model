# After-game scoring — 2026-06-10

## Aggregate PMF metrics

- n = 180
- NLL mean = 2.1370
- RPS mean = 0.0720
- mean error = +0.0540
- |mean error| = 2.8240
- outcome prob assigned mean = 0.2168

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 15 | 1.5296 | 0.0391 | +0.0459 | 0.9887 | 0.2454 |
| blk | 15 | 0.8059 | 0.0667 | -0.1431 | 0.5852 | 0.5917 |
| fg3m | 15 | 1.4717 | 0.1644 | -0.5950 | 1.3167 | 0.3169 |
| pa | 15 | 3.3270 | 0.0595 | +0.4921 | 6.2742 | 0.0455 |
| pr | 15 | 3.3388 | 0.0526 | +0.5759 | 6.2738 | 0.0420 |
| pra | 15 | 3.4327 | 0.0502 | +0.6217 | 6.4273 | 0.0391 |
| pts | 15 | 3.1931 | 0.0736 | +0.4463 | 5.8827 | 0.0575 |
| ra | 15 | 2.1745 | 0.0361 | +0.1754 | 1.8126 | 0.1205 |
| reb | 15 | 1.7938 | 0.0348 | +0.1296 | 1.1713 | 0.1839 |
| stl | 15 | 1.3584 | 0.1350 | -0.3552 | 0.9350 | 0.3897 |
| stocks | 15 | 1.6408 | 0.0839 | -0.5000 | 1.1859 | 0.2697 |
| tov | 15 | 1.5781 | 0.0685 | -0.2462 | 1.0342 | 0.2999 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 36 | 1.6599 | 0.0381 | +1.5779 | 2.1127 |
| core | 36 | 2.1933 | 0.0898 | +0.1568 | 2.6546 |
| rotation | 12 | 1.7542 | 0.0518 | +3.4203 | 3.4203 |
| starter | 96 | 2.3427 | 0.0806 | -0.9769 | 3.0797 |

## Market-line scoring (non-push rows)

- non-push rows = 2,775
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
