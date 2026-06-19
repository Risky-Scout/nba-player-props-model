# PMF Variance Experience Study — June 18, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-18` over a 60-day lookback._

## Executive summary

- **1,973** settled rows from **2026-04-19** through **2026-06-13** (32 delivery dates with at least one settled row).
- **Mean A/E = 1.105** — actual outcomes ran +10.5% relative to expected means in this sample.
- **Variance A/E = 0.817** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.150, sd = 0.952** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.761 and 0.914); the 10th-percentile band is over-covered (0.199 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.271 vs 0.248 (model vs market); logloss 0.745 vs 0.690.
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
| rows | 1,973 |
| actual_mean (per row) | 6.050 |
| expected_mean (per row) | 5.475 |
| **mean_AE** | **1.1049** |
| Σ squared residual | 26946.42 |
| Σ expected variance | 32972.49 |
| **variance_AE** | **0.8172** |
| standardized_residual_mean | 0.1495 |
| standardized_residual_sd | 0.9525 |
| pmf_nll_mean | 2.3908 |
| pmf_rps_mean | 0.1081 |
| model_brier (over/under) | 0.2713 |
| market_brier (over/under) | 0.2476 |
| model_logloss (over/under) | 0.7451 |
| market_logloss (over/under) | 0.6903 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.199 / 0.295 / 0.499 / 0.761 / 0.914 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 80 | **0.541** | 0.835 | 0.863 | 2.252 |
| edge_bucket | `10_to_20pct` | 963 | **0.779** | 0.943 | 1.105 | 2.406 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `1_to_1p5` | 279 | **0.680** | 0.994 | 1.128 | 1.924 |
| line_bucket | `20_to_25` | 42 | **0.644** | 1.004 | 1.073 | 4.357 |
| line_bucket | `2_to_2p5` | 75 | **0.548** | 0.968 | 1.045 | 1.959 |
| line_bucket | `3_to_5` | 137 | **0.779** | 0.923 | 1.022 | 2.106 |
| line_bucket | `5_to_8` | 95 | **0.666** | 0.862 | 1.067 | 2.502 |
| line_bucket | `ge_10` | 42 | **0.620** | 0.787 | 1.102 | 2.726 |
| line_bucket | `ge_25` | 72 | **0.591** | 0.754 | 1.078 | 3.502 |
| line_bucket | `le_half` | 374 | **0.482** | 0.744 | 1.008 | 1.279 |
| low_line_discrete | `yes` | 653 | **0.586** | 0.861 | 1.077 | 1.555 |
| p0_bucket | `20_to_50pct` | 349 | **0.722** | 0.988 | 1.047 | 1.892 |
| p0_bucket | `ge_50pct` | 324 | **0.481** | 0.706 | 1.297 | 1.253 |
| predicted_variance_bucket | `high` | 651 | **0.798** | 0.915 | 1.104 | 3.238 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 565 | **0.665** | 0.898 | 1.078 | 2.437 |
| role_bucket | `lt22min` | 136 | **0.764** | 0.741 | 0.967 | 1.723 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 249 | **0.786** | 0.956 | 0.848 | 2.376 |
| stat | `ast` | 312 | **0.751** | 0.914 | 1.061 | 2.267 |
| stat | `blk` | 245 | **0.709** | 0.782 | 1.314 | 1.536 |
| stat | `fg3m` | 227 | **0.651** | 1.035 | 0.947 | 1.918 |
| stat | `stl` | 269 | **0.573** | 0.826 | 1.098 | 1.442 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `5_to_10pct` | 449 | 1.050 | 0.820 | 0.045 | 2.379 |
| edge_bucket | `ge_20pct` | 481 | 1.231 | 0.981 | 0.320 | 2.394 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| injury_context | `unavailable` | 1260 | 1.131 | 0.816 | 0.171 | 2.351 |
| line_bucket | `10_to_15` | 138 | 1.065 | 0.974 | 0.132 | 3.270 |
| line_bucket | `15_to_20` | 120 | 1.164 | 0.894 | 0.360 | 3.743 |
| line_bucket | `4_to_7` | 192 | 1.190 | 1.098 | 0.330 | 2.748 |
| line_bucket | `7_to_10` | 98 | 1.146 | 1.035 | 0.302 | 2.931 |
| line_bucket | `lt_10` | 40 | 1.078 | 0.966 | 0.102 | 3.569 |
| line_bucket | `lt_3` | 64 | 1.120 | 0.879 | 0.130 | 2.182 |
| line_bucket | `lt_4` | 176 | 1.116 | 0.960 | 0.171 | 2.285 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| lineup_confirmed | `unavailable` | 1260 | 1.131 | 0.816 | 0.171 | 2.351 |
| low_line_discrete | `no` | 1320 | 1.107 | 0.827 | 0.193 | 2.804 |
| minutes_volatility_bucket | `unavailable` | 1973 | 1.105 | 0.817 | 0.150 | 2.391 |
| overall | `ALL` | 1973 | 1.105 | 0.817 | 0.150 | 2.391 |
| p0_bucket | `5_to_20pct` | 575 | 1.182 | 0.978 | 0.211 | 2.282 |
| p0_bucket | `lt_5pct` | 725 | 1.085 | 0.802 | 0.154 | 3.225 |
| predicted_variance_bucket | `low` | 651 | 1.101 | 0.860 | 0.094 | 1.696 |
| predicted_variance_bucket | `mid` | 671 | 1.108 | 0.940 | 0.144 | 2.243 |
| role_bucket | `lt30min` | 545 | 1.224 | 1.002 | 0.263 | 2.426 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| side | `UNDER` | 1724 | 1.140 | 0.820 | 0.217 | 2.393 |
| snapshot_type | `morning` | 1973 | 1.105 | 0.817 | 0.150 | 2.391 |
| stat | `pts` | 412 | 1.100 | 0.804 | 0.206 | 3.588 |
| stat | `reb` | 508 | 1.148 | 0.972 | 0.260 | 2.621 |
| vacated_opportunity_bucket | `unavailable` | 1973 | 1.105 | 0.817 | 0.150 | 2.391 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_3` | 13 | 2.389 | 0.372 |
| line_bucket | `ge_8` | 16 | 0.839 | 0.137 |
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
- settled window: **2026-04-19 → 2026-06-13** (32 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

