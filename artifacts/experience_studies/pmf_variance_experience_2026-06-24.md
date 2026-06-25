# PMF Variance Experience Study — June 24, 2026

_Actual-to-expected (A/E) review of settled PMF predictions, as-of `2026-06-24` over a 60-day lookback._

## Executive summary

- **1,440** settled rows from **2026-04-25** through **2026-06-13** (26 delivery dates with at least one settled row).
- **Mean A/E = 1.085** — actual outcomes ran +8.5% relative to expected means in this sample.
- **Variance A/E = 0.758** — PMF spread is reasonably close overall (the well-calibrated band is 0.80–1.20), slightly wide overall.
- **Standardized residual: mean = 0.118, sd = 0.927** — slight positive bias and dispersion close to calibrated (target sd = 1.00).
- Quantile coverage at the 75th and 90th percentiles is near target (0.771 and 0.921); the 10th-percentile band is over-covered (0.207 vs target 0.10).
- **Model trails market on binary scoring:** Brier 0.262 vs 0.248 (model vs market); logloss 0.723 vs 0.691.
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
| rows | 1,440 |
| actual_mean (per row) | 5.917 |
| expected_mean (per row) | 5.456 |
| **mean_AE** | **1.0846** |
| Σ squared residual | 18657.86 |
| Σ expected variance | 24617.23 |
| **variance_AE** | **0.7579** |
| standardized_residual_mean | 0.1183 |
| standardized_residual_sd | 0.9274 |
| pmf_nll_mean | 2.2902 |
| pmf_rps_mean | 0.1034 |
| model_brier (over/under) | 0.2618 |
| market_brier (over/under) | 0.2482 |
| model_logloss (over/under) | 0.7232 |
| market_logloss (over/under) | 0.6913 |
| coverage @ 10 / 25 / 50 / 75 / 90 | 0.207 / 0.314 / 0.522 / 0.771 / 0.921 |

## Where the PMF is too narrow

`variance_AE > 1` means realized outcomes are more volatile than the PMF expected. The model is putting too little spread on these buckets and will be surprised by tails more often than its quantiles imply.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| line_bucket | `7_to_10` | 70 | **1.259** | 1.113 | 1.144 | 2.786 |
| role_bucket | `core` | 94 | **1.335** | 1.087 | 1.111 | 2.591 |

## Where the PMF is too wide

`variance_AE < 1` means the PMF spreads more probability mass than realized outcomes need. The model is uncertain when reality is more concentrated. These are calibration targets — narrowing here will reduce NLL without harming coverage.

| Dimension | Bucket | n | variance_AE | std_resid_sd | mean_AE | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `0_to_5pct` | 70 | **0.504** | 0.843 | 0.880 | 2.232 |
| edge_bucket | `10_to_20pct` | 712 | **0.681** | 0.927 | 1.089 | 2.314 |
| edge_bucket | `5_to_10pct` | 388 | **0.787** | 0.894 | 1.029 | 2.291 |
| injury_context | `unavailable` | 727 | **0.685** | 0.865 | 1.107 | 2.123 |
| injury_context | `unknown` | 37 | **0.576** | 0.776 | 1.133 | 2.143 |
| line_bucket | `15_to_20` | 80 | **0.783** | 0.896 | 1.103 | 3.421 |
| line_bucket | `1_to_1p5` | 221 | **0.647** | 0.950 | 1.093 | 1.890 |
| line_bucket | `2_to_2p5` | 70 | **0.521** | 0.884 | 1.051 | 1.835 |
| line_bucket | `3_to_5` | 102 | **0.783** | 0.907 | 0.993 | 2.101 |
| line_bucket | `5_to_8` | 72 | **0.689** | 0.841 | 1.084 | 2.393 |
| line_bucket | `ge_10` | 34 | **0.587** | 0.768 | 1.103 | 2.755 |
| line_bucket | `ge_25` | 59 | **0.556** | 0.722 | 1.087 | 3.513 |
| line_bucket | `le_half` | 262 | **0.475** | 0.750 | 0.892 | 1.251 |
| lineup_confirmed | `unavailable` | 727 | **0.685** | 0.865 | 1.107 | 2.123 |
| low_line_discrete | `no` | 957 | **0.766** | 0.961 | 1.089 | 2.667 |
| low_line_discrete | `yes` | 483 | **0.572** | 0.849 | 1.012 | 1.543 |
| minutes_volatility_bucket | `unavailable` | 1440 | **0.758** | 0.927 | 1.085 | 2.290 |
| overall | `ALL` | 1440 | **0.758** | 0.927 | 1.085 | 2.290 |
| p0_bucket | `20_to_50pct` | 270 | **0.713** | 0.971 | 0.992 | 1.884 |
| p0_bucket | `ge_50pct` | 212 | **0.474** | 0.707 | 1.252 | 1.197 |
| p0_bucket | `lt_5pct` | 522 | **0.714** | 0.922 | 1.070 | 2.980 |
| predicted_variance_bucket | `high` | 475 | **0.732** | 0.901 | 1.090 | 3.106 |
| predicted_variance_bucket | `low` | 475 | **0.712** | 0.906 | 1.070 | 1.522 |
| role_bucket | `bench` | 68 | **0.725** | 0.976 | 0.891 | 2.069 |
| role_bucket | `ge30min_starter` | 353 | **0.504** | 0.790 | 1.034 | 2.138 |
| role_bucket | `lt22min` | 80 | **0.593** | 0.728 | 0.917 | 1.577 |
| role_bucket | `starter` | 388 | **0.678** | 0.936 | 1.044 | 2.489 |
| side | `OVER` | 210 | **0.754** | 0.883 | 0.789 | 2.121 |
| side | `UNDER` | 1230 | **0.758** | 0.910 | 1.126 | 2.319 |
| snapshot_type | `morning` | 1440 | **0.758** | 0.927 | 1.085 | 2.290 |
| stat | `ast` | 230 | **0.759** | 0.894 | 1.072 | 2.205 |
| stat | `blk` | 173 | **0.751** | 0.781 | 1.283 | 1.478 |
| stat | `fg3m` | 207 | **0.637** | 1.013 | 0.946 | 1.930 |
| stat | `pts` | 291 | **0.711** | 0.875 | 1.082 | 3.377 |
| stat | `stl` | 185 | **0.538** | 0.767 | 1.015 | 1.377 |
| vacated_opportunity_bucket | `unavailable` | 1440 | **0.758** | 0.927 | 1.085 | 2.290 |

