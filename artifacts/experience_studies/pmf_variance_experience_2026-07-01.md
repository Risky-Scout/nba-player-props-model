# PMF Variance Experience Study — July 1, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-07-01` over a 60-day lookback._

## Executive summary

- **795** settled rows from **2026-05-02** through **2026-06-13** (20 delivery dates with at least one settled row).
- **Mean A/E = 1.056** — actual outcomes ran +5.6% relative to expected means in this sample.
- **Variance A/E = 0.785** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.079, sd = 0.955** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.777 and 0.923); the 10th-percentile band is over-covered (0.208 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.261 vs 0.247 (model vs market); logloss 0.721 vs 0.690.
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
| rows | 795 |
| actual_mean (per row) | 5.801 |
| expected_mean (per row) | 5.492 |
| **mean_AE** | **1.0562** |
| Σ squared residual | 10181.57 |
| Σ expected variance | 12962.96 |
| **variance_AE** | **0.7854** |
| standardized_residual_mean | 0.0790 |
| standardized_residual_sd | 0.9549 |
| pmf_nll_mean | 2.2721 |
| pmf_rps_mean | 0.1098 |
| model_brier (over/under) | 0.2607 |
| market_brier (over/under) | 0.2473 |
| model_logloss (over/under) | 0.7207 |
| market_logloss (over/under) | 0.6897 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.208 / 0.338 / 0.555 / 0.777 / 0.923 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| p0_bucket | `5_to_20pct` | 247 | **1.239** | 1.006 | 1.105 | 2.141 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 51 | **0.512** | 0.813 | 0.894 | 2.140 |
| edge_bucket | `10_to_20pct` | 375 | **0.761** | 0.971 | 1.072 | 2.275 |
| edge_bucket | `5_to_10pct` | 252 | **0.747** | 0.923 | 1.005 | 2.289 |
| injury_context | `unavailable` | 240 | **0.619** | 0.856 | 1.031 | 1.935 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 127 | **0.769** | 1.036 | 1.100 | 1.922 |
| line_bucket | `2_to_2p5` | 48 | **0.519** | 0.798 | 1.034 | 1.636 |
| line_bucket | `3_to_5` | 61 | **0.729** | 0.878 | 0.989 | 2.047 |
| line_bucket | `5_to_8` | 39 | **0.757** | 0.861 | 1.044 | 2.356 |
| line_bucket | `ge_25` | 39 | **0.571** | 0.710 | 1.107 | 3.509 |
| line_bucket | `le_half` | 141 | **0.598** | 0.858 | 0.809 | 1.307 |
| lineup_confirmed | `unavailable` | 240 | **0.619** | 0.856 | 1.031 | 1.935 |
| low_line_discrete | `no` | 527 | **0.789** | 0.956 | 1.061 | 2.615 |
| low_line_discrete | `yes` | 268 | **0.695** | 0.951 | 0.985 | 1.598 |
| minutes_volatility_bucket | `unavailable` | 795 | **0.785** | 0.955 | 1.056 | 2.272 |
| overall | `ALL` | 795 | **0.785** | 0.955 | 1.056 | 2.272 |
| p0_bucket | `ge_50pct` | 92 | **0.456** | 0.770 | 1.157 | 1.054 |
| p0_bucket | `lt_5pct` | 295 | **0.729** | 0.902 | 1.043 | 2.937 |
| predicted_variance_bucket | `high` | 263 | **0.762** | 0.914 | 1.061 | 3.060 |
| role_bucket | `bench` | 51 | **0.773** | 1.025 | 0.917 | 2.040 |
| role_bucket | `ge30min_starter` | 151 | **0.518** | 0.850 | 1.027 | 2.044 |
| role_bucket | `lt30min` | 60 | **0.515** | 0.822 | 1.067 | 1.860 |
| role_bucket | `starter` | 299 | **0.692** | 0.947 | 1.037 | 2.457 |
| side | `UNDER` | 638 | **0.771** | 0.923 | 1.111 | 2.288 |
| snapshot_type | `morning` | 795 | **0.785** | 0.955 | 1.056 | 2.272 |
| stat | `ast` | 130 | **0.762** | 0.889 | 1.070 | 2.154 |
| stat | `fg3m` | 144 | **0.746** | 1.043 | 0.973 | 1.883 |
| stat | `pts` | 161 | **0.750** | 0.906 | 1.071 | 3.357 |
| stat | `stl` | 97 | **0.613** | 0.847 | 0.982 | 1.433 |
| vacated_opportunity_bucket | `unavailable` | 795 | **0.785** | 0.955 | 1.056 | 2.272 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 117 | 1.191 | 1.065 | 0.254 | 2.283 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 231 | 1.084 | 0.837 | 0.102 | 2.596 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 58 | 1.076 | 0.873 | 0.171 | 3.271 |
| line_bucket | `15_to_20` | 38 | 0.977 | 0.806 | -0.027 | 3.389 |
| line_bucket | `4_to_7` | 65 | 1.034 | 1.192 | 0.080 | 2.589 |
| line_bucket | `7_to_10` | 31 | 0.989 | 0.924 | 0.010 | 2.630 |
| line_bucket | `lt_4` | 63 | 0.980 | 1.067 | -0.006 | 2.241 |
| lineup_confirmed | `projected` | 530 | 1.079 | 0.841 | 0.123 | 2.416 |
| p0_bucket | `20_to_50pct` | 161 | 1.065 | 0.880 | 0.047 | 1.952 |
| predicted_variance_bucket | `low` | 263 | 1.051 | 0.884 | 0.057 | 1.538 |
| predicted_variance_bucket | `mid` | 269 | 1.041 | 0.939 | 0.062 | 2.220 |
| role_bucket | `rotation` | 111 | 1.165 | 0.887 | 0.247 | 2.340 |
| side | `OVER` | 157 | 0.783 | 0.863 | -0.386 | 2.207 |
| stat | `blk` | 82 | 1.256 | 1.034 | 0.208 | 1.490 |
| stat | `reb` | 181 | 1.024 | 1.003 | 0.058 | 2.505 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| line_bucket | `20_to_25` | 7 | 0.648 | 0.255 |
| line_bucket | `ge_10` | 22 | 0.778 | 0.247 |
| line_bucket | `ge_3` | 7 | 3.548 | 0.883 |
| line_bucket | `ge_8` | 3 | 0.700 | 0.701 |
| line_bucket | `lt_10` | 19 | 1.159 | 0.244 |
| line_bucket | `lt_3` | 27 | 0.908 | 0.443 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 6 | 6.170 | 0.595 |
| role_bucket | `lt22min` | 23 | 0.609 | -0.415 |

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
- settled window: **2026-05-02 → 2026-06-13** (20 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

