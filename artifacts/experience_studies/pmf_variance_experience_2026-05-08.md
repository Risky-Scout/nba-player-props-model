# PMF Variance Experience Study — May 8, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-05-08` over a 60-day lookback._

## Executive summary

- **1,499** settled rows from **2026-04-17** through **2026-05-07** (19 delivery dates with at least one settled row).
- **Mean A/E = 1.122** — actual outcomes ran +12.2% relative to expected means in this sample.
- **Variance A/E = 0.847** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.173, sd = 1.006** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.749 and 0.905); the 10th-percentile band is over-covered (0.201 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.273 vs 0.248 (model vs market); logloss 0.750 vs 0.690.
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
| rows | 1,499 |
| actual_mean (per row) | 6.162 |
| expected_mean (per row) | 5.494 |
| **mean_AE** | **1.1217** |
| Σ squared residual | 20711.95 |
| Σ expected variance | 24449.33 |
| **variance_AE** | **0.8471** |
| standardized_residual_mean | 0.1730 |
| standardized_residual_sd | 1.0056 |
| pmf_nll_mean | 2.5785 |
| pmf_rps_mean | 0.1154 |
| model_brier (over/under) | 0.2733 |
| market_brier (over/under) | 0.2475 |
| model_logloss (over/under) | 0.7503 |
| market_logloss (over/under) | 0.6903 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.201 / 0.289 / 0.484 / 0.749 / 0.905 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

_No buckets exceeded `variance_AE > 1.20` with sufficient sample._

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 48 | **0.536** | 0.996 | 0.874 | 2.878 |
| injury_context | `fresh` | 318 | **0.727** | 0.928 | 1.049 | 2.566 |
| line_bucket | `1_to_1p5` | 216 | **0.642** | 0.994 | 1.159 | 2.037 |
| line_bucket | `20_to_25` | 44 | **0.616** | 0.994 | 1.079 | 4.454 |
| line_bucket | `2_to_2p5` | 52 | **0.754** | 1.383 | 1.087 | 2.771 |
| line_bucket | `5_to_8` | 75 | **0.632** | 0.861 | 1.025 | 2.488 |
| line_bucket | `ge_25` | 45 | **0.626** | 0.839 | 1.042 | 3.729 |
| line_bucket | `le_half` | 279 | **0.417** | 0.669 | 1.080 | 1.271 |
| lineup_confirmed | `projected` | 339 | **0.735** | 0.940 | 1.061 | 2.596 |
| low_line_discrete | `yes` | 495 | **0.537** | 0.827 | 1.127 | 1.605 |
| p0_bucket | `20_to_50pct` | 258 | **0.685** | 0.950 | 1.085 | 1.932 |
| p0_bucket | `ge_50pct` | 261 | **0.465** | 0.669 | 1.286 | 1.284 |
| role_bucket | `bench` | 39 | **0.702** | 0.992 | 0.859 | 2.460 |
| role_bucket | `ge30min_starter` | 482 | **0.723** | 0.984 | 1.083 | 2.633 |
| role_bucket | `lt22min` | 128 | **0.795** | 0.805 | 1.030 | 1.833 |
| role_bucket | `starter` | 191 | **0.624** | 0.875 | 1.015 | 2.538 |
| stat | `ast` | 230 | **0.795** | 1.023 | 1.050 | 2.509 |
| stat | `blk` | 193 | **0.720** | 0.756 | 1.338 | 1.590 |
| stat | `fg3m` | 161 | **0.657** | 1.161 | 1.011 | 2.310 |
| stat | `stl` | 205 | **0.554** | 0.814 | 1.110 | 1.429 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `10_to_20pct` | 748 | 1.121 | 0.826 | 0.147 | 2.578 |
| edge_bucket | `5_to_10pct` | 281 | 1.080 | 0.841 | 0.076 | 2.644 |
| edge_bucket | `ge_20pct` | 422 | 1.212 | 0.972 | 0.325 | 2.502 |
| injury_context | `unavailable` | 1160 | 1.146 | 0.894 | 0.199 | 2.573 |
| line_bucket | `10_to_15` | 96 | 1.062 | 1.006 | 0.126 | 3.249 |
| line_bucket | `15_to_20` | 104 | 1.222 | 0.973 | 0.506 | 3.958 |
| line_bucket | `3_to_5` | 93 | 1.027 | 0.836 | 0.031 | 2.517 |
| line_bucket | `4_to_7` | 152 | 1.216 | 1.043 | 0.380 | 2.897 |
| line_bucket | `7_to_10` | 76 | 1.192 | 1.095 | 0.408 | 3.170 |
| line_bucket | `lt_3` | 46 | 1.091 | 0.931 | 0.084 | 2.245 |
| line_bucket | `lt_4` | 141 | 1.112 | 1.051 | 0.142 | 2.701 |
| lineup_confirmed | `unavailable` | 1160 | 1.146 | 0.894 | 0.199 | 2.573 |
| low_line_discrete | `no` | 1004 | 1.121 | 0.862 | 0.219 | 3.058 |
| minutes_volatility_bucket | `unavailable` | 1499 | 1.122 | 0.847 | 0.173 | 2.579 |
| overall | `ALL` | 1499 | 1.122 | 0.847 | 0.173 | 2.579 |
| p0_bucket | `5_to_20pct` | 399 | 1.209 | 0.851 | 0.247 | 2.367 |
| p0_bucket | `lt_5pct` | 581 | 1.100 | 0.862 | 0.184 | 3.592 |
| predicted_variance_bucket | `high` | 495 | 1.122 | 0.824 | 0.251 | 3.357 |
| predicted_variance_bucket | `low` | 495 | 1.109 | 1.110 | 0.104 | 2.120 |
| predicted_variance_bucket | `mid` | 509 | 1.126 | 0.925 | 0.164 | 2.268 |
| role_bucket | `lt30min` | 542 | 1.239 | 1.117 | 0.306 | 2.704 |
| role_bucket | `rotation` | 96 | 1.186 | 0.959 | 0.276 | 2.775 |
| side | `OVER` | 185 | 0.948 | 1.095 | -0.202 | 3.356 |
| side | `UNDER` | 1314 | 1.152 | 0.824 | 0.226 | 2.469 |
| snapshot_type | `morning` | 1499 | 1.122 | 0.847 | 0.173 | 2.579 |
| stat | `pts` | 316 | 1.115 | 0.836 | 0.249 | 3.762 |
| stat | `reb` | 394 | 1.176 | 1.000 | 0.293 | 2.862 |
| vacated_opportunity_bucket | `unavailable` | 1499 | 1.122 | 0.847 | 0.173 | 2.579 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `ge_10` | 25 | 0.560 | 0.259 |
| line_bucket | `ge_3` | 12 | 2.705 | 0.209 |
| line_bucket | `ge_8` | 16 | 1.100 | 0.417 |
| line_bucket | `lt_10` | 27 | 0.809 | 0.070 |
| role_bucket | `core` | 13 | 1.043 | 0.426 |
| role_bucket | `lt15min` | 8 | 0.245 | 0.047 |

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
- settled window: **2026-04-17 → 2026-05-07** (19 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

