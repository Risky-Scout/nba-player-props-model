# Derek Live Snapshot Pipeline (Phase 13L)

This document describes Derek's per-game live snapshot pipeline. It is
**additive** to the existing daily delivery and nightly training pipelines
and does not modify Wizard of Odds outputs, the daily PMF review package,
champion promotion, or nightly retraining.

## What changed

1. **Morning baseline is no longer Derek's main actionable snapshot.** The
   existing morning / WoO-monetization deliveries continue to ship as
   before, but Derek now also receives **per-game live snapshots** that
   recompute PMFs closer to tip-off using the freshest available inputs.

2. **Two pre-game snapshots per game.**
   - **T-minus-25**: ~25 minutes before scheduled tip. Recomputes PMFs
     using the latest available injury / availability / projected-minutes /
     market inputs.
   - **Close-lock**: ~5 minutes before tip (more conservative than -2 to
     absorb GitHub Actions runner latency). Recomputes PMFs or fails
     verification — never reuses post-tip data.

3. **Confirmed-lineup status is recorded explicitly.** Phase 13L does NOT
   wire a confirmed-lineup source. Every snapshot manifest carries
   `lineup_confirmed=false`, `lineup_aware=false`,
   `lineup_blocker="no confirmed lineup source wired"`. When a future
   phase wires a real confirmed-lineup source, the runner will populate
   `lineup_source`, `lineup_fetched_at_utc`, and flip the booleans —
   everything downstream is already wired to consume those fields.

4. **Confirmed outs are removed or marked non-actionable.** `predict.py`
   already filters confirmed-out players out of the predictions parquet.
   Phase 13L's per-game runner inherits that behavior. The snapshot
   manifest records `players_removed_confirmed_out`,
   `players_marked_non_actionable`, and `active_players_projected`.

5. **Market comparison is snapshot-specific.** Each snapshot's
   `market_comparison.{csv,parquet}` reflects the market available at
   the snapshot run time. The T-minus-25 snapshot is generated 25 min
   before tip; the close-lock snapshot is generated ~5 min before tip.
   `market_no_vig_over_prob` and `model_p_over` are paired per row so
   downstream scoring (Phase 13L-bis) can compute snapshot-specific
   model-vs-market deltas.

6. **After-game scoring will be snapshot-specific.** Phase 13L core scope
   ships the snapshot runner + dispatcher + verifier. The scoring +
   rolling-benchmark scripts that consume snapshot outputs after games
   are deferred to a follow-up phase (13L-bis) — they require live
   snapshots to actually exist for completed games before they can be
   built on real data.

7. **Movement between T-minus-25 and close.** Once both snapshots exist
   for a game, downstream tooling will compute model-probability and
   market-probability deltas. Phase 13L-bis emits the per-game
   `snapshot_comparison.{csv,parquet,md}`.

8. **Accuracy improvement is evaluated prospectively, not assumed.** No
   claim that live snapshots improve accuracy is made until 13L-bis's
   snapshot-specific scoring proves it on completed games.

## Output structure

```
deliveries/<YYYY-MM-DD>/derek_game_snapshots/
  <game_id>/
    t_minus_25/
      snapshot_manifest.json     # provenance + recomputation proof
      snapshot_report.md
      prop_summary.{csv,parquet}
      full_pmf_wide.{csv,parquet}
      outcome_level_probabilities.{csv,parquet}
      market_comparison.{csv,parquet}
    close_lock/
      <same files>
    snapshot_comparison.{csv,parquet,md}  # 13L-bis: emitted when both snapshots exist
```

`deliveries/<date>/derek_game_snapshots/` is **only ever written by Phase 13L
scripts**. The verifier `scripts/verify_phase13l_no_breakage.py` enforces that
the new pipeline never writes under `wizard_of_odds/`, `derek_forward_feed/`,
`pmf_model_review_package/`, or `canonical_source/`.

## Snapshot modes

Every snapshot manifest declares its **`snapshot_mode`** explicitly:

- **`production_live`** — the runner invoked `scripts/predict.py` itself
  during this snapshot's window and got a clean exit. Manifest carries
  `pmfs_recomputed=true`, `pmf_source=live_snapshot_recomputed`,
  `pmf_recomputation_predict_invocation_succeeded=true`. This is the only
  mode that proves true live PMF recomputation.
- **`backfill_demo`** — the runner ran with `--allow-backfill-test` (or
  workflow input `allow_backfill_test=true`) and reused an existing
  canonical `predictions/all_props_<date>.parquet`. Manifest carries
  `pmfs_recomputed=false`, `pmf_source=live_snapshot_reused_canonical`.
  This is **infrastructure proof only** — it verifies the snapshot
  pipeline plumbing, not live recomputation.

Production cron and normal `workflow_dispatch` runs are **production_live**.
Canonical reuse is allowed only with the explicit `--allow-backfill-test`
flag. In production-live mode, if predict.py cannot be invoked
successfully, the runner exits 1 with `DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED`
rather than silently falling back to canonical reuse.

## Key fields recorded per snapshot manifest

