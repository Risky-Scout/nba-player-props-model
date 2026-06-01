# SGP Engine — Readiness Gates & Promotion Policy

This document defines the conditions required before the SGP Engine may be
activated by default in the production Full Deliveries pipeline.

Until all gates below pass, the SGP Engine runs in **opt-in / diagnostic mode
only** via the `run_sgp_engine=true` workflow input or `ENABLE_SGP_ENGINE=true`
environment variable.

---

## Gate 1 — Engineering Stability

- [ ] Full repo tests pass (`pytest` green)
- [ ] SGP-specific tests pass (112/112, 0 xfailed)
- [ ] Local delivery smoke test passes (`run_sgp_engine_daily.py`)
- [ ] SGP output verifier passes (`verify_sgp_delivery_outputs.py status=PASS`)
- [ ] WoO SGP page builds without error
- [ ] Existing PMF delivery pipeline passes with SGP **disabled** (must not depend on SGP step)

**Current status:** ✅ Engineering stability gates pass (as of 2026-05-31).

---

## Gate 2 — Input Integrity

- [ ] PMF source discovery correctly identifies `canonical_source/MODEL_ONLY` files
- [ ] As-of contract passes (`verify_sgp_bundle_asof_contract.py`)
- [ ] All PMFs are valid (sum to 1.0 ± 0.001, no negative masses)
- [ ] Marginal preservation report: mean absolute error ≤ 0.025
- [ ] Combo coherence report exists and drift ≤ 0.05 stat units per combo
- [ ] Dependency diagnostics parquet generated with ≥ 1 pair per game

**Current status:** ✅ Input integrity gates pass for available slates.

---

## Gate 3 — Simulation Integrity

- [ ] Factor weights loaded from learned PIT residuals (not hardcoded defaults)
- [ ] Fallback factor weights labeled explicitly in `simulation_diagnostics.json`
- [ ] Competitive same-team Dirichlet minutes pool active (`minutes_pool_used: true`)
- [ ] Team minutes sum ≈ 240 per sim (± 5 for OT scenarios)
- [ ] Overtime / blowout / close-game mechanisms represented in factor weights
- [ ] Same-player cross-stat correlation diagnostics show physically plausible values:
  - `same_player_cross_stat` mean r ≥ 0.25
  - `same_player_combo_overlap` mean r ≥ 0.60
- [ ] Same-team correlations positive but < cross-player correlations (Dirichlet effect confirmed)

**Current status:** ✅ Simulation integrity gates pass. PIT-fitted weights loaded from
153,664 OOF observations (924 games, 2025-12-10 → 2026-05-09).

---

## Gate 4 — Calibration Readiness

- [ ] ≥ 500 historical SGP backtest rows in `data/sgp_backtest_rows.parquet`
- [ ] Joint probability calibrator fit on out-of-sample / walk-forward data
  (accumulated via `scripts/score_sgp_after_game.py` after each game settles)
- [ ] Calibration report includes ECE, Brier, LogLoss, slope/intercept
- [ ] Reliability by probability bucket: max bin error ≤ 0.075
- [ ] Reliability by leg count: ECE ≤ 0.05 for 2-leg and 3-leg separately
- [ ] Reliability by stat mix: ECE ≤ 0.06 per cell with ≥ 40 samples
- [ ] Reliability by role mix: ECE ≤ 0.06 per cell with ≥ 40 samples
- [ ] Reliability by relationship type: ECE ≤ 0.06 per cell with ≥ 40 samples

**Current status:** ❌ Calibration gate blocked — no backtest rows yet.
`sgp_gate_status.json` reports `INSUFFICIENT_SAMPLE`.
Backtest rows will accumulate automatically once `score_sgp_after_game.py`
runs after each settled game. Re-run `fit_sgp_joint_calibrator.py` once
≥ 500 rows are available.

---

## Gate 5 — Market / Comparison Readiness

- [ ] Independence baseline (`market_corr_factor = 1.0`) computed for all tickets
- [ ] If actual SGP market odds available: `market_corr_factor` populated from no-vig market price
- [ ] All market-correlation fields labeled as `diagnostic` / `placeholder` when
  actual market SGP prices are unavailable
- [ ] No output falsely claims market superiority
- [ ] `corr_factor_delta_vs_market` populated and interpretable

**Current status:** ✅ Independence baseline computed for all 500 tickets.
Market SGP prices not yet ingested; `market_corr_factor = 1.0` (independence
baseline) with honest labeling. No market-superiority claim made.

---

## Gate 6 — Promotion Policy

The SGP Engine may be enabled by default in production delivery **only after
Gates 1–5 all pass**.

Promotion checklist:
- [ ] Gates 1–5 all pass
- [ ] PR reviewed and approved
- [ ] Change `ENABLE_SGP_ENGINE: "false"` → `"true"` in
  `.github/workflows/nba_pmf_delivery.yml`
- [ ] Confirm existing delivery pipeline still passes after enabling
- [ ] Update this document with promotion date and final gate-pass evidence

---

## Manual / Opt-In Activation (before promotion)

Run SGP Engine for a single date without affecting production:

```bash
gh workflow run "NBA Player Props — Production Pipeline" \
  --repo Risky-Scout/nba-player-props-model \
  -f stage=delivery \
  -f mode=derek_near_lineup \
  -f delivery_date=YYYY-MM-DD \
  -f as_of_date=YYYY-MM-DD \
  -f force_run=true \
  -f run_predict=false \
  -f run_sgp_engine=true
```

Or locally:

```bash
python3 scripts/run_sgp_engine_daily.py --date YYYY-MM-DD --repo-root . --n-sims 25000
python3 scripts/build_sgp_woo_page.py --date YYYY-MM-DD --repo-root .
python3 scripts/verify_sgp_delivery_outputs.py --date YYYY-MM-DD --repo-root .
```

---

## Output Isolation

SGP Engine outputs write exclusively to:

- `deliveries/{date}/sgp_engine/` — prices, simulation, calibration, market comparison, WoO export
- `public_export/wizard_of_odds/sgp/` — public HTML / CSV / JSON WoO SGP page

The SGP Engine **never** modifies:

- `deliveries/{date}/canonical_source/`
- `deliveries/{date}/wizard_of_odds/`
- `deliveries/{date}/derek_forward_feed/`
- Any existing PMF delivery file

---

## WoO Page Labeling Policy

Before Gate 4 passes:
> "SGP Engine Diagnostic / Model Price Mode — Joint calibration pending
> historical SGP backtest sample. No market-superiority claim is made."

After Gate 4 passes but before Gate 6 (promotion):
> "SGP Engine — Model Price Mode (calibrated, not yet certified for market superiority)"

After Gate 6 (promotion):
> CERTIFIED rows may be surfaced. Diagnostic banner removed.
