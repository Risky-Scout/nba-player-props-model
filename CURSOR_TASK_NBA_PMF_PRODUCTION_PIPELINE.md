# Cursor Task — NBA PMF Production Pipeline v3

Read all `.cursor/rules/*.mdc` files before editing.

## Mission

Make `.github/workflows/nba_pmf_delivery.yml` the single slate-aware production workflow while preserving all existing model, calibration, injury, lineup, Phase 8, Phase 13, delivery, and benchmark behavior.

This is not a model rewrite. It is orchestration, timing, validation, and promotion safety.

## Phase 0 — Inventory before editing

Before changing code, create a local notes file:

`_cursor_inventory_nba_pmf_delivery.md`

Inventory the exact commands and script arguments used in:

- `.github/workflows/daily_pmf_delivery.yml`
- `.github/workflows/nightly_training_calibration.yml`
- `.github/workflows/phase8.yml`
- `.github/workflows/phase13o_live_context_training.yml`
- `.github/workflows/phase13p_live_context_challenger.yml`
- `.github/workflows/phase13q_contextual_challenger.yml`
- `.github/workflows/phase13r_contextual_deployment_verification.yml`
- `.github/workflows/phase13s_direct_lineup_contextual_pmf.yml`
- `.github/workflows/derek_live_game_snapshots.yml`
- `.github/workflows/m86_delivery_contract_verifiers.yml`
- `.github/workflows/wizard_of_odds_ftp_deploy.yml`

Also inspect argparse/help for key scripts before using flags:
- `scripts/run_daily_delivery_pipeline.py`
- `scripts/run_nightly_training_and_calibration.py`
- `scripts/predictions_readiness_gate.py`
- `scripts/run_after_game_complete_scoring.py`
- Phase 8 scripts
- Phase 13 scripts

Do not invent flags.

## Phase 1 — Schedule resolver

Create:

`scripts/resolve_nba_pmf_schedule.py`

It must output:

- delivery_date
- as_of_date
- stage
- mode
- run_predict
- run_training
- run_phase8
- run_phase13
- run_delivery
- run_after_game
- run_verifiers
- allow_promote
- force_run
- valid_skip_reason

Support:
- `--event-name`
- `--schedule`
- `--manual-stage`
- `--manual-mode`
- `--manual-delivery-date`
- `--manual-as-of-date`
- `--manual-force-run`
- `--github-output`
- `--now-utc` for tests

Rules:
- timezone = America/New_York
- 06:30 UTC after_game scores previous ET slate
- 09:30/12:30 UTC model_chain with allow_promote=true
- 15:30/18:30/21:30 UTC model_chain_no_promote with allow_promote=false
- 14:00 UTC predict
- 15:00 UTC WoO morning
- 18:00/20:00 UTC WoO refresh
- Derek candidate windows valid-skip unless near a tip

For Derek:
- 35 to 11 minutes pre-tip => derek_near_lineup
- 10 to 0 minutes pre-tip => close_lock
- otherwise valid_skip_reason=outside_slate_delivery_window

For tests, allow:
`NBA_PMF_TEST_TIPOFF_ET=2026-05-20T20:30:00-04:00`

## Phase 2 — Workflow timing and architecture

Update:

`.github/workflows/nba_pmf_delivery.yml`

Required schedule:

```yaml
schedule:
  - cron: "30 6 * * *"
  - cron: "30 9 * * *"
  - cron: "30 12 * * *"
  - cron: "0 14 * * *"
  - cron: "0 15 * * *"
  - cron: "30 15 * * *"
  - cron: "0 18 * * *"
  - cron: "30 18 * * *"
  - cron: "0 20 * * *"
  - cron: "30 21 * * *"
  - cron: "25 22 * * *"
  - cron: "40,55 22 * * *"
  - cron: "10,25,40,55 23,0,1,2 * * *"
  - cron: "10 3 * * *"
  - cron: "25 3 * * *"
```

Add workflow_dispatch input:
- `force_run`
- stage options: predict, model_chain, model_chain_no_promote

Replace inline schedule routing with `scripts/resolve_nba_pmf_schedule.py`.

Remove workflow-level concurrency.

Add job-level concurrency:
- model chain by as_of_date
- Phase 8 by as_of_date
- Phase 13 by as_of_date
- predict by delivery_date
- delivery by delivery_date + mode
- after_game by delivery_date

Jobs:
1. resolve_context
2. readiness
3. model_chain_training_calibration
4. phase8_pmf_calibration_diagnostics_market_eval
5. phase13_live_context_contextual_lineup
6. predict_daily
7. delivery_build
8. after_game_scoring
9. final_contract_verifiers

Delivery must not depend on model_chain/Phase8/Phase13. It reads latest approved champion.

## Phase 3 — Model chain and calibration

The model chain must preserve the old nightly workflow behavior.

Use existing scripts and flags from inventory.

Required:
- settled-stat refresh/backfill with old 7-day BDL lag pattern
- `run_nightly_training_and_calibration.py`
- role/stat calibration
- promotion only before 14:30 UTC and only when gates pass
- no-promote at 15:30/18:30/21:30 UTC
- manual default no_promote=true

Add/maintain a calibration and market-superiority verification step.

Prefer existing repo scripts. If no single contract script exists, create:

`scripts/verify_calibration_market_superiority_contract.py`

It must read existing benchmark/calibration artifacts and enforce the inequalities in `.cursor/rules/02_calibration_market_superiority.mdc`.

