# After-game scoring — 2026-05-28

## Aggregate PMF metrics

- n = 168
- NLL mean = 2.4632
- RPS mean = 0.0781
- mean error = +1.8632
- |mean error| = 3.1230
- outcome prob assigned mean = 0.1780

## Per-stat

| stat | n | NLL | RPS | mean_err | |mean_err| | p_assigned |
|---|---:|---:|---:|---:|---:|---:|
| ast | 14 | 2.1659 | 0.0657 | +0.5355 | 1.8731 | 0.1748 |
| blk | 14 | 0.8998 | 0.0744 | -0.2194 | 0.5682 | 0.5575 |
| fg3m | 14 | 1.8459 | 0.1809 | -0.1372 | 1.0890 | 0.1902 |
| pa | 14 | 3.5762 | 0.0583 | +4.2470 | 6.4392 | 0.0422 |
| pr | 14 | 3.6908 | 0.0591 | +5.2294 | 6.5002 | 0.0412 |
| pra | 14 | 3.9695 | 0.0620 | +5.7649 | 7.4840 | 0.0374 |
| pts | 14 | 3.3874 | 0.0676 | +3.7115 | 5.3160 | 0.0441 |
| ra | 14 | 3.2535 | 0.0661 | +2.0534 | 3.5265 | 0.0748 |
| reb | 14 | 2.4192 | 0.0572 | +1.5179 | 1.9751 | 0.1334 |
| stl | 14 | 1.3148 | 0.1073 | -0.2418 | 0.7342 | 0.3125 |
| stocks | 14 | 1.6443 | 0.0787 | -0.4631 | 1.1661 | 0.2356 |
| tov | 14 | 1.3907 | 0.0596 | +0.3605 | 0.8046 | 0.2929 |

## Per-role bucket

| role | n | NLL | RPS | mean_err | |mean_err| |
|---|---:|---:|---:|---:|---:|
| core | 48 | 2.5828 | 0.0813 | +2.5308 | 3.3826 |
| rotation | 60 | 2.2616 | 0.0715 | +0.4543 | 2.4570 |
| starter | 60 | 2.5690 | 0.0820 | +2.7381 | 3.5814 |

## Market-line scoring (non-push rows)

- non-push rows = 2,489
- model logloss = nan
- model brier  = nan

## Honest framing

Scoring is on the canonical model-only PMF (no market anchoring). TOV PMFs are scored as emitted by the production Phase 8 calibrators with no Phase 10D / 10D.2 overlay applied. The structural TOV refit plan is in `docs/phase11_tov_structural_refit_plan.md`.
