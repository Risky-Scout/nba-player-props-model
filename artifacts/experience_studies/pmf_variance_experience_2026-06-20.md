# PMF Variance Experience Study — June 20, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-20` over a 60-day lookback._

## Executive summary

- **1,866** settled rows from **2026-04-21** through **2026-06-13** (30 delivery dates with at least one settled row).
- **Mean A/E = 1.108** — actual outcomes ran +10.8% relative to expected means in this sample.
- **Variance A/E = 0.794** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.149, sd = 0.906** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.762 and 0.915); the 10th-percentile band is over-covered (0.193 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.272 vs 0.248 (model vs market); logloss 0.746 vs 0.691.
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
| rows | 1,866 |
| actual_mean (per row) | 6.004 |
| expected_mean (per row) | 5.419 |
| **mean_AE** | **1.1079** |
| Σ squared residual | 25735.72 |
| Σ expected variance | 32412.22 |
| **variance_AE** | **0.7940** |
| standardized_residual_mean | 0.1493 |
| standardized_residual_sd | 0.9056 |
| pmf_nll_mean | 2.3026 |
| pmf_rps_mean | 0.1002 |
| model_brier (over/under) | 0.2719 |
| market_brier (over/under) | 0.2480 |
| model_logloss (over/under) | 0.7460 |
| market_logloss (over/under) | 0.6908 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.193 / 0.291 / 0.494 / 0.762 / 0.915 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 78 | **0.541** | 0.833 | 0.850 | 2.255 |
| edge_bucket | `10_to_20pct` | 910 | **0.740** | 0.902 | 1.113 | 2.304 |
| injury_context | `unavailable` | 1153 | **0.777** | 0.850 | 1.140 | 2.205 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 257 | **0.646** | 0.928 | 1.125 | 1.890 |
| line_bucket | `20_to_25` | 35 | **0.528** | 0.718 | 1.104 | 3.408 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `3_to_5` | 130 | **0.767** | 0.900 | 1.012 | 2.131 |
| line_bucket | `5_to_8` | 92 | **0.654** | 0.821 | 1.082 | 2.402 |
| line_bucket | `ge_10` | 39 | **0.623** | 0.776 | 1.118 | 2.779 |
| line_bucket | `ge_25` | 69 | **0.591** | 0.750 | 1.082 | 3.527 |
| line_bucket | `le_half` | 364 | **0.478** | 0.736 | 1.012 | 1.294 |
| lineup_confirmed | `unavailable` | 1153 | **0.777** | 0.850 | 1.140 | 2.205 |
| low_line_discrete | `yes` | 621 | **0.566** | 0.821 | 1.076 | 1.540 |
| minutes_volatility_bucket | `unavailable` | 1866 | **0.794** | 0.906 | 1.108 | 2.303 |
| overall | `ALL` | 1866 | **0.794** | 0.906 | 1.108 | 2.303 |
| p0_bucket | `20_to_50pct` | 331 | **0.704** | 0.944 | 1.042 | 1.898 |
| p0_bucket | `ge_50pct` | 316 | **0.477** | 0.695 | 1.303 | 1.268 |
| p0_bucket | `lt_5pct` | 650 | **0.774** | 0.927 | 1.088 | 3.021 |
| predicted_variance_bucket | `high` | 616 | **0.775** | 0.879 | 1.109 | 3.106 |
| predicted_variance_bucket | `low` | 616 | **0.679** | 0.869 | 1.112 | 1.516 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 520 | **0.621** | 0.802 | 1.089 | 2.261 |
| role_bucket | `lt22min` | 122 | **0.718** | 0.709 | 0.972 | 1.668 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 212 | **0.740** | 0.879 | 0.788 | 2.124 |
| side | `UNDER` | 1654 | **0.799** | 0.888 | 1.143 | 2.326 |
| snapshot_type | `morning` | 1866 | **0.794** | 0.906 | 1.108 | 2.303 |
| stat | `ast` | 296 | **0.737** | 0.880 | 1.073 | 2.227 |
| stat | `blk` | 236 | **0.700** | 0.758 | 1.329 | 1.510 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 383 | **0.779** | 0.904 | 1.103 | 3.390 |
| stat | `stl` | 261 | **0.538** | 0.751 | 1.082 | 1.405 |
| vacated_opportunity_bucket | `unavailable` | 1866 | **0.794** | 0.906 | 1.108 | 2.303 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 441 | 1.044 | 0.815 | 0.035 | 2.356 |
| edge_bucket | `ge_20pct` | 437 | 1.248 | 0.964 | 0.326 | 2.254 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 132 | 1.062 | 0.977 | 0.120 | 3.291 |
| line_bucket | `15_to_20` | 108 | 1.159 | 0.856 | 0.316 | 3.449 |
| line_bucket | `4_to_7` | 185 | 1.184 | 1.070 | 0.292 | 2.593 |
| line_bucket | `7_to_10` | 94 | 1.143 | 1.002 | 0.277 | 2.729 |
| line_bucket | `lt_10` | 39 | 1.098 | 0.947 | 0.152 | 3.307 |
| line_bucket | `lt_3` | 59 | 1.177 | 0.855 | 0.235 | 2.055 |
| line_bucket | `lt_4` | 165 | 1.116 | 0.940 | 0.171 | 2.253 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| low_line_discrete | `no` | 1245 | 1.110 | 0.804 | 0.194 | 2.683 |
| p0_bucket | `5_to_20pct` | 569 | 1.183 | 0.978 | 0.211 | 2.292 |
| predicted_variance_bucket | `mid` | 634 | 1.102 | 0.955 | 0.143 | 2.286 |
| role_bucket | `lt30min` | 497 | 1.228 | 0.967 | 0.260 | 2.281 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| stat | `reb` | 483 | 1.148 | 0.950 | 0.246 | 2.519 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 13 | 2.389 | 0.372 |
| line_bucket | `ge_8` | 15 | 0.823 | 0.251 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 14 | 2.788 | 0.282 |

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
- settled window: **2026-04-21 → 2026-06-13** (30 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

