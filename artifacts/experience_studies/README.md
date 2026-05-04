# PMF Variance Experience Studies

Actuarial-style actual-to-expected (A/E) reviews of settled PMF predictions. One study per as-of date; the latest reflects the freshest joinable settled sample.

## What the study measures

Each settled (player, game, stat, line, side) row carries a model PMF and a realized outcome. Per row we compute and roll up:

- **Mean calibration** — `mean_AE = Σ actual / Σ expected_mean`. 1.00 = unbiased point estimate. Reads on whether PMF means systematically over- or under-shoot.
- **Variance calibration** — `variance_AE = Σ (actual − mean)² / Σ expected_variance`. 1.00 = PMF spread matches reality. > 1 means realized outcomes are more volatile than the PMF said (PMF too narrow); < 1 means the PMF is wider than reality.
- **Standardized residuals** — `(actual − mean) / √variance`. Calibrated PMFs produce residuals with mean ≈ 0 and sd ≈ 1.
- **Quantile coverage** — fraction of actuals at or below the model 10/25/50/75/90th percentiles. Should equal α.
- **PMF likelihood** — mean negative-log-likelihood of the realized outcome plus ranked probability score (RPS).
- **Model-vs-market scoring** — over/under Brier and logloss using `model_p_over` and the market no-vig over probability. Lower is better.

Aggregations are reported overall and by stat / side / snapshot_type / lineup_confirmed / role_bucket / minutes_volatility_bucket / injury_context_bucket / vacated_opportunity_bucket / edge_bucket / p0_bucket / predicted_variance_bucket / line_bucket / low_line_discrete.

## Latest study

- **As-of 2026-05-03:** https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-05-03.md
- Sibling artifacts in the same folder:
  - `pmf_variance_experience_2026-05-03.csv` — bucket-level metrics table.
  - `pmf_variance_experience_2026-05-03.json` — machine-readable schema with overall, buckets, provenance.

## Current sample definition

- **1,001** settled player-prop rows.
- Window: **2026-04-17** through **2026-05-02** (15 delivery dates with at least one settled row).
- Snapshot coverage: **morning / current settled rows only.** T-minus-25 and close-lock rows are not yet scored — `score_derek_live_snapshots_after_game.py` reports `pending_outcomes` until enough live snapshots accumulate joinable game stats.
- Lookback parameter: 60 days. Min sample for non-thin buckets: 30.

## Current headline metrics

| metric | value | reading |
|---|---:|---|
| rows | 1,001 | settled player-prop rows |
| mean A/E | **1.144** | actuals ran ~14.4% above expected means |
| variance A/E | **0.913** | reasonably close, slightly wide |
| standardized residual mean | 0.211 | slight positive bias |
| standardized residual sd | 1.052 | dispersion close to calibrated (target 1.00) |
| coverage @ 10 | 0.195 | over-covered low tail |
| coverage @ 75 | 0.746 | near target |
| coverage @ 90 | 0.899 | near target |
| model Brier (over/under) | **0.278** | trails market |
| market Brier (over/under) | **0.246** | — |
| model logloss (over/under) | **0.762** | trails market |
| market logloss (over/under) | **0.688** | — |

The model trails the market on binary scoring in this sample. Read the study as a recalibration roadmap, not a market-superiority claim.

## Where the model is too narrow / too wide

From the latest study (n ≥ 30, sufficient sample):

- **Too narrow (variance A/E > 1.20):** `predicted_variance_bucket=low` (1.41), `side=OVER` (1.36), `stat=fg3m` (2.01).
- **Too wide (variance A/E < 0.80):** `low_line_discrete=yes` (0.63), `p0 ≥ 50%` (0.50), `ge30min_starter` role (0.75), `stat=ast` (0.72), `stat=blk` (0.59), `stat=stl` (0.55), and several line buckets (`le_half`, `5_to_8`, `20_to_25`).

## Verifier outcomes

The verifier (`scripts/verify_pmf_variance_experience_study.py`) emits one of:

- **`PMF_VARIANCE_EXPERIENCE_STUDY_PASS`** — all metrics finite, sample non-empty, market-superiority caveat present (or absent because market data is absent), live-context limitations documented, links present.
- **`PMF_VARIANCE_EXPERIENCE_STUDY_WARN`** — same pass criteria, but the model trails the market on Brier in this sample (or thin-sample / link warnings exist). The WARN status is intentional and is itself the audit trail. The current as-of-2026-05-03 run emits WARN because the model trails market on Brier; the report flags this honestly.
- **`PMF_VARIANCE_EXPERIENCE_STUDY_FAILED`** — missing files, invalid metrics, parse errors, or dishonest report language (e.g. missing the no-market-superiority caveat when warranted).

## How future studies will be interpreted

- The study runs daily after `after_game_scoring` settles. The daily PMF delivery `after_game` workflow runs both the build and the verifier as non-blocking steps — insufficient samples produce honest `WARN` reports rather than failing the pipeline.
- Conclusions should never be drawn from a single day. Trends matter: if mean A/E stays > 1.10 for several weeks, the role-aware mean centering needs re-fitting. If `variance_AE` for a stat moves outside 0.80–1.20 with n ≥ 100, that stat-level dispersion calibration is the next target.
- Once **t_minus_25** and **close_lock** rows have realized outcomes joined, the snapshot-type comparison becomes the primary use of this study. Until then, it is a morning-slate diagnostic only.
- `lineup_confirmed`, `injury_context`, `minutes_volatility`, and `vacated_opportunity` buckets remain thin or unavailable. They will become meaningful only as the after-game scoring feed accumulates more delivery dates and the live-context fields populate.

## Provenance

- Build script: `scripts/build_pmf_variance_experience_study.py`
- Verifier: `scripts/verify_pmf_variance_experience_study.py`
- Inputs:
  - `deliveries/<date>/after_game_scoring/after_game_scoring.parquet` (Source A — preferred metadata: snapshot_type, role_bucket, lineup/injury freshness)
  - `predictions/all_props_<date>.parquet` joined with `data/player_game_stats.parquet` (Source B — row spine: per (player, stat, side, line) with realized outcomes)
- The Phase 13X Wizard of Odds protections still apply — this study reads from `predictions/` and `deliveries/<date>/after_game_scoring/`, never from WoO outputs.
