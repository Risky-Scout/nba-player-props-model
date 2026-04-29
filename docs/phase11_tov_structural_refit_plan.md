# Phase 11 — Structural TOV refit plan

## Verdict on Phase 10D / 10D.2 overlays

**Phase 10D and Phase 10D.2 TOV overlays are not production-safe.** They
shall not be wired into `src/nba_props_model/pipelines/predict.py`,
`scripts/export_live_pmf_slate.py`, `scripts/build_daily_pmf_delivery.py`,
or any production runner. Every emitted TOV PMF carries
`tov_status="current_phase8"` to make this verdict auditable in every
delivery.

Why:

- **Phase 10D** (`rolling_selective_hybrid_expanding`, ref:
  `docs/phase10d_independent_validation_report.md`) — improved overall
  NLL (1.461 → 1.410) and `p0_err` (+0.121 → +0.033) on the 2026-03-01 →
  2026-03-17 independent window, but absolute mean bias worsened
  (0.011 → 0.048). Per-block traces show the hybrid selected
  `rolling_p0_plus_pos` for starter and core in every March block;
  uniform conditional-positive renormalization of starter/core PMFs
  inflated the mean by ~0.07 because their conditional-positive mean is
  ≥ 2 turnovers. **9 / 15 acceptance gates passed; G3 (|bias|), G7 (BFR
  bias), G9/G10 (starter/core bias) failed.**

- **Phase 10D.2** (`docs/phase10d2_tov_mean_preserving_report.md`) —
  built five mean-preserving variants (exponential-tilt mean preservation,
  k=1-only redistribution, starter/core-guarded, role-selective
  conservative hybrid, convex blend with role caps). Two variants
  (`c3_starter_guarded`, `c4_role_selective_conservative`) pass all 15
  gates on the broader Phase 10C walk-forward span (48,492 rows,
  |bias| 0.054 → 0.017) but **none pass on the Phase 10D independent
  window** under strict no-worsen gates. The fundamental obstruction:
  on the narrow March window the current PMF's |bias| is anomalously
  small (0.011) so any p0 fix that moves mean — even by 0.0002 — fails
  G3, and any tilt that preserves mean must distort the conditional
  shape, which trips G5 P≥2.

The structural defect lives in the Phase 8 TOV head, not in any post-hoc
calibration layer. The rest of this document plans the next refit.

---

## TOV root defect

The Phase 8 TOV head is trained as a marginal cross-entropy classifier
over the count support. Three observed pathologies converge:

1. **Systematic p0 zero-inflation.** Across all role buckets, predicted
   `P(TOV = 0)` is too high by 0.10–0.15 (Phase 10A.2 / 10B forensics,
   Phase 10C rolling diagnostics).
2. **Mean-bias / p0-fix tradeoff.** Lowering p0 by Δ and uniformly
   rescaling the conditional-positive PMF inflates the unconditional
   mean by `Δ · cond_pos_mean`. For starter/core, `cond_pos_mean ≥ 2.4`
   so a 0.10 p0 fix produces a 0.24 mean inflation.
3. **Role-bucket bias drift.** Per-role bias direction drifts over the
   season; bench/fringe/rotation/inactive_risk PMFs carry the largest
   residual bias and the bias direction shifts.

Post-hoc p0 repair alone cannot reconcile (1)–(3) simultaneously while
preserving per-role mean bias. The next move is a structural change to
the head.

---

## Refit design

### 1. Zero-inflated TOV head

Replace the marginal cross-entropy classifier with a two-component
zero-inflated head:

```
P(TOV = 0)         = p0
P(TOV = k | k≥1)   = q_k        (conditional-positive PMF)
P(TOV = k)         = p0 · 1[k=0] + (1 − p0) · q_k · 1[k≥1]
```

- **`p0` head**: sigmoid output trained jointly on the same feature
  bundle, with binary cross-entropy against `(TOV == 0)`.
- **`q_k` head**: softmax over `k = 1, 2, …, K_max` trained only on
  rows where `TOV ≥ 1` using categorical cross-entropy. Truncate at
  `K_max = 12` (Phase 8 verified upper support, ref `MAX_K = 13` in
  `scripts/phase10c_tov_rolling_zero_inflated_pmf.py`).
- Joint loss is a weighted sum (recommend `1.0 · BCE_p0 +
  1.0 · CE_qk` with the conditional CE only over positive rows).

This gives the marginal `P(TOV=0)` a direct gradient against the
observed zero rate, instead of fitting it implicitly through a
13-class softmax that cannot tell zero from positive.

### 2. Minutes-aware features fed to both heads

Both `p0` and `q_k` heads must receive minutes signal at training time.
Pass-through features:

- `minutes_mean`
- `minutes_q10`, `minutes_q25`, `minutes_q50`, `minutes_q75`,
  `minutes_q90` (already produced by the minutes pipeline; see
  `src/nba_props_model/models/minutes.py`)
- `p_inactive`
- `role_bucket` (one-hot over six roles)
- `role_starter`, `role_core`, `role_rotation`, `role_bench`,
  `role_fringe`, `role_inactive_risk` flags

