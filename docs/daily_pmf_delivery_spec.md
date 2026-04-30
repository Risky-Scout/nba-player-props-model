# Daily PMF delivery spec

This document is the contract for the daily NBA player-prop PMF delivery
pipeline. It defines two daily deliverables, their on-disk layout, the
canonical row schema, the snapshot lifecycle, and the quality flags that
must accompany every row.

The current production model is **Phase 10C** (commit `b7949ed`). Phase 10D
and Phase 10D.2 TOV overlays did not pass independent validation and are
**not** wired into production; see
`docs/phase10d2_tov_mean_preserving_report.md` and
`docs/phase11_tov_structural_refit_plan.md`.

---

## 1. Deliverables

Two packages, both rooted at `deliveries/YYYY-MM-DD/` for the slate's local
calendar date (US/Eastern).

### 1.1 Derek review package

```
deliveries/YYYY-MM-DD/pmf_model_review_package/
  01_START_HERE.html
  02_MODEL_REVIEW_OVERVIEW.html
  03_PMF_DISTRIBUTION_VIEWER.html
  04_PROP_SUMMARY.csv
  04_PROP_SUMMARY.parquet
  05_FULL_PMF_WIDE.csv
  05_FULL_PMF_WIDE.parquet
  06_OUTCOME_LEVEL_PROBABILITIES.csv
  06_OUTCOME_LEVEL_PROBABILITIES.parquet
  machine_readable/
    model_only.parquet
    model_only.jsonl
    model_only.csv
    pmf_cal_meta.json
  after_game_scoring.csv          (added post-tip by the scoring runner)
  after_game_scoring.parquet      (added post-tip)
  after_game_summary.md           (added post-tip)
  README.md
  PMF_MODEL_REVIEW_PACKAGE_YYYY-MM-DD.zip
```

Audience: human review. The HTML viewers render distributions; the
CSV/parquet files are the same data in flat form. The `machine_readable/`
folder contains exactly the canonical model-only PMF — no market joins, no
edges, no anchoring.

### 1.2 Wizard of Odds production package

```
deliveries/YYYY-MM-DD/wizard_of_odds/
  fair_odds_board.csv
  fair_odds_board.parquet
  fair_odds_board.jsonl
  full_pmfs_wide.csv
  full_pmfs_wide.parquet
  full_pmfs_outcome_level.csv
  full_pmfs_outcome_level.parquet
  market_comparison.csv
  market_comparison.parquet
  publishable_edges.csv
  publishable_edges.parquet
  after_game_clv_and_scoring.csv  (added post-tip)
  after_game_clv_and_scoring.parquet
  after_game_clv_and_scoring.md
  run_manifest.json
```

Audience: WoO ingestion + edge publishing. Each file has a precise role:

| file | role |
|---|---|
| `fair_odds_board.*` | One row per (player, stat, line) with the model's fair over/under probabilities and American odds. Independent of any book. |
| `full_pmfs_wide.*` | One row per (player, stat) with `p0`, `p_ge_1` … `p_ge_20`, `mean`, `median`, `mode`. |
| `full_pmfs_outcome_level.*` | Long form: one row per (player, stat, k) with `P(outcome=k)`. |
| `market_comparison.*` | One row per (player, stat, line, book) with the model fair odds joined to the book's offered odds and no-vig probability. |
| `publishable_edges.*` | Subset of `market_comparison` filtered by edge thresholds and quality flags. |
| `run_manifest.json` | Source timestamps, snapshot lifecycle, quality flag rollup, model version. |

---

## 2. Canonical row schema

Every row in every CSV/parquet/jsonl file in either package MUST carry the
columns below. Rows where a column is not applicable carry `null` (parquet
NA), not the string `"null"`. Numeric columns are `float64` unless noted.

### 2.1 Identity / scheduling
| column | type | source of truth |
|---|---|---|
| `player_name` | str | `predictions/all_props_{date}.parquet` |
| `player_id` | int (nullable) | NBA `player_id` if available |
| `team` | str | 3-letter abbreviation |
| `opponent` | str | 3-letter abbreviation |
| `is_home` | bool | from schedule |
| `game_id` | int | NBA `game_id` |
| `game_start_time` | str (ISO 8601, with timezone) | schedule (ET local + UTC) |
| `stat` | str | one of `pts, reb, ast, tov, fg3m` (extensible) |