| Field | Meaning |
| --- | --- |
| `snapshot_mode` | `production_live` or `backfill_demo` (see above) |
| `pmfs_recomputed` | `true` only when predict.py was invoked by THIS runner with exit 0 |
| `pmf_source` | `live_snapshot_recomputed` (production_live) or `live_snapshot_reused_canonical` (backfill_demo) |
| `pmf_recomputation_predict_invocation_succeeded` | `true` iff this runner ran predict.py and it exited 0 |
| `pmf_recomputation_backfill_reused_canonical` | `true` iff the runner reused an existing canonical parquet |
| `prediction_run_id` | Per-snapshot run identifier |
| `prediction_code_commit` | Git SHA at snapshot time |
| `pmf_generated_at_utc` | mtime of the predictions parquet — must be ≥ run_started_at in production_live |
| `input_manifest_hash` | SHA-256 prefix of the consumed `predictions/all_props_<date>.parquet` |
| `pmf_output_hash` | SHA-256 prefix of the snapshot's `full_pmf_wide.parquet` |
| `champion_*` | Mirrors `artifacts/models/registry/champion_pointer.json` rich fields |
| `lineup_confirmed` | `false` until a confirmed-lineup source is wired (Phase 13L does not fake this) |
| `lineup_blocker` | Honest text when `lineup_confirmed=false` |
| `no_post_tip_data_used` | Always `true` (verifier enforces) |
| `no_challenger_artifacts_used` | Always `true` (verifier enforces) |

## Scripts

- `scripts/run_derek_live_game_snapshot.py` — per-game-per-snapshot runner.
- `scripts/dispatch_derek_live_game_snapshots.py` — schedule-aware dispatcher.
- `scripts/verify_derek_live_snapshots.py` — integrity verifier.
- `scripts/verify_phase13l_no_breakage.py` — confirms Phase 13L did not
  break Phase 13K wiring or champion pointer schema.

## Workflow

`.github/workflows/derek_live_game_snapshots.yml` runs every 10 min during
the NBA game window (22:00–03:50 UTC). Each cron firing:

1. Resolves today's delivery date.
2. Dispatches `t_minus_25` and `close_lock` snapshots for any game whose
   target time falls inside the current execution window.
3. Verifies snapshot integrity.
4. Verifies no-breakage of prior Phase 13K wiring.
5. Uploads all snapshot artifacts.
6. Commits the new snapshot files to `origin/main` under
   `Joseph Shackelford <josephshack@gmail.com>`.

**Production cron does NOT pass `--allow-backfill-test`.** That flag is
opt-in for operator backfill / local testing only.

## How to inspect a snapshot

```bash
# Manifest
cat deliveries/2026-05-01/derek_game_snapshots/21681995/t_minus_25/snapshot_manifest.json | jq .

# Verifier
python3 scripts/verify_derek_live_snapshots.py --delivery-date 2026-05-01

# Dispatch report
cat artifacts/derek_live_snapshots/2026-05-01/dispatch_t_minus_25.json | jq .
```

## Pass-line signals

| PASS line | Owner | Meaning |
| --- | --- | --- |
| `DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_PASS` | runner + verifier | Emitted by the runner ONLY when its snapshot is `production_live` with `pmfs_recomputed=true`. Emitted by the verifier ONLY when EVERY snapshot in the delivery date is `production_live` + recomputed. Never emitted for any backfill/demo snapshot. |
| `DEREK_LIVE_SNAPSHOT_INFRASTRUCTURE_BACKFILL_PASS` | runner + verifier | Emitted in place of the recomputed-pass-line when the snapshot or collection is `backfill_demo`. Means: pipeline plumbing verified; live recomputation NOT proven. |
| `DEREK_LIVE_SNAPSHOT_DISPATCH_PASS` | dispatcher | Dispatcher fired all due games for the requested snapshot type |
| `DEREK_LIVE_SNAPSHOTS_PASS` | verifier | All snapshots in the date have valid manifests + mode/source consistency + champion match + lineup honesty + PMF validity. Mode-agnostic — emitted for both production_live and backfill_demo collections. |
| `PHASE13L_NO_BREAKAGE_PASS` | no-breakage verifier | Phase 13K PASS-line tokens still present, workflows still valid YAML, champion_pointer rich fields intact, no Phase 13L pollution of protected delivery sub-folders |
| `DEREK_LIVE_SNAPSHOT_RECOMPUTED_PMFS_FAILED` | runner | Production-live mode could not invoke predict.py (e.g. target_date != today, predict.py exit != 0, predictions parquet missing). The runner refuses to silently reuse canonical PMFs in production-live mode. |

## What Phase 13L has and has not proven

- **Proven (backfill_demo on 2026-05-01 and 2026-04-30):** snapshot
  pipeline plumbing — dispatcher fan-out, runner per-game artifact
  emission, snapshot_manifest schema, verifier integrity checks,
  GitHub Actions workflow wiring, champion-pointer linkage.
- **Not yet proven:** true production-live recomputation. That requires
  a scheduled or workflow-dispatched **production_live** run that
  produces `pmfs_recomputed=true` / `pmf_source=live_snapshot_recomputed`
  on a real NBA slate during a live game window. Until that run lands,
  the recomputed-pass-line cannot be honestly emitted.
- **Still not wired:** confirmed-lineup source. Every snapshot manifest
  carries `lineup_confirmed=false` /
  `lineup_blocker="no confirmed lineup source wired"` until a future
  phase wires a real source.

## Deferred to Phase 13L-bis

- `scripts/score_derek_live_snapshots_after_game.py` (per-snapshot PMF scoring + market deltas)
- `scripts/build_rolling_derek_snapshot_benchmark.py` (28-day rolling benchmark)
- The PASS lines `DEREK_T_MINUS_25_SCORING_PASS`, `DEREK_CLOSE_LOCK_SCORING_PASS`, `DEREK_SNAPSHOT_CALIBRATION_PASS`, `DEREK_LIVE_SNAPSHOT_BENCHMARK_PASS`
- Per-game `snapshot_comparison.{csv,parquet,md}` emitter
- `aggregate_snapshot_scoring.{md,csv,json}`

These all require live snapshots to exist for completed games. Phase 13L
core ships the snapshot pipeline first; once snapshots are flowing through
production cron, 13L-bis builds the scoring+comparison tools on top.
