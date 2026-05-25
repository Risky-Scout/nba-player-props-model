# NBA PMF Model — Cursor Handoff Document
_Written: 2026-05-25. Read this before touching anything._

---

## 1. What This Project Is

A fully automated NBA player-prop betting model that:
1. **Trains and calibrates** through the previous day's game results every morning
2. **Predicts** all player props for today's slate using projected lineups (morning)
3. **Re-predicts** close to tip-off using official lineups + latest injury data
4. **Exports** Wizard of Odds (WoO) deliveries and Derek forward-feed snapshots
5. **Scores** previous games after they finish

The model produces a full discrete **probability mass function (PMF)** `p_i(k)` for each player-stat outcome — not just a point estimate. It competes against the market's no-vig implied probability on log-loss and Brier score.

**Canonical branch:** `main` on `origin` (GitHub: `Risky-Scout/nba-player-props-model`)

---

## 2. Current State (as of 2026-05-25)

```
champion_model_id:        challenger-2026-05-24
trained_through_date:     2026-05-24
calibrated_through_date:  2026-05-24
feature_set_id:           phase13s_direct_lineup_injury_pmf_driver_v1
contextual_trained_through_date: 2026-05-24
```

Both `champion_pointer.json` and `fresh_delivery_model_pointer.json` are current through 2026-05-24. The pipeline is healthy. The model is a **Phase 13S direct-lineup contextual PMF** (the highest tier — it incorporates live lineups, injuries, vacated opportunity features, and direct lineup composition PMF sensitivity).

---

## 3. Architecture Overview

### Two-Layer Model
| Layer | What it is | Updated |
|---|---|---|
| **Base model** | LightGBM/Ridge PMF trained on historical stats | Daily (~3.5 hrs) |
| **Contextual overlay** (Phase 13S) | Ridge adjustment layer on top of base, uses lineup/injury features | Daily (runs after base) |

The contextual overlay is what matters for predictions. Even if the base model is slightly stale, the contextual overlay updates the PMFs based on today's lineups. **Phase 13S promotion is the thing that actually matters day-to-day.**

### The Single Source of Truth
```
artifacts/models/registry/champion_pointer.json
```
Never modify this by hand outside of the scripts. Two promotion scripts write to it:
- `scripts/promote_direct_lineup_challenger.py` (Phase 13S — primary path)
- `scripts/promote_contextual_challenger.py` (Phase 13R — fallback)

### Delivery Architecture
```
deliveries/YYYY-MM-DD/
├── canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet  ← NEVER market-anchor this
├── wizard_of_odds/
├── derek_forward_feed/
│   └── derek_unique_props_summary.csv  ← NEVER modify this file
├── derek_game_snapshots/
├── pmf_model_review_package/
└── after_game_scoring/  (populated after games finish)
```

---

## 4. Production Schedule (all times Eastern)

| Time (ET) | Stage | Workflow job |
|---|---|---|
| **2:30 AM** | After-game scoring (previous slate) | `after_game` |
| **3:30 AM** | Model chain: training + calibration + Phase 8 + Phase 13 + promotion | `model_chain_training_calibration` → `phase8` → `phase13` |
| **8:30 AM** | Model chain retry (if 3:30 AM failed) | same |
| **10:00 AM** | Predict today's slate | `predict_daily` |
| **10:30 AM** | WoO morning delivery | `woo_delivery` |
| **2:30 PM** | Promotion cutoff — no same-day promotion after this | (resolver gate) |
| **2:00–4:00 PM** | Intraday model chain runs (no-promote) | |
| **T-25 min before each game** | Derek projected-lineup snapshot | `derek_live_game_snapshots.yml` |
| **T-10 min before each game** | Derek confirmed-lineup snapshot (close_lock) | `derek_live_game_snapshots.yml` |

The canonical workflow is `nba_pmf_delivery.yml`. `nightly_training_calibration.yml` is a **legacy duplicate** that was investigated — it has been left with its cron triggers because it provides a small amount of non-duplicate Phase 8 retry logic, but beware it runs concurrently with `nba_pmf_delivery.yml`.

---

## 5. Key Scripts (the ones that matter most)

