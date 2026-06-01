# SGP Engine Build Plan

## Mission

Build an institutional-grade same-game joint probability engine that consumes daily full-PMF deliveries and produces calibrated SGP fair probabilities and fair odds.

Core product truth: if the engine says a class of SGP outcomes is 60%, those outcomes should realize at approximately 60% out of sample.

---

## 1. Current Production State

**Status: opt-in diagnostic / model-price**

The SGP Engine is installed on `main` (`f661b8bd`) as opt-in infrastructure.

```
ENABLE_SGP_ENGINE=false
run_sgp_engine default: "false"
calibration_status: INSUFFICIENT_SAMPLE
promotion_status: DIAGNOSTIC_NO_BACKTEST
CERTIFIED rows: 0
```

All current price rows are `MODEL_PRICE` or `DIAGNOSTIC_ONLY`. No row is `CERTIFIED`.

No market-superiority claim is made. No unsupported claim language exists in outputs.

### Architecture

```
Daily PMF delivery (canonical_source)
        │
        ▼
build_sgp_slate_state_bundle.py
        │
        ▼
NBASimulator (factor-based, ghost/remainder Dirichlet minutes)
        │
        ▼
SimulationTape (per-player-stat simulated outcomes)
        │
        ▼
price_tickets_to_frame (SGPTicket → calibrated_joint_probability)
        │
        ▼
HierarchicalCalibratorRegistry (when trained)
        │
        ▼
Delivery: deliveries/{date}/sgp_engine/
Public:   public_export/wizard_of_odds/sgp/
```

### NBA v1 Simulator Mechanics

- **Factors**: pace, total, close-game, blowout, overtime, team offense/shooting/rebounds/turnovers, player minutes/usage/shooting/defense
- **PMF anchoring**: final calibrated atom PMFs define the marginal distribution via rank-remapping (inverse CDF)
- **Joint structure**: shared latent Gaussian factors create same-game dependency
- **Ghost/remainder bucket**: Dirichlet allocation absorbs untracked bench minutes so tracked player expected minutes remain centered on PMF-delivered expectations

### Pipeline Isolation

The SGP Engine is **opt-in only** until all readiness gates pass:
- `ENABLE_SGP_ENGINE=false` by default in all workflows
- SGP failures never block production PMF delivery
- SGP outputs are isolated to `deliveries/{date}/sgp_engine/` and `public_export/wizard_of_odds/sgp/`
- The WoO SGP page carries a diagnostic banner until Gate 4 passes

---

## 2. Requirements Before Default Production Activation

The SGP Engine must remain disabled by default (`run_sgp_engine: default "false"`) until **all** of the following gates explicitly pass and the user provides written approval.

### Gate 1 — Historical backtest rows accumulated

- **Minimum 500 settled SGP rows** required for factor weight fitting
- **Minimum 50 rows** required for joint calibrator initialization
- All rows must be generated **point-in-time** (no look-ahead into future outcomes)
- Source: `data/sgp_backtest_rows.parquet`
- Deduplication key: `(prediction_date, as_of_date, game_id, sgp_id)`

### Gate 2 — Joint calibrator fit

- `scripts/run_sgp_training_and_calibration.py` must complete with `status=FIT_COMPLETE`
- Calibrator artifact at `artifacts/models/sgp/joint_calibrators/joint_calibrator_latest.pkl`
- Walk-forward holdout: train on earliest 80% of game dates, validate on most-recent 20%

### Gate 3 — Segment reliability

Required segment dimensions with sufficient sample:
- `leg_count` (2-leg vs 3-leg)
- `relationship_type` (same_player / same_team / opponent)
- `stat_mix` (pure_counting / includes_sparse / includes_combo)
- `role_mix` (starter-only / bench-involved / mixed)
- `lineup_status` (official / projected / unknown)
- `contains_sparse_stat` (True/False)
- `contains_combo_overlap` (True/False)
- `contains_alt_line` (True/False)
- `line_percentile_bucket` (low_tail / lower_mid / mid / upper_mid / high_tail)

Reliability monotone: predicted probability buckets must correspond to increasing observed hit rates.

### Gate 4 — Calibration quality (OOF holdout)

| Metric | Threshold |
|--------|-----------|
| ECE | ≤ 0.025 |
| MCE | ≤ 0.075 |
| Calibration slope | 0.90 ≤ slope ≤ 1.10 |
| \|Calibration intercept\| | ≤ 0.025 |

