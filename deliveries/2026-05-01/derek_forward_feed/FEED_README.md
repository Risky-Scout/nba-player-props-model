# Derek forward feed — 2026-05-01

This package is the forward-looking PMF feed for the dated slate. All PMFs are **model-only** and were never market-anchored. Market columns are reference-only.

## Files Derek should archive daily

Open these in order. Archive the entire `derek_forward_feed/` folder per date.

- `feed_manifest.json` — provenance, row counts, finality.
- `morning_snapshot.csv` — pre-lineup snapshot (canonical).
- `morning_snapshot.parquet` — same data, columnar.
- `morning_snapshot.jsonl` — same data, one JSON record per line.
- `latest_available_snapshot.csv` / `.parquet` — convenience pointer to the freshest snapshot on disk for this date (lineup_snapshot when available, else morning_snapshot).
- `lineup_snapshot.{csv,parquet,jsonl}` — official-lineup / near-tip snapshot when produced.
- `lineup_snapshot_status.json` — present only when no lineup snapshot package exists yet; documents the honest reason.

## Snapshot summary

- **morning**: not produced
- **lineup**  rows: 1369  snapshot_time_utc: `2026-05-01T23:15:06Z`

## Schema (per row)

Identity, model PMF, market reference, quality/finality. The full column list is documented in the feed_manifest.json `schema` block.
- One row per (player, stat, book, line) where a market quote exists.
- One model-only row per (player, stat) where no market exists (book and line blank).
- TOV PMFs (when present in canonical) appear as model-only rows.

## Hard rules

- PMFs are sourced from `pmf_model_review_package/machine_readable/model_only.parquet` — the canonical model-only file.
- Market fields come from `wizard_of_odds/market_comparison.parquet`. Market is reference-only; PMFs are never market-anchored.
- Phase 10D / 10D.2 TOV overlays are **not** wired in. TOV PMFs (when emitted) come from Phase 8 calibrators; see the run manifest's `tov_overlay` and `tov_status`.
- After-game outcomes are scored separately under `deliveries/{date}/after_game_scoring/` once finals are available.
