# Derek PMF Snapshots — June 5, 2026

Generated 2026-06-06T00:23:25Z.

## Snapshot status

| Matchup | Current-live | T-minus-25 | Close-lock |
| --- | --- | --- | --- |
| Knicks @ Spurs | Available | Available (late but pre-tip) | Scheduled |

Each subfolder is `<game_id>/<snapshot_type>/`. Visible labels use team names; the numeric `game_id` is preserved in file paths and technical manifests for the audit trail.

## How to read this package

- **Start with the matchup-level `snapshot_report.md`** — it summarizes the slate, top edges, contextual minutes deltas, lineup status, and publishability gates.
- **Use `market_comparison.csv`** for side / line / model / market / edge / review status. The `edge_publish_status` and `edge_reasonability_status` columns govern action — anything tagged `WATCHLIST`, `REVIEW`, or `PUBLISH_BLOCKER` is not for action.
- **Use `full_pmf_wide.csv`** for the full per-row PMF JSON plus market probabilities — one row per (player, stat, side, line, book).
- **Use `outcome_level_probabilities.csv`** for the long-form outcome probabilities (one row per `(prop, k)`, `p_k` summing to 1 per prop). Repaired in Phase 13AB on 2026-05-03; verifier `scripts/verify_derek_outcome_level_probabilities.py` runs daily.
- **Use the PMF variance experience study** for after-the-fact calibration diagnostics: mean A/E, variance A/E, standardized residuals, quantile coverage, model-vs-market Brier and logloss across stat / side / role / line / edge / p0 / predicted-variance buckets. Sample is the trailing 60-day settled window (morning / current only). The report itself flags where the model is too narrow, too wide, or under-projecting means.
- **Current-live snapshots without confirmed lineups are watchlist / baseline output**, not final confirmed-lineup action output. The `lineup_confirmed` column in `market_comparison.csv` and the `WATCHLIST_NOT_CONFIRMED_LINEUP` publish status make this explicit.

## Per-game files

### Knicks @ Spurs

_Game ID `21716135` (used in paths only). Tip time UTC: `2026-06-06T00:40:00Z`._

- **Current-live** (Available):
  - [snapshot_report.md](21716135/current_live/snapshot_report.md)
  - [market_comparison.csv](21716135/current_live/market_comparison.csv)
  - [full_pmf_wide.csv](21716135/current_live/full_pmf_wide.csv)
  - [outcome_level_probabilities.csv](21716135/current_live/outcome_level_probabilities.csv)
  - [pmf_driver_decomposition.md](21716135/current_live/pmf_driver_decomposition.md)
  - [lineup_injury_impact_report.md](21716135/current_live/lineup_injury_impact_report.md)
  - [direct_lineup_impact_report.md](21716135/current_live/direct_lineup_impact_report.md)
- **T-minus-25** (Available (late but pre-tip)):
  - [snapshot_report.md](21716135/t_minus_25/snapshot_report.md)
  - [market_comparison.csv](21716135/t_minus_25/market_comparison.csv)
- **Close-lock**: Scheduled

## PMF variance experience study

- Latest study: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-06-05.md
- Index: https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/README.md
- Sample: trailing 60-day settled window of player-prop rows, morning / current settled rows only. T-minus-25 and close-lock scoring will become meaningful only after enough live snapshots settle — the prospective live-context sample still needs to build.
- Headline metrics (mean A/E, variance A/E, model Brier, market Brier, model logloss, market logloss) are reported in the linked study. In the current sample the model trails the market on binary scoring.
- Status: this is a diagnostic and improvement report. **Do not claim market superiority from this sample.** Next improvements: mean calibration, low-line discrete handling, fg3m dispersion, bucket-level recalibration, more settled live snapshots, confirmed-lineup / injury-context experience tracking.

