# Derek PMF Snapshots — May 3, 2026

Generated 2026-05-03T23:36:31Z.

## Snapshot status

| Matchup | Current-live | T-minus-25 | Close-lock |
| --- | --- | --- | --- |
| Raptors @ Cavaliers | Available | Pending dispatch | Pending dispatch |
| Magic @ Pistons | Available, stale baseline | Missed during setup window; documented, not backfilled | Missed during setup window; documented, not backfilled |

Each subfolder is `<game_id>/<snapshot_type>/`. Visible labels use team names; the numeric `game_id` is preserved in file paths and technical manifests for the audit trail.

## Per-game files

### Raptors @ Cavaliers

_Game ID `21682000` (used in paths only). Tip time UTC: `2026-05-03T23:40:00Z`._

- **Current-live** (Available):
  - [snapshot_report.md](21682000/current_live/snapshot_report.md)
  - [market_comparison.csv](21682000/current_live/market_comparison.csv)
  - [full_pmf_wide.csv](21682000/current_live/full_pmf_wide.csv)
  - [outcome_level_probabilities.csv](21682000/current_live/outcome_level_probabilities.csv)
  - [pmf_driver_decomposition.md](21682000/current_live/pmf_driver_decomposition.md)
  - [lineup_injury_impact_report.md](21682000/current_live/lineup_injury_impact_report.md)
  - [direct_lineup_impact_report.md](21682000/current_live/direct_lineup_impact_report.md)
- **T-minus-25**: Pending dispatch
- **Close-lock**: Pending dispatch

### Magic @ Pistons

_Game ID `21684819` (used in paths only). Tip time UTC: `2026-05-03T19:40:00Z`._

- **Current-live** (Available, stale baseline):
  - [snapshot_report.md](21684819/current_live/snapshot_report.md)
  - [market_comparison.csv](21684819/current_live/market_comparison.csv)
  - [full_pmf_wide.csv](21684819/current_live/full_pmf_wide.csv)
  - [outcome_level_probabilities.csv](21684819/current_live/outcome_level_probabilities.csv)
  - [pmf_driver_decomposition.md](21684819/current_live/pmf_driver_decomposition.md)
  - [lineup_injury_impact_report.md](21684819/current_live/lineup_injury_impact_report.md)
  - [direct_lineup_impact_report.md](21684819/current_live/direct_lineup_impact_report.md)
- **T-minus-25** (Missed during setup window; documented, not backfilled):
  - [missed_snapshot_report.md](21684819/t_minus_25/missed_snapshot_report.md)
- **Close-lock** (Missed during setup window; documented, not backfilled):
  - [missed_snapshot_report.md](21684819/close_lock/missed_snapshot_report.md)

## PMF variance experience study

- [pmf_variance_experience_2026-05-03.md](https://github.com/Risky-Scout/nba-player-props-model/blob/main/artifacts/experience_studies/pmf_variance_experience_2026-05-03.md)
- Actuarial-style actual-to-expected diagnostic for settled rows. PMF variance is reasonably close overall but the model under-projects means and trails market on Brier/logloss in the current sample, so this is a diagnostic and improvement report rather than a market-superiority claim.

