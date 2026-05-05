# Derek review examples — 2026-05-04

_Generated 2026-05-05T02:43:30+00:00._

Plain-English walkthrough of the files in this folder. Use them to validate that ingestion and downstream consumption is structurally sound for Derek / EV Analytics.

## What's in this folder

- `missing_projection_audit.csv` — every (player, stat)   combination expected for the slate, with `status=DELIVERED` or   `status=MISSING` plus the reason for any miss (no market line,   no minutes, ingestion mismatch, etc.).   **196 rows.**
- `context_event_audit.md` — schema for capturing late-breaking   lineup / injury news (e.g. Ayo Dosunmu ruled out at 3 PM ET).   Shows the worked example format and which production reports   carry the same fields.
- `player_difference_decomposition.csv` — per (player, stat)   view of model mean vs market line, role bucket, lineup /   injury context, and short distribution notes (p0, variance,   mean−line shift).   **65 rows.**
- `README.md` — this file.

## How to use these in a Derek call

1. **Coverage check** — open `missing_projection_audit.csv` and    filter `status=MISSING`. Each row tells you why the model did    not produce a prop for that (player, stat). The most common    honest reason is `no market line for any prop on this player`    — Derek's pipeline can confirm whether the sportsbook posted    a market.
2. **Late-news framework** — `context_event_audit.md` shows the    field shape Derek's downstream tooling should expect when an    event drops within the snapshot window. The worked example is    illustrative; the real fields come from the snapshot's    `lineup_injury_impact_report.md` and    `direct_lineup_impact_report.md`.
3. **Why this player diverges from market** — open    `player_difference_decomposition.csv` and sort by    `model_mean − market_line`. Each row's `distribution_notes`    records the headline reason: high p0 (DNP risk), wide    variance (uncertain minutes), or a mean shift relative to the    line.

## Hard rules

- These files are derived from `predictions/all_props_<date>.parquet` and the per-snapshot manifests. **No model   probabilities are re-computed.**
- When a Derek-named player (Ayo Dosunmu, Wembanyama, etc.) is   not in tonight's slate, the audit explicitly shows   `status=NOT_IN_SLATE` rather than fabricating a row.
- Coverage gaps map to specific reasons; ingestion mismatches   are flagged distinctly from honest "no market line".

