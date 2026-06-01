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

The simulator uses a **ghost/remainder bucket** for Dirichlet minutes allocation to prevent inflation: untracked bench minutes are absorbed by a synthetic player and discarded, so tracked player expected minutes remain centered on PMF-delivered expectations.

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

**Branch:** `feature/sgp-engine-v1-deliveries-integration` (merged to `main` as `f661b8bd`)
**Status:** Merged as opt-in diagnostic/model-price SGP Engine.

### What was completed in PR #64

- **SGP is opt-in.** `ENABLE_SGP_ENGINE=false`, `run_sgp_engine` default `"false"` in all workflows. Existing production PMF delivery is unaffected when SGP is disabled.
- **Critical Dirichlet minutes inflation bug fixed.** Ghost/remainder bucket in `NBASimulator` absorbs untracked bench minutes so `E[simulated_minutes] = exp_mins[pid]`. Mean abs_error: **0.80%** (was 5.68%), FAIL rate: **0%** (was 56.8%).
- **Marginal preservation report** expanded to 20-column full schema with TV distance, CDF diff, status.
- **All required output files** generated: `calibration_context.parquet`, `factor_weights_used.json`, `sgp_reliability_by_segment.csv`, `sgp_publishable_edges.parquet`.
- **Market correlation placeholder labels** explicit: `market_corr_factor_source=independence_placeholder`, `actual_sgp_market_odds_available=False`.
- **Current calibration state is INSUFFICIENT_SAMPLE.** No historical SGP backtest rows exist yet. All price rows are `MODEL_PRICE`, 0 `CERTIFIED`.
- **WoO SGP page is diagnostic/model-price mode.** Displays all required phrases; no forbidden phrases.
- **Test suite: 131 SGP tests, all passing.**

### Current calibration state

```
gate_status:                  INSUFFICIENT_SAMPLE
calibration_available:        false
market_superiority_certified: false
marginal_preservation:        WARN (mean=0.80%, max=3.3%, fail_rate=0%)
price tier distribution:      MODEL_PRICE: 500 / CERTIFIED: 0
```

---

## Shadow Training + Calibration Branch

**Branch:** `feature/sgp-shadow-training-calibration`

This branch implements the daily training and calibration system that must run every in-season day to accumulate backtest rows and produce promotion-ready calibration artifacts.

### Daily shadow training workflow

For each in-season day D, with `as_of_date = D - 1`:

```bash
python3 scripts/run_sgp_training_and_calibration.py \
  --as-of-date YYYY-MM-DD \
  --repo-root . \
  --season-mode auto \
  --auto-build-dates
```

#### Stage 1 — Resolve as-of context
- Confirm `as_of_date < today` (hard-fail if not).
- Identify latest settled game date from `data/oof_stat_pmf_predictions.parquet`.
- Valid-skip (exit 0) if no game data found and `--season-mode auto`.

#### Stage 2 — Build/refresh SGP backtest rows
- Auto-detect which game dates lack backtest coverage.
- Run `build_sgp_backtest_rows.py` for missing dates when `--auto-build-dates` is set.
- Append/merge into `data/sgp_backtest_rows.parquet`.
- Filter strictly to `<= as_of_date` before training (no leakage).

#### Stage 3 — Fit PIT factor weights
- Compute midpoint PIT from `data/oof_stat_pmf_predictions.parquet` (pmf column = numpy ndarray, k starts at 0).
- Convert PIT to Gaussian z-scores via `scipy.stats.norm.ppf`.
- Estimate within-player cross-stat empirical correlations by pivoting `(player_id, game_date)`.
- Estimate cross-player same-team and opponent correlations from backtest 2-leg pairs.
- Apply shrinkage: `r_shrunk = (n / (n + 400)) * r_empirical`.
- Write `artifacts/models/sgp/factor_weights/factor_weights_{as_of_date}.json` and `_latest.json`.

Shrinkage note: `shrink_k=400` means a cell needs 400+ rows before empirical correlation has 50% weight. This prevents spurious over-fitting on small samples.