### Gate 5 — Market superiority (when market SGP odds exist)

| Gate | Threshold |
|------|-----------|
| UCB95(model_logloss − market_logloss) | < −0.0025 |
| UCB95(model_brier − market_brier) | < −0.0010 |

**Not yet applicable** — no actual SGP market odds ingested. Currently `market_corr_factor_source=independence_placeholder` and `actual_sgp_market_odds_available=False`.

### Gate 6 — No false claims

- WoO SGP page must not contain: `certified edge`, `proven market superiority`, `guaranteed`, `continuously beats`
- `verify_sgp_delivery_outputs.py` must exit 0 with `status=PASS`
- `marginal_preservation_status` must be `PASS` or `WARN` (not `FAIL`)

### Gate 7 — Explicit user approval

Written approval required before:
- Setting `run_sgp_engine` default to `true`
- Setting `ENABLE_SGP_ENGINE` to `true`
- Marking any row `CERTIFIED`

---

## 3. Daily Shadow Training Process

### Objective

Train and calibrate the SGP Engine every NBA in-season day through the previous day (`as_of_date = delivery_date - 1`).

### Command

```bash
python3 scripts/run_sgp_training_and_calibration.py \
  --as-of-date YYYY-MM-DD \
  --repo-root . \
  --season-mode auto \
  --auto-build-dates
```

### GitHub Actions Workflow

```
.github/workflows/sgp_shadow_training.yml
```

Daily at 12:30 UTC (08:30 ET), after overnight box-score settlement. Manual dispatch via `as_of_date`, `auto_build_dates`, `no_commit`, `force_run`.

This workflow does **not** affect `nba_pmf_delivery.yml` and does **not** enable SGP delivery.

### Stage 1 — Resolve as-of context

- Reject `as_of_date >= today` with hard exit 1
- Identify latest settled game date from `data/oof_stat_pmf_predictions.parquet`
- Determine whether `as_of_date` was a no-game day (offseason, rest day)
- **Valid-skip with exit 0** if no new settled games exist since last run

### Stage 2 — Build/refresh SGP backtest rows

- Auto-detect historical delivery dates with PMF outputs
- Find dates not already in `data/sgp_backtest_rows.parquet`
- For each missing date: generate SGP candidates, price them with that date's PMFs, join settled outcomes
- Settlement rules:
  - `over hits if actual > line`
  - `under hits if actual < line`
  - `push if actual == line` on integer line → `actual_hit = NaN` (excluded by default)
  - `actual_hit = 1` only if **every non-push leg hits**
  - `actual_hit = 0` if any non-push leg loses
- Append/merge into `data/sgp_backtest_rows.parquet` (dedup by prediction_date, as_of_date, game_id, sgp_id)
- Filter strictly to `<= as_of_date` before any training (no future leakage)

### Stage 3 — Fit PIT factor weights

Inputs:
- `data/oof_stat_pmf_predictions.parquet` (pmf column = numpy ndarray, k starts at 0)
- `data/sgp_backtest_rows.parquet` (empirical correlation targets)

Method:
1. For each `(player_id, game_date, stat)`, load OOF PMF and actual outcome `y`
2. Compute midpoint PIT: `u = F(y−1) + 0.5 × p(y)`, clamp to [1e-6, 1−1e-6]
3. Convert to Gaussian z-score: `z = norm.ppf(u)`
4. Pivot to `(game_date, player_id × stat)` matrix
5. Estimate within-player cross-stat empirical correlations
6. Estimate cross-player same-team correlations from backtest 2-leg pairs
7. Apply shrinkage: `r_shrunk = (n / (n + 400)) × r_empirical`
8. Fit factor loadings `W` such that `W Wᵀ ≈ target_corr_matrix`

Output artifacts:
- `artifacts/models/sgp/factor_weights/factor_weights_{as_of_date}.json`
- `artifacts/models/sgp/factor_weights/factor_weights_latest.json`

Required `_meta` fields: `as_of_date`, `method`, `trained_rows`, `n_games`, `factor_names`, `weights`, `target_correlations`, `fit_diagnostics`, `fallback_used`, `sample_sizes_by_cell`, `shrinkage_k`, `latest_actual_box_score_date`, `created_at_utc`.

**Safety**: never overwrite `factor_weights_latest.json` with an invalid fit. If eligible rows < 500, valid-skip or retain previous latest artifact.

