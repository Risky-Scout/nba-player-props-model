# Phase 10C — Rolling TOV zero-inflated full-PMF repair report

**OOF horizon**: 49,525 TOV rows, dates 2024-10-23 → 2026-03-31.
**Evaluation**: rolling walk-forward; train = prior N days, eval = next 7-day block. Windowings tested: 30d, 60d, 90d, expanding-past.
**Gates**: 12 acceptance-gate concepts (G1–G12), expanded to 15 sub-checks per candidate.

## Q1 — Does rolling p0 repair solve TOV zero-inflation?

| windowing | n_eval | current p0_err | rolling_global_p0 p0_err | rolling_role_p0 p0_err | rolling_p0_plus_pos p0_err |
|---|---:|---:|---:|---:|---:|
| 30d | 47,871 | +0.126 | -0.003 | -0.003 | -0.003 |
| 60d | 48,492 | +0.127 | -0.002 | -0.002 | -0.002 |
| 90d | 48,492 | +0.127 | -0.002 | -0.002 | -0.002 |
| expanding | 48,492 | +0.127 | +0.003 | +0.003 | +0.003 |

## Q2 — Which candidate wins?

**Winner**: `rolling_selective_hybrid` on **expanding** windowing — NLL 1.4380, RPS 0.0500, |bias| 0.010.

Other 12-of-12 gate-passing candidates:
- `rolling_selective_hybrid` (90d): NLL 1.4579, |bias| 0.014

## Q3 — Did it improve full PMF quality (not just line probs)?

YES — full PMF metrics show NLL Δ -0.0446, RPS Δ -0.00141, PIT mean 0.512, PIT std 0.283.

## Q4 — Did it protect starter/core?

- **starter** (n=10,701): NLL Δ -0.0455, |bias| Δ -0.0619 (holdout |bias|: current 0.123 → candidate 0.061)
- **core** (n=12,611): NLL Δ -0.0600, |bias| Δ -0.0572 (holdout |bias|: current 0.060 → candidate 0.002)

## Q5 — Did it improve bench/fringe/rotation?

- **bench** (n=8,038): NLL Δ -0.0348, |bias| Δ +0.0015
- **fringe** (n=3,104): NLL Δ +0.0243, |bias| Δ -0.0034
- **rotation** (n=10,788): NLL Δ -0.0196, |bias| Δ -0.0045

## Q6 — Are role-bucket bias drifts still present?

Per-role |mean bias| under current vs winning candidate (expanding, `rolling_selective_hybrid`):

| role | n | current |bias| | candidate |bias| | Δ |
|---|---:|---:|---:|---:|
| inactive_risk | 3,250 | 0.112 | 0.015 | -0.098 |
| fringe | 3,104 | 0.015 | 0.012 | -0.003 |
| bench | 8,038 | 0.007 | 0.009 | +0.002 |
| rotation | 10,788 | 0.007 | 0.002 | -0.004 |
| core | 12,611 | 0.060 | 0.002 | -0.057 |
| starter | 10,701 | 0.123 | 0.061 | -0.062 |

## Q7 — Safe to convert into a production TOV PMF cal layer?

YES — `rolling_selective_hybrid` on **expanding** windowing passed all 12 gates on a fully walk-forward evaluation (every block uses train data strictly prior to the evaluation block).

**Recommendation**: wire this candidate as a runtime TOV PMF calibration layer using the same windowing scheme. Refit on the trailing window before each eval block in production.

## Q8 — If not, what base-model structural change is required?

Not applicable — a rolling repair winner exists.

## Honest framing

This is a leakage-safe, market-data-free, rolling walk-forward analysis on 49,525 TOV OOF rows spanning 2024-10-23 → 2026-03-31. No Odds-API call was made. No production wiring is performed by this script — it only produces calibrated PMF candidates and gate verdicts. Production wiring requires a passing 12-gate verdict on this rolling evaluation **and** a second-window or second-season replication.