The current Phase 8 TOV head consumes a feature bundle that is
minutes-thin. The 10A–10C forensics show that bench / fringe /
rotation / inactive_risk PMFs carry the largest residual bias and
that bias drifts over the season — minutes features at training time
let the head learn the right per-minutes shape rather than relying
on a post-hoc role-bucket CDF stretch.

### 3. Conditional-positive TOV head

Train a TOV-specific `q_k` head only on `TOV ≥ 1` rows. The shape
`q_1, q_2, q_3, q_4, q_{≥5}` is well-defined on this restricted
sample and carries information that the full-support marginal head
cannot expose because zero rows dominate the gradient.

### 4. Recombination at inference

```
  p_pmf[0]  = p0
  p_pmf[k]  = (1 − p0) · q_k     for k = 1 … K_max
```

Numerically, enforce non-negativity, renormalize, and validate
(Σp = 1, finite, non-negative) at write time. The PMF written to
`predictions/all_props_{date}.parquet` is this recombined PMF, and
`scripts/export_live_pmf_slate.py` consumes it as before.

### 5. Rolling calibrator after refit

Once the refit produces new OOF PMFs, re-evaluate Phase 10D / 10D.2
overlays on the rebuilt PMFs. The conditional-positive shape will be
different and the overlay may then satisfy the Phase 10D.2 gates that
were unsatisfiable on the current PMFs. Do not run this evaluation
until the refit OOFs exist.

---

## OOF / training-data plan

- **Re-run Phase 8 OOF** with the new head architecture, holding the
  current splits constant (15 folds; same `pmf-calibration/` and
  `phase8-outputs/artifacts/` layout under `/tmp/phase8_full_vectorized_success/`).
- **Walk-forward eval only.** No part of the validation window
  (2026-03-01 → 2026-03-17) leaks into training, calibration, or
  hyperparameter selection.
- **Calibrators trained per role bucket** as today; confirm the
  zero-inflated decomposition does not change the per-role calibrator
  contract.

---

## Acceptance gates for the structural refit

A refit candidate ships only if it passes **every** gate below on the
Phase 10C walk-forward span **and** on the Phase 10D independent window.

| gate | rule |
|---|---|
| **G1** | Overall TOV NLL improves vs current Phase 8 PMFs. |
| **G2** | Overall TOV RPS improves vs current. |
| **G3** | Overall absolute mean bias does not worsen. |
| **G4** | Overall absolute p0 error improves. |
| **G5** | Starter and core absolute mean bias do not worsen by more than 0.015. |
| **G6** | Starter and core NLL do not materially worsen (Δ ≤ 0.005). |
| **G7** | Bench / fringe / rotation aggregate NLL **or** RPS improves. |
| **G8** | Bench / fringe / rotation aggregate absolute mean bias does not worsen. |
| **G9** | No role bucket with `n ≥ 100` worsens absolute mean bias by more than 0.02. |
| **G10** | All emitted PMFs valid (`Σp = 1` to 1e-6, non-negative, finite). |
| **G11** | Walk-forward calibration only — no eval-window rows in any calibrator fit. |
| **G12** | Repeat all gates on a third independent window (cross-season or cross-month) before production wiring. |

These gates are tighter than the Phase 10D / 10D.2 gates on G5 and G9
because the structural refit must not need a post-hoc overlay to clear
them. If the refit only clears the gates with an overlay, that overlay
is itself subject to a separate Phase 10-style validation pass.

---

## Production-wiring contract

After all 12 gates pass:

1. **Pin a model version.** Tag the refit with a phase identifier
   (e.g. `phase11_zinb`) and embed it in `model_version` strings in
   every delivery (see `docs/daily_pmf_delivery_spec.md` §2.6).
2. **Switch `tov_status`** in the daily-delivery runner from
   `current_phase8` to `phase11_zinb` only after the model version is
   pinned and the refit calibrators are committed.
3. **Refit calibrators ship in a separate commit** from any post-hoc
   overlay. The default is *no overlay*; an overlay ships only after
   independent re-validation on the refit's OOF rows.
4. **Honest framing**: the structural refit does not authorize
   re-running Phase 10D / 10D.2 overlays under the same gate suite as
   before; rebuilt PMFs warrant a fresh validation pass on a fresh
   window.

---

## Out-of-scope for Phase 11A

Phase 11A delivers code/docs only:

- `docs/daily_pmf_delivery_spec.md`
- `scripts/build_daily_pmf_delivery.py`
- `scripts/score_daily_pmf_delivery_after_game.py`
- `docs/phase11_tov_structural_refit_plan.md` (this file)

Phase 11A does **not**:

- run a refit,
- ship overlays,
- modify `src/nba_props_model/pipelines/predict.py`,
- modify Phase 8 calibrators,
- re-run Phase 8,
- call the Odds API.

The refit (Phase 11B+) is gated by approvals on this plan.

---

## Honest framing

This plan is a contract for the next model iteration. It is not a
benchmark and it has not been validated against any new training data.
TOV PMFs in production today carry the systematic p0 zero-inflation and
mean-bias tradeoff documented in
`docs/phase10d2_tov_mean_preserving_report.md`. The daily delivery
runner emits those TOV PMFs as-is, with `tov_status="current_phase8"`,
until the structural refit clears the 12 gates above.