### Stage 4 — Fit hierarchical joint calibrators

Inputs:
- `data/sgp_backtest_rows.parquet` filtered to `<= as_of_date`

Split:
- Sort by `prediction_date` or `as_of_date`
- Train on earliest 80% of game dates
- Validate (OOF) on most-recent 20% of game dates

Minimum samples:
- Global calibrator: **n ≥ 500**
- Exact segment: n ≥ 500
- Parent stat/relationship: n ≥ 300
- Relationship type: n ≥ 200
- Leg count: n ≥ 200

Fallback hierarchy:
```
exact segment (≥500)
    → parent segment (≥300)
    → relationship type (≥200)
    → leg count (≥200)
    → global (≥500)
    → no calibration (INSUFFICIENT_SAMPLE)
```

Shrinkage: `final_p = w × cell_calibrated_p + (1−w) × parent_calibrated_p`, `w = n / (n + 400)`

OOF holdout metrics: ECE, MCE, Brier, LogLoss, calibration slope/intercept, reliability_by_bucket, reliability_by_segment.

Output artifacts:
- `artifacts/models/sgp/joint_calibrators/joint_calibrator_{as_of_date}.pkl`
- `artifacts/models/sgp/joint_calibrators/joint_calibrator_latest.pkl`

### Stage 5 — Reports and registry pointer

| Artifact | Path |
|----------|------|
| Training report | `artifacts/models/sgp/reports/sgp_training_report_{as_of_date}.json` |
| Calibration report | `artifacts/models/sgp/reports/sgp_calibration_report_{as_of_date}.json` |
| Gate report | `artifacts/models/sgp/reports/sgp_gate_report_{as_of_date}.json` |
| Segment reliability | `artifacts/models/sgp/reports/sgp_reliability_by_segment_{as_of_date}.csv` |
| Registry pointer | `artifacts/models/sgp/registry/sgp_model_pointer.json` |

### SGP Model Pointer Schema

```json
{
  "sgp_model_version": "v1",
  "trained_through_date": "YYYY-MM-DD",
  "calibrated_through_date": "YYYY-MM-DD",
  "latest_actual_box_score_date": "YYYY-MM-DD",
  "factor_weights_artifact": "artifacts/models/sgp/factor_weights/factor_weights_YYYY-MM-DD.json",
  "factor_weights_artifact_exists": true,
  "joint_calibrator_artifact": "artifacts/models/sgp/joint_calibrators/joint_calibrator_YYYY-MM-DD.pkl",
  "joint_calibrator_artifact_exists": true,
  "n_backtest_rows": 0,
  "n_settled": 0,
  "n_games": 0,
  "n_segments": 0,
  "n_certified_segments": 0,
  "factor_weights_status": "DIAGNOSTIC_NO_BACKTEST",
  "calibration_status": "DIAGNOSTIC_NO_BACKTEST",
  "promotion_status": "DIAGNOSTIC_NO_BACKTEST",
  "all_gates_pass": false,
  "non_market_gates_pass": false,
  "market_superiority_certified": false,
  "market_sgp_odds_available": false,
  "default_delivery_enabled": false,
  "oof_ece": null,
  "oof_mce": null,
  "oof_slope": null,
  "oof_intercept": null,
  "commit_sha": "abc1234",
  "created_at_utc": "YYYY-MM-DDTHH:MM:SSZ"
}
```

Valid `promotion_status` values:
- `DIAGNOSTIC_NO_BACKTEST` — no historical rows yet
- `VALID_SKIP_NO_NEW_DATA` — valid-skip, no new settled games
- `FACTOR_WEIGHTS_ONLY` — factor weights fit but calibrator not ready
- `CALIBRATOR_FIT_INSUFFICIENT_SEGMENTS` — global fit only, segments insufficient
- `FIT_COMPLETE_NOT_CERTIFIED` — all calibration gates pass except market gate
- `CERTIFIED_SEGMENTS_AVAILABLE` — market gate passes on qualifying segments
- `DEFAULT_PRODUCTION_APPROVED` — **never set programmatically; requires explicit user approval**

### SGP Backtest Row Schema (41 columns)

`data/sgp_backtest_rows.parquet` is the backbone of all calibration.