| Script | Purpose |
|---|---|
| `scripts/resolve_nba_pmf_schedule.py` | Resolves `as_of_date`, `stage`, `allow_promote` for every workflow run. Central to all scheduling logic. |
| `scripts/run_nightly_training_and_calibration.py` | Orchestrates base model training. Calls `calibrate_daily_challenger_pmfs.py` (NOTE: this is a STUB — see §8). |
| `scripts/promote_challenger_if_validated.py` | Promotes base model challenger. Market gates are **soft/diagnostic only** — they do NOT block promotion (Option A policy, line ~185). |
| `scripts/promote_direct_lineup_challenger.py` | Promotes Phase 13S contextual model. **Recently fixed** to also update `champion_model_id`, `trained_through_date`, `calibrated_through_date`. |
| `scripts/promote_contextual_challenger.py` | Promotes Phase 13R contextual model (fallback to 13S). Same fix applied. |
| `scripts/write_fresh_delivery_pointer.py` | Writes `fresh_delivery_model_pointer.json`. Market gates are diagnostic only here too. |
| `scripts/build_daily_pmf_delivery.py` | Builds the full delivery folder for a date. |
| `scripts/dispatch_derek_live_game_snapshots.py` | Dispatches T-25 and T-10 Derek snapshots. |
| `scripts/verify_corrected_pmf_delivery.py` | Verifies delivery folder completeness. |
| `scripts/verify_stat_role_ucb_contract.py` | Market superiority gate — must exit 0 to claim superiority. |

---

## 6. Required Stats (all 12 must be covered)

```python
DELIVERY_REQUIRED_TARGETS_CANONICAL = [
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
    "stocks",  # = stl + blk
    "pa",      # = pts + ast
    "pr",      # = pts + reb
    "ra",      # = reb + ast  ← was wrongly in FORBIDDEN_STATS, now fixed
    "pra",     # = pts + reb + ast
]
```

`ra` was previously excluded from the stat/role calibration matrix and various FORBIDDEN_STATS lists. That has been fixed across: `build_m6_3_stat_role_calibration_report.py`, `validate_champion_vs_challenger.py`, `refresh_daily_inputs.py`.

The calibration matrix is now **12 stats × 4 role buckets = 72 rows** (was 66).

---

## 7. Role Buckets

```
bench, rotation, core, starter
```

Used throughout calibration, delivery, and market-superiority reporting. Never remove role_bucket logic.

---

## 8. Known Architectural Limitations (do not "fix" without a plan)

### A. Base model never actually gets a new `champion_model_id` from `promote_challenger_if_validated.py`
The base model challenger promotion (`promote_challenger_if_validated.py`) is blocked by a contextual regression guard: if the existing champion is contextual (Phase 13S), the new base challenger must ALSO be contextual to replace it. Since the base challenger's `feature_set_id` is not `phase13s_*`, it is blocked. The base fields (`champion_model_id`, `trained_through_date`) are now updated by Phase 13 promotion instead (§5 fix). This is the intended behavior going forward.

### B. `.gitignore` blocks challenger .pkl and .parquet files
`artifacts/models/challengers/**/*.pkl` and `**/*.parquet` are gitignored. This prevents challenger calibration artifacts from being committed, which is why base model promotion through `promote_challenger_if_validated.py` always shows `rows_scored: 0`. This is intentional (large binary files). The Phase 13 path is the canonical promotion path.

---

## 9. Bugs Fixed in This Chat Session (with commit hashes)

| Bug | Fix | Commit |
|---|---|---|
| `champion_model_id` / `trained_through_date` frozen at 2026-04-30 despite Phase 13 running | Phase 13 promotion scripts now write base champion fields | `dd12a1f7` |
| Phase 13 `PROMOTION_DONE` detection falsely triggered on idempotent skip | Added `skip_promotion` guard in commit step | `badd1a31` |
| `SCHEDULER_TIP_TIME_UNRESOLVABLE_WITH_SLATE` in Derek runs | Fixed `_extract_games_list` + `_resolve_slate_tipoff` key priority | `a352b6a3` |
| Derek snapshot source mismatch on `--skip-derek-snapshots` | Gated entire manifest iteration loop on flag | `6aee383e` |
| Phase 8 → Phase 13 blocked when Phase 8 was idempotently skipped | Changed `needs.phase8.result == 'success'` to `success\|\|skipped` | `43c3a0a1` |
| Model chain cron at 09:30 UTC (5:30 AM ET), changed to 07:30 UTC (3:30 AM ET) | Updated cron + resolver `MODEL_CHAIN_PROMOTE_CRONS` | (multiple commits) |
| `ra` (reb+ast) excluded from stat/role matrix as FORBIDDEN | Removed from FORBIDDEN_STATS, added to COMBO_STATS, matrix now 72 rows | (multiple commits) |
| Promotion scripts signaled success without verifying disk write | Added readback verification in both Phase 13 promotion scripts | PR #57 |
| `sync_and_push()` silently dropped champion_pointer.json commits during rebase | Comprehensive rebase conflict handling rewrite | `36ceec33` |
| Derek close_lock snapshot at T-6 min, changed to T-10 | Changed `CLOSE_LOCK_OFFSET_MIN` 6→10 | `ad041a37` |
| After-game consistency check failed on missing `lineup_snapshot.parquet` | Conditional check | (earlier commit) |