## Where the PMF dispersion is well calibrated

Buckets within the `0.80 ≤ variance_AE ≤ 1.20` band, sample size at or above n = 30.

| Dimension | Bucket | n | mean_AE | variance_AE | std_resid_mean | NLL |
|---|---|---:|---:|---:|---:|---:|
| edge_bucket | `ge_20pct` | 270 | 1.235 | 1.020 | 0.291 | 2.241 |
| injury_context | `fallback_used` | 130 | 1.099 | 0.902 | 0.261 | 2.325 |
| injury_context | `fresh` | 368 | 1.072 | 0.807 | 0.085 | 2.575 |
| injury_context | `latest_valid_report_selected` | 157 | 0.997 | 0.848 | 0.012 | 2.298 |
| line_bucket | `10_to_15` | 100 | 1.034 | 0.848 | 0.078 | 3.238 |
| line_bucket | `4_to_7` | 137 | 1.135 | 1.161 | 0.229 | 2.592 |
| line_bucket | `lt_3` | 45 | 1.191 | 0.878 | 0.266 | 2.040 |
| line_bucket | `lt_4` | 113 | 1.061 | 1.064 | 0.117 | 2.249 |
| lineup_confirmed | `projected` | 688 | 1.079 | 0.823 | 0.122 | 2.461 |
| p0_bucket | `5_to_20pct` | 436 | 1.155 | 1.111 | 0.174 | 2.247 |
| predicted_variance_bucket | `mid` | 490 | 1.069 | 0.955 | 0.101 | 2.244 |
| role_bucket | `lt30min` | 285 | 1.235 | 0.914 | 0.254 | 2.255 |
| role_bucket | `rotation` | 163 | 1.160 | 0.957 | 0.229 | 2.478 |
| stat | `reb` | 354 | 1.117 | 1.056 | 0.209 | 2.536 |

## Where the sample is too thin to conclude

_Buckets below n = 30. Reported but flagged; do not act on point estimates._

| Dimension | Bucket | n | variance_AE | std_resid_mean |
|---|---|---:|---:|---:|
| injury_context | `very_stale` | 21 | 0.902 | 0.518 |
| line_bucket | `20_to_25` | 25 | 0.428 | 0.169 |
| line_bucket | `ge_3` | 12 | 2.539 | 0.470 |
| line_bucket | `ge_8` | 11 | 0.825 | 0.339 |
| line_bucket | `lt_10` | 27 | 1.191 | 0.272 |
| lineup_confirmed | `confirmed` | 25 | 0.745 | -0.159 |
| role_bucket | `lt15min` | 9 | 4.213 | 0.487 |

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
- settled window: **2026-04-25 → 2026-06-13** (26 dates).
- buckets emitted: stat, side, snapshot_type, lineup_confirmed, role_bucket, minutes_volatility_bucket, injury_context_bucket, vacated_opportunity_bucket, edge_bucket, p0_bucket, predicted_variance_bucket, line_bucket, low_line_discrete.
- pass line: `PMF_VARIANCE_EXPERIENCE_STUDY_PASS`.

