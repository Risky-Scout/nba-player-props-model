# Simulator Overhaul Staged Plan (Spec Only)

## Scope and guardrails

This plan defines a **phased simulator-overhaul track** for prop-specific stochastic
variables and joint-correlation support without a one-shot rewrite.

Hard guardrails:
- keep `.github/workflows/nba_pmf_delivery.yml` as the only canonical workflow
- no merge/promote path changes in this track until validation gates pass
- no fabricated data, no post-outcome features, no leakage shortcuts
- no removal of existing calibration, market, injury, lineup, or role-bucket gates

## Requirements mapping

The implementation must support two requirement families:

1. **Prop-specific stochastic variables**  
   Per-leg random-variable definitions (distribution family, support, hurdle/zero-inflation
   behavior, and conditioning features) for each covered stat/prop type.

2. **Joint-correlation requirements**  
   Multi-leg joint simulation that can express within-player and within-game dependence,
   backed by PSD-safe correlation handling and explicit fallback behavior.

## Phase 0 - Contract freeze and data dictionary

Deliverables:
- define a versioned variable dictionary for each prop type:
  - outcome domain/support
  - conditional mean/dispersion parameterization
  - p0/hurdle contract (when applicable)
  - required feature dependencies
- define joint-correlation contract:
  - allowed leg sets
  - correlation source priority (empirical residual matrix, fallback strategy)
  - PSD repair and sampling reproducibility contract
- pin a simulator API compatibility contract before code changes

Exit criteria:
- schema written and reviewed
- explicit non-goals listed (no delivery-format rewrite, no workflow rewrite)

## Phase 1 - Feature plumbing (read/write safe)

Deliverables:
- add typed feature plumbing for prop-specific simulator inputs
- add invariant checks (nulls, ranges, role-bucket completeness, freshness metadata)
- wire feature manifests so each simulation run records exact input provenance

Implementation constraints:
- no behavior change to existing simulator outputs in this phase
- new code path behind config/flag; default remains current behavior

Exit criteria:
- parity tests pass with old/new path disabled
- smoke test proves no output drift when flag is off

## Phase 2 - Simulator API extension

Deliverables:
- add explicit simulator request model:
  - list of legs with per-leg stochastic variable spec
  - simulation config (draws, seed, variance/temperature controls)
  - dependency mode (`independent`, `correlated`)
- add backward-compatible adapter from current call sites

Implementation constraints:
- no call-site breakage for existing delivery scripts
- deterministic behavior for fixed random seed

Exit criteria:
- API-shape tests + backward-compat tests pass
- benchmark confirms acceptable runtime regression budget

## Phase 3 - Joint-correlation engine integration

Deliverables:
- integrate correlation-aware sampler using existing correlation-engine sources
- enforce PSD projection and stable decomposition behavior
- add fallback path when correlation matrix is unavailable/unstable

Validation checks:
- correlation matrix diagnostics artifact per run
- fallback-rate tracking with thresholds
- explicit warning channel when fallback exceeds threshold

Exit criteria:
- simulation numerics stable across repeated seeds
- no invalid covariance/correlation failures in gated test set

## Phase 4 - Calibration layer alignment

Deliverables:
- align simulator outputs with current PMF + calibration stack
- add stat/role calibration hooks where simulator-induced drift appears
- keep p0/hurdle, mean-shift, and variance-temperature controls separable

Validation checks:
- PMF validity gate: nonnegative probs, sums near 1, finite moments
- calibration gates (ECE, PIT_KS, mean/variance error) per stat-role where eligible

Exit criteria:
- no hidden regression against existing calibration contracts
- no market-superiority claim unless verifier scripts certify

## Phase 5 - Validation gates and rollout sequencing

Deliverables:
- add explicit simulator-overhaul verification suite:
  - unit tests for variable contracts and simulator API
  - integration tests for correlated vs independent modes
  - regression tests for delivery contracts and workflow shape
- define staged rollout:
  1. canary diagnostics-only mode (no promotion impact)
  2. shadow scoring versus incumbent path
  3. gated promotion eligibility after sustained pass window

Stop-on-first-impact policy:
- halt rollout immediately on any of:
  - PMF validity failure
  - calibration gate failure
  - delivery contract break
  - material market regression beyond configured tolerance

## Milestone checklist (execution order)

1. Phase 0 contract freeze and sign-off
2. Phase 1 feature plumbing behind flag
3. Phase 2 simulator API extension with adapter
4. Phase 3 correlation integration + fallback diagnostics
5. Phase 4 calibration alignment and drift controls
6. Phase 5 validation suite and canary rollout

## Explicitly deferred

- no full rewrite of training pipeline
- no replacement of canonical workflow routing
- no direct production promotion from this plan artifact alone