### 2.2 Market context (nullable for stats with no market line)
| column | type | notes |
|---|---|---|
| `line` | float | the offered line |
| `book` | str | `bookmaker_key` from Odds API; `null` for `fair_odds_board` rows that are line-grid (model-only) |
| `market_over_odds` | int (American) | offered |
| `market_under_odds` | int (American) | offered |
| `market_no_vig_over_prob` | float | de-vigged from `market_over_odds`/`market_under_odds` |

### 2.3 Model PMF (always populated)
| column | type | notes |
|---|---|---|
| `pmf_source` | str | identifies which Phase produced the PMF (e.g. `phase10c_role_aware_active_conditioned`) |
| `calibration_source` | str | identifies the active calibrator (e.g. `phase8_role_aware_pmf_cal_v2`) |
| `role_bucket` | str | one of `inactive_risk, fringe, bench, rotation, core, starter` |
| `mean` | float | Σ k·p_k |
| `median` | int | smallest k such that CDF(k) ≥ 0.5 |
| `mode` | int | argmax over support |
| `p0` | float | P(stat = 0) |
| `p_ge_1` … `p_ge_20` | float | tail probabilities; columns past the support upper bound carry 0.0 |

### 2.4 Fair odds + edge (per offered line; null when `line` is null)
| column | type | notes |
|---|---|---|
| `model_p_over` | float | P(stat > line) using the canonical model PMF; for half-lines this is unambiguous, for whole-number lines pushes are excluded from the model probability |
| `fair_over_odds_american` | int | American odds derived from `model_p_over` |
| `fair_under_odds_american` | int | American odds derived from `1 - model_p_over` |
| `edge` | float | `model_p_over - market_no_vig_over_prob` (signed; positive = over edge) |

### 2.5 Snapshot lifecycle
| column | type | values |
|---|---|---|
| `snapshot_type` | str | `morning` (≥4 hr to tip), `pre_close` (~30 min to tip), `close_lock` (T-5 min from tip), `after_game` (post-final) |
| `snapshot_time_utc` | str (ISO 8601 UTC) | timestamp the snapshot was captured |

### 2.6 Provenance
| column | type | notes |
|---|---|---|
| `model_version` | str | git SHA + phase tag (e.g. `b7949ed#phase10c`) |
| `pipeline_run_id` | str | UUID per delivery run |

### 2.7 Quality flags (always populated)
Each flag is an `enum` string. The set of accepted values is fixed per flag.

| flag | values | meaning |
|---|---|---|
| `pmf_valid` | `ok`, `bad_shape`, `non_finite`, `negative_prob` | structural sanity of the PMF row |
| `pmf_sum_error` | float (numeric, `\|Σp − 1\|`) | absolute deviation from 1 before any renormalization |
| `calibration_confidence` | `high`, `medium`, `low` | `high` for `core/starter/rotation`; `medium` for `bench/fringe`; `low` for `inactive_risk` and any role with < 50 OOF rows in the active calibrator's fit |
| `market_coverage_status` | `full`, `partial`, `sparse`, `none` | `full`: every Tier-1 book present; `partial`: 2+ books; `sparse`: 1 book; `none`: no market |
| `tov_status` | `current_phase8`, `overlay_off` | always `current_phase8` while Phase 10D/10D.2 overlays are not in production. Documents that no TOV overlay is applied. The run-level `manifest.tov_status` field uses a different vocabulary (`present` vs `missing_from_prediction_source`) and reports whether the prediction source emitted any TOV rows at all. |
| `injury_freshness_status` | `fresh` (≤3 hr), `stale` (3–12 hr), `very_stale` (>12 hr), `unknown` | per-row mtime of the injury source feeding `p_inactive` |
| `lineup_freshness_status` | `confirmed`, `projected`, `unknown` | derived from upstream availability source. `projected` is set when `role_bucket` was derived from the `mp_bucket` projected-minutes feature in predict.py; `confirmed` requires a confirmed-lineup source (not currently consumed). |
| `role_freshness_status` | `confirmed_lineup`, `derived_from_projected_minutes`, `missing` | row-level provenance for `role_bucket` itself. `derived_from_projected_minutes` means we mapped predict.py's `mp_bucket` (4-bucket projected-minutes feature) to a 4-tier role; `missing` means `role_bucket` could not be derived for that row. |

