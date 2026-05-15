# Derek pipeline forensic audit — 2026-05-15

**Author:** automated audit + fix session (hotfix-derek-no-game-guard)
**Slate under audit:** tonight = 2026-05-15; previous slate = 2026-05-14 (no NBA games — true zero-game day)
**Failing cron:** [`gh run view 25910547616`](https://github.com/Risky-Scout/nba-player-props-model/actions/runs/25910547616) (after_game @ 09:27 UTC)
**Champion pointer (origin/main):** `challenger-2026-05-13`, calibrated_through_date `2026-05-13`. The 05-14 gap is honest; do not chase it.

> The morning `woo_morning_monetization` for 2026-05-15 succeeded
> (run 25907562462 @ 08:12 UTC). Tonight's Derek forward feed
> (`deliveries/2026-05-15/derek_forward_feed/`) is already on disk
> with 5,238 rows and passes
> `scripts/verify_derek_forward_feed_contract.py`. The blocker was
> the after-game job for *yesterday*, which red-failed the entire
> automation chain because it had no graceful no-game-day path.


## 1. Pipeline map

```
                          ┌──────────────────────────────────────────────────┐
                          │ scripts/run_daily_delivery_pipeline.py           │
                          │   resolves --mode → dispatcher                   │
                          └──────────────────────────────────────────────────┘
                                          │
       ┌──────────────────────────────────┼───────────────────────────────────┐
       │                                  │                                   │
 ┌─────▼─────────────────────┐  ┌─────────▼──────────────┐   ┌────────────────▼───────────────┐
 │ woo_morning_monetization │  │ derek_near_lineup       │   │ after_game (2:30 AM ET cron)   │
 │   15:00 UTC daily        │  │   T-35 + every 15 min   │   │   06:30 UTC daily              │
 │   builds tonight's       │  │   produces Derek lineup │   │   scores yesterday's slate     │
 │   Derek morning feed     │  │   snapshot              │   │   refreshes Derek latest_avail │
 └───────────────────┬──────┘  └─────────┬──────────────┘   └────────────────┬──────────────┘
                     │                    │                                  │
       (sees stat_grid + canonical built upstream by Daily Pipeline)         │
                     │                    │                                  │
                     ▼                    ▼                                  ▼
       ┌────────────────────────────────────────────────────────────────────────┐
       │ scripts/build_derek_forward_feed.py  --snapshot {morning|lineup|both}  │
       │                                                                        │
       │  Reads:                                                                │
       │    deliveries/{date}/pmf_model_review_package/machine_readable/        │
       │      model_only.parquet                  (canonical PMFs)              │
       │    deliveries/{date}/wizard_of_odds/                                   │
       │      market_comparison.parquet           (reference-only)              │
       │      run_manifest.json                                                 │
       │    data/freshness_manifest/{date}.json                                 │
       │                                                                        │
       │  Writes deliveries/{date}/derek_forward_feed/                          │
       │    morning_snapshot.{csv,parquet,jsonl}                                │
       │    lineup_snapshot.{csv,parquet,jsonl}      (when lineup mode)         │
       │    lineup_snapshot_status.json              (when no lineup pkg yet)   │
       │    latest_available_snapshot.{csv,parquet}  (snapshot pointer)         │
       │    feed_manifest.json                                                  │
       │    feed_manifest.champion_stamp.json        (stamp_delivery_champion)  │
       │    FEED_README.md                                                      │
       │    derek_forward_feed.{parquet,csv,jsonl}   (M8.8 unified feed)        │
       │    manifest.json                            (M8.8 manifest)            │
       │    derek_forward_feed_unified_skip.json     (when latest snap empty)   │
       └────────────────────────────────────────────────────────────────────────┘
                     │                    │
                     ▼                    ▼
       ┌──────────────────────────────────────────────┐
       │ scripts/build_derek_game_snapshots_from_     │
       │   delivery.py  (writes deliveries/{date}/    │
       │     derek_game_snapshots/{game_id}/{type}/)  │
       └──────────────────────────────────────────────┘
                     │
                     ▼
       ┌──────────────────────────────────────────────┐
       │ scripts/verify_corrected_pmf_delivery.py     │
       │   (Derek+WoO source-consistency gate,        │
       │    invoked by derek_near_lineup / close_lock)│
       └──────────────────────────────────────────────┘

DEREK LIVE PER-GAME SNAPSHOTS  (separate workflow: derek_live_game_snapshots.yml)
       ┌─────────────────────────────────────────────────────────────────────┐
       │ scripts/dispatch_derek_live_game_snapshots.py                       │
       │   honest "predictions_parquet_missing" / "predictions_parquet_      │
       │   present_but_no_games" branches; uses snapshot state machine to    │
       │   decide DUE/LATE/MISSED per (game_id, snapshot_type).              │
       └─────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
       ┌─────────────────────────────────────────────────────────────────────┐
       │ scripts/run_derek_live_game_snapshot.py  (per-game runner)          │
       │   writes deliveries/{date}/derek_game_snapshots/{game_id}/{type}/   │
       │   snapshot_manifest.json + full_pmf_wide.parquet                    │
       └─────────────────────────────────────────────────────────────────────┘

AFTER-GAME SCORING (after_game cron)
       ┌─────────────────────────────────────────────────────────────────────┐
       │ scripts/run_daily_delivery_pipeline.py --mode after_game            │
       │   1. scripts/refresh_daily_inputs.py  --no-odds-fetch               │
       │   2. ⟂ NEW: _detect_no_games_day(date)                              │
       │      → if predictions parquet & canonical parquet both 0 rows,      │
       │        write Derek/after_game/slate sentinels and short-circuit.    │
       │   3. scripts/score_daily_pmf_delivery_after_game.py                 │
       │   4. scripts/build_derek_forward_feed.py --snapshot both            │
       │   5. scripts/build_deliveries_index.py                              │
       │                                                                     │
       │ Verifiers (skipped on no-games-day short-circuit):                  │
       │   - audit_daily_delivery_completeness.py                            │
       │   - verify_derek_forward_feed_contract.py  (run_mode-aware now)     │
       │   - audit_injury_lineup_run_modes.py                                │
       │   - audit_github_delivery_automation.py                             │
       │   - verify_after_game_scoring_package_consistency.py                │
       │     (recognises no_games_today.json sentinel now)                   │
       └─────────────────────────────────────────────────────────────────────┘

NIGHTLY TRAINING / CALIBRATION  (nightly_training_calibration.yml @ 09:30 UTC + retries)
       Produces the champion artifact that the morning Derek/WoO feeds
       consume via artifacts/models/registry/champion_pointer.json. Derek
       NEVER reads challenger artifacts directly — only the pointer.
```


## 2. Current on-disk state of `deliveries/2026-05-15/derek_*`

### `deliveries/2026-05-15/derek_forward_feed/`

| file | bytes | schema / row count | status |
|---|---|---|---|
| `FEED_README.md` | 1,997 | human-readable | OK |
| `derek_forward_feed.csv` | 3,154,394 | 5,238 rows | OK |
| `derek_forward_feed.jsonl` | 9,082,232 | 5,238 lines | OK |
| `derek_forward_feed.parquet` | 210,727 | 5,238 rows × 55 cols; all M8.8 required cols present | **PASSES `verify_derek_forward_feed_contract.py`** |
| `feed_manifest.champion_stamp.json` | 880 | `challenger-2026-05-13` | OK |
| `feed_manifest.json` | 5,521 | morning: 5,238 / with_market 4,740 / model_only 498 / tov 66 | OK |
| `latest_available_snapshot.csv` | 13,196,403 | 5,238 rows | OK |
| `latest_available_snapshot.parquet` | 974,655 | 5,238 rows | OK |
| `lineup_snapshot_status.json` | 397 | **STALE (May 14 10:58)** — see FINDING-3 | LOW |
| `manifest.json` | 461 | M8.8 unified manifest | OK |
| `morning_snapshot.{csv,parquet,jsonl}` | — | 5,238 rows each | OK |

**No `lineup_snapshot.*` files yet** — the lineup snapshot is built only by `derek_near_lineup` mode (22:25 UTC and every 15 min after). The morning feed never builds it. That is correct behavior. The stale `lineup_snapshot_status.json` is from yesterday's run (cosmetic).

### `deliveries/2026-05-15/derek_game_snapshots/`

| entry | content | status |
|---|---|---|
| `21707977/` | live snapshot dir (1 sub-snapshot) | OK |
| `21709238/` | live snapshot dir (1 sub-snapshot) | OK |
| `README.md` | per-snapshot README | OK |
| `aggregate_snapshot_scoring.{json,md}` | aggregator output | OK |

Tonight's Derek per-game snapshots will be created by the
`derek_live_game_snapshots.yml` workflow starting at T-25 to first tip.


## 3. Findings

### FINDING-1 — `BLOCKER` — `after_game` cron red-fails on no-game-prev-day
- **Location:** `scripts/run_daily_delivery_pipeline.py` (mode `after_game`), `scripts/verify_derek_forward_feed_contract.py`, `scripts/audit_injury_lineup_run_modes.py`.
- **Symptom (literal):**
  ```
  rows_total=0 — no market-line rows to score on this slate
  morning rows=0  with_market=0  model_only=0  tov=0
  DEREK_FORWARD_FEED_CONTRACT_FAIL missing derek_forward_feed.parquet
  INJURY_LINEUP_RUN_MODE_AUDIT_FAIL
  ##[error]Process completed with exit code 2.
  ```
- **Root cause:** the after-game scoring path always invokes the strict M8.8 verifier bundle (`audit_daily_delivery_completeness`, `verify_derek_forward_feed_contract`, `audit_injury_lineup_run_modes`, `audit_github_delivery_automation`) even when the prior slate had zero games. The Derek-feed builder honestly skips writing `derek_forward_feed.parquet` when the latest snapshot frame is empty (it writes `derek_forward_feed_unified_skip.json` instead), and the contract verifier interprets the missing parquet as a hard failure regardless of `--run-mode`. `audit_injury_lineup_run_modes` independently red-fails because the `final_after_game` mode yields 0 feature rows on a no-game day. Net effect: a clean no-game day breaks the entire automation chain and prevents the next morning's WoO/Derek delivery from running.
- **Calibration impact:** **no.** This is a control-flow guard; nothing in the PMF math, calibration, or market-superiority pipeline is touched.
- **Fix risk:** low. The detection is narrow (BOTH parquets must exist with zero rows) and refuses to trigger on missing files.
- **Status:** **FIXED in this session.** New helper `_detect_no_games_day(date)` in `scripts/run_daily_delivery_pipeline.py` plus `_emit_after_game_no_games_skip()` that writes:
  - `deliveries/{date}/derek_forward_feed/after_game_no_games_status.json`
  - `deliveries/{date}/after_game_scoring/no_games_status.json`
  - `deliveries/{date}/no_games_today.json` (slate-level sentinel)
  …and prints `DEREK_AFTER_GAME_VALID_SKIP date=<date> reason=no_games_prev_day`. When the detector fires, `run_after_game` returns `(0, skip_verify=True)` and `main()` skips the verify bundle entirely. Detection requires BOTH `predictions/all_props_<date>.parquet` AND `deliveries/<date>/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet` to exist with zero rows; either being missing or non-empty causes the normal flow to continue (so a real data outage still red-fails). New tests: `tests/test_after_game_no_games_short_circuit.py` (5 tests, all pass).

### FINDING-2 — `HIGH` — `verify_derek_forward_feed_contract.py` did not honor the run-mode spec
- **Location:** `scripts/verify_derek_forward_feed_contract.py:21-50`.
- **Symptom (literal):** `DEREK_FORWARD_FEED_CONTRACT_FAIL missing derek_forward_feed.parquet`.
- **Root cause:** the M8.8 delivery-contract spec (`src/nba_props_model/delivery/delivery_contract.py:332-364`) marks `derek_forward_feed/derek_forward_feed.{parquet,csv,jsonl}` as `REQUIRED` for `MORNING_EXPECTED`/`T25`/`T5` and `OPTIONAL` for `FINAL_AFTER_GAME`/`BACKTEST`. The verifier did not take a `--run-mode` argument and hard-failed any missing parquet, irrespective of mode. This is the same class of stale-schema mismatch that the WoO verifiers had earlier in this hotfix session.
- **Calibration impact:** **no.** Verifier-only change; no producer or PMF math touched.
- **Fix risk:** low. The producer (`scripts/build_derek_forward_feed.py:572-592`) already writes `derek_forward_feed_unified_skip.json` when the snapshot frame is empty; we simply honor that.
- **Status:** **FIXED in this session.** Added `--run-mode` arg + an honest-skip detector that accepts any of `derek_forward_feed_unified_skip.json`, `after_game_no_games_status.json`, or the slate-level `no_games_today.json`. When the parquet is absent AND run-mode ∈ {`final_after_game`,`backtest`} AND an honest-skip marker is on disk, the verifier emits `DEREK_FORWARD_FEED_CONTRACT_VALID_SKIP` and returns 0. Otherwise the legacy fail behavior is preserved (verified by the new `test_verify_does_not_skip_for_strict_run_modes` test). Caller (`run_daily_delivery_pipeline.py::_verify_m88_delivery_bundle`) now passes `--run-mode run_stamp`.

### FINDING-3 — `LOW` — `lineup_snapshot_status.json` is stale for tonight's feed (cosmetic)
- **Location:** `deliveries/2026-05-15/derek_forward_feed/lineup_snapshot_status.json` (mtime May 14 10:58, content `status: pending_lineup_snapshot` from yesterday's `--snapshot both` run).
- **Symptom:** the file is on disk but reflects 2026-05-14, not 2026-05-15. Tonight's morning run only built `--snapshot morning` so it never overwrote the file.
- **Root cause:** `scripts/build_derek_forward_feed.py:928-984` only writes `lineup_snapshot_status.json` inside the `--snapshot {lineup,both}` branch; the `--snapshot morning` path leaves any prior file alone. The `feed_manifest.json:lineup_status` field is correctly `null` for this morning run, so downstream consumers reading the manifest see the truth — the orphan file is only a Derek-folder cosmetic.
- **Calibration impact:** no.
- **Fix risk:** low (could add a "delete-or-rewrite if `--snapshot morning`" branch), but the manifest is the source of truth.
- **Status:** **NOT WORTH FIXING right now** (consumers read `feed_manifest.json`; the orphan file will be overwritten by the next `derek_near_lineup` run at 22:25 UTC). Flagged for tracking.

### FINDING-4 — `MEDIUM` — `verify_after_game_scoring_package_consistency.py` did not recognise no-games-day sentinel
- **Location:** `scripts/verify_after_game_scoring_package_consistency.py:103-345`.
- **Symptom:** on a true no-games day, `after_game_scoring.{parquet,csv}` is absent and `expected_target_stats_coverage.json` is absent, so several checks fail and the script returns 1. This would not have surfaced today (the orchestrator failed first in the after_game cron at line 9:30:12, before the workflow's `Phase 13K — after-game package consistency` step ran), but would have surfaced as the next blocker as soon as FINDING-1 was fixed.
- **Root cause:** the verifier did not know about the no-games-day sentinel files written by the orchestrator.
- **Calibration impact:** no.
- **Fix risk:** low.
- **Status:** **FIXED in this session.** Added a no-games-day short-circuit at the top of `main()` that checks for `deliveries/{date}/no_games_today.json` OR `deliveries/{date}/after_game_scoring/no_games_status.json`, writes a `valid_skip_no_games_prev_day` report, and emits `AFTER_GAME_SCORING_PACKAGE_CONSISTENCY_VALID_SKIP date=<date> reason=no_games_prev_day` with exit 0.

### FINDING-5 — `LOW` — `dispatch_derek_live_game_snapshots.py` already has the no-games branch
- **Location:** `scripts/dispatch_derek_live_game_snapshots.py:368-403`.
- **Symptom:** none — already handled. The dispatcher emits `DEREK_LIVE_SNAPSHOT_DISPATCH_PASS` + `DEREK_LIVE_SNAPSHOT_DISPATCH_PENDING_NO_GAMES` and writes `dispatch/{date}/dispatch_{snapshot_type}.json` with `slate_status="predictions_parquet_missing"` or `"predictions_parquet_present_but_no_games"`. The expected behavior on a no-games-yesterday + games-today combo is exactly this branch firing for the dispatcher and the run-time snapshot generator never being invoked.
- **Status:** **NOT WORTH FIXING — already correct.** Confirmed by reading lines 358-403 inline.

### FINDING-6 — `LOW` — `build_derek_forward_feed.py` empty-input safety is already correct
- **Location:** `scripts/build_derek_forward_feed.py:572-592`, `914-984`, `1042-1048`.
- **Symptom:** today's failing cron log shows `lineup: not present — wrote lineup_snapshot_status.json (no fabrication)` and `morning rows=0 with_market=0 model_only=0 tov=0` — both branches handle empty input cleanly, write `feed_manifest.json`, write `lineup_snapshot_status.json` honestly, AND write `derek_forward_feed_unified_skip.json` instead of `derek_forward_feed.parquet` when the unified frame is empty.
- **Status:** **NOT WORTH FIXING — already correct.** This is the producer the contract verifier now recognises as honest in FINDING-2.

### FINDING-7 — `MEDIUM` — `feed_manifest.json` records `lineup_status: null` instead of an explicit "morning-only" status
- **Location:** `scripts/build_derek_forward_feed.py:1006-1031` (the morning-only path in `--snapshot morning` mode).
- **Symptom:** today's `feed_manifest.json` has `"lineup": null, "lineup_status": null`. Verifier `scripts/verify_derek_forward_feed.py:184-230` accepts this. Stale orphan `lineup_snapshot_status.json` on disk is a separate file (FINDING-3).
- **Calibration impact:** no.
- **Status:** **NOT WORTH FIXING (left as TODO).** The verifier accepts both null and a populated status. Future cleanup could populate `lineup_status` with `{status: "not_built_in_morning_mode"}` for clarity. Logged for follow-up.

### FINDING-8 — `LOW` — Other after-game verifiers tolerate no-games-day cleanly
- `scripts/verify_oddsapi_market_registry_contract.py` — checks registry, no per-date dependency.
- `scripts/verify_no_legacy_prediction_artifacts.py` — checks absence patterns, no positive content required.
- `scripts/verify_daily_delivery_folder_contract.py` — checks subdir existence; orchestrator always creates them (verified line 297-314 of `run_daily_delivery_pipeline.py`).
- `scripts/verify_availability_freshness.py` — checks `data/player_availability_asof.parquet` mtime, slate-agnostic.
- `scripts/verify_woo_public_artifacts_target_allowlist.py` — emits `WOO_PUBLIC_TARGET_ALLOWLIST_PASS (no artifacts)` when public_export files are absent (line 61-63).
- **Status:** **CONFIRMED OK** by code inspection.

### FINDING-9 — `OPS_NAMING` — `derek_near_lineup` mode name is confusing
- **Location:** `scripts/run_daily_delivery_pipeline.py:716-744`, workflow `daily_pmf_delivery.yml:693-887`.
- **Symptom:** the mode runs at T-35 and every 15 min through to 03:10 UTC; "near_lineup" suggests "near tip" but it actually fires before BDL has confirmed lineups for most games (snapshot_type stamped `near_tip` or `lineup` via `_resolve_lineup_snapshot_type`).
- **Status:** **FLAG FOR USER DECISION.** Proposed rename: `derek_pre_close_refresh`. The workflow file is out-of-scope for this hotfix (only `scripts/`, `src/`, `tests/`, `artifacts/derek_pipeline_audit/2026-05-15/forensics.md` are committable per session rules); we do not propose to land this rename now.


## 4. Workflow structure cheat sheet

### `.github/workflows/daily_pmf_delivery.yml`

Single workflow with 8 jobs, each gated by cron + workflow_dispatch + (in some cases) `workflow_run` from the Daily Pipeline. `concurrency` group is `daily-pmf-delivery-${{ github.ref }}`; runs never cancel mid-flight.

| job | plain English | trigger | reads | writes | downstream |
|---|---|---|---|---|---|
| `morning` | Manual-only legacy backfill since Phase 12D. Refresh inputs, rebuild canonical/stat-grid, build the morning Derek feed; does **not** publish a WoO public export. | `workflow_dispatch` mode=morning only | `predict.py` output, BDL injuries, `model_only.parquet` | `deliveries/{date}/derek_forward_feed/morning_snapshot.*`, `pmf_model_review_package/`, `wizard_of_odds/` (canonical only) | nothing (manual) |
| `full_day` | Manual full backfill that runs `woo_morning_monetization` → `woo_afternoon_refresh` → `derek_near_lineup` → `close_lock` → `after_game` in order. | `workflow_dispatch` mode=full_day | union of below | union of below | nothing (manual) |
| `woo_morning_monetization` | First WoO public run of the day. Builds canonical morning delivery, builds Derek morning forward feed (M8.8 `run_mode=morning_expected`, finality `PROVISIONAL_EARLY_MARKET`), publishes protected WoO public JSON + dashboard. | cron `0 15 * * *`; `workflow_run` from Daily Pipeline; dispatch | `model_only.parquet`, `market_comparison.parquet`, freshness manifest, champion pointer | `deliveries/{date}/derek_forward_feed/morning_snapshot.*`, `public_export/wizard_of_odds/{date}/`, `deliveries/{date}/wizard_of_odds/` | downstream Derek refreshes (`derek_near_lineup`) consume the morning Derek feed; dashboard/affiliate output is published. |
| `woo_afternoon_refresh` | Mid-afternoon WoO public refresh. Rebuilds `pre_close` canonical and re-publishes the WoO public export. Does **not** touch Derek's feed. | cron `0 18 * * *`, `0 20 * * *`; dispatch | latest WoO `pre_close` canonical, market_comparison | `deliveries/{date}/wizard_of_odds/`, public_export refreshed | downstream Derek refreshes consume the same canonical_source. |
| `derek_near_lineup` | Derek's first publishable evaluation snapshot. Rebuilds `pre_close` canonical, builds `--snapshot lineup` Derek feed (M8.8 `run_mode=t25`), republishes WoO (no monetization label override), runs strict Derek+WoO source-consistency verifier (`verify_corrected_pmf_delivery.py`), runs M8.6 event-market validation bundle (loss rows, promotion claim, stat-role superiority, calibration audits). | cron `25 22 * * *`, `40,55 22 * * *`, `10,25,40,55 23-2 * * *`, `10 3 * * *`; `workflow_run`; dispatch | model_only, market_comparison, BDL lineups, freshness manifest, champion pointer | `deliveries/{date}/derek_forward_feed/lineup_snapshot.*`, `derek_game_snapshots/`, `pmf_model_review_package/`, `wizard_of_odds/`, public_export updated | `derek_schedule_bridge` fires `derek_live_game_snapshots.yml` for per-game live snapshots. |
| `close_lock` | Final lineup/market lock at 03:25 UTC. Same as `derek_near_lineup` but with `--snapshot close_lock` and M8.8 `run_mode=t5`. | cron `25 3 * * *`; dispatch | as above | as above with `close_lock` snapshot label | `after_game` (next day). |
| `after_game` | Yesterday's slate: refresh inputs (no odds), score outcomes, refresh Derek `latest_available_snapshot` pointer, run M8.6 after-game contract verifiers, run after-game scoring package consistency, build rolling market benchmark + PMF variance experience study. | cron `30 6 * * *`; dispatch | yesterday's box scores, prediction parquet, canonical PMF parquet, market_comparison | `deliveries/{date-1}/after_game_scoring/`, `pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md`, `wizard_of_odds/after_game_clv_and_scoring.md`, rolling-market-benchmark JSON/MD | nightly_training reads `after_game_scoring/` & `pmf_model_review_package/` to update the champion challenger pipeline. |
| `derek_schedule_bridge` | One-step trigger that fires `derek_live_game_snapshots.yml` whenever the Derek-relevant crons in this workflow fire. | cron mirrors of derek_near_lineup; dispatch | nothing | nothing (just `gh workflow run`) | `derek_live_game_snapshots.yml` (separate workflow). |

### `.github/workflows/nightly_training_calibration.yml`

| job | plain English | trigger | reads | writes | downstream |
|---|---|---|---|---|---|
| `nightly_training` | Trains a challenger for `yesterday_ET` (with deferred-retry pattern at 09:30 / 12:30 / 15:30 / 18:30 / 21:30 UTC), calibrates, validates, runs market-superiority + UCB contract gates, and atomically promotes the challenger to champion when all gates pass. Production champion is unchanged on any failure. Commits the refreshed BDL stats parquet back to main regardless of training outcome. | cron `30 9,12,15,18,21 * * *`; dispatch | `data/player_game_stats.parquet`, OOF rows, market closing odds, champion_pointer | `artifacts/models/challengers/`, `artifacts/models/registry/champion_pointer.json` (only on promotion), `artifacts/nightly_training/{date}/`, `artifacts/promotion/{date}/` | downstream `daily_pmf_delivery.yml` reads the new pointer first thing at 15:00 UTC. |

### `.github/workflows/derek_live_game_snapshots.yml`

| job | plain English | trigger | reads | writes |
|---|---|---|---|---|
| `derek_live_snapshots` | Every 10 minutes during the live window (16:00-04:00 UTC), the snapshot state machine decides per-game per-snapshot-type (T-25 / current_live / close_lock) whether to fire `scripts/run_derek_live_game_snapshot.py`. Honors the no-game branch in the dispatcher. | cron `0,10,20,30,40,50 16-4 * * *`; dispatch | tonight's predictions parquet, schedule, prior snapshot manifests | `deliveries/{date}/derek_game_snapshots/{game_id}/{type}/` snapshot_manifest.json + full_pmf_wide.parquet |


## 5. Verification matrix

| step | command | result |
|---|---|---|
| AST parse all changed scripts | `python -c "import ast; ast.parse(open(f).read())"` for each | OK (3/3) |
| `compileall` | `python -m compileall scripts/run_daily_delivery_pipeline.py scripts/verify_derek_forward_feed_contract.py scripts/verify_after_game_scoring_package_consistency.py` | OK |
| New unit tests | `pytest tests/test_after_game_no_games_short_circuit.py tests/test_derek_forward_feed_contract.py -q` | **12 passed** |
| Adjacent Derek tests | `pytest tests/test_derek_forward_feed_verifier.py tests/test_injury_lineup_run_modes.py -q` | **5 passed** (no regressions) |
| Contract verifier on tonight's feed | `python scripts/verify_derek_forward_feed_contract.py --date 2026-05-15` | `DEREK_FORWARD_FEED_CONTRACT_PASS` |
| Tonight's M8.8 unified feed structure | parquet has 5,238 rows × 55 cols; all `DEREK_UNIFIED_REQUIRED_COLUMNS` present | OK |


## 6. Items requiring user judgment

1. **`derek_near_lineup` rename.** Confusing name; runs T-35 → 03:10 UTC. Proposed: `derek_pre_close_refresh`. **Decision needed.** Workflow rename is out of scope for this hotfix (only `scripts/`, `src/`, `tests/`, this report committable).
2. **Stale `lineup_snapshot_status.json` cosmetic.** Should `build_derek_forward_feed.py --snapshot morning` overwrite the file to keep tonight's Derek folder internally consistent? Trade-off: ergonomic but adds a write the user can argue is "not the morning builder's job". Recommendation: leave the manifest as the source of truth; document in `FEED_README.md`.
3. **`feed_manifest.json.lineup_status` semantic.** Currently `null` in `--snapshot morning` mode. Should this become an explicit `{"status": "not_built_in_morning_mode"}` for clarity? Verifier already tolerates both.
