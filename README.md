# NBA Player Props PMF Production System

This repo produces full discrete PMFs for NBA player prop outcomes, converts PMFs into fair over/under probabilities, compares those probabilities to market prices, and publishes daily outputs for:

- **Derek / EV Analytics** GitHub delivery package — per-game current-live, T-minus-25, and close-lock snapshots with PMF, market comparison, edge audit, and human-readable reports.
- **Wizard of Odds** public + dev pages — `nba-props.html`, `nba-pmf-research.html`, plus the `affiliate_dashboard.json` / `pmf_research.json` contract.
- **Internal training, recalibration, scoring, and operator health reports** — nightly retraining, deferred-retry settled-outcome ingestion, after-game scoring, PMF variance experience study, single-page operator dashboard.

The model is scored prospectively against market via Brier, logloss/NLL, mean/variance A/E, and quantile coverage. **Do not claim market superiority** unless the latest rolling benchmark supports it. Today's variance experience study reports `model_trails_market=True`; treat the model as a recalibration roadmap, not a market-beating signal.

---

## Current production status

- **generated_at_utc:** 2026-05-05T01:30:00+00:00
- **latest origin/main SHA (at the time of this README):** `84cade383e5a48f94e1665eafc837e1a3a239bff` (regenerate via `scripts/build_daily_status_readmes.py` after each push)
- **run_date:** 2026-05-04
- **ET slate date:** 2026-05-04
- **latest settled outcome date:** 2026-05-03 (`data/player_game_stats.parquet` max_game_date)
- **champion_model_id:** `challenger-2026-04-30`
- **trained_through_date:** 2026-04-30
- **calibrated_through_date:** 2026-04-30
- **latest completed challenger (no-promote):** `challenger-2026-05-03` (cutoff training PASS, promotion withheld per `gate_failed:promotion_clock_safe`)

> **Note:** `PASS` for an artifact is **not** the same as a scheduled-cron success. Manual recovery and scheduled success are reported as separate rows in the grid below.

## Production status grid

| row | status | notes |
|---|---|---|
| **scheduled_training_cron** | VALID_SKIP | Multi-cron deferred-retry pattern on origin/main. Resolver halts → `TRAINING_VALID_SKIP_PASS` (exit 0), not red failure. Today's morning cron (run `25316091911`) red-failed pre-13AJ; manual recovery via workflow_dispatch (run `25340019625`) trained challenger-2026-05-03 successfully. Tomorrow's scheduled crons (09:30 / 12:30 / 15:30 / 18:30 / 21:30 UTC) will valid-skip until BDL settles 2026-05-04 outcomes, then run automatically. |
| **training_run** | PASS | `artifacts/models/challengers/2026-05-03/{train_manifest,calibration_manifest,validation_report,promotion_decision}.json` + `aggregate_input_audit.json` (`no_leakage_pass=true`, max=2026-05-03). |
| **scheduled_recalibration_cron** | VALID_SKIP | Same workflow chain as training. Same retry cadence. |
| **recalibration_run** | PASS | Calibration manifest `dry_run=false`, `status=ok`. PMF calibration log present. |
| **daily_predictions** | PASS | `predictions/all_props_2026-05-04.parquet` (65 rows, 2 games), `singles_2026-05-04.json` (8 picks), `pmf_display_2026-05-04.json` (8 props), `nba_props_today.json` refreshed (count=65, date=2026-05-04). |
| **derek_near_lineup** | PASS | `deliveries/2026-05-04/derek_forward_feed/feed_manifest.json` exists. ET-anchored date resolution + predict.py prerequisite check (Phase 13AJ) prevent the post-midnight UTC rollover failure. |
| **derek_current_live** | PENDING | 2026-05-04 current_live snapshots have not yet been produced for either game (workflow runs throughout the day). For the canonical previous-day delivery (2026-05-03), all current_live snapshots are PASS. |
| **derek_t_minus_25** | MISSED_DOCUMENTED + PENDING | Game 21708671 (tipped 2026-05-04 20:13 ET / 2026-05-05 00:13 UTC): `missed_snapshot_manifest.json` written by dispatcher (state=`MISSED_POST_TIP`, no fabricated pre-tip data). Game 21707972 (tips 2026-05-04 21:40 ET): T-25 dispatcher fires within minutes at the next cron. |
| **derek_close_lock** | PENDING + MISSED_DOCUMENTED | Same shape as T-25. Same resolution. |
| **derek_after_game_scoring** | PENDING | 2026-05-04 outcomes settle overnight after games conclude. Tomorrow's `after_game` cron (06:30 UTC) joins outcomes and emits `DEREK_AFTER_GAME_SCORING_PASS`. The previous delivery (2026-05-03) is PASS today: `snapshots_scored=2  props_scored=68  unjoined=0`. |
| **woo_public_export** | PASS | `predictions/nba-props.html` (45 KB) + `predictions/nba_props_today.json` (count=65, date=2026-05-04) + `public_export/wizard_of_odds/2026-05-04/{affiliate_dashboard,pmf_research}.json`, `latest/`, root copies. PMF research uses tail-bucket convention (`"<k>+"` labels for sparse upper tails). |
| **woo_after_game_scoring** | PENDING | Same upstream condition as Derek scoring. 2026-05-03 is PASS today (`props_scored=68  mean_nll=2.7432`). |

