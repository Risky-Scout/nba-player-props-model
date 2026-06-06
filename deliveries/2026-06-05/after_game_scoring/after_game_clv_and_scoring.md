# After-game scoring — 2026-06-05

## Aggregate PMF metrics

- n = 192
- NLL mean = 2.2841
- RPS mean = 0.0806
- mean error = -0.3464
- |mean error| = 2.3464
- outcome prob assigned mean = 0.1803

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 16 | 1.8174 | 0.0481 | -0.4075 | 0.9703 | 0.2443 |
| blk | 16 | 1.3570 | 0.1425 | -0.4636 | 0.7557 | 0.4108 |
| fg3m | 16 | 1.3953 | 0.1696 | -0.3204 | 0.9429 | 0.3090 |
| pa | 16 | 3.1023 | 0.0427 | -0.3121 | 4.6655 | 0.0558 |
| pr | 16 | 3.1962 | 0.0385 | +0.0893 | 4.7482 | 0.0505 |
| pra | 16 | 3.2837 | 0.0406 | -0.3182 | 5.1938 | 0.0476 |
| pts | 16 | 3.0589 | 0.0496 | +0.0954 | 4.1760 | 0.0577 |
| ra | 16 | 2.5608 | 0.0477 | -0.4136 | 2.0700 | 0.1186 |
| reb | 16 | 2.0728 | 0.0413 | -0.0061 | 1.5023 | 0.1469 |
| stl | 16 | 1.4954 | 0.1367 | -0.5367 | 0.8281 | 0.2887 |
| stocks | 16 | 1.9782 | 0.1206 | -0.9847 | 1.1299 | 0.2054 |
| tov | 16 | 2.0916 | 0.0892 | -0.5783 | 1.1746 | 0.2278 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| bench | 36 | 1.7777 | 0.0418 | +0.7240 | 1.4353 |
| core | 24 | 1.8351 | 0.0466 | -0.0226 | 1.7512 |
| rotation | 24 | 1.8653 | 0.0739 | -0.5519 | 1.6772 |
| starter | 108 | 2.6458 | 0.1026 | -0.7294 | 2.9312 |

## Market-line scoring (non-push rows)

- non-push rows = 2,782
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