---

## 3. Snapshot lifecycle

A delivery is generated at four canonical points per slate. Every emitted
row tags its `snapshot_type` and `snapshot_time_utc`. The same delivery
folder is written to four times; each write **appends a row partition** to
the same parquet/CSV files (de-duped on
`(player_id, stat, line, book, snapshot_type)`).

| snapshot | trigger | what it does |
|---|---|---|
| `morning` | ≥4 hr to first tip | Run model; pull morning Odds API snapshot; write fair-odds board + market comparison. |
| `pre_close` | ~30 min before each game's tip | Refresh model if injuries/lineups changed; pull pre-close odds. |
| `close_lock` | T-5 min from tip | Final lock snapshot for CLV scoring. **Source of truth for closing market.** |
| `after_game` | game finals available | Score outcomes and emit `after_game_scoring.*` and `after_game_clv_and_scoring.*`. |

The `morning` row is the canonical model-only output; `close_lock` is the
canonical closing market reference. Edges are computed at every snapshot,
but `publishable_edges.*` only includes rows tagged `morning` or
`pre_close`.

---

## 4. Hard rules (model-only canonical)

These rules are enforced at write time by the runner and re-checked by the
scorer.

1. **The model-only PMF is canonical.** No market anchoring is ever applied
   to the canonical PMF. Files in `pmf_model_review_package/machine_readable/`
   contain only model-only PMFs.
2. **Market is a reference layer.** `market_comparison.*` and
   `publishable_edges.*` join model-only PMFs to market lines side-by-side.
   The model PMF column values do not change as a function of the market.
3. **Sparse market coverage does not drop the row.** If a stat has no
   market for a player, the row is still emitted with `line=null` and
   `market_coverage_status` set; only fields that require a line are null.
4. **TOV PMFs are emitted using the current Phase 8 calibrators.** No
   Phase 10D or 10D.2 overlay is applied. `tov_status` is `current_phase8`.
   This is documented in every `run_manifest.json`.
5. **Quality flags are mandatory** — every row in every file has all the
   flags from §2.7 populated.
6. **Provenance is mandatory** — `model_version` and `pipeline_run_id` are
   present on every row and reproduced verbatim in `run_manifest.json`.
7. **Reproducibility** — given the same `predictions/all_props_{date}.parquet`
   and the same odds snapshot, the runner produces byte-identical PMF
   numerics. Random tie-breaking is seeded.

---

## 5. `run_manifest.json` schema

