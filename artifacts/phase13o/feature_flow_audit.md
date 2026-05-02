# Phase 13O Feature Flow Audit

**Generated:** 2026-05-02
**Audited at commit:** `15c01dc` (origin/main HEAD at phase 13O start)
**Author:** Joseph Shackelford <josephshack@gmail.com>

This audit answers the 16 questions of Phase 13O Part B with file paths,
line numbers, and explicit verdicts. It is the **honest baseline** that
Path B implementation must respect.

## Verdict (one paragraph)

Today, BDL lineup context enters the prediction pipeline **after** PMF
construction and calibration. It is a post-prediction metadata
annotation; the trained quantile, hurdle, and rate models do **not**
consume any lineup feature. Historical BDL lineup data is **not
available** for past games (`artifacts/live_lineups/` exists for
2026-04-30 / 2026-05-01 only and the persisted parquets are empty —
BDL only returns lineups for the current pre-tip window). The existing
nightly training pipeline is, however, structurally extensible: a new
`live_context.py` feature module + a parallel challenger trainer can
add live-context features without modifying the existing nightly
flow, the WoO-shared predict.py default path, or champion promotion
gates. **Therefore:** Phase 13O Path B can deliver the feature
infrastructure + sensitivity tests + workflow stub today, but the
"retrain so PMFs become lineup-aware" step is gated on either
(a) real BDL lineup history (forward-collectable only — call it
**LINEUP_HISTORY_LIMITED**), or (b) a substitute starter proxy
derived from `player_availability_asof.parquet`'s `prob_active` +
position. PMF sensitivity to lineup changes will **not** pass today;
it requires a retrained challenger that includes the new features in
its saved feature lists.

## 16 audit questions

| # | Question | Answer (file:line) |
| --- | --- | --- |
| 1 | Where is the training dataframe built? | `src/nba_props_model/pipelines/train.py` (training feature matrix) plus `src/nba_props_model/features/engineering.py:build_player_game_features` for per-row feature dicts |
| 2 | Where are feature columns selected? | `src/nba_props_model/features/engineering.py` — feature lists for each stat are saved as `features_<stat>.pkl` and `rate_<stat>_features.pkl` under `artifacts/models/` |
| 3 | Where are trained feature lists saved? | `artifacts/models/features_pts.pkl`, `features_reb.pkl`, `features_ast.pkl`, `features_blk.pkl`, `features_stl.pkl`, `features_fg3m.pkl`, `features_tov.pkl`, plus `rate_<stat>_features.pkl` and `hurdle_<stat>_features.pkl` |
| 4 | Where are trained feature lists loaded at prediction time? | `src/nba_props_model/pipelines/predict.py:load_models()` — restores the lists alongside the joblib model bundles |
| 5 | Which features are currently consumed by the minutes model? | `src/nba_props_model/models/minutes.py:minutes_distribution()` uses `availability` rows from `player_availability_asof.parquet` (e.g. `prob_active`, `days_since_last_played`, `num_teammates_out_total`, `vacated_minutes_*`) but does **not** accept any lineup/starter argument |
| 6 | Which features are currently consumed by rate models? | `src/nba_props_model/features/engineering.py:build_player_game_features` returns features like `pts_per_min_mean_last10`, `adv_usage_percentage_mean_last10`, `mp_mean_last10`, plus `injury_and_vacancy_features` (`starter_out_flag`, `primary_creator_out_flag`, `center_out_flag`). None are BDL-lineup-derived |
| 7 | Which features are consumed by PMF simulation? | `_pmf_build_for_stat(feature_row=base_ix, ...)` in `pipelines/predict.py` (~line 1167) — same features as the rate models above |
| 8 | Which features are consumed by PMF calibration? | role-aware calibrators load by `role_bucket` (derived from minutes-driven rule) — NOT from `role_bucket_post_lineup` |
| 9 | Are `current_starter` / `confirmed_starter` / `confirmed_bench` / `lineup_confirmed` / `role_source` / `role_bucket_post_lineup` in any trained feature list? | **NO.** Confirmed by inspection of every `features_*.pkl` filename pattern in `artifacts/models/` — none mention starter/lineup/role_source |
| 10 | Are injury/availability statuses in any trained feature list? | Partially — binary flags `starter_out_flag`, `primary_creator_out_flag`, `center_out_flag` are in `injury_and_vacancy_features`. Continuous `vacated_*` features are MONITOR-only (not in gates) |
| 11 | Are teammate-out / vacated-minutes / vacated-usage features in any trained feature list? | Available in `data/player_availability_asof.parquet` and computed historically; per audit, currently in MONITOR block only (not in gates) |
| 12 | Does BDL lineup context currently enter before minutes/rate prediction? | **NO** |
| 13 | Does BDL lineup context currently enter only after prediction rows are generated? | **YES** — `_join_lineup_context_into_rows` in `src/nba_props_model/pipelines/predict.py:624` is called at line ~1323 after all PMFs are computed and `all_singles` is populated |
| 14 | Does changing lineup_context currently change PMF output? | **NO.** It changes 12 metadata columns appended to each row (`bdl_lineup_present`, `current_starter`, `confirmed_starter`, `confirmed_bench`, `lineup_position`, `lineup_source`, `lineup_confirmed`, `role_source`, `role_bucket_pre_lineup`, `role_bucket_post_lineup`, `lineup_context_supplied`, `lineup_affects_pmf_features`) — none feed back into PMF generation |
| 15 | Does changing injury/availability currently change PMF output or only actionability? | **Both, partially.** `availability` features (prob_active, vacated_minutes, etc.) DO enter `minutes_distribution()` and influence the minutes prior; `INACTIVE_STATUSES` filter excludes confirmed-out players from actionable output. But binary `is_actionable` / `non_actionable_reason` columns are post-PMF metadata |
| 16 | What precise upstream insertion points are required for true lineup/injury PMF impact? | (a) `build_player_game_features()` must accept a `lineup_context` dict and produce new columns. (b) `minutes_distribution()` must accept lineup context (currently only takes `availability` row). (c) The rate/quantile/hurdle models must be retrained with the new feature columns; their `features_*.pkl` lists must include them. (d) Calibration buckets must accept `role_bucket_post_lineup`. (e) Prediction must use the new feature lists |