| Column | Description |
|--------|-------------|
| `prediction_date` | Slate date this row was priced for |
| `as_of_date` | Last information date used |
| `game_id` | Game identifier |
| `sgp_id` | Unique row identifier |
| `leg_count` | Number of legs |
| `legs_json` | JSON array of leg definitions |
| `relationship_type` | same_player / same_team / opponent / cross_game |
| `stat_mix` | pure_counting / includes_sparse / includes_combo / mixed |
| `role_mix` | Role bucket combination |
| `same_player_count` | Legs from same player |
| `same_team_count` | Legs from same team |
| `opponent_count` | Legs from opposing teams |
| `contains_combo_overlap` | Any combo stat + component |
| `contains_sparse_stat` | stl / blk / stocks present |
| `contains_alt_line` | Line far from PMF mean |
| `line_percentile_bucket` | low_tail / lower_mid / mid / upper_mid / high_tail |
| `lineup_status` | official / projected / unknown |
| `raw_joint_probability` | Simulated joint probability (pre-calibration) |
| `calibrated_joint_probability` | Post-calibration probability |
| `independent_probability` | Product of marginal PMF probabilities |
| `correlation_factor` | raw_joint / independent |
| `actual_hit` | 1=all legs hit, 0=any leg missed, NaN=push/unsettled |
| `market_sgp_probability` | No-vig market SGP probability (NaN if unavailable) |
| `market_sgp_odds` | Fair decimal market odds (NaN if unavailable) |
| `market_corr_factor` | market_sgp_prob / market_independence_prob |
| `model_corr_factor` | calibrated_joint / independent |
| `corr_factor_delta_vs_market` | model_corr_factor − market_corr_factor |
| `model_logloss` | −log(calibrated_joint_probability) |
| `model_brier` | (calibrated_joint_probability − actual_hit)² |
| `market_logloss` | −log(market_sgp_probability) |
| `market_brier` | (market_sgp_probability − actual_hit)² |
| `independence_logloss` | −log(independent_probability) |
| `independence_brier` | (independent_probability − actual_hit)² |
| `logloss_delta_vs_market` | model_logloss − market_logloss |
| `brier_delta_vs_market` | model_brier − market_brier |
| `logloss_delta_vs_independence` | model_logloss − independence_logloss |
| `brier_delta_vs_independence` | model_brier − independence_brier |
| `pmf_source_file` | PMF source file used |
| `model_version` | Champion model version |
| `sgp_engine_version` | SGP Engine version ("v1") |
| `created_at_utc` | ISO timestamp of row creation |

---

## 4. NoVig Trader-Grade Output Roadmap

This section documents the target output for a NoVig-style trading context. None of these fields are fully live yet — they become relevant after Gates 1–4 pass.

### Target output schema (per SGP candidate)

| Field | Description |
|-------|-------------|
| `fair_probability` | Calibrated joint probability (= `calibrated_joint_probability`) |
| `fair_decimal_odds` | `1 / fair_probability` |
| `fair_american_odds` | American odds converted from decimal |
| `bid_probability` | `fair_probability − half_spread` |
| `ask_probability` | `fair_probability + half_spread` |
| `quote_width` | `ask_probability − bid_probability` |
| `confidence_tier` | CERTIFIED / MODEL_PRICE / DIAGNOSTIC_ONLY / SUPPRESSED |
| `calibration_tier` | Segment-level calibration status |
| `liability_limit` | Max exposure (function of confidence + liquidity) |
| `max_position_size` | Max units to quote |
| `marginal_edge_component` | Edge from model PMF vs. market leg probabilities |
| `correlation_edge_component` | Edge from model_corr_factor vs. market_corr_factor |
| `total_edge` | `calibrated_joint_probability / market_sgp_probability − 1` |
| `adverse_selection_flag` | True if line moved against model |
| `stale_input_flag` | True if PMF or lineup is stale |
| `lineup_uncertainty_flag` | True if lineup not confirmed |
| `sparse_stat_flag` | True if stl / blk / stocks involved |
| `tail_line_flag` | True if any leg in low_tail or high_tail bucket |
| `market_corr_factor` | Market-implied correlation factor |
| `model_corr_factor` | Model-implied correlation factor |
| `corr_factor_delta_vs_market` | model − market correlation factor delta |

### Quote width logic

Quote width widens when:
- Calibration sample is small for this segment
- Lineup is not officially confirmed
- Sparse stat (stl / blk / stocks) is involved
- High-tail alt line
- Market SGP odds are missing
- MC standard error is high (≥ 0.02 on 25k sims → need 100k+ sims)
- Marginal preservation drift is high
- Recent injury or minutes restriction uncertainty
- Low market liquidity or high adverse selection signal

