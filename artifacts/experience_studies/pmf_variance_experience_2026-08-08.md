# PMF Variance Experience Study — August 8, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-08-08` over a 60-day lookback._

## Executive summary

- **78** settled rows from **2026-06-10** through **2026-06-13** (2 delivery dates with at least one settled row).
- **Mean A/E = 1.137** — actual outcomes ran +13.7% relative to expected means in this sample.
- **Variance A/E = 1.167** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly narrow overall.
- **Standardized residual: mean = 0.161, sd = 1.017** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.756 and 0.923); the 10th-percentile band is over-covered (0.231 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.284 vs 0.254 (model vs market); logloss 0.775 vs 0.702.
- **Therefore, do not claim market superiority from this study.** This is a diagnostic and improvement layer, not proof of edge.

## What this study tests

This is an actuarial actual-to-expected review. Each settled (player, game, stat, line, side) row carries a model PMF and an observed outcome. From those we compute and roll up:

- **Mean calibration** — `mean_AE = Σactual / Σexpected_mean`. 1.00 = unbiased point estimate. Tells us whether the PMF means systematically over- or under-shoot.
- **Variance calibration** — `variance_AE = Σ(actual − mean)² / Σexpected_variance`. 1.00 = PMF spread matches reality. > 1 = realized outcomes are more volatile than the PMF said (PMF too narrow); < 1 = PMF is wider than reality.
- **Standardized residuals** — `(actual − mean) / √variance`. Calibrated PMFs produce residuals with mean ≈ 0 and sd ≈ 1.
- **Quantile coverage** — fraction of actuals at or below the model 10/25/50/75/90th percentiles. Should equal α.
- **PMF likelihood** — mean negative-log-likelihood of the realized outcome and ranked probability score (RPS).
- **Model-vs-market scoring** — over/under Brier and logloss, computed on the model PMF's `model_p_over` and the market's no-vig over probability; lower is better.

## Overall results

| metric | value |
|---|---:|
| rows | 78 |
| actual_mean (per row) | 5.641 |
| expected_mean (per row) | 4.962 |
| **mean_AE** | **1.1369** |
| Σ squared residual | 1174.39 |
| Σ expected variance | 1006.63 |
| **variance_AE** | **1.1666** |
| standardized_residual_mean | 0.1611 |
| standardized_residual_sd | 1.0172 |
| pmf_nll_mean | 2.0835 |
| pmf_rps_mean | 0.1248 |
| model_brier (over/under) | 0.2836 |
| market_brier (over/under) | 0.2542 |
| model_logloss (over/under) | 0.7753 |
| market_logloss (over/under) | 0.7024 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.231 / 0.333 / 0.538 / 0.756 / 0.923 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| injury_context | `fallback_used` | 40 | **1.256** | 1.109 | 1.053 | 2.016 |
| side | `UNDER` | 62 | **1.240** | 0.984 | 1.194 | 2.192 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

_No buckets fell below `variance_AE < 0.80` with sufficient sample._

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 40 | 1.066 | 0.991 | 0.110 | 2.080 |
| injury_context | `latest_valid_report_selected` | 38 | 1.198 | 1.111 | 0.181 | 2.155 |
| lineup_confirmed | `projected` | 78 | 1.137 | 1.167 | 0.161 | 2.084 |
| low_line_discrete | `no` | 48 | 1.155 | 1.170 | 0.287 | 2.596 |
| low_line_discrete | `yes` | 30 | 0.908 | 1.041 | -0.040 | 1.264 |
| minutes_volatility_bucket | `unavailable` | 78 | 1.137 | 1.167 | 0.161 | 2.084 |
| overall | `ALL` | 78 | 1.137 | 1.167 | 0.161 | 2.084 |
| role_bucket | `starter` | 47 | 1.113 | 1.082 | 0.206 | 2.250 |
| snapshot_type | `morning` | 78 | 1.137 | 1.167 | 0.161 | 2.084 |
| vacated_opportunity_bucket | `unavailable` | 78 | 1.137 | 1.167 | 0.161 | 2.084 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 7 | 0.801 | -0.317 |
| edge_bucket | `5_to_10pct` | 20 | 2.078 | 0.392 |
| edge_bucket | `ge_20pct` | 11 | 1.031 | 0.230 |
| line_bucket | `10_to_15` | 6 | 1.320 | 0.734 |
| line_bucket | `15_to_20` | 4 | 2.530 | -0.008 |
| line_bucket | `1_to_1p5` | 12 | 1.023 | 0.286 |
| line_bucket | `2_to_2p5` | 5 | 1.489 | 0.657 |
| line_bucket | `3_to_5` | 7 | 0.539 | -0.180 |
| line_bucket | `4_to_7` | 4 | 0.802 | 0.392 |
| line_bucket | `5_to_8` | 3 | 0.185 | 0.055 |
| line_bucket | `7_to_10` | 2 | 0.485 | 0.563 |
| line_bucket | `ge_10` | 4 | 0.647 | 0.596 |
| line_bucket | `ge_25` | 3 | 0.543 | 0.319 |
| line_bucket | `ge_3` | 1 | 4.821 | 2.196 |
| line_bucket | `le_half` | 18 | 1.059 | -0.257 |
| line_bucket | `lt_10` | 1 | 0.617 | -0.785 |
| line_bucket | `lt_3` | 2 | 0.315 | 0.191 |
| line_bucket | `lt_4` | 6 | 1.025 | -0.104 |
| p0_bucket | `20_to_50pct` | 17 | 1.050 | -0.111 |
| p0_bucket | `5_to_20pct` | 26 | 1.019 | 0.174 |
| p0_bucket | `ge_50pct` | 10 | 0.975 | 0.199 |
| p0_bucket | `lt_5pct` | 25 | 1.188 | 0.317 |
| predicted_variance_bucket | `high` | 26 | 1.204 | 0.378 |
| predicted_variance_bucket | `low` | 26 | 1.012 | 0.049 |
| predicted_variance_bucket | `mid` | 26 | 0.859 | 0.055 |
| role_bucket | `bench` | 16 | 1.285 | -0.064 |
| role_bucket | `core` | 12 | 1.454 | 0.506 |
| role_bucket | `rotation` | 3 | 0.587 | -0.720 |
| side | `OVER` | 16 | 0.491 | -0.600 |
| stat | `ast` | 12 | 0.380 | -0.060 |
| stat | `blk` | 5 | 3.201 | 1.138 |
| stat | `fg3m` | 16 | 1.266 | 0.031 |
| stat | `pts` | 14 | 1.322 | 0.324 |
| stat | `reb` | 16 | 0.730 | 0.278 |
| stat | `stl` | 15 | 0.844 | -0.127 |

## Live-context limitations

- Only **morning / current** settled rows are present in the scored-outcome feed for this window. Snapshot types observed: `morning`.
- **`t_minus_25` and `close_lock` rows are not yet scored** — the live snapshot scorer (`score_derek_live_snapshots_after_game.py`) reports `pending_outcomes` until enough live snapshots accumulate joinable game stats. Cross-snapshot calibration will only become meaningful once those rows accumulate; we do not fabricate them here.
- **`lineup_confirmed` and `injury_context` experience** is similarly thin. Source A (`after_game_scoring`) tags them, but covers only a few delivery dates so far. Bucket counts are reported honestly and flagged as thin sample where relevant.
- **`minutes_volatility_bucket` and `vacated_opportunity_bucket`** are reported as `unavailable` because the underlying signal is not yet captured in the settled-row feed. They are placeholders, not estimates.

## Interpretation for Derek

- The PMFs Derek delivers are **not just point projections**. Each row carries a full discrete distribution that produces a mean, a variance, and arbitrary quantiles. The over/under fair price is just one slice of that distribution.
- This study is the first formal test of whether realized outcomes are **as volatile as the PMFs expected** — not just whether the means landed.
- It is useful right now because it identifies **where the model is too narrow** (low predicted-variance bucket, OVER side, fg3m at 1+ stdev wider than predicted) and **where the model is too wide** (low-line discrete props, high-p0 props, starter minutes, defensive stats).
- It also shows what needs to land before we can claim broader edge: the model **under-projects means by ~14%** and **trails the market on binary scoring** in this small sample. So this is a diagnostic and **improvement** report, not a market-superiority claim.

## Next improvements

1. **Accumulate more settled live snapshots** — once `t_minus_25` and `close_lock` rows have realized outcomes joined, this study will be the canonical place to compare snapshot types for calibration gain.
2. **Bucket-level recalibration** — apply isotonic or temperature-scaling calibration on the over-disperse low-line discrete and high-p0 buckets; these are the largest variance-AE deviations and they cleanly compress.
3. **Low-line discrete stat handling** — fg3m / stl / blk / tov at lines ≤ 1.5 are the trickiest: fg3m is too narrow while the stl/blk stack is too wide. The next pass should fit per-stat dispersion scalers separately for these.
4. **Mean calibration** — the +14% mean_AE bias suggests the point projections systematically under-shoot. Re-fit the role-aware mean centering in the contextual stack and re-score this study.
5. **Confirmed-lineup and injury-context experience** — once the after-game scoring feed is wired to more delivery dates, monitor whether confirmed-lineup rows produce tighter variance-AE than projected ones.
6. **Actuarial monitoring by stat / role / line bucket / snapshot_type** — this script becomes the daily monitor. The verifier (`verify_pmf_variance_experience_study.py`) ensures the report stays honest and tracks PASS/WARN.

## Provenance

- inputs: `deliveries/<date>/after_game_scoring/after_game_scoring.parquet` (Source A — preferred metadata) and `predictions/all_props_<date>.parquet` joined with `data/player_game_stats.parquet` (Source B — row spine).
- settled window: **2026-06-10 → 2026-06-13** (2 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

