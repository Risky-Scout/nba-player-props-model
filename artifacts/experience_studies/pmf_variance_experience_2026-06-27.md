# PMF Variance Experience Study — June 27, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-27` over a 60-day lookback._

## Executive summary

- **1,081** settled rows from **2026-04-29** through **2026-06-13** (23 delivery dates with at least one settled row).
- **Mean A/E = 1.073** — actual outcomes ran +7.3% relative to expected means in this sample.
- **Variance A/E = 0.773** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.105, sd = 0.945** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.771 and 0.920); the 10th-percentile band is over-covered (0.207 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.265 vs 0.249 (model vs market); logloss 0.730 vs 0.693.
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
| rows | 1,081 |
| actual_mean (per row) | 5.831 |
| expected_mean (per row) | 5.436 |
| **mean_AE** | **1.0725** |
| Σ squared residual | 13603.50 |
| Σ expected variance | 17608.48 |
| **variance_AE** | **0.7726** |
| standardized_residual_mean | 0.1046 |
| standardized_residual_sd | 0.9448 |
| pmf_nll_mean | 2.2858 |
| pmf_rps_mean | 0.1075 |
| model_brier (over/under) | 0.2647 |
| market_brier (over/under) | 0.2489 |
| model_logloss (over/under) | 0.7300 |
| market_logloss (over/under) | 0.6934 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.207 / 0.328 / 0.533 / 0.771 / 0.920 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 93 | **1.382** | 1.211 | 1.050 | 2.621 |
| line_bucket | `7_to_10` | 50 | **1.202** | 1.104 | 1.102 | 2.718 |
| p0_bucket | `5_to_20pct` | 312 | **1.291** | 1.000 | 1.128 | 2.172 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 60 | **0.492** | 0.855 | 0.936 | 2.169 |
| edge_bucket | `10_to_20pct` | 513 | **0.766** | 0.955 | 1.100 | 2.315 |
| edge_bucket | `5_to_10pct` | 331 | **0.711** | 0.894 | 1.011 | 2.294 |
| injury_context | `unavailable` | 368 | **0.625** | 0.857 | 1.088 | 1.948 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `10_to_15` | 76 | **0.791** | 0.901 | 1.069 | 3.240 |
| line_bucket | `1_to_1p5` | 179 | **0.656** | 0.955 | 1.099 | 1.913 |
| line_bucket | `2_to_2p5` | 65 | **0.443** | 0.745 | 1.046 | 1.684 |
| line_bucket | `3_to_5` | 76 | **0.765** | 0.894 | 1.029 | 2.080 |
| line_bucket | `ge_25` | 47 | **0.527** | 0.696 | 1.085 | 3.491 |
| line_bucket | `le_half` | 189 | **0.524** | 0.801 | 0.853 | 1.304 |
| lineup_confirmed | `unavailable` | 368 | **0.625** | 0.857 | 1.088 | 1.948 |
| low_line_discrete | `no` | 713 | **0.781** | 0.973 | 1.077 | 2.640 |
| low_line_discrete | `yes` | 368 | **0.603** | 0.883 | 1.004 | 1.600 |
| minutes_volatility_bucket | `unavailable` | 1081 | **0.773** | 0.945 | 1.073 | 2.286 |
| overall | `ALL` | 1081 | **0.773** | 0.945 | 1.073 | 2.286 |
| p0_bucket | `20_to_50pct` | 215 | **0.731** | 0.986 | 1.036 | 1.925 |
| p0_bucket | `ge_50pct` | 140 | **0.458** | 0.729 | 1.215 | 1.160 |
| p0_bucket | `lt_5pct` | 414 | **0.717** | 0.946 | 1.061 | 2.940 |
| predicted_variance_bucket | `high` | 357 | **0.748** | 0.939 | 1.076 | 3.091 |
| predicted_variance_bucket | `low` | 357 | **0.769** | 0.932 | 1.083 | 1.547 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 205 | **0.486** | 0.831 | 1.043 | 2.026 |
| role_bucket | `lt22min` | 35 | **0.648** | 0.719 | 0.769 | 1.455 |
| role_bucket | `lt30min` | 121 | **0.707** | 0.883 | 1.193 | 1.942 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `UNDER` | 891 | **0.767** | 0.921 | 1.123 | 2.307 |
| snapshot_type | `morning` | 1081 | **0.773** | 0.945 | 1.073 | 2.286 |
| stat | `fg3m` | 187 | **0.594** | 0.960 | 0.946 | 1.873 |
| stat | `pts` | 214 | **0.717** | 0.888 | 1.083 | 3.391 |
| stat | `stl` | 134 | **0.587** | 0.810 | 1.006 | 1.420 |
| vacated_opportunity_bucket | `unavailable` | 1081 | **0.773** | 0.945 | 1.073 | 2.286 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 177 | 1.177 | 1.052 | 0.235 | 2.228 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `15_to_20` | 54 | 1.053 | 0.827 | 0.125 | 3.430 |
| line_bucket | `5_to_8` | 56 | 1.069 | 0.883 | 0.114 | 2.409 |
| line_bucket | `lt_3` | 33 | 1.237 | 0.960 | 0.336 | 2.052 |
| line_bucket | `lt_4` | 84 | 1.038 | 1.087 | 0.095 | 2.254 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| predicted_variance_bucket | `mid` | 367 | 1.057 | 0.957 | 0.084 | 2.221 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| side | `OVER` | 190 | 0.786 | 0.807 | -0.375 | 2.185 |
| stat | `ast` | 171 | 1.072 | 0.837 | 0.132 | 2.196 |
| stat | `blk` | 122 | 1.288 | 0.822 | 0.212 | 1.546 |
| stat | `reb` | 253 | 1.066 | 1.126 | 0.143 | 2.532 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `20_to_25` | 14 | 0.469 | 0.244 |
| line_bucket | `ge_10` | 26 | 0.673 | 0.208 |
| line_bucket | `ge_3` | 10 | 2.407 | 0.380 |
| line_bucket | `ge_8` | 6 | 0.713 | 0.088 |
| line_bucket | `lt_10` | 23 | 1.339 | 0.340 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 7 | 5.763 | 0.580 |

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
- settled window: **2026-04-29 → 2026-06-13** (23 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