## What is and isn't available historically

| Source | Coverage | Suitable for training? |
| --- | --- | --- |
| BDL `/lineups` (v2) | 2026-04-30 → 2026-05-01 only; observed empty for past games | **No** — forward-collectable only |
| `data/player_availability_asof.parquet` | 2023-10-24+ (82,627 rows; dense) | **Yes** — contains `prob_active`, `num_teammates_out_total`, `vacated_minutes_*`, `vacated_fga_total`, `teammate_out_count_*` |
| `data/nba_injury_reports.parquet` | 2025-10-22+ (32,548 rows; timestamped) | **Yes (timestamped)** — `current_status`, `dnp_*` flags |
| `data/player_game_stats.parquet` `did_start` column | **Not present** | **No** — BDL box scores don't include starter flag |

## Implications for Path B

1. **Lineup-confirmed features** can only be added to training rows
   from 2026-05-02 forward (when forward collection of BDL lineups
   begins); set `lineup_confirmed=False` for all historical rows.
2. **Injury/availability + vacated-opportunity features** ARE
   trainable historically (already partially used in MONITOR block).
   Promoting these from MONITOR → gates is the lowest-risk Path B
   gain.
3. **`reconstructed_starter` proxy** (e.g.
   `prob_active >= threshold AND no team-mate-with-same-position
   confirmed-starting`) could approximate BDL starter for historical
   rows, but is NOT equivalent and would be a fabrication if claimed
   as a confirmed starter feature.
4. **Retraining itself** is forbidden by the Phase 13O autonomy rule
   without a workflow run. The fix is to deliver the feature module +
   training dataset builder + workflow stub now, and dispatch the
   retraining workflow when the operator is ready.
5. **PMF sensitivity to lineup changes** cannot be proven today: the
   currently-promoted champion does NOT consume the new features. The
   sensitivity verifier must report this honestly via
   `PHASE13O_PMF_SENSITIVITY_BLOCKED_PENDING_RETRAINING`.

`PHASE13O_FEATURE_FLOW_AUDIT_PASS`