```jsonc
{
  "delivery_date": "2026-04-29",
  "pipeline_run_id": "<uuid>",
  "snapshot_type": "morning|pre_close|close_lock|after_game",
  "snapshot_time_utc": "2026-04-29T18:27:55Z",
  "model_version": "b7949ed#phase10c",
  "phase8_calibration_source": "phase8_role_aware_pmf_cal_v2",
  "finality_status": "final|provisional",
  "finality_blocker_codes": ["injury_very_stale", "lineup_unconfirmed", "missing_stats:tov"],
  "finality_blockers": [
    {
      "code": "injury_very_stale",
      "detail": "data/player_availability_asof.parquet age > 12 hr; predictions were produced against stale availability.",
      "required_to_resolve": "BDL_API_KEY for live BDL injury fetch OR refreshed nba_injury_reports.parquet, then re-run scripts/predict.py"
    },
    /* ... one entry per blocker, all carrying code/detail/required_to_resolve ... */
  ],
  "tov_overlay": "off",
  "tov_overlay_reason": "Phase 10D/10D.2 failed independent validation gates",
  "tov_status": "present | missing_from_prediction_source",
  "target_stats": {
    "expected": ["pts","reb","ast","tov","fg3m"],
    "in_delivery": ["ast","blk","fg3m","pts","reb","stl"],
    "missing": ["tov"],
    "extra_relative_to_supported": ["blk","stl"]
  },
  "sources": {
    "model_only_parquet": {
      "path": "deliveries/{date}/canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet",
      "mtime_utc": "...",
      "sha256": "...",
      "auto_built_from_predictions": true
    },
    "predictions_parquet": {
      "path": "predictions/all_props_2026-04-29.parquet",
      "mtime_utc": "..."
    },
    "availability_table": {
      "path": "data/player_availability_asof.parquet",
      "mtime_utc": "...",
      "freshness_status": "fresh|stale|very_stale"
    },
    "odds_snapshot": {
      "path": "data/odds_api/processed/{date}/odds_pairs_*.parquet",
      "mtime_utc": "...",
      "books_seen": ["fanduel", "draftkings", "..."],
      "coverage_status": "full|partial|sparse|none",
      "fetch_status": "consumed_from_disk|skipped:no_disk_snapshot|skipped:no_odds_fetch_flag"
    }
  },
  "row_counts": {
    "fair_odds_board": 0,
    "full_pmfs_wide": 0,
    "market_comparison": 0,
    "publishable_edges": 0
  },
  "quality_rollup": {
    "pmf_valid_ok_pct": 1.0,
    "pmf_sum_error_max": 0.0,
    "calibration_confidence": {"high": 0, "medium": 0, "low": 0},
    "market_coverage_status": {"full": 0, "partial": 0, "sparse": 0, "none": 0},
    "injury_freshness_status": {"fresh": 0, "stale": 0, "very_stale": 0, "unknown": 0},
    "lineup_freshness_status": {"confirmed": 0, "projected": 0, "unknown": 0}
  },
  "warnings": [],
  "no_odds_fetch": false,
  "freshness_manifest": {
    "path": "data/freshness_manifest/2026-04-29.json",
    "built_at_utc": "...",
    "overall_status": "ready|partial|not_ready|missing",
    "odds_status": "ok|partial|fail|skipped|skipped:no_api_key",
    "regions_requested": ["us","us2"],
    "books_seen": ["..."],
    "tov_status": "present|missing_from_prediction_source",
    "predictions_mtime_utc": "...",
    "availability_freshness_status": "fresh|stale|very_stale|unknown",
    "finals_finality_status": "finals_pending|finals_present|unknown"
  }
}
```

The `freshness_manifest` block is populated by reading
`data/freshness_manifest/{date}.json`, which `scripts/refresh_daily_inputs.py`
writes before each build. See `docs/daily_data_freshness_runbook.md` for
the producer-side schema and on-call response.

---

## 6. After-game scoring

The after-game runner is the only writer of `after_game_*` files. It
appends to both packages without rewriting the morning/pre_close/close_lock
rows. Required columns added on top of §2:

| column | type | notes |
|---|---|---|
| `actual_outcome` | int | realized stat |
| `pmf_nll` | float | `-log P(actual)` |
| `pmf_rps` | float | ranked probability score |
| `mean_error` | float | `mean − actual_outcome` |
| `outcome_prob_assigned` | float | `P(actual)` |
| `over_realized` | bool | `actual > line` (null if line null) |
| `under_realized` | bool | `actual < line` (null if line null) |
| `is_push` | bool | `actual == line` for whole-number lines |
| `model_logloss` | float | `-(y log p + (1-y) log(1-p))` over non-push rows |
| `model_brier` | float | `(p - y)^2` |
| `clv_close_minus_morning_p` | float | `model_p_over_close - market_no_vig_over_prob_morning` |
| `clv_book_close_minus_morning_p` | float | `market_no_vig_over_prob_close - market_no_vig_over_prob_morning` |
| `model_edge_movement` | float | `edge_close - edge_morning` |

---

## 7. Validation contract (acceptance gates that must pass before publish)

The runner will refuse to write `publishable_edges.*` if any of these
fail:

| gate | rule |
|---|---|
| G_PMF_SUM | for every row, `\|Σp − 1\| ≤ 1e-6` |
| G_PMF_NONNEG | every `p_k ≥ -1e-9` |
| G_PMF_FINITE | every `p_k` finite |
| G_PROVENANCE | `model_version` and `pipeline_run_id` non-null on every row |
| G_TOV_OVERLAY_OFF | every TOV row has `tov_status="current_phase8"` |
| G_LEAKAGE | `snapshot_time_utc < game_start_time` for every non-`after_game` row |

These are runner-side gates and are independent of model-quality gates,
which live in `docs/phase11_tov_structural_refit_plan.md` and the Phase
10D/10D.2 reports.

---

## 7a. Pipeline orchestration

A daily slate is produced by three scripts driven by
`.github/workflows/daily_pmf_delivery.yml`:

```
scripts/refresh_daily_inputs.py     ← fetches Odds API (regions us+us2),
                                       writes data/freshness_manifest/{date}.json
scripts/build_daily_pmf_delivery.py ← consumes predictions + odds + freshness
                                       manifest, writes both delivery folders
                                       and wizard_of_odds/run_manifest.json
scripts/score_daily_pmf_delivery_after_game.py
                                    ← consumes box-score finals, appends
                                       after_game_*.* to both folders
```

The workflow runs scheduled jobs on a UTC cron. Phase 12D retired the
morning cron — the first publishable scheduled run is now
`pre_close` at 22:25 UTC (6:25 PM ET during NBA playoffs), defined as
the earliest expected tipoff minus 35 minutes. `pre_close` then
refreshes every 15 minutes through 03:10 UTC so later-game lineup and
inactive updates flow into the feed. A late `close_lock` snapshot
fires at 03:25 UTC, and `after_game` scoring fires at 06:30 UTC for
yesterday's slate.

| job          | UTC cron                                 | snapshot      |
|--------------|------------------------------------------|---------------|
| `pre_close`  | `25 22 * * *` (first publishable run)    | `pre_close`   |
| `pre_close`  | `40,55 22 * * *`                          | `pre_close`   |
| `pre_close`  | `10,25,40,55 23,0,1,2 * * *`              | `pre_close`   |
| `pre_close`  | `10 3 * * *` (final pre-close refresh)   | `pre_close`   |
| `close_lock` | `25 3 * * *`                              | `close_lock`  |
| `after_game` | `30 6 * * *`                              | `after_game`  |
| `morning`    | (retired in Phase 12D — manual-only)     | `morning`     |

`scripts/run_daily_delivery_pipeline.py` further gates pre_close /
close_lock runs to a [now − 15, now + 45] minute window around any
tipoff for the date, when schedule data is on disk; pass
`--force-run` to bypass the gate during manual backfills.

Only `deliveries/{date}/{canonical_source,pmf_model_review_package,wizard_of_odds}/`
are staged in CI commits. `data/odds_api/`, `data/freshness_manifest/`,
`artifacts/`, scratch HTML files, and any failed Phase 10D / 10D.2
overlay artifacts are never staged.

---

## 8. Honest framing

This spec describes the contract for the **current safest committed model
(Phase 10C / `b7949ed`)**. TOV PMFs are emitted via the existing Phase 8
role-aware calibrators with **no Phase 10D / 10D.2 overlay**. TOV bias and
zero-inflation tradeoffs documented in
`docs/phase10d2_tov_mean_preserving_report.md` are still present in
emitted TOV PMFs; the structural refit plan in
`docs/phase11_tov_structural_refit_plan.md` is the path to fix them.

### 8a. TOV is currently absent from the slate

`predict.py` is **market-driven** — it emits one `(player, stat, line, side)`
row per offered book line. When no book offers a TOV market for a given
slate, no TOV row is generated and `manifest.target_stats.missing` lists
`tov`.

Until the **Phase 11C player-stat-grid prediction refactor** lands, TOV
will appear in the manifest's `target_stats.missing` set whenever no
book offers a TOV market that day. This is recorded in every delivery as
the blocker code `missing_stats:tov`. The refactor will emit one model-only
PMF row per `(player, eligible_stat)` regardless of whether a market line
is offered.

### 8b. role_bucket provenance

`role_bucket` is filled today from `predict.py`'s `mp_bucket` (a 4-bucket
projected-minutes feature derived from `mp_mean_last10` per
`src/nba_props_model/correlation/sgp_engine.py:mp_bucket`). The mapping is
deterministic:

| `mp_bucket` | `mp_mean_last10` window | derived `role_bucket` |
|-------------|-------------------------|------------------------|
| 3           | ≥ 30 min                | `starter`              |
| 2           | 22–30 min               | `rotation`             |
| 1           | 15–22 min               | `bench`                |
| 0           | < 15 min                | `fringe`               |

We do **not** synthesize `core` or `inactive_risk` from this signal —
those tiers require usage data and confirmed-lineup status which we do
not currently consume. The row-level `role_freshness_status` records
`derived_from_projected_minutes` so downstream consumers can distinguish
this from a confirmed-lineup source.
