# Derek / EV Analytics schema contract

This document is the stable schema contract for files Derek's pipeline ingests from this repo. Additive columns are allowed without notice. **Breaking column renames or removals require advance notice and a corresponding bump in `schema_version` on the affected file.**

Per-day delivery root: `deliveries/<date>/derek_game_snapshots/`

Per-game folders: `<game_id>/<snapshot_type>/` where `<snapshot_type>` ∈ `{current_live, t_minus_25, close_lock}`.

---

## 1. `market_comparison.csv`

Per-prop view of model vs market, one row per (player, stat, side, line, book).

**Required columns:**

| column | type | notes |
|---|---|---|
| `row_id` | int | stable per-row identifier within the file |
| `source_row_id` | int | alias for `row_id` (kept for downstream consumers that key on either name) |
| `player_id` | int | NBA / BDL player id |
| `player_name` | string | |
| `game_id` | int | |
| `game` | string | "Away Team @ Home Team" — when present |
| `stat` | enum | one of `pts`, `reb`, `ast`, `fg3m`, `stl`, `blk`, `tov` |
| `side` | enum | `OVER` / `UNDER` |
| `line` | float | sportsbook line |
| `bet_vendor` / `book` | string | sportsbook key (e.g. `draftkings`, `fanduel`) |
| `model_prob` | float | model probability of the side hitting (0–1) |
| `market_prob` | float | no-vig market probability (0–1) |
| `raw_edge` | float | `model_prob − market_prob` |
| `edge_publish_status` | enum | `ACTIONABLE_REVIEWED` / `WATCHLIST_NOT_CONFIRMED_LINEUP` / `REVIEW_LARGE_EDGE` / `REVIEW_PUSH_LINE` / `PUBLISH_BLOCKER` |
| `calibration_support_status` | enum | `CALIBRATION_SUPPORTED` / `SAMPLE_LIMITED` / `SAMPLE_THIN` / `REVIEW_REQUIRED` |
| `lineup_confirmed` | bool | confirmed-lineup flag |
| `contextual_feature_set_id` | string | model feature-set id (e.g. `phase13s_direct_lineup_injury_pmf_driver_v1`) |
| `pmf` | string (JSON dict) | `{"<k>": p, ...}` per integer outcome value |
| `pmf_mean`, `pmf_median`, `pmf_variance` | float | summary moments of the PMF |
| `model_p_over` | float | over probability under the model PMF (push-aware) |
| `market_no_vig_over_prob` | float | when present |
| `q_preds` | string (JSON dict) | quantile dict `{"0.10": q10, "0.25": q25, ...}` |

**Hard rule:** `edge_publish_status` and `calibration_support_status` are stamped by `scripts/apply_derek_edge_publishability.py` after the runner writes the snapshot. Verify columns exist before consuming.

---

## 2. `outcome_level_probabilities.csv`

Long-form PMF view, one row per `(prop, k)`.

**Required columns:**

| column | type | notes |
|---|---|---|
| `row_id` | int | matches `market_comparison.csv.row_id` |
| `source_row_id` | int | alias of `row_id` |
| `player_id` | int | |
| `player_name` | string | |
| `game_id` | int | |
| `game` | string | |
| `team_id` | int | |
| `stat`, `side`, `line` | as above | |
| `bet_vendor` / `book` | string | |
| `model_prob`, `market_prob` | float | from the source row (per-prop, repeated for each k) |
| `edge_publish_status`, `calibration_support_status`, `contextual_feature_set_id`, `lineup_confirmed` | as above | repeated |
| `snapshot_type` | enum | `current_live` / `t_minus_25` / `close_lock` |
| `k` | int | discrete outcome value |
| `p_k` | float | probability mass at `k` |

**Invariants:**
- `Σ p_k = 1.0 ± 0.005` per `source_row_id`.
- `p_k ≥ 0` and finite.
- The terminal point at the highest `k` represents tail mass when there is a gap > 1 between the last two `k` values; downstream consumers (e.g. PMF research charts) should render it as a labeled tail bucket (`"<k>+"`), not as `P(X = k_max)`.

---

## 3. `full_pmf_wide.csv`

Wide-format per-prop view containing the full PMF JSON plus market and meta columns.

**Required columns:** all of `market_comparison.csv` (above) plus the canonical `pmf` JSON column.

`pmf` is a JSON dict `{"<k>": p, ...}` whose keys are integer outcome values cast to strings. Sum of values is 1.0 ± 0.005.

---

## 4. Reports (Markdown)

