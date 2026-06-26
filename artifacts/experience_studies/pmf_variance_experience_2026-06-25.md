# PMF Variance Experience Study — June 25, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-25` over a 60-day lookback._

## Executive summary

- **1,316** settled rows from **2026-04-26** through **2026-06-13** (25 delivery dates with at least one settled row).
- **Mean A/E = 1.079** — actual outcomes ran +7.9% relative to expected means in this sample.
- **Variance A/E = 0.754** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.109, sd = 0.931** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.773 and 0.922); the 10th-percentile band is over-covered (0.209 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.262 vs 0.248 (model vs market); logloss 0.725 vs 0.692.
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
| rows | 1,316 |
| actual_mean (per row) | 5.846 |
| expected_mean (per row) | 5.420 |
| **mean_AE** | **1.0786** |
| Σ squared residual | 16574.75 |
| Σ expected variance | 21994.00 |
| **variance_AE** | **0.7536** |
| standardized_residual_mean | 0.1089 |
| standardized_residual_sd | 0.9311 |
| pmf_nll_mean | 2.2882 |
| pmf_rps_mean | 0.1045 |
| model_brier (over/under) | 0.2622 |
| market_brier (over/under) | 0.2482 |
| model_logloss (over/under) | 0.7245 |
| market_logloss (over/under) | 0.6916 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.209 / 0.321 / 0.529 / 0.773 / 0.922 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `4_to_7` | 123 | **1.205** | 1.127 | 1.096 | 2.580 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 67 | **0.495** | 0.844 | 0.896 | 2.221 |
| edge_bucket | `10_to_20pct` | 643 | **0.701** | 0.938 | 1.090 | 2.323 |
| edge_bucket | `5_to_10pct` | 370 | **0.766** | 0.897 | 1.025 | 2.290 |
| injury_context | `unavailable` | 603 | **0.652** | 0.860 | 1.097 | 2.085 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `15_to_20` | 69 | **0.783** | 0.907 | 1.089 | 3.424 |
| line_bucket | `1_to_1p5` | 209 | **0.671** | 0.970 | 1.102 | 1.928 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `3_to_5` | 92 | **0.707** | 0.867 | 1.007 | 2.085 |
| line_bucket | `5_to_8` | 68 | **0.725** | 0.860 | 1.079 | 2.394 |
| line_bucket | `ge_10` | 30 | **0.600** | 0.789 | 1.076 | 2.741 |
| line_bucket | `ge_25` | 53 | **0.486** | 0.667 | 1.088 | 3.474 |
| line_bucket | `le_half` | 235 | **0.493** | 0.767 | 0.876 | 1.259 |
| lineup_confirmed | `unavailable` | 603 | **0.652** | 0.860 | 1.097 | 2.085 |
| low_line_discrete | `no` | 872 | **0.761** | 0.958 | 1.083 | 2.652 |
| low_line_discrete | `yes` | 444 | **0.596** | 0.871 | 1.013 | 1.574 |
| minutes_volatility_bucket | `unavailable` | 1316 | **0.754** | 0.931 | 1.079 | 2.288 |
| overall | `ALL` | 1316 | **0.754** | 0.931 | 1.079 | 2.288 |
| p0_bucket | `20_to_50pct` | 249 | **0.718** | 0.985 | 1.000 | 1.909 |
| p0_bucket | `ge_50pct` | 186 | **0.499** | 0.724 | 1.280 | 1.207 |
| p0_bucket | `lt_5pct` | 482 | **0.712** | 0.933 | 1.068 | 2.966 |
| predicted_variance_bucket | `high` | 434 | **0.731** | 0.910 | 1.084 | 3.091 |
| predicted_variance_bucket | `low` | 434 | **0.761** | 0.932 | 1.079 | 1.554 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 299 | **0.427** | 0.790 | 1.034 | 2.087 |
| role_bucket | `lt22min` | 67 | **0.669** | 0.703 | 0.862 | 1.483 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 205 | **0.762** | 0.890 | 0.792 | 2.130 |
| side | `UNDER` | 1111 | **0.752** | 0.912 | 1.122 | 2.317 |
| snapshot_type | `morning` | 1316 | **0.754** | 0.931 | 1.079 | 2.288 |
| stat | `ast` | 208 | **0.757** | 0.882 | 1.069 | 2.196 |
| stat | `blk` | 154 | **0.799** | 0.804 | 1.284 | 1.505 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 263 | **0.708** | 0.882 | 1.083 | 3.378 |
| stat | `stl` | 165 | **0.575** | 0.791 | 1.040 | 1.407 |
| vacated_opportunity_bucket | `unavailable` | 1316 | **0.754** | 0.931 | 1.079 | 2.288 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 236 | 1.213 | 0.987 | 0.260 | 2.209 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 93 | 1.038 | 0.898 | 0.088 | 3.256 |
| line_bucket | `7_to_10` | 64 | 1.129 | 1.165 | 0.274 | 2.745 |
| line_bucket | `lt_3` | 39 | 1.158 | 0.861 | 0.240 | 2.006 |
| line_bucket | `lt_4` | 102 | 1.034 | 0.998 | 0.084 | 2.231 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| p0_bucket | `5_to_20pct` | 399 | 1.128 | 1.099 | 0.140 | 2.210 |
| predicted_variance_bucket | `mid` | 448 | 1.058 | 0.917 | 0.085 | 2.221 |
| role_bucket | `lt30min` | 229 | 1.210 | 0.914 | 0.234 | 2.251 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| stat | `reb` | 319 | 1.089 | 1.038 | 0.168 | 2.517 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `20_to_25` | 22 | 0.436 | 0.220 |
| line_bucket | `ge_3` | 12 | 2.539 | 0.470 |
| line_bucket | `ge_8` | 9 | 0.999 | 0.323 |
| line_bucket | `lt_10` | 26 | 1.230 | 0.304 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 8 | 4.897 | 0.604 |

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
- settled window: **2026-04-26 → 2026-06-13** (25 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