---

## 10. Key Workflow Files

### Primary: `.github/workflows/nba_pmf_delivery.yml`
The single canonical orchestrator. Contains:
- `resolve_context` job (runs `scripts/resolve_nba_pmf_schedule.py` — determines the stage for every run)
- `after_game` job
- `model_chain_training_calibration` job
- `phase8_pmf_calibration_diagnostics_market_eval` job
- `phase13_live_context_contextual_lineup` job (Phase 13O→13P→13Q→13R→13S in sequence)
- `predict_daily` job
- `woo_delivery` job
- `derek_delivery` job

### Derek: `.github/workflows/derek_live_game_snapshots.yml`
Separate workflow for T-25 and T-10 game snapshots. Runs on a dense cron grid (every 15 min from 6:40 PM ET through 10:55 PM ET).

### Legacy (do not remove, do not add new cron triggers):
- `nightly_training_calibration.yml` — legacy, runs concurrently with main
- `phase8.yml`, `phase13*.yml` — individual phase workflows, largely superseded by `nba_pmf_delivery.yml`

---

## 11. Rules / Constraints (NEVER violate)

1. **Never modify** `deliveries/*/derek_forward_feed/derek_unique_props_summary.csv`
2. **Never market-anchor** `canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet`
3. **Never claim market superiority** unless `scripts/verify_stat_role_ucb_contract.py` exits 0
4. Market gates are **diagnostic only** — they update `market_quality_status` and `promotion_eligible` flags but do NOT block promotion or daily delivery
5. **Never remove**: leakage checks, injury features, lineup features, role_bucket logic
6. **Never use post-outcome features** or full-data OOF leakage
7. If a source is missing: valid-skip + write structured diagnostics; never fabricate data
8. Phase 13 must run in strict order: 13O → 13P → 13Q → 13R → 13S

---

## 12. Market Superiority Verification

```bash
python scripts/build_event_market_loss_rows.py --date 2026-05-12
python scripts/build_stat_role_market_superiority_report.py --date 2026-05-12 --include-ineligible --min-scored-rows 100 --min-market-joined-rows 100
python scripts/verify_stat_role_ucb_contract.py --label 2026-05-12 --min-n 100
```

Gates (per stat × role cell):
- `UCB95(model_logloss - market_logloss) < -0.0025`
- `UCB95(model_brier - market_brier) < -0.0010`

Calibration gates (per cell):
- `ECE ≤ 0.025`, `PIT_KS ≤ 0.075`, `|mean_error| ≤ 0.15`, `|variance_error| ≤ 0.20`

---

## 13. After Any Change — Required Verification

```bash
python3 -m compileall src scripts
python3 scripts/build_event_market_loss_rows.py --date 2026-05-12
python3 scripts/build_stat_role_market_superiority_report.py --date 2026-05-12 --include-ineligible --min-scored-rows 100 --min-market-joined-rows 100
python3 scripts/verify_stat_role_ucb_contract.py --label 2026-05-12 --min-n 100
```

Also run after YAML changes:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/nba_pmf_delivery.yml'))" && echo "YAML_OK"
```

---

## 14. Debug Instrumentation Still Present

There is still debug instrumentation in `scripts/promote_direct_lineup_challenger.py` (around line ~292) that writes to `.cursor/debug-cd71ad.log`. This is intentionally left in until the next Phase 13 promotion run confirms the fix (`champion_model_id` advances to `challenger-2026-05-25`) in production. **Remove the `#region agent log` block after that confirmation.**

---

## 15. What To Do Tomorrow Morning

After the 3:30 AM ET model chain runs on 2026-05-26:

1. Check `artifacts/models/registry/champion_pointer.json` — should show `trained_through_date: 2026-05-25`
2. Check `deliveries/2026-05-26/` exists with all required folders
3. If Phase 13 ran and `champion_model_id` advanced to `challenger-2026-05-25`, the fix is confirmed — remove the debug instrumentation block in `promote_direct_lineup_challenger.py`
4. If the model chain shows `PHASE13_ALREADY_COMPLETE_FOR_AS_OF_DATE`, that's normal (idempotency) — check that the previous day's promotion actually committed by checking `champion_pointer.json`

---

## 16. Prior Chat Transcript

Full debug history: `/Users/josephshackelford/.cursor/projects/Users-josephshackelford-repos-nba-player-props-model-pmf-fix/agent-transcripts/cd71adcf-2c16-42a5-becf-f1d1eae6304c/`
