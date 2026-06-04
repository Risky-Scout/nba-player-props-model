# SGP Engine Build Plan

## Mission

Build a same-game joint probability engine that consumes daily full-PMF deliveries and produces calibrated SGP fair odds inside `deliveries/<date>/sgp_engine/`.

## Architecture

1. Build `slate_state_bundle_v1` from the daily PMF delivery.
2. Run sport-specific full-game simulation.
3. Generate a reusable simulation tape.
4. Evaluate SGP tickets directly against simulated box scores.
5. Apply out-of-sample joint probability calibrators where available.
6. Write fair odds, diagnostics, and manifest outputs into the same daily delivery folder.

## NBA v1 mechanics

The first NBA simulator is a marginal-anchored game-mechanism factor simulator:
- game factors: pace, total, close-game, blowout, overtime
- team factors: offense, shooting, threes, assists, rebound pool, turnovers, defensive activity
- player factors: minutes, usage, shooting, energy, defense, foul risk
- PMF anchoring: final calibrated atom PMFs define the marginal distribution
- joint structure: shared factors create same-game dependency

This is designed to be enriched with possession-level simulation as the PMF repo exports more latent ingredients.

## Production promotion rule

Do not claim market superiority until:
- historical backtest rows are generated point-in-time
- joint reliability buckets pass
- calibrated joint probability beats raw simulator out-of-sample
- raw/calibrated simulator beats independence baseline
- comparison to market SGP prices, if available, passes bootstrap gates

## Pipeline isolation policy (§0B–0F)

The SGP Engine is **opt-in only** until all readiness gates pass.

- `ENABLE_SGP_ENGINE=false` by default in `.github/workflows/nba_pmf_delivery.yml`
- Enable per-run via `run_sgp_engine=true` workflow dispatch input
- SGP failures never block the existing production PMF delivery
- SGP outputs are isolated to `deliveries/{date}/sgp_engine/` and `public_export/wizard_of_odds/sgp/`
- The WoO SGP page carries a diagnostic banner until Gate 4 (calibration) passes

Full readiness gates and promotion checklist: **[docs/SGP_READINESS_GATES.md](SGP_READINESS_GATES.md)**

---

## PR #64 Status

**Branch:** `feature/sgp-engine-v1-deliveries-integration`
**Commit:** `354947f6` (latest: WoO mode heading + docs)
**Status:** Merge-ready as opt-in diagnostic/model-price SGP Engine.

### What was completed

- **SGP is opt-in.** `ENABLE_SGP_ENGINE=false` and `run_sgp_engine` default `false` in all workflows. Existing production PMF delivery is unaffected when SGP is disabled.
- **Critical Dirichlet minutes inflation bug fixed.** A ghost/remainder bucket in `NBASimulator` absorbs untracked bench minutes so each player's `E[simulated_minutes] = exp_mins[pid]`.
  - Mean abs_error: **0.80%** (was 5.68%)
  - Mean signed bias: **-0.61%** (was +5.7%)
  - FAIL rate: **0%** (was 56.8%)
- **Marginal preservation report** expanded to 20-column full schema with TV distance, CDF diff, status.
- **Daily SGP training/calibration script** (`scripts/run_sgp_training_and_calibration.py`) exists. Valid-skips with exit 0 when no backtest rows; hard-fails if `as_of_date >= today`.
- **All required output files** are generated: `calibration_context.parquet`, `factor_weights_used.json`, `sgp_reliability_by_segment.csv`, `sgp_publishable_edges.parquet`.
- **Market correlation placeholder labels** are explicit: `market_corr_factor_source=independence_placeholder`, `actual_sgp_market_odds_available=False`.
- **Current calibration state is diagnostic.** `gate_status=INSUFFICIENT_SAMPLE` because no historical SGP backtest rows exist yet. All 500 price rows have `tier=MODEL_PRICE`, 0 `CERTIFIED`.
- **WoO SGP page is diagnostic/model-price mode.** Displays "SGP Engine Diagnostic / Model Price Mode", "Joint calibration pending historical SGP backtest sample", and "No market-superiority claim is made."
- **Test suite: 131 SGP tests, all passing.** 21 new tests added covering Dirichlet minutes fix, schema compliance, market labels, and backtest row structure.

### Current calibration state

```
gate_status:                INSUFFICIENT_SAMPLE
calibration_available:      false
market_superiority_certified: false
marginal_preservation:      WARN (mean=0.80%, max=3.3%, fail_rate=0%)
price tier distribution:    MODEL_PRICE: 500 / CERTIFIED: 0
```

---

## Requirements before default production activation

The SGP Engine must remain `run_sgp_engine: default "false"` until **all** of the following gates pass:

**Gate 1 — Historical backtest rows accumulated**
- Minimum 500 settled 2-leg SGP rows required for factor weight fitting.
- Minimum 50 settled rows required for joint calibrator initialization.
- Rows must be generated point-in-time (no look-ahead into future outcomes).

**Gate 2 — Joint calibrator fit walk-forward through previous day**
- `scripts/run_sgp_training_and_calibration.py` must complete with `status=FIT_COMPLETE`.
- Calibrator artifact at `artifacts/models/sgp/joint_calibrators/joint_calibrator_latest.pkl`.

**Gate 3 — Reliability acceptable by all required segments**
- Segment dimensions: `leg_count`, `stat_mix`, `role_mix`, `relationship_type`, `sparse_stat`, `combo_overlap`, `alt_line`, `lineup_status`, `line_percentile_bucket`.
- Calibration slope: `0.90 ≤ slope ≤ 1.10` in each well-populated segment.
- Reliability monotone: predicted probability buckets must correspond to increasing observed hit rates.

**Gate 4 — Calibration quality**
- ECE ≤ 0.025 (global) and ≤ 0.05 per segment where `n ≥ 100`.
- MCE ≤ 0.075.
- No persistent systematic bias.

**Gate 5 — Market superiority where market baseline exists**
- When actual SGP market odds are available: `UCB95(model_logloss − market_logloss) < −0.0025`.
- When actual SGP market odds are available: `UCB95(model_brier − market_brier) < −0.0010`.
- These gates are not yet applicable (no SGP market odds ingested).

**Gate 6 — No false claims**
- WoO SGP page must not contain any of: `certified edge`, `proven market superiority`, `guaranteed`, `continuously beats`.
- `verify_sgp_delivery_outputs.py` must exit 0 with `status=PASS`.
- `marginal_preservation_status` must be `PASS` or `WARN` (not `FAIL`).

**Gate 7 — User approval**
- Explicit sign-off required before changing `run_sgp_engine` default to `true` or `ENABLE_SGP_ENGINE` to `true`.

Until all gates pass, the SGP Engine is an opt-in diagnostic/model-price engine with strong infrastructure and no unsupported claims.