Known empirical insight to preserve:
> `stl / blk / stocks` carry high game-factor loadings because pace and defensive activity drive sparse defensive opportunities across both teams.

#### Stage 4 — Fit hierarchical joint calibrators
- Walk-forward split: hold out most-recent 20% of game dates as OOF holdout.
- Fit global + segment-level isotonic calibrators using `HierarchicalCalibratorRegistry`.
- Segments: `leg_count`, `relationship_type`, `stat_mix`, `role_mix`, `lineup_status`, `contains_sparse_stat`, `contains_combo_overlap`, `contains_alt_line`, `line_percentile_bucket`.
- Shrinkage fallback hierarchy: exact cell (≥500) → parent segment (≥300) → relationship type (≥200) → leg_count (≥200) → global (≥500) → no-calibration.
- Write `artifacts/models/sgp/joint_calibrators/joint_calibrator_{as_of_date}.pkl` and `_latest.pkl`.

#### Stage 5 — Produce reports
- **Training report**: `artifacts/models/sgp/reports/sgp_training_report_{as_of_date}.json`
- **Calibration report**: `artifacts/models/sgp/reports/sgp_calibration_report_{as_of_date}.json`
  - OOF metrics: ECE, MCE, Brier, LogLoss, calibration slope/intercept.
- **Gate report**: `artifacts/models/sgp/reports/sgp_gate_report_{as_of_date}.json`
  - Gates 1–5 evaluated and explained.
- **Segment reliability**: `artifacts/models/sgp/reports/sgp_reliability_by_segment_{as_of_date}.csv`
- **Registry pointer**: `artifacts/models/sgp/registry/sgp_model_pointer.json`

### Registry pointer schema

```json
{
  "trained_through_date": "YYYY-MM-DD",
  "calibrated_through_date": "YYYY-MM-DD",
  "n_backtest_rows": 0,
  "n_settled": 0,
  "n_games": 0,
  "n_segments": 0,
  "factor_weights_artifact": "artifacts/models/sgp/factor_weights/factor_weights_YYYY-MM-DD.json",
  "joint_calibrator_artifact": "artifacts/models/sgp/joint_calibrators/joint_calibrator_YYYY-MM-DD.pkl",
  "factor_weights_status": "INSUFFICIENT_DATA",
  "calibration_status": "INSUFFICIENT_DATA",
  "promotion_status": "INSUFFICIENT_SAMPLE",
  "all_gates_pass": false,
  "non_market_gates_pass": false,
  "market_superiority_certified": false,
  "updated_at_utc": "...",
  "note": "SGP Engine remains opt-in..."
}
```

---

## SGP Backtest Row Schema (41 columns)

`data/sgp_backtest_rows.parquet` is the backbone of all calibration.

