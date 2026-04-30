# Daily data freshness runbook

This runbook describes how `scripts/refresh_daily_inputs.py` produces
`data/freshness_manifest/{date}.json`, how
`scripts/build_daily_pmf_delivery.py` consumes it, and what an on-call
operator should do when an input is missing or stale.

The freshness manifest is the **single source of truth** for whether a
delivery is `final`, `provisional`, or `not_deliverable_ready`. Every
field below maps 1:1 onto a row of the per-delivery `run_manifest.json`
and the per-row quality flags described in §2.7 of
`docs/daily_pmf_delivery_spec.md`.

---

## 1. The manifest at a glance

`data/freshness_manifest/{YYYY-MM-DD}.json` is written every time
`scripts/refresh_daily_inputs.py` runs. It is **never** staged — it is
an input to the delivery, not a delivery artifact. `.gitignore` does not
explicitly list it; the per-job `git add` invocation in
`.github/workflows/daily_pmf_delivery.yml` only stages the
`deliveries/{date}/` folders, so the manifest never enters git via the
normal pipeline.

Schema (v1):

```jsonc
{
  "delivery_date": "2026-04-29",
  "built_at_utc": "2026-04-29T18:27:34Z",
  "schema_version": 1,
  "snapshot_type": "morning_7am",
  "regions_requested": ["us", "us2"],
  "odds": {
    "status": "ok | partial | fail | skipped | skipped:no_api_key",
    "runs": [ /* one entry per region with start/end + exit code */ ],
    "files": [ /* every odds_pairs_*.parquet under data/odds_api/processed/{date}/ */ ],
    "books_seen": ["betmgm","draftkings", "..."],
    "stats_seen": ["ast","fg3m","pts","reb"],
    "total_rows": 5186,
    "market_coverage_status": "full | partial | sparse | none"
  },
  "predictions": {
    "path": "predictions/all_props_2026-04-29.parquet",
    "exists": true,
    "mtime_utc": "2026-04-29T16:18:08Z",
    "age_hours": 2.16,
    "rows": 104,
    "stats_in_predictions": ["ast","blk","fg3m","pts","reb","stl"],
    "missing_supported_stats": ["tov"],
    "tov_status": "missing_from_prediction_source"
  },
  "predictions_refresh": null,
  "availability_table": {
    "path": "data/player_availability_asof.parquet",
    "exists": true,
    "mtime_utc": "2026-04-19T01:47:03Z",
    "age_hours": 257.77,
    "freshness_status": "fresh | stale | very_stale | unknown"
  },
  "model_artifacts": {
    "files": [ /* pmf_cal_meta.json, pmf_cal_role_*.pkl, etc. */ ],
    "calibration_source": "phase8_role_aware_pmf_cal_v2",
    "phase": "phase10c",
    "tov_overlay_status": "off",
    "tov_overlay_reason": "Phase 10D/10D.2 overlay failed independent validation; see docs/phase11_tov_structural_refit_plan.md",
    "all_present": true
  },
  "finals": {
    "path": "data/player_game_stats.parquet",
    "exists": true,
    "mtime_utc": "...",
    "age_hours": 13.4,
    "has_finals_for_date": false,
    "finality_status": "finals_pending | finals_present"
  },
  "overall_status": "ready | partial | not_ready",
  "tov_status": "missing_from_prediction_source | current_phase8"
}
```

`overall_status` is computed as:

| condition                                                    | status      |
|--------------------------------------------------------------|-------------|
| predictions missing OR model artifacts incomplete            | `not_ready` |
| odds `status != ok`, but predictions + artifacts present     | `partial`   |
| everything present and `odds.status == ok`                   | `ready`     |

`build_daily_pmf_delivery.py` does **not** refuse to publish on
`partial` or `not_ready` — those signals propagate into the
`run_manifest.freshness_manifest.overall_status` field and are reflected
in the `finality_status` rollup so downstream consumers can decide.

---

## 2. Freshness classification

`age_hours` is computed against UTC now and bucketed:

| bucket        | age           | semantics                                              |
|---------------|---------------|--------------------------------------------------------|
| `fresh`       | ≤ 3 hr        | the input was refreshed for this slate                 |
| `stale`       | 3 hr – 12 hr  | the input is the same as last slate but still useful   |
| `very_stale`  | > 12 hr       | the input has not been refreshed in a day              |
| `unknown`     | file missing  | the input is not on disk at all                        |

These thresholds match `_injury_freshness()` in
`scripts/build_daily_pmf_delivery.py` so that the row-level
`injury_freshness_status` flag and the manifest's
`availability_table.freshness_status` agree.

---

## 3. On-call response

| symptom                                          | likely cause                                                  | fix                                                                                                                                  |
|--------------------------------------------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `odds.status == skipped:no_api_key`              | `ODDS_API_KEY` env var unset in the job                        | confirm GitHub Actions secret `ODDS_API_KEY` is populated; never paste the key into logs                                              |
| `odds.status == fail` for one region             | The Odds API returned 429/5xx for that region group            | rerun `refresh_daily_inputs.py --regions <failing_region>` once; if persistent, drop the region for this slate and note in the PR    |
| `predictions.exists == false`                    | `predictions/all_props_{date}.parquet` not produced upstream   | rerun the prediction job (see `daily_predictions.yml`); only then re-trigger `daily_pmf_delivery.yml`                                |
| `predictions.tov_status == missing_from_prediction_source` | predict.py is market-driven and emitted no TOV rows | NOT fixable today; requires Phase 11C player-stat-grid prediction refactor (see `docs/phase11_tov_structural_refit_plan.md` §3). Until then, finality_status stays provisional with blocker `missing_stats:tov`. |
| `availability_table.freshness_status == very_stale` | injury feed not refreshed                                   | requires `BDL_API_KEY` (BDL `/v1/player_injuries`) **and** an upstream `predict.py` re-run. The delivery still ships, but `finality_status` carries blocker `injury_very_stale`. The freshness manifest captures the exact env var needed in `model_artifacts` / `availability_table` rollups. |
| `model_artifacts.all_present == false`           | a calibrator pickle is missing                                 | this is an emergency — never proceed; rebuild artifacts from the most recent retrain run                                              |
| `finals.has_finals_for_date == true` AND no `after_game_*` files in delivery | the after-game scorer did not run               | rerun `scripts/score_daily_pmf_delivery_after_game.py --date {date}`                                                                  |
| `role_freshness_status == derived_from_projected_minutes` for every row | no confirmed-lineup source consumed | acceptable for `provisional` delivery. To reach `final`, wire confirmed lineups (BDL `get_lineups` or NBA injury report starter flag) into `predict.py` and republish predictions. |
| `role_freshness_status == missing` for any row | predictions did not emit `mp_bucket` for that (player, stat) | confirms an upstream predict.py regression; investigate `correlation/sgp_engine.mp_bucket` invocation in the predict pipeline before shipping |

---

## 3a. Required external credentials and their effect on `finality_status`

| credential / source        | env var(s)        | what stops working without it                                                                                              | resulting blocker codes                  |
|----------------------------|--------------------|----------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| The Odds API               | `ODDS_API_KEY`     | `refresh_daily_inputs.py` skips the live snapshot; `market_comparison` and `publishable_edges` are empty.                  | `market_coverage_none`                   |
| BallDontLie injury feed    | `BDL_API_KEY`      | `predict.py` falls back to whatever is on disk; `data/player_availability_asof.parquet` ages out and the feature is stale. | `injury_very_stale`                      |
| NBA official injury report | (no key required, requires `nbainjuries` Python package on the runner) | `merge_injury_sources` returns an empty official report; predict.py runs with BDL only. Same blocker code as above when stale. | `injury_very_stale`                      |
| Confirmed lineups          | `BDL_API_KEY` (`/v1/lineups` endpoint) | `role_bucket` cannot be confirmed; we fall back to `derived_from_projected_minutes`. The delivery still ships. | `lineup_unconfirmed`                     |
| Phase 11C model-only-grid  | _internal model refactor; not an external credential_ | TOV (and any other supported stat with no offered market line) is silently absent from predictions. | `missing_stats:tov` (or any supported stat) |

`build_daily_pmf_delivery.py` writes the `required_to_resolve` field on
every blocker entry in `wizard_of_odds/run_manifest.json` so on-call
operators don't have to re-derive the mapping above from memory.