Quote width narrows when:
- Segment is CERTIFIED with sufficient sample
- Official lineup confirmed
- Strong calibration reliability
- Low MC standard error
- Stable player minutes and role

### Correlation edge decomposition

```
total_edge = marginal_edge + correlation_edge

marginal_edge =
    product(model_leg_p) / product(market_leg_p) - 1

correlation_edge =
    model_corr_factor / market_corr_factor - 1

total_edge =
    calibrated_joint_probability / market_sgp_probability - 1
```

The real SGP advantage should come primarily from **better correlation modeling**. If marginal edge is large but correlation edge is small, the SGP is better priced as individual props.

### Market SGP odds ingestion

When market SGP odds become available:

1. Add `market_sgp_decimal_odds` to bundle ingestion pipeline
2. Remove vig: `market_sgp_probability = 1 / fair_market_decimal_odds`
3. Compute `market_corr_factor = market_sgp_prob / product(market_leg_marginal_probs)`
4. Set `market_corr_factor_source = "market_book"` and `actual_sgp_market_odds_available = True`
5. Enable Gate 5 (UCB95 market superiority) evaluation

Target schema for `data/sgp_market_odds.parquet`:

| Column | Description |
|--------|-------------|
| `snapshot_time_utc` | Odds snapshot timestamp |
| `game_id` | Game identifier |
| `book` | Sportsbook (DraftKings, FanDuel, NoVig, etc.) |
| `sgp_id` | Matched SGP candidate identifier |
| `legs_json` | JSON array of matched legs |
| `market_decimal_odds` | Book decimal odds (including vig) |
| `market_american_odds` | American odds |
| `market_implied_probability` | 1 / market_decimal_odds |
| `no_vig_market_probability` | Vig-removed market probability |
| `individual_leg_no_vig_probs_json` | Per-leg no-vig probability array |
| `market_independence_probability` | Product of individual leg no-vig probs |
| `market_corr_factor` | no_vig_market_prob / market_independence_prob |
| `source` | Data vendor / method |

---

## 5. Calibration Gates

### Gate evaluation logic

```python
# Gate 1 — sufficient sample
gate1 = (n_settled >= 500)

# Gate 2 — ECE
gate2 = (oof_ece is not None and oof_ece <= 0.025)

# Gate 3 — MCE
gate3 = (oof_mce is not None and oof_mce <= 0.075)

# Gate 4 — calibration slope
gate4 = (oof_slope is not None and 0.90 <= oof_slope <= 1.10)

# Gate 5 — market superiority (UCB95)
# Only evaluable when actual_sgp_market_odds_available=True
gate5 = (
    ucb95_logloss_delta_vs_market < -0.0025
    and ucb95_brier_delta_vs_market < -0.0010
)

non_market_gates_pass = gate1 and gate2 and gate3 and gate4
all_gates_pass = non_market_gates_pass and gate5
```

### Calibration metrics definitions

**ECE (Expected Calibration Error):**
```
ECE = Σ_b (n_b/N) × |mean_predicted_b − observed_rate_b|
```
Bins: 10 equal-width bins in [0, 1].

**MCE (Maximum Calibration Error):**
```
MCE = max_b |mean_predicted_b − observed_rate_b|
```

**Calibration slope and intercept:**
From logistic regression of `actual_hit ~ logit(calibrated_joint_probability)`:
- Perfect calibration: slope = 1.0, intercept = 0.0
- Under-confidence: slope > 1.0 (model is too flat)
- Over-confidence: slope < 1.0 (model is too sharp)

**UCB95 for market gates:**
```
delta = model_metric - market_metric
ucb95 = delta + 1.645 × std_error(delta) / sqrt(n)
```
Claim market superiority only if `ucb95 < threshold`.

### Reliability table requirements

For each calibration bucket (10 bins):
- `bin_lower`, `bin_upper`: probability range
- `n`: sample count
- `mean_predicted`: average model probability in bin
- `observed_rate`: fraction of rows where `actual_hit = 1`
- `calibration_error`: `|mean_predicted - observed_rate|`
- `is_reliable`: `calibration_error ≤ 0.05` (for bins with n ≥ 30)

---

## 6. Segment Reliability Requirements

