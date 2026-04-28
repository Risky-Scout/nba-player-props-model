# Live PMF export — 2026-04-27 (after 20:29 ET)

## Slate

Two games, both tipping after the 20:29 ET cutoff:
- **Oklahoma City Thunder @ Phoenix Suns** — 21:30 ET
- **Minnesota Timberwolves @ Denver Nuggets** — 22:30 ET

Earlier game (Detroit @ Orlando) is intentionally excluded.

## Primary file for Derek's model evaluation

```
player_prop_pmfs_tonight_MODEL_ONLY.parquet
```

This contains the **standalone calibrated model PMFs**. These are NOT
market-anchored. `pmf_json` is the model's own distribution, computed
from active-conditioning + role-aware Phase 8 calibration (and, for
FG3M only, the validated tail shrink). Use this file to evaluate the
standalone model's accuracy versus the market.

Market columns (`line`, `market_fair_over_prob`, `market_source`,
`market_offered_side`, `market_offered_odds`, `model_edge_vs_market`)
are included **only as reference** so Derek can compare the model's
`p_over_line` to the available de-vigged market probability. Those
columns do **not** alter `pmf_json`.

A separate `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.*`
bundle is included for reference only; its `pmf_json` IS market-tilted
(CDF anchored at the offered line). It must NOT be used to evaluate
the standalone model.

## Source freshness (HONEST)

| Source | mtime / status |
|---|---|
| `predictions/all_props_2026-04-27.parquet` | **2026-04-27T14:27:23.761456** (morning predict run) |
| `data/player_availability_asof.parquet` | mtime 2026-04-18T21:47:03.906101; **0 rows for 2026-04-27** |
| Fresh local predict re-run | NOT possible — `BDL_API_KEY` not set in this shell. |
| GitHub Actions refresh path | `.github/workflows/daily_predictions.yml` runs at 13:00 UTC daily with the BDL secret; that workflow would need to be re-triggered to refresh today's all_props. |

**Implications:**
- Source PMFs reflect the morning run only — late-breaking injuries, scratches, or roster changes after ~14:27 local time are NOT incorporated.
- Market columns are de-vigged probabilities from the predict pipeline's morning fetch — **not** the closing line. If sharp action moved a line after 14:27 ET, the market anchor is stale.
- Availability table for 2026-04-27 is empty; we fall back to historical inactive priors per player.

## Slate

Two games, both tipping after the 20:29 ET cutoff:
- **Oklahoma City Thunder @ Phoenix Suns** — 21:30 ET
- **Minnesota Timberwolves @ Denver Nuggets** — 22:30 ET

Earlier game (Detroit @ Orlando) is intentionally excluded.

## Files

| File | Purpose |
|---|---|
| **`player_prop_pmfs_tonight_MODEL_ONLY.parquet`** | **canonical standalone-model PMFs**; `pmf_json` is model-only |
| `player_prop_pmfs_tonight_MODEL_ONLY.csv` | same MODEL-ONLY data, CSV |
| `player_prop_pmfs_tonight_MODEL_ONLY.jsonl` | same MODEL-ONLY data, JSONL |
| `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.parquet` | reference only — `pmf_json` is market-tilted; do NOT use for standalone-model evaluation |
| `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.csv` | reference only — same as above, CSV |
| `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.jsonl` | reference only — same as above, JSONL |
| `pmf_calibrators/pmf_cal_role_*.pkl` | Phase 8 role-aware PMF calibrators (pts/reb/ast/tov/fg3m) |
| `pmf_calibrators/pmf_cal_meta.json` | calibration metadata: target=`active_conditioned_prop_live`, version=`role_aware_pmf_cal_v1` |

## How the model-only PMF was built

1. **Source PMFs** come from `predictions/all_props_2026-04-27.parquet`, the
   full-universe output of the morning predict pipeline.
2. **Active-conditioning**: `pmf_active = active_condition_pmf(raw_pmf, p_inactive)`
   where `p_inactive` is taken from the locally-computed minutes distribution.
3. **Role-aware calibration**: `RoleAwarePMFCalibrator.apply(pmf_active, role_bucket=...)`
   from the Phase 8 walk-forward calibrators.
4. **FG3M tail shrink** (FG3M ONLY): for k≥7,
   `pmf[k] = 0.2 * cal[k] + 0.8 * pmf_active[k]`, then renormalized. Corrects
   the validated upper-tail overshoot from the Phase 8 audit.
5. **No market tilt** is applied to the MODEL-ONLY `pmf_json`. The model's
   own `p_over_line` is preserved exactly so its disagreement with the
   market is visible via `model_edge_vs_market`.

## How the market-anchored REFERENCE PMF was built

After the four model-only steps above, the PMF is **mass-preservingly
tilted** so that the new CDF satisfies `P(stat > line) = market_fair_over_prob`.
Within-under and within-over shape are preserved exactly; only inter-side
mass is re-weighted. When no market line is present, the reference PMF
equals the model PMF.

**Caveats on the market-anchored reference:**
- This is **market-anchored**, NOT a claim that the standalone model beats the market.
- The market source is the predict pipeline's morning de-vigged book consensus, NOT closing or live.
- The latest matched audit found the closing market beats the standalone calibrated model on log-loss in 9 of 11 cohorts (95% CI). The tilt is a useful comparison artifact, not a model performance claim.

## `pmf_source` tag values

MODEL-ONLY file:
| Value | Path |
|---|---|
| `cal_role_aware_v1:{role_bucket}` | role-aware Phase 8 cal applied (pts/reb/ast/tov) |
| `cal_role_aware_v1+fg3m_tail_shrink_k7_w0.2` | FG3M only; cal + tail-shrink |
| `no_calibrator_fallback_raw` | calibrator missing for stat (should not occur for pts/reb/ast/tov/fg3m) |

MARKET-ANCHORED REFERENCE file: same tags as above with a trailing `+market_tilt` when the row had a finite line + market prob.

## Schema (MODEL-ONLY canonical)

| Column | Notes |
|---|---|
| `export_timestamp_et` | when this bundle was generated |
| `source_*` | freshness provenance for the morning predict run + availability table |
| `game_date` | `2026-04-27` for all rows |
| `game_id`, `game_start_et`, `team`, `opponent`, `team_id`, `team_abbr` | game / team context |
| `team_name_source`, `is_home`, `is_home_source` | how team & home/away were resolved |
| `player_id`, `player_name` | identity |
| `stat` | one of pts/reb/ast/tov/fg3m |
| `role_bucket`, `role_source`, `minutes_mean`, `minutes_q50`, `p_inactive_used` | role-aware-cal context |
| `pmf_source` | model-only PMF tag (see above) |
| `support_min`, `support_max` | PMF support is `0..support_max` |
| `pmf_json` | **model-only PMF** as JSON `{"k": prob}`; entries with prob ≤ 1e-9 omitted |
| `mean`, `p0`, `p_ge_1`..`p_ge_20` | summary stats from `pmf_json` |
| `line` | offered prop line (when present) |
| `p_over_line` | model's `P(stat > line)` from `pmf_json` |
| `p_over_line_model` | same as `p_over_line` (kept for cross-file parity) |
| `market_fair_over_prob` | de-vigged market over prob (reference) |
| `market_source` | `predict_pipeline_devigged_morning` when matched |
| `market_offered_side`, `market_offered_odds` | offered market context |
| `model_edge_vs_market` | `p_over_line_model - market_fair_over_prob` — the model's signed disagreement with the market |

## Reproducing

```
python scripts/export_live_pmf_slate.py
```

Reads only local files. No API calls. Outputs are deterministic given
the same inputs.