---

## 4. Hard rules echoed in this runbook

These rules are enforced by `refresh_daily_inputs.py` and verified by
the validator in `build_daily_pmf_delivery.py`:

1. **Never log the API key.** `oddsapi_nba_props.py` masks `apiKey` in
   every URL log line. `refresh_daily_inputs.py` reads the key from
   `os.environ` and never prints it.
2. **Never fabricate inputs.** If predictions / availability / finals /
   odds are missing, the manifest faithfully records `exists=false` and
   the build either refuses (predictions/artifacts missing) or ships
   provisional with the freshness blockers spelled out.
3. **Never wire Phase 10D / 10D.2 TOV overlays.** `model_artifacts.
   tov_overlay_status` is hard-coded to `off` and the row-level
   `tov_status` flag is `current_phase8` regardless of what is on disk.
4. **Never market-anchor model-only PMFs.** The freshness manifest is
   advisory only. `build_daily_pmf_delivery.py` reads it for status
   propagation and does not adjust any PMF probability based on a
   market field.

---

## 5. Wiring with `build_daily_pmf_delivery.py`

```
$ python scripts/refresh_daily_inputs.py --date YYYY-MM-DD --regions us us2
   ↓ writes data/freshness_manifest/YYYY-MM-DD.json
$ python scripts/build_daily_pmf_delivery.py --date YYYY-MM-DD --snapshot morning
   ↑ auto-discovers data/freshness_manifest/YYYY-MM-DD.json
   ↑ surfaces: overall_status, odds_status, books_seen, regions_requested,
              predictions_mtime_utc, availability_freshness_status,
              tov_status, finals_finality_status
   ↓ writes deliveries/YYYY-MM-DD/wizard_of_odds/run_manifest.json
        with the freshness fields embedded under
        manifest.freshness_manifest
```

The two scripts are coupled by the manifest contract above, not by
shared imports — either can be rerun independently for forensics.

---

## 6. Storage hygiene

- `data/odds_api/raw/` and `data/odds_api/processed/` accumulate one
  subfolder per UTC date. They are not staged. Prune locally with
  `find data/odds_api/{raw,processed} -mtime +30 -type d` if disk
  pressure is a concern.
- `data/freshness_manifest/` accumulates one JSON per delivery date.
  Same retention policy as above; not staged.

---

## 7. Related docs

- `docs/daily_pmf_delivery_spec.md` — the delivery contract (row
  schema, validation gates, finality rollup).
- `docs/phase11_tov_structural_refit_plan.md` — why TOV is the only
  expected-missing supported stat today.
- `.github/workflows/daily_pmf_delivery.yml` — the scheduled jobs that
  drive this pipeline in CI. Phase 12D retired the morning cron and
  Phase 12D-amend split the schedule into two lifecycles: WoO's
  monetization feed (15:00 / 18:00 / 20:00 UTC) and Derek's evaluation
  feed (22:25 UTC first run, every-15-min refresh through 03:10 UTC,
  03:25 UTC close lock). After-game scoring stays at 06:30 UTC. The
  `morning` job remains manual-only.

## 8. Schedule-driven gating (Phase 12D)

`scripts/run_daily_delivery_pipeline.py` reads
`data/odds_api/processed/{date}/*.parquet` (or
`data/historical_game_odds.parquet` as fallback) to determine the
slate's tipoff times and skips `derek_near_lineup` / `close_lock`
runs where no game tipoff falls within `[now − 15 min, now + 45 min]`.
Pass `--force-run` to bypass the gate for manual backfills outside the
lineup window. When schedule data isn't yet on disk (fresh CI checkout
before `refresh_daily_inputs.py`), the gate is permissive — the cron
schedule is the primary timing control, and a single missed gate-check
costs at most one extra Odds API request, never a fabricated PMF.

The WoO monetization runs (`woo_morning_monetization`,
`woo_afternoon_refresh`) **deliberately bypass the gate** — the
public-facing feed publishes on its own clock so users can see model
predictions and click affiliate odds buttons earlier in the day, with
`finality_status_public=PROVISIONAL_EARLY_MARKET` until lineups
confirm.