## Derek outputs

Path: `deliveries/<date>/derek_game_snapshots/`

Each delivery includes:
- `README.md` — per-day index keyed by team-name matchup.
- Per-game folders `<game_id>/<snapshot_type>/` where `<snapshot_type>` ∈ `{current_live, t_minus_25, close_lock}`.
- Within each snapshot folder:
  - `snapshot_report.md` — plain-English summary
  - `market_comparison.csv` — per-prop model vs market, edge_publish_status, calibration_support_status
  - `full_pmf_wide.csv` — full per-row PMF JSON
  - `outcome_level_probabilities.csv` — long-form PMF (`source_row_id`, `row_id`, `k`, `p_k`)
  - `lineup_injury_impact_report.md` / `pmf_driver_decomposition.md` / `direct_lineup_impact_report.md`
  - `missed_snapshot_manifest.json` + `missed_snapshot_report.md` when a pre-tip snapshot was honestly missed (e.g. game already tipped before the workflow had a chance to publish; the dispatcher writes a documented marker rather than fabricating pre-tip data).
  - `failed_snapshot_manifest.json` + `failed_snapshot_report.md` (Phase 13AJ) when the runner subprocess crashed mid-snapshot — captures full child stdout, stderr, and Python traceback so partial directories cannot mask as PASS.

**Hard rule:** do **not** fabricate pre-tip snapshots after tip. Missed pre-tip snapshots must be documented, not backfilled as if live.

The Derek snapshot index for today: `deliveries/2026-05-04/derek_game_snapshots/`

## Wizard of Odds public export

Public URLs (deployed dev environment):

- https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html
- https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-pmf-research
- https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-pmf-research.html

Required JSON contract (verified locally + remotely):

```
public_export/wizard_of_odds/<date>/affiliate_dashboard.json   (rows non-empty)
public_export/wizard_of_odds/<date>/pmf_research.json          (players non-empty)
public_export/wizard_of_odds/latest/affiliate_dashboard.json   (mirror of latest <date>)
public_export/wizard_of_odds/latest/pmf_research.json
public_export/wizard_of_odds/affiliate_dashboard.json          (root copy)
public_export/wizard_of_odds/pmf_research.json                 (root copy)
```

`pmf_research.json` renders the terminal survival-ladder mass as a tail bucket (e.g. `"20+"`) with `is_tail: true`, never as `P(X=20)` masquerading as a single discrete-point probability.

## Model performance / calibration

The model is scored prospectively. **No claim is made of market superiority**; today's variance experience study explicitly reports `model_trails_market=True`.

Latest sample (as-of 2026-05-03; 1,208 settled rows, lookback 60 days):

| metric | value | reading |
|---|---:|---|
| mean A/E | 1.144 | actuals exceed expected means by ~14.4% — recalibration target |
| variance A/E | 0.913 | PMF spread reasonably close (band 0.80–1.20) |
| std residual mean | 0.211 | slight positive bias |
| std residual sd | 1.052 | dispersion close to calibrated |
| model Brier (over/under) | 0.278 | trails market |
| market Brier (over/under) | 0.246 | — |
| model logloss (over/under) | 0.762 | trails market |
| market logloss (over/under) | 0.688 | — |
| coverage @ 90 | 0.899 | near-target |

