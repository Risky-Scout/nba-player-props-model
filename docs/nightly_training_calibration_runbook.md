# Nightly Training & Calibration — Operator Runbook

This runbook covers the Phase 13A/13B champion–challenger automation. It tells
you how to run, inspect, recover, and (eventually) extend the system.

## TL;DR

| Question | Answer |
| --- | --- |
| What runs nightly? | `.github/workflows/nightly_training_calibration.yml` at **09:30 UTC** |
| What does it do today? | Dry-run challenger snapshot of champion → all gates fail "no improvement" → no promotion → champion unchanged |
| What about real retraining? | **Blocked.** Authoritative analysis: `docs/phase13c_real_training_blockers.md` (Phase 13B's analysis was superseded — daily-training in this codebase is `scripts/calibrate_pmf.py`, not `pipelines/train.py`). |
| Can it disrupt Derek/WoO deliveries? | No. 14:30 UTC promotion cutoff guards the 15:00 UTC WoO publish window |
| Where is the current champion recorded? | `artifacts/models/registry/champion_pointer.json` |
| How do I check the system is healthy? | `python3 scripts/verify_daily_automation_health.py` → must print `DAILY_AUTOMATION_HEALTH_PASS` |

## Timing schedule (UTC)

| Time | Job | Source |
| --- | --- | --- |
| 06:30 | After-game scoring (yesterday's slate) | `daily_pmf_delivery.yml` |
| **09:30** | **Nightly training/calibration** | `nightly_training_calibration.yml` |
| 14:30 | **Promotion cutoff** — orchestrator refuses to promote past this time | constant in `training_automation.py` |
| 15:00 | WoO morning monetization | `daily_pmf_delivery.yml` |
| 18:00 | WoO afternoon refresh | `daily_pmf_delivery.yml` |
| 20:00 | WoO afternoon refresh | `daily_pmf_delivery.yml` |
| 22:25 | Derek first evaluation snapshot | `daily_pmf_delivery.yml` |
| 22:40–03:10 | Derek near-lineup refreshes (every 15 min) | `daily_pmf_delivery.yml` |
| 03:25 | Close lock | `daily_pmf_delivery.yml` |

The nightly training workflow has `timeout-minutes: 240`. Worst-case finish is
13:30 UTC, leaving a 60-minute buffer before the 14:30 promotion cutoff and a
90-minute buffer before the 15:00 WoO publish.

## How the pipeline runs

The orchestrator `scripts/run_nightly_training_and_calibration.py` runs these
steps in order, halting safely on any failure:

1. **Outcome refresh** — `scripts/refresh_bdl_player_game_stats.py --end-date <date>` (best-effort; failure is advisory only).
2. **Readiness** — `scripts/check_daily_training_readiness.py --date <date>`. Verifies outcome rows, stat columns, no impossible values, no future leakage in inputs, no active promotion lock, sample-size floors. **Blocking failure halts the run**, champion unchanged.
3. **Train challenger** — `scripts/train_daily_challenger_model.py --as-of-date <date> [--dry-run|--no-dry-run]`.
4. **Calibrate challenger** — `scripts/calibrate_daily_challenger_pmfs.py --as-of-date <date> [--dry-run|--no-dry-run]`.
5. **Validate** — `scripts/validate_champion_vs_challenger.py --as-of-date <date>`. Applies 16 promotion gates. Writes `validation_report.json` and `promotion_decision.json`.
6. **Promote (maybe)** — `scripts/promote_challenger_if_validated.py --as-of-date <date>`. Skipped if `--no-promote` was set, if past 14:30 UTC, or if `decision.promote=false`. Atomic pointer swap behind a lockfile.
7. **Smoke tests** — champion pointer well-formed, Derek + WoO scripts present.
8. **Run manifest** — `artifacts/nightly_training/<date>/run_manifest.json` + `run_summary.md`.

After the run, the verifier prints one of:

- `TRAINING_AUTOMATION_VERIFICATION_PASS` (Phase 13A backwards-compat line; always printed on success)
- followed by `TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS` or `TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS`

## The three operational paths

### Path A — Dry-run (current default)

What happens: challenger snapshots the current champion. All comparative gates
fail because there is no improvement to demonstrate. `decision.promote=false`.
Champion stays unchanged.

This is the **scheduled** behavior today. It exercises the pipeline end-to-end
every night, ensuring the framework still works without changing production.

```
python3 scripts/run_nightly_training_and_calibration.py \
    --as-of-date 2026-04-29 \
    --dry-run
python3 scripts/verify_training_automation.py --as-of-date 2026-04-29
# → TRAINING_AUTOMATION_VERIFICATION_PASS
# → TRAINING_AUTOMATION_DRY_RUN_VERIFICATION_PASS
```

### Path B — `--no-promote`

What happens: full pipeline runs, validation gates evaluate, no promotion
happens regardless of the decision. Use this for trial real-training runs once
the blockers are cleared.

```
python3 scripts/run_nightly_training_and_calibration.py \
    --as-of-date 2026-04-29 \
    --no-promote
```

### Path C — Real training (blocked)

What it would do: build real challenger calibrators (and per-fold partial
refits of minutes / rate / hurdle / fg3m) in
`artifacts/models/challengers/<date>/`, score both sides on a leakage-safe
holdout, and promote if the gates pass. This path is intentionally
unimplemented; `_train_full_candidate()` raises `NotImplementedError` and the
calibration script's real path falls back the same way.

The real surface that needs to be unblocked is `scripts/calibrate_pmf.py`
(plus a small downstream patch in
`src/nba_props_model/calibration/pmf_calibration.py` so the final-fit step
respects the output-dir override). See
`docs/phase13c_real_training_blockers.md` for the corrected analysis,
acceptance criteria for Phase 13D, and the ~335 LOC of changes required.

## Inspecting a run

Every run writes a single, predictable directory:

```
artifacts/nightly_training/<as_of_date>/
├── run_manifest.json                      # the canonical run record
├── run_summary.md                         # human-readable summary
├── readiness_report.json                  # copy of the readiness output
├── validation_report.json                 # copy of the validation output
├── promotion_decision.json                # copy of the promotion decision
├── promotion_manifest.json                # only if promotion actually fired
├── smoke_test_report.json                 # champion-pointer / Derek / WoO smokes
├── automation_verification_report.json    # the verifier's structured output
├── automation_verification_summary.md     # the verifier's human summary
└── logs/                                  # per-step subprocess logs (gitignored)
```

The challenger workspace is at `artifacts/models/challengers/<as_of_date>/`
(only JSON manifests are committed; pickles + parquets are gitignored).

## How to tell whether the champion changed

The cheapest signal: compare `model_version` in `champion_pointer.json` to its
prior value.

```
git log -p artifacts/models/registry/champion_pointer.json | head -40
```

If the latest commit changed `model_version`, a promotion happened. The CSV
log captures every promotion attempt:

```
cat artifacts/models/registry/promotion_log.csv
```

After a successful promotion the prior champion's metadata is preserved at
`artifacts/models/champion/v_<timestamp>/`, including the previous pointer
backed up as `champion_pointer.previous.json`.

## How to roll back the champion pointer

If a bad promotion ever lands, the rollback is to copy the previous pointer
back into place. The previous pointer is recorded in two ways:

1. The latest backup directory: `ls artifacts/models/champion/ | grep '^v_' | sort | tail -1`.
   That directory contains `champion_pointer.previous.json`.
2. Git history: `git log artifacts/models/registry/champion_pointer.json` →
   pick the prior commit and `git show <sha>:artifacts/models/registry/champion_pointer.json > /tmp/prev.json`.

Then atomically swap it back. **Always do this through Python or `mv`, never
through a half-written write:**

```
python3 - <<'PY'
import shutil
from pathlib import Path
shutil.copy2("/tmp/prev.json",
             "artifacts/models/registry/champion_pointer.json")
PY
```

After rollback, also restore any model pickles you copied during the
promotion. In Phase 13A/B the promotion does not copy pickles (challenger
artifacts live alongside, not on top of, champion artifacts) so usually the
pointer-only rollback is enough.

## How to verify daily automation health

```
python3 scripts/verify_daily_automation_health.py
```

This 14-check probe reports on the WoO export, Derek feed, all required
workflows, the champion pointer, no-overlap between training and delivery
crons, no dirty production files, no secrets in outputs, and that delivery
scripts do not reference challenger directories. Final line on success:
`DAILY_AUTOMATION_HEALTH_PASS`. Outputs land at
`artifacts/automation_health/latest_health_*`.

Run this whenever you are debugging a delivery issue and want to rule out
infrastructure drift.

## How to inspect a no-promotion report

The most common outcome is `decision.promote=false`. To find the reason:

```
python3 -c '
import json
d = json.load(open("artifacts/models/challengers/2026-04-29/promotion_decision.json"))
print("promote:", d["promote"])
print("reason:", d["reason"])
print("gates_failed:", d["gates_failed"])
'
```

Common no-promotion reasons:

| `reason` | Meaning |
| --- | --- |
| `gate_failed:nll_improves_or_non_worse` | Challenger's NLL did not improve. (Always true in dry-run.) |
| `gate_failed:promotion_clock_safe` | UTC time was at or past 14:30. The orchestrator hit the cutoff before validate could decide. |
| `gate_failed:pmf_validity` | One or more PMF parquets had probabilities that did not sum to 1, were negative, or were non-finite. Production champion is suspected; investigate. |
| `gate_failed:derek_feed_compatibility` / `gate_failed:woo_export_compatibility` | A Derek or WoO delivery script is missing. Check `git status` on `scripts/`. |
| `gate_failed:no_phase10d_overlays_referenced` | A Phase 10D / 10D.2 token leaked into a manifest. Investigate; do not promote. |
| `secret_in_manifest_aborted_promotion` | A plausible API key shape was found in a manifest. Inspect, scrub, re-run. |

## Non-interference with Derek and Wizard of Odds

The framework is designed so that delivery jobs read **only** from the flat
champion directory `artifacts/models/`. They never reference
`artifacts/models/challengers/`. The verifier enforces this via
`check_isolation`, and the daily health check repeats the same scan.

Promotion happens behind a lockfile (`artifacts/models/registry/promotion.lock`,
created with `O_EXCL`). If a delivery script ever needs to assert "champion is
not being modified right now," that lock is the contract.

## Authorship

All commits to this surface must be authored as
`Joseph Shackelford <josephshack@gmail.com>`. The workflow's `Stage and
commit` step uses `git config` and `--author` to enforce this. No `Claude`,
`Anthropic`, or `Bot` co-author trailer is used in this project.