| Column | Type | Description |
|--------|------|-------------|
| `prediction_date` | str | Slate date this row was priced for |
| `as_of_date` | str | Last information date used |
| `game_id` | str | Game identifier |
| `sgp_id` | str | Unique row identifier |
| `ticket_id` | str | Internal ticket identifier |
| `leg_count` | int | Number of legs (currently always 2) |
| `n_legs` | int | Alias for leg_count |
| `legs_json` | str | JSON array of leg definitions |
| `relationship_type` | str | same_player / same_team / opponent / cross_game |
| `stat_mix` | str | pure_counting / combo_overlap / sparse_defensive / mixed |
| `role_mix` | str | role bucket combination |
| `same_player_count` | int | Legs from same player |
| `same_team_count` | int | Legs from same team |
| `opponent_count` | int | Legs from opposing teams |
| `contains_combo_overlap` | bool | Any combo stat + component |
| `contains_sparse_stat` | bool | stl / blk / stocks present |
| `contains_alt_line` | bool | Line > 3 pts from PMF mean |
| `line_percentile_bucket` | str | low_tail / lower_mid / mid / upper_mid / high_tail / tail / mixed |
| `lineup_status` | str | official / projected / unknown |
| `raw_joint_probability` | float | Simulated joint probability (pre-calibration) |
| `calibrated_joint_probability` | float | Post-calibration probability |
| `independent_probability` | float | Product of marginal PMF probabilities |
| `correlation_factor` | float | raw_joint / independent |
| `model_corr_factor` | float | calibrated_joint / independent |
| `market_sgp_probability` | float | No-vig market SGP probability (NaN if unavailable) |
| `market_sgp_odds` | float | Fair decimal market odds (NaN if unavailable) |
| `market_corr_factor` | float | market_sgp_prob / market_independence_prob |
| `market_corr_factor_source` | str | "independence_placeholder" until real market SGP odds are ingested |
| `corr_factor_delta_vs_market` | float | model_corr_factor - market_corr_factor |
| `leg_1_player_id` | str | |
| `leg_1_stat` | str | |
| `leg_1_line` | float | |
| `leg_1_side` | str | over / under |
| `leg_1_marginal_probability_pmf` | float | |
| `leg_2_player_id` | str | |
| `leg_2_stat` | str | |
| `leg_2_line` | float | |
| `leg_2_side` | str | |
| `leg_2_marginal_probability_pmf` | float | |
| `fair_american_odds` | float | |
| `simulation_count` | int | MC simulation draws used |
| `actual_hit` | float | 1.0=hit, 0.0=miss, NaN=unsettled |
| `hit_result` | float | Alias for actual_hit (backwards-compat) |
| `model_logloss` | float | Negative log-likelihood of model probability |
| `model_brier` | float | Brier score of model probability |
| `market_logloss` | float | NLL of market probability (NaN if unavailable) |
| `market_brier` | float | Brier score of market probability (NaN if unavailable) |
| `logloss_delta_vs_market` | float | model_logloss - market_logloss |
| `brier_delta_vs_market` | float | model_brier - market_brier |
| `independence_logloss` | float | NLL of independence baseline |
| `independence_brier` | float | Brier of independence baseline |
| `logloss_delta_vs_independence` | float | model_logloss - independence_logloss |
| `brier_delta_vs_independence` | float | model_brier - independence_brier |
| `pmf_source_file` | str | PMF source file used |
| `model_version` | str | Champion model version |
| `sgp_engine_version` | str | SGP Engine version ("v1") |
| `created_at_utc` | str | ISO timestamp of row creation |

**Settlement rules:**
- `actual_hit = 1` only if every leg hits (over/under vs. actual stat, integer lines push → excluded or 0.5 split).
- `actual_hit = 0` if any leg loses.
- Pushes are excluded by default (`actual_hit = NaN`).

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
- ECE ≤ 0.025 (OOF holdout).
- MCE ≤ 0.075 (OOF holdout).
- No persistent systematic bias.

**Gate 5 — Market superiority where market baseline exists**
- When actual SGP market odds are available: `UCB95(model_logloss − market_logloss) < −0.0025`.
- When actual SGP market odds are available: `UCB95(model_brier − market_brier) < −0.0010`.
- These gates are not yet applicable (no SGP market odds ingested).

**Gate 6 — No false claims**
- WoO SGP page must not contain: `certified edge`, `proven market superiority`, `guaranteed`, `continuously beats`.
- `verify_sgp_delivery_outputs.py` must exit 0 with `status=PASS`.
- `marginal_preservation_status` must be `PASS` or `WARN` (not `FAIL`).

**Gate 7 — User explicit approval**
- Explicit sign-off required before changing `run_sgp_engine` default to `true` or `ENABLE_SGP_ENGINE` to `true`.

Until all gates pass, the SGP Engine is an opt-in diagnostic/model-price engine.

---

## NoVig Trader-Grade Output Roadmap

This roadmap documents the eventual target for SGP Engine outputs in a NoVig-style trading context. None of these outputs are live yet.

### Target output schema (per SGP candidate)