Do not fake passing metrics.
If insufficient data, output `insufficient_sample` and block superiority claim/promotion.

## Phase 4 — Phase 8

Phase 8 runs only after successful model_chain_training_calibration.

Copy known-working commands from `.github/workflows/phase8.yml`.

Preserve:
- PMF calibration folds
- OOF aggregation
- combo OOF PMFs
- combo PMF calibrators
- diagnostics
- market-eval required
- role bucket contract
- combo role calibration contract
- unexplained calibration NaN verifier

## Phase 5 — Phase 13O/P/Q/R/S

Phase 13 runs only after successful Phase 8.

Strict order:
1. 13O live-context training dataset
2. 13P live-context challenger
3. 13Q contextual challenger
4. 13R contextual deployment verification
5. 13S direct-lineup contextual PMF

Use existing commands from the Phase 13 workflows.

Maintain:
- injury context
- lineup context
- live-context features
- direct-lineup features
- sensitivity checks
- leakage checks
- validation gates

Promote 13R/13S only when:
- allow_promote=true
- no_promote=false
- all validation/calibration/market gates pass

## Phase 6 — Predict daily

Add `predict_daily`.

Run at 14:00 UTC.

Must:
- run predictions readiness gate
- use existing prediction entrypoint from old workflow
- verify prediction outputs if verifier exists
- commit only prediction artifacts and automation health

## Phase 7 — Delivery build

Must:
- run predictions readiness gate before delivery pipeline
- pass `--force-run` only when resolver output force_run=true
- preserve hash of `deliveries/$D/derek_forward_feed/derek_unique_props_summary.csv`
- run delivery pipeline
- stamp champion metadata
- strip empty columns
- write review previews
- enforce CSV size contract
- run delivery verifiers
- build delivery index
- commit only approved delivery outputs

If BDL player props are empty:
- valid-skip BDL-only Derek main-line summary
- do not fabricate lines
- do not add status columns to derek_unique_props_summary.csv
- write status JSON if useful

## Phase 8 — After-game

Scheduled 06:30 UTC must score previous ET slate.

Must:
- run after-game scorer
- verify package consistency
- build rolling market benchmark if script exists
- build PMF variance/experience study if script exists
- run CSV hygiene and size contract
- build delivery index
- commit after-game delivery artifacts

## Phase 9 — Final verifiers

Final verifiers must run only if selected prerequisite stage jobs succeeded or skipped.

Do not run noisy verifiers after a failed prerequisite.

## Tests

Create/update:
- `tests/test_nba_pmf_delivery_schedule_resolver.py`
- `tests/test_nba_pmf_delivery_workflow_shape.py`
- `tests/test_calibration_market_superiority_contract.py` if a new contract script is created
- `tests/test_derek_bdl_empty_props_valid_skip.py` if BDL empty-props behavior is changed

Required resolver test cases:
- 06:30 UTC after_game previous ET date
- 09:30 UTC model_chain allow_promote=true
- 15:30 UTC model_chain_no_promote allow_promote=false
- 14:00 UTC predict
- manual delivery force_run=true
- 2026-05-20 8:30 PM ET:
  - 23:55 UTC => derek_near_lineup
  - 00:10 UTC => derek_near_lineup
  - 00:25 UTC => close_lock
  - 22:25 UTC => outside_slate_delivery_window

## Validation

Run:

```bash
python3 -m py_compile scripts/resolve_nba_pmf_schedule.py
python3 -m py_compile scripts/enforce_delivery_csv_size_contract.py
python3 -m py_compile scripts/run_daily_delivery_pipeline.py
python3 -m py_compile scripts/build_derek_forward_feed.py

python3 - <<'PY'
from pathlib import Path
import yaml
p = Path(".github/workflows/nba_pmf_delivery.yml")
with p.open("r", encoding="utf-8") as f:
    yaml.safe_load(f)
print(f"YAML_OK {p}")
PY

pytest -q \
  tests/test_nba_pmf_delivery_schedule_resolver.py \
  tests/test_nba_pmf_delivery_workflow_shape.py \
  tests/test_predictions_readiness_gate.py \
  tests/test_daily_pmf_delivery_workflow_shape.py \
  tests/test_derek_unique_props_summary.py \
  tests/test_derek_feed_source_contract.py
```

If a new calibration contract script is created, also run its test.

## Branch and PR

Use:

```bash
git fetch origin
git switch -c fix/nba-pmf-delivery-production-timing-and-calibration origin/main || git switch fix/nba-pmf-delivery-production-timing-and-calibration
```

Commit:

```bash
git add .github/workflows/nba_pmf_delivery.yml scripts tests .cursor CURSOR_READ_THIS_FIRST.md CURSOR_TASK_NBA_PMF_PRODUCTION_PIPELINE.md
git commit -m "ci: make NBA PMF Delivery production-timed and calibration-gated"
```

PR:

```bash
gh pr create \
  --base main \
  --head fix/nba-pmf-delivery-production-timing-and-calibration \
  --title "ci: make NBA PMF Delivery production-timed and calibration-gated" \
  --body "Makes the consolidated NBA PMF Delivery workflow slate-aware and production-timed, preserves Phase 8 and Phase 13O/P/Q/R/S chains, adds calibration/market-superiority gates, protects Derek unique summary, enforces CSV contracts, and keeps old workflows enabled until the new pipeline passes a full day."
```

Do not disable old workflows yet.
