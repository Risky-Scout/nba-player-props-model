# Wizard of Odds — 2026-05-07

## Run status — 2026-05-07 — snapshot `pre_close`

**PROVISIONAL** — safe to use, with the caveats below

- props: **330**
- books: **14**
- market coverage: **full**
- injury freshness: **fresh**
- role provenance: `derived_from_projected_minutes`: 330
- model: `c181c86#phase10c`

### Caveats

Full detail (including the `required_to_resolve` field for each blocker) is in `wizard_of_odds/run_manifest.json`.

- `lineup_unconfirmed` — No confirmed-lineup rows were present. This is acceptable for morning/provisional outputs but not final lock outputs.

---

## Files

| file | role |
|---|---|
| `fair_odds_board.{csv,parquet,jsonl}` | one row per (player, stat, line) with the model's fair over/under American odds. Independent of any book. |
| `full_pmfs_wide.{csv,parquet}` | one row per (player, stat) with `pmf_json`, `mean`, `median`, `mode`, `p0`, `p_ge_1 … p_ge_20`. |
| `full_pmfs_outcome_level.{csv,parquet}` | long form: one row per (player, stat, k) with `P(outcome=k)`. |
| `market_comparison.{csv,parquet}` | one row per (player, stat, line, book) joining the model fair odds to the book's offered odds and no-vig probability. |
| `publishable_edges.{csv,parquet}` | subset of `market_comparison` filtered by `\|edge\| ≥ threshold` and quality flags. |
| `run_manifest.json` | sources, snapshot lifecycle, quality rollup, model version, finality status, and the freshness manifest passthrough. |
| `after_game_clv_and_scoring.{csv,parquet,md}` | post-tip CLV + scoring artifacts (added by `scripts/score_daily_pmf_delivery_after_game.py`). |

## Run summary

- **finality_status**: `provisional`
- **finality_blockers**: `['lineup_unconfirmed']`
- **market_coverage_status**: `full`
- **odds.fetch_status**: `consumed_from_disk`
- **books_seen**: `14`
- **freshness.overall_status**: `not_ready`
- **availability_freshness_status**: `fresh`
- **role_freshness_status (rollup)**: `{'derived_from_projected_minutes': 330}`
- **tov_status**: `present`
- **row counts**: fair_odds_board=7722, full_pmfs_wide=330, market_comparison=1617, publishable_edges=1127
- **after-game scoring**: `pending_outcomes` — scoring runner has not yet been invoked for this delivery

## Hard rules echoed in this package

- **Model-only PMFs are canonical.** Market columns are reference only; no probability has been adjusted to fit a book line.
- **TOV PMFs (when present) come from Phase 8 calibrators with no Phase 10D / 10D.2 overlay** — those overlays did not pass independent validation.
- **Sparse market coverage does not drop a row** — every model-only row is emitted; market joins are best-effort.
- **Provenance** — `model_version` and `pipeline_run_id` are present on every row and reproduced verbatim in `run_manifest.json`.

See `docs/daily_pmf_delivery_spec.md` for the full row schema and §7 validation gates, and `docs/daily_data_freshness_runbook.md` for the freshness manifest contract.