The SGP calibration system must evaluate reliability separately for each segment dimension. A segment is "certified" if:
- `n ≥ 200` (sufficient sample for that segment)
- `ECE ≤ 0.025`
- `0.90 ≤ calibration_slope ≤ 1.10`

### Required segment dimensions

| Dimension | Values |
|-----------|--------|
| `leg_count` | 2, 3 |
| `stat_mix` | `pure_counting`, `includes_sparse`, `includes_combo`, `mixed` |
| `role_mix` | `starter_only`, `bench_involved`, `mixed` |
| `relationship_type` | `same_player`, `same_team`, `opponent`, `cross_game` |
| `contains_sparse_stat` | `True`, `False` |
| `contains_combo_overlap` | `True`, `False` |
| `contains_alt_line` | `True`, `False` |
| `lineup_status` | `official`, `projected`, `unknown` |
| `line_percentile_bucket` | `low_tail`, `lower_mid`, `mid`, `upper_mid`, `high_tail` |

### Why segment reliability matters

The SGP Engine is expected to be materially less accurate for:
- **Sparse stats** (stl/blk): high variance, game-context-driven, lower PMF accuracy
- **Alt lines** (tail buckets): model is least calibrated at extremes
- **Lineup unknown**: uncertainty in role/minutes propagates to joint probability
- **Opponent pairs**: independent-ish; correlation is weak but present

Accurate segment-level calibration allows the engine to:
1. Widen quote width for uncertified segments
2. Suppress `CERTIFIED` tier for segments with insufficient sample
3. Build trust incrementally as more data accumulates

### Reliability tracking

For each segment, track over time:
```
date | segment | n | ece | slope | intercept | is_certified
```

Store in: `artifacts/models/sgp/reports/sgp_reliability_by_segment_{as_of_date}.csv`

A segment moves from `DIAGNOSTIC_ONLY` → `MODEL_PRICE` → `CERTIFIED` as:
1. Sample size grows past threshold
2. ECE drops below 0.025
3. Calibration slope enters [0.90, 1.10]

### Competitive minutes / role simulation integrity

The ghost/remainder Dirichlet bucket fix is essential. Never regress it.

Rules:
- Do not allocate full 240 team minutes only to tracked players
- If only 8–9 tracked players have PMFs, add ghost/remainder bucket
- Ghost bucket absorbs untracked bench/garbage time minutes
- Same-team minutes competition must exist (negative within-team correlation)
- Overtime adds minutes mostly to core/starter roles
- Blowout reduces starter/core minutes and increases bench/fringe/ghost minutes
- Close game increases starter/core minutes

Diagnostics always written in `simulation_diagnostics.json`:
- `minutes_allocation_method`
- `ghost_minutes_expected_by_team`
- `tracked_expected_minutes_by_team`
- `marginal_preservation_mean_abs_error`
- `marginal_preservation_fail_rate`
- `marginal_preservation_status`

---

## PR #64 Status

**Branch:** `feature/sgp-engine-v1-deliveries-integration` (merged to `main` as `f661b8bd`)

### What was completed in PR #64

- SGP is opt-in. `ENABLE_SGP_ENGINE=false`, `run_sgp_engine` default `"false"`.
- Critical Dirichlet minutes inflation bug fixed. Ghost/remainder bucket. Mean abs_error: **0.80%**, FAIL rate: **0%**.
- Marginal preservation report expanded to 20-column full schema.
- All required output files generated.
- Market correlation placeholder labels explicit.
- WoO SGP page is diagnostic/model-price mode.
- 131 SGP tests passing.

### Shadow Training + Calibration Branch

**Branch:** `feature/sgp-shadow-training-calibration`

This branch implements the daily training and calibration system plus exhaustive SGP coverage:

- **Exhaustive 2-leg coverage**: ALL C(n,2) combinations of player-stat over legs
- **3-leg coverage**: up to 5,000 per game from shuffled enumeration
- **Fair odds on every row**: `fair_probability`, `fair_decimal_odds`, `fair_american_odds`
- **Daily shadow training workflow**: `.github/workflows/sgp_shadow_training.yml`
- **Training artifact verifier**: `scripts/verify_sgp_training_artifacts.py`
- **Market correlation baseline stub**: `scripts/build_sgp_market_correlation_baseline.py`
- **Pointer hardened** with `n_certified_segments`, `commit_sha`, full schema
- **182 tests passing** (131 original + 51 new)