| Field | Description |
|-------|-------------|
| `fair_probability` | Calibrated joint probability |
| `fair_decimal_odds` | 1 / fair_probability |
| `fair_american_odds` | Converted American odds |
| `bid_probability` | fair_probability - half_spread |
| `ask_probability` | fair_probability + half_spread |
| `quote_width` | ask_probability - bid_probability |
| `confidence_tier` | CERTIFIED / MODEL_PRICE / DIAGNOSTIC_ONLY / SUPPRESSED |
| `calibration_tier` | Segment-level calibration status |
| `liability_limit` | Max exposure in dollar terms (function of confidence + liquidity) |
| `max_position_size` | Max units to quote |
| `marginal_edge_component` | Edge from model PMF vs. market leg probabilities |
| `correlation_edge_component` | Edge from model_corr_factor vs. market_corr_factor |
| `total_edge` | calibrated_joint_probability - market_sgp_probability |
| `adverse_selection_flag` | True if line moved against model significantly |
| `stale_input_flag` | True if PMF or lineup > X hours old |
| `lineup_uncertainty_flag` | True if lineup not confirmed |
| `sparse_stat_flag` | True if stl / blk / stocks involved |
| `tail_line_flag` | True if any leg in low_tail or high_tail bucket |
| `market_corr_factor` | Market-implied correlation factor |
| `model_corr_factor` | Model-implied correlation factor |
| `corr_factor_delta_vs_market` | model - market correlation factor delta |

### Quote width logic

Quote width expands when:
- Calibration sample is small for this segment.
- Lineup is not officially confirmed.
- Sparse stat (stl / blk / stocks) is involved.
- Alt-line tail bucket.
- Market SGP odds are missing.
- MC standard error is high (≥ 0.02 on 25k sims → need 100k+ sims).
- Marginal preservation drift is high.
- Recent injury or minutes restriction uncertainty.
- Low market liquidity / high adverse selection signal.

Quote width narrows when:
- Segment is CERTIFIED with sufficient sample.
- Official lineup confirmed.
- Strong calibration reliability.
- Low MC standard error.
- Stable player minutes and role.

### Correlation edge decomposition

For NoVig trading, separate the total SGP edge into:

```
total_edge = marginal_edge + correlation_edge

marginal_edge =
    product(model_leg_p) / product(market_leg_p) - 1

correlation_edge =
    model_corr_factor / market_corr_factor - 1

total_edge =
    calibrated_joint_probability / market_sgp_probability - 1
```

The real SGP advantage should come primarily from **better correlation modeling**, not only from marginal prop edge. If marginal edge is large but correlation edge is small, it may indicate the SGP is better priced as individual props rather than parlays.

### When to ingest actual market SGP odds

When market SGP odds become available from a data vendor:

1. Add `market_sgp_decimal_odds` to the bundle ingestion pipeline.
2. Compute `market_sgp_probability = 1 / fair_market_decimal_odds` (remove vig first).
3. Compute `market_corr_factor = market_sgp_prob / product(market_leg_marginal_probs)`.
4. Set `market_corr_factor_source = "market_book"`.
5. Set `actual_sgp_market_odds_available = True`.
6. Enable Gate 5 (UCB95 market superiority) evaluation.

Until then, `market_corr_factor_source = "independence_placeholder"` and `actual_sgp_market_odds_available = False` must remain explicit in all outputs.

### Competitive minutes / role simulation integrity

The ghost/remainder Dirichlet bucket fix is essential. Never regress it.

Rules:
- Do not allocate full 240 team minutes only to tracked players.
- If only 8–9 tracked players have PMFs, add ghost/remainder bucket.
- Ghost bucket absorbs untracked bench/garbage time minutes.
- Same-team minutes competition must exist (negative within-team correlation).
- Overtime adds minutes mostly to core/starter roles.
- Blowout reduces starter/core minutes and increases bench/fringe/ghost minutes.
- Close game increases starter/core minutes.

Minutes allocation diagnostics (always written in `simulation_diagnostics.json`):
- `minutes_allocation_method`
- `ghost_minutes_expected_by_team`
- `tracked_expected_minutes_by_team`
- `marginal_preservation_mean_abs_error`
- `marginal_preservation_fail_rate`
- `marginal_preservation_status`