Reports:
- Variance experience study index: `artifacts/experience_studies/README.md`
- Latest study: `artifacts/experience_studies/pmf_variance_experience_2026-05-03.md`
- Daily model report: `artifacts/model_daily_reports/2026-04-30/daily_model_training_report.md` (champion); `artifacts/model_daily_reports/2026-05-03/daily_model_training_report.md` (no-promote challenger)

## Production workflows

| workflow | purpose |
|---|---|
| `.github/workflows/nightly_training_calibration.yml` | 5× daily cron (09:30/12:30/15:30/18:30/21:30 UTC). Pre-resolver BDL refresh + multi-cron deferred-retry. Halt = `TRAINING_VALID_SKIP_PASS` (exit 0), real crash = red. Writes audit artifacts and commits as Joseph Shackelford. |
| `.github/workflows/daily_predictions.yml` | Daily 13:00 UTC predict + grade. Refreshes `nba_props_today.json`, runs `verify_daily_prediction_outputs`, `verify_woo_nba_props_page`, daily automation health, full production contract. |
| `.github/workflows/daily_pmf_delivery.yml` | Multi-mode (`derek_near_lineup` / `woo_morning_monetization` / `woo_afternoon_refresh` / `after_game`). Near-lineup uses TZ=America/New_York date resolution; predict.py runs first if dated parquet missing. After-game cron (06:30 UTC) settles outcomes and re-runs scoring + experience study. |
| `.github/workflows/derek_game_snapshots.yml` | Per-game current_live / T-25 / close-lock dispatcher every 15 min during the slate window. Hardened child-failure logging + `failed_snapshot_manifest.json` writer (Phase 13AJ). |
| `.github/workflows/wizard_of_odds_ftp_deploy.yml` | Pushes WoO public export artifacts to the FTP host that backs the deployed pages. |

Each workflow honors:
- Scheduled training/recalibration retries or valid-skips when upstream settled data is unavailable.
- Daily predictions must generate `predictions/all_props_<date>.parquet`.
- Derek near-lineup generates/waits for predictions, never fails because the prediction parquet is missing.
- Derek T-25/close-lock fires only when due, otherwise PENDING/NOT_DUE.
- After-game scoring remains PENDING until outcomes are settled.

## Operator runbook

One-command daily check:

```
python3 scripts/operator_daily_check.py \
  --date $(date -u +%Y-%m-%d) \
  --derek-date $(TZ=America/New_York date +%Y-%m-%d) \
  --required-outcomes-through $(TZ=America/New_York date -d 'yesterday' +%Y-%m-%d 2>/dev/null \
                                || TZ=America/New_York date -v-1d +%Y-%m-%d)
```

Lower-level individual verifiers:

```
python3 scripts/verify_full_daily_production_contract.py \
  --date 2026-05-04 --derek-date 2026-05-04 --required-outcomes-through 2026-05-03

python3 scripts/verify_daily_readme_freshness.py \
  --date 2026-05-04 --derek-date 2026-05-04

python3 scripts/verify_woo_public_export_contract.py \
  --date 2026-05-04 \
  --base-url https://dev.wizardofodds.com/tools/odds-scanner/predictions \
  --require-remote
```

## Latest artifact links

- Daily automation health (today): `artifacts/automation_health/daily_automation_health_2026-05-04.md`
- Full production contract (today): `artifacts/automation_health/full_daily_production_contract_2026-05-04.json`
- Latest model daily report: `artifacts/model_daily_reports/2026-05-03/daily_model_training_report.md`
- Latest experience study: `artifacts/experience_studies/pmf_variance_experience_2026-05-03.md`
- Latest Derek delivery (canonical, complete): `deliveries/2026-05-03/derek_game_snapshots/README.md`
- Today's Derek delivery (in-progress): `deliveries/2026-05-04/derek_game_snapshots/`
- Latest WoO public export: `public_export/wizard_of_odds/2026-05-04/`
- WoO public export latest pointer: `public_export/wizard_of_odds/latest/`