| file | purpose |
|---|---|
| `snapshot_report.md` | plain-English executive summary: top edges, contextual minutes deltas, driver attribution, publishability gates |
| `lineup_injury_impact_report.md` | lineup confirmation, BDL injury fetch result, counts of confirmed starters / bench / out |
| `direct_lineup_impact_report.md` | per-row direct-lineup driver attribution: starter / bench changes, lineup composition impact |
| `pmf_driver_decomposition.md` | per-row contextual minutes / rate deltas with Phase 13S driver attribution |

---

## 5. Missed-snapshot markers

When a near-tip snapshot was honestly missed (game already tipped before the workflow had a chance to publish), the dispatcher writes:

| file | content |
|---|---|
| `missed_snapshot_manifest.json` | `schema_version`, `delivery_date`, `snapshot_type`, `game_id`, `commence_time_utc`, `missed_reason`, `state` (= `MISSED_POST_TIP` or `MISSED_DOCUMENTED`), `no_fake_pretip_snapshot=true`, `production_fix_applied=true`, `generated_at_utc` |
| `missed_snapshot_report.md` | plain-English explanation referencing the audit trail |

**Hard rule:** missed snapshots are documented, never backfilled as if live.

---

## 6. Failed-snapshot markers (Phase 13AJ)

When the snapshot runner subprocess crashes mid-write, the dispatcher writes:

| file | content |
|---|---|
| `failed_snapshot_manifest.json` | `schema_version`, `delivery_date`, `game_id`, `snapshot_type`, `child_command`, `child_returncode`, `child_stdout_tail`, `child_stderr_tail`, `child_traceback`, `output_path`, `output_path_contents`, `required_files_missing`, `state` (= `PARTIAL_FAILED` or `FAILED_NO_OUTPUT`), `generated_at_utc` |
| `failed_snapshot_report.md` | full child stderr / stdout / traceback for operator audit |

Verifiers downgrade the snapshot to `FAIL` whenever this marker is present. There is **no path** by which a partial directory passes as a complete snapshot.

---

## 7. Versioning + breaking changes

- `schema_version` field appears on every JSON manifest. Bump major version on breaking changes.
- Additive CSV columns are always permitted.
- Removing or renaming a CSV column requires:
  1. Update this document with the old → new name and effective date.
  2. Update `scripts/verify_derek_email_claimed_files.py` to enforce the new name.
  3. Update Derek's downstream pipeline.
  4. Bump `schema_version` on the affected file.
- `row_id` and `source_row_id` are kept stable as aliases. Downstream consumers may key on either.

---

## 8. Fields downstream may safely assume

- Every `current_live` / `t_minus_25` / `close_lock` snapshot folder contains EITHER:
  1. The full file set (`snapshot_manifest.json`, `snapshot_report.md`, `prop_summary.{csv,parquet}`, `full_pmf_wide.{csv,parquet}`, `outcome_level_probabilities.{csv,parquet}`, `market_comparison.{csv,parquet}`, `pmf_driver_decomposition.md`, `lineup_injury_impact_report.md`, `direct_lineup_impact_report.md`); OR
  2. A `missed_snapshot_manifest.json` + `missed_snapshot_report.md` documenting an honest missed window; OR
  3. A `failed_snapshot_manifest.json` + `failed_snapshot_report.md` documenting a runner crash.

Empty / partial folders without one of those three states are forbidden.

- `snapshot_manifest.json` always carries `snapshot_mode` ∈ `{production_live, production_live_current, backfill_demo}`. Production verifiers reject `backfill_demo` for production_live grading. Derek's ingestion may filter on `snapshot_mode == "production_live"` if it wants production-only data.

- The `snapshot_validity_status` field on `snapshot_manifest.json` carries one of:
  - `on_time_or_current_live` — generated within the dispatcher's tolerance window.
  - `late_but_pre_tip` — generated after the target window but before tip.
  - `post_tip_stale_baseline` — current_live re-read post-tip; PMFs not refreshed against post-tip state (Phase 13Z honesty).

---

## 9. Consumer testing recipe

Before changing your ingestion code, run:

```
python3 scripts/verify_derek_email_claimed_files.py --delivery-date <date>
python3 scripts/verify_derek_outcome_level_probabilities.py --delivery-date <date>
python3 scripts/verify_derek_live_snapshots.py --delivery-date <date>
python3 scripts/verify_derek_production_live_e2e.py --delivery-date <date>
```

All of these read against this contract. Any FAIL means a breaking change has slipped past the schema-stability rule above.

---

**Maintainer:** Joseph Shackelford <josephshack@gmail.com>
**Last updated:** 2026-05-05 (Phase 13AL)
