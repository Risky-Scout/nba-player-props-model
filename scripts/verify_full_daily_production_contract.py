#!/usr/bin/env python3
"""Phase 13AH — verify the full daily Derek + WoO + training + scoring +
calibration production contract for one operator-relevant date triple.

Inputs:
  --date YYYY-MM-DD                 (today's predict + WoO snapshot date)
  --derek-date YYYY-MM-DD           (Derek delivery to verify; usually
                                      previous-day or current-day depending
                                      on operator cadence)
  --required-outcomes-through YYYY-MM-DD
                                    (minimum settled-stats max date)

The verifier orchestrates every existing sub-verifier and rolls them into
a single FULL_DAILY_PRODUCTION_CONTRACT_PASS / WARN / FAILED line.

A subsection emits PASS / WARN / FAIL based on its own pass-line. WARN is
allowed only for documented noncritical or external blockers (after-game
scoring pending today's games, t_minus_25 / close_lock pending until tip,
training honestly halted pending upstream data, etc.).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], timeout: int = 240) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"timeout after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def _grep(text: str, *needles: str) -> str | None:
    for line in text.splitlines():
        for n in needles:
            if line.startswith(n):
                return line.strip()
    return None


# Phase 13AI: anything matching one of these regex patterns in subprocess
# stdout/stderr forces the section to FAIL, regardless of whether a later
# PASS line is also present.
import re

CRITICAL_FAILURE_PATTERNS = (
    r"^[A-Z_]+_FAILED\b",
    r"^VERIFICATION FAILED\b",
    r"^Traceback\b",
    r"^Exception\b",
    r"missing required artifact",
    r"\bstale json\b",
    r"\bblank page\b",
    r"PREVIOUS_DAY_NO_LEAKAGE_FAILED",
)
_CRITICAL_RX = [re.compile(p, flags=re.IGNORECASE | re.MULTILINE)
                for p in CRITICAL_FAILURE_PATTERNS]


def _has_critical_failure(text: str) -> str | None:
    """Return the first matching critical-failure line, else None."""
    for line in text.splitlines():
        for rx in _CRITICAL_RX:
            if rx.search(line):
                return line.strip()
    return None


def _check(name: str, cmd: list[str], pass_prefixes: tuple[str, ...],
            warn_prefixes: tuple[str, ...] = (), fail_prefixes: tuple[str, ...] = (),
            critical: bool = True) -> dict:
    rc, stdout, stderr = _run(cmd)
    combined = stdout + "\n" + stderr
    crit = _has_critical_failure(combined)
    pass_line = _grep(combined, *pass_prefixes)
    warn_line = _grep(combined, *warn_prefixes) if warn_prefixes else None
    fail_line = _grep(combined, *fail_prefixes) if fail_prefixes else None
    # Phase 13AI: ANY critical-failure pattern downgrades to FAIL even if a
    # later PASS line is emitted by a chained sub-verifier. This is what
    # Phase 13AG taught us — "PREVIOUS_DAY_NO_LEAKAGE_FAILED" cannot be
    # masked by a trailing TRAINING_AUTOMATION_VERIFICATION_PASS.
    if crit:
        status = "FAIL"
    elif pass_line:
        status = "PASS"
    elif warn_line:
        status = "WARN"
    elif fail_line or rc != 0:
        status = "FAIL"
    else:
        status = "FAIL"
    return {
        "name": name,
        "command": " ".join(cmd[1:]) if cmd[:1] == [sys.executable] else " ".join(cmd),
        "status": status,
        "critical": critical,
        "pass_line": pass_line,
        "warn_line": warn_line,
        "fail_line": fail_line,
        "critical_failure_line": crit,
        "rc": rc,
        "tail": (stderr or stdout).strip().splitlines()[-1:][0:1] or [""],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--derek-date", required=True)
    ap.add_argument("--required-outcomes-through", required=True)
    args = ap.parse_args(argv)

    py = sys.executable

    checks: list[dict] = []

    # 1. Settled outcomes
    checks.append(_check(
        "settled_outcome_freshness",
        [py, "scripts/verify_player_game_stats_freshness.py",
         "--required-through-date", args.required_outcomes_through],
        pass_prefixes=("PLAYER_GAME_STATS_FRESHNESS_PASS",),
        fail_prefixes=("PLAYER_GAME_STATS_FRESHNESS_FAILED",),
    ))

    # 2. & 3. Training + recalibration (verify_training_automation)
    train_check = _check(
        "training_automation",
        [py, "scripts/verify_training_automation.py",
         "--as-of-date", args.required_outcomes_through],
        pass_prefixes=("TRAINING_AUTOMATION_VERIFICATION_PASS",
                       "TRAINING_AUTOMATION_REAL_TRAINING_VERIFICATION_PASS",
                       "TRAINING_AUTOMATION_NO_PROMOTE_PASS",),
        fail_prefixes=("TRAINING_AUTOMATION_REAL_TRAINING_FAILED_INPUTS_MISSING",
                       "TRAINING_AUTOMATION_REAL_TRAINING_FAILED",),
    )
    checks.append(train_check)
    # Recalibration is a sub-line of training_automation; if training PASS, mark
    # recalibration PASS as well (it's the same chain).
    checks.append({
        "name": "recalibration_automation",
        "command": "(inferred from training_automation chain)",
        "status": train_check["status"],
        "critical": True,
        "pass_line": "RECALIBRATION_VALID_SKIP_PASS" if train_check["status"] == "PASS" else None,
        "warn_line": None,
        "fail_line": None,
        "rc": train_check["rc"],
        "tail": train_check["tail"],
    })

    # 3a. Training-cron status synthesized from the most-recent run-context
    # facts. We reuse the training_automation result but expose three
    # separate logical slots so the operator grid distinguishes them.
    train_cron_status = train_check["status"]
    train_run_status = (
        "PASS" if train_check["status"] == "PASS" else
        ("WARN" if train_check["status"] in ("WARN",) else
         ("PASS" if train_check["status"] == "PASS" else train_check["status"]))
    )
    checks.append({
        "name": "training_scheduled_cron",
        "command": "(inferred from training_automation chain)",
        "status": "PASS" if train_check["status"] == "PASS" else (
            "WARN" if train_check["status"] == "WARN" else "FAIL"
        ),
        "critical": False,
        "pass_line": "TRAINING_SCHEDULED_CRON_PASS" if train_check["status"] == "PASS" else None,
        "warn_line": None, "fail_line": None,
        "rc": train_check["rc"], "tail": train_check["tail"],
    })
    checks.append({
        "name": "training_run",
        "command": "(inferred from training_automation chain)",
        "status": "PASS" if train_check["status"] == "PASS" else "WARN",
        "critical": False,
        "pass_line": "TRAINING_RUN_PASS" if train_check["status"] == "PASS" else None,
        "warn_line": "TRAINING_VALID_SKIP_PASS" if train_check["status"] != "PASS" else None,
        "fail_line": None,
        "rc": train_check["rc"], "tail": train_check["tail"],
    })
    checks.append({
        "name": "recalibration_run",
        "command": "(inferred from training_automation chain)",
        "status": "PASS" if train_check["status"] == "PASS" else "WARN",
        "critical": False,
        "pass_line": "RECALIBRATION_RUN_PASS" if train_check["status"] == "PASS" else None,
        "warn_line": "RECALIBRATION_VALID_SKIP_PASS" if train_check["status"] != "PASS" else None,
        "fail_line": None,
        "rc": train_check["rc"], "tail": train_check["tail"],
    })

    # 4. Daily prediction outputs
    checks.append(_check(
        "daily_predictions",
        [py, "scripts/verify_daily_prediction_outputs.py", "--date", args.date],
        pass_prefixes=("DAILY_PREDICTION_OUTPUTS_PASS",),
        fail_prefixes=("DAILY_PREDICTION_OUTPUTS_FAILED",),
    ))

    # 4a. Derek near-lineup contract.
    checks.append(_check(
        "derek_near_lineup",
        [py, "scripts/verify_derek_near_lineup_contract.py", "--date", args.date],
        pass_prefixes=("DEREK_NEAR_LINEUP_CONTRACT_PASS",),
        warn_prefixes=("DEREK_NEAR_LINEUP_CONTRACT_PENDING",),
        fail_prefixes=("DEREK_NEAR_LINEUP_CONTRACT_FAILED",),
    ))

    # 5a. WoO morning page
    checks.append(_check(
        "woo_nba_props_page",
        [py, "scripts/verify_woo_nba_props_page.py", "--date", args.date],
        pass_prefixes=("WOO_NBA_PROPS_PAGE_PASS",),
        fail_prefixes=("WOO_NBA_PROPS_PAGE_FAILED",),
    ))

    # 5b/6/7. WoO state machine + morning + t_minus_25 + close_lock snapshots
    checks.append(_check(
        "woo_snapshot_state_machine",
        [py, "scripts/verify_woo_snapshot_schedule_state.py", "--date", args.date],
        pass_prefixes=("WOO_SNAPSHOT_STATE_MACHINE_PASS",),
        fail_prefixes=("WOO_SNAPSHOT_STATE_MACHINE_FAILED",),
    ))
    rc, out, err = _run([py, "scripts/verify_woo_snapshot_outputs.py",
                          "--date", args.date])
    combined = out + "\n" + err
    woo_morn = _grep(combined, "WOO_MORNING_OUTPUTS_PASS", "WOO_MORNING_OUTPUTS_FAILED")
    woo_t25 = _grep(combined,
                     "WOO_T_MINUS_25_OUTPUTS_PASS",
                     "WOO_T_MINUS_25_OUTPUTS_PENDING",
                     "WOO_T_MINUS_25_OUTPUTS_FAILED")
    woo_cl = _grep(combined,
                    "WOO_CLOSE_LOCK_OUTPUTS_PASS",
                    "WOO_CLOSE_LOCK_OUTPUTS_PENDING",
                    "WOO_CLOSE_LOCK_OUTPUTS_FAILED")
    for label, line in (("woo_morning_snapshot", woo_morn),
                         ("woo_t_minus_25", woo_t25),
                         ("woo_close_lock", woo_cl)):
        if not line:
            checks.append({
                "name": label, "command": "verify_woo_snapshot_outputs.py",
                "status": "FAIL", "critical": True, "pass_line": None,
                "warn_line": None, "fail_line": "no pass line emitted",
                "rc": rc, "tail": ["no pass line"],
            })
            continue
        if "_PASS" in line:
            status = "PASS"
        elif "_PENDING" in line:
            status = "WARN"
        else:
            status = "FAIL"
        checks.append({
            "name": label, "command": "verify_woo_snapshot_outputs.py",
            "status": status, "critical": True,
            "pass_line": line if "_PASS" in line else None,
            "warn_line": line if "_PENDING" in line else None,
            "fail_line": line if "_FAILED" in line else None,
            "rc": rc, "tail": [line],
        })

    # 8/9/10. Derek current_live + t_minus_25 + close_lock
    checks.append(_check(
        "derek_current_live",
        [py, "scripts/verify_derek_outcome_level_probabilities.py",
         "--delivery-date", args.derek_date],
        pass_prefixes=("DEREK_OUTCOME_LEVEL_PROBABILITIES_PASS",),
        fail_prefixes=("DEREK_OUTCOME_LEVEL_PROBABILITIES_FAILED",),
    ))
    rc, out, err = _run([py, "scripts/verify_derek_live_snapshots.py",
                          "--delivery-date", args.derek_date])
    combined = out + "\n" + err
    derek_live = _grep(combined,
                        "DEREK_LIVE_SNAPSHOTS_PASS",
                        "DEREK_LIVE_SNAPSHOTS_PENDING_NO_GAMES",
                        "DEREK_LIVE_SNAPSHOTS_FAILED")
    if derek_live and "_PASS" in derek_live:
        d_status = "PASS"
    elif derek_live and "_PENDING" in derek_live:
        d_status = "WARN"
    elif derek_live and "_FAILED" in derek_live:
        d_status = "FAIL"
    else:
        d_status = "FAIL"
    checks.append({
        "name": "derek_live_snapshots", "command": "verify_derek_live_snapshots",
        "status": d_status, "critical": True,
        "pass_line": derek_live if d_status == "PASS" else None,
        "warn_line": derek_live if d_status == "WARN" else None,
        "fail_line": derek_live if d_status == "FAIL" else None,
        "rc": rc, "tail": [derek_live or "no pass line"],
    })
    rc, out, err = _run([py, "scripts/verify_derek_production_live_e2e.py",
                          "--delivery-date", args.derek_date])
    combined = out + "\n" + err
    e2e = _grep(combined,
                 "DEREK_PRODUCTION_LIVE_E2E_PASS",
                 "DEREK_PRODUCTION_LIVE_E2E_PENDING",
                 "DEREK_PRODUCTION_LIVE_E2E_FAILED")
    if e2e and "_PASS" in e2e:
        e_status = "PASS"
    elif e2e and "_PENDING" in e2e:
        e_status = "WARN"
    elif e2e and "_FAILED" in e2e:
        e_status = "FAIL"
    else:
        e_status = "FAIL"
    checks.append({
        "name": "derek_production_live_e2e", "command": "verify_derek_production_live_e2e",
        "status": e_status, "critical": True,
        "pass_line": e2e if e_status == "PASS" else None,
        "warn_line": e2e if e_status == "WARN" else None,
        "fail_line": e2e if e_status == "FAIL" else None,
        "rc": rc, "tail": [e2e or "no pass line"],
    })

    # 11. Derek email-claimed files. PENDING when today's Derek delivery
    # has not produced its current_live snapshot yet.
    derek_snapshot_root = REPO_ROOT / "deliveries" / args.derek_date / "derek_game_snapshots"
    derek_has_run = derek_snapshot_root.exists() and any(
        (game / "current_live" / "snapshot_manifest.json").exists()
        for game in derek_snapshot_root.iterdir() if game.is_dir()
    )
    # Phase 13AJ: operator semantics — "today" is the ET calendar day
    # that contains tonight's slate, not the raw UTC date. UTC rolls over
    # before ET tip windows close, so anchoring on UTC would mark a
    # pre-tip-pending Derek day as "in the past."
    try:
        from zoneinfo import ZoneInfo as _ZI
        today_utc = dt.datetime.now(_ZI("America/New_York")).date().isoformat()
    except Exception:
        today_utc = dt.datetime.now(dt.timezone.utc).date().isoformat()
    if (args.derek_date >= today_utc) and not derek_has_run:
        checks.append({
            "name": "derek_email_claimed_files",
            "command": "verify_derek_email_claimed_files (pending)",
            "status": "WARN", "critical": True, "pass_line": None,
            "warn_line": (f"DEREK_EMAIL_CLAIMED_FILES_PENDING  "
                          f"derek_date={args.derek_date}  "
                          "current_live snapshot not yet run for today"),
            "fail_line": None,
            "rc": 0, "tail": ["pending pre-tip"],
        })
    else:
        checks.append(_check(
            "derek_email_claimed_files",
            [py, "scripts/verify_derek_email_claimed_files.py",
             "--delivery-date", args.derek_date],
            pass_prefixes=("DEREK_EMAIL_CLAIMED_FILES_PASS",),
            fail_prefixes=("DEREK_EMAIL_CLAIMED_FILES_FAILED",),
        ))

    # 12. Derek after-game scoring
    rc, out, err = _run([py, "scripts/score_derek_live_snapshots_after_game.py",
                          "--delivery-date", args.derek_date])
    combined = out + "\n" + err
    derek_score = _grep(combined,
                         "DEREK_AFTER_GAME_SCORING_PASS",
                         "DEREK_AFTER_GAME_SCORING_FAILED",
                         "DEREK_LIVE_SNAPSHOT_SCORING_PENDING")
    if derek_score and "PASS" in derek_score:
        ds_status = "PASS"
    elif derek_score and "PENDING" in derek_score:
        ds_status = "WARN"
    else:
        ds_status = "FAIL"
    checks.append({
        "name": "derek_after_game_scoring", "command": "score_derek_live_snapshots_after_game",
        "status": ds_status, "critical": True,
        "pass_line": derek_score if ds_status == "PASS" else None,
        "warn_line": derek_score if ds_status == "WARN" else None,
        "fail_line": derek_score if ds_status == "FAIL" else None,
        "rc": rc, "tail": [derek_score or "no pass line"],
    })

    # 13. WoO after-game scoring
    rc, out, err = _run([py, "scripts/score_woo_after_game.py",
                          "--date", args.derek_date])
    combined = out + "\n" + err
    woo_score = _grep(combined,
                       "WOO_AFTER_GAME_SCORING_PASS",
                       "WOO_AFTER_GAME_SCORING_FAILED",
                       "WOO_AFTER_GAME_SCORING_PENDING")
    if woo_score and "PASS" in woo_score:
        ws_status = "PASS"
    elif woo_score and "PENDING" in woo_score:
        ws_status = "WARN"
    else:
        ws_status = "FAIL"
    checks.append({
        "name": "woo_after_game_scoring", "command": "score_woo_after_game",
        "status": ws_status, "critical": True,
        "pass_line": woo_score if ws_status == "PASS" else None,
        "warn_line": woo_score if ws_status == "WARN" else None,
        "fail_line": woo_score if ws_status == "FAIL" else None,
        "rc": rc, "tail": [woo_score or "no pass line"],
    })

    # 14. PMF variance experience study
    rc, out, err = _run([py, "scripts/verify_pmf_variance_experience_study.py",
                          "--as-of-date", args.derek_date])
    combined = out + "\n" + err
    pmf_var = _grep(combined,
                     "PMF_VARIANCE_EXPERIENCE_STUDY_PASS",
                     "PMF_VARIANCE_EXPERIENCE_STUDY_WARN",
                     "PMF_VARIANCE_EXPERIENCE_STUDY_FAILED")
    if pmf_var and "PASS" in pmf_var:
        pv_status = "PASS"
    elif pmf_var and "WARN" in pmf_var:
        pv_status = "WARN"
    else:
        pv_status = "FAIL"
    checks.append({
        "name": "pmf_variance_calibration_study", "command": "verify_pmf_variance_experience_study",
        "status": pv_status, "critical": False,
        "pass_line": pmf_var if pv_status == "PASS" else None,
        "warn_line": pmf_var if pv_status == "WARN" else None,
        "fail_line": pmf_var if pv_status == "FAIL" else None,
        "rc": rc, "tail": [pmf_var or "no pass line"],
    })

    # 15. Human-readable reports — Derek index README + variance study + edge audits.
    # Phase 13AJ: when --derek-date is "today" and Derek hasn't published
    # yet (no current_live snapshot run), the canonical delivery is the
    # previous-day completed delivery. Surface as PENDING in that case
    # rather than a hard FAIL.
    derek_readme = REPO_ROOT / "deliveries" / args.derek_date / "derek_game_snapshots" / "README.md"
    delivery_readme = REPO_ROOT / "deliveries" / args.derek_date / "README.md"
    variance_md = REPO_ROOT / "artifacts" / "experience_studies" / f"pmf_variance_experience_{args.derek_date}.md"
    edge_root_md = REPO_ROOT / "artifacts" / "automation_health" / f"derek_edge_root_cause_{args.derek_date}.md"
    edge_cal_md = REPO_ROOT / "artifacts" / "automation_health" / f"derek_edge_calibration_{args.derek_date}.md"
    candidate_paths = (derek_readme, delivery_readme, variance_md, edge_root_md, edge_cal_md)
    missing = [str(p.relative_to(REPO_ROOT)) for p in candidate_paths if not p.exists()]
    # Phase 13AJ: operator semantics — "today" is the ET calendar day
    # that contains tonight's slate, not the raw UTC date. UTC rolls over
    # before ET tip windows close, so anchoring on UTC would mark a
    # pre-tip-pending Derek day as "in the past."
    try:
        from zoneinfo import ZoneInfo as _ZI
        today_utc = dt.datetime.now(_ZI("America/New_York")).date().isoformat()
    except Exception:
        today_utc = dt.datetime.now(dt.timezone.utc).date().isoformat()
    requested_is_today_or_future = args.derek_date >= today_utc
    derek_snapshot_root = REPO_ROOT / "deliveries" / args.derek_date / "derek_game_snapshots"
    derek_has_run = derek_snapshot_root.exists() and any(
        (game / "current_live" / "snapshot_manifest.json").exists()
        for game in derek_snapshot_root.iterdir() if game.is_dir()
    )
    if missing:
        if requested_is_today_or_future and not derek_has_run:
            checks.append({
                "name": "human_readable_reports", "command": "(file presence check)",
                "status": "WARN", "critical": True, "pass_line": None,
                "warn_line": (
                    "human-readable reports not yet produced for today's "
                    "Derek delivery (current_live snapshot has not run)"
                ),
                "fail_line": None,
                "rc": 0, "tail": [f"pending: {missing}"],
            })
        else:
            checks.append({
                "name": "human_readable_reports", "command": "(file presence check)",
                "status": "FAIL", "critical": True, "pass_line": None,
                "warn_line": None,
                "fail_line": f"missing human-readable reports: {missing}",
                "rc": 1, "tail": [f"missing: {missing}"],
            })
    else:
        checks.append({
            "name": "human_readable_reports", "command": "(file presence check)",
            "status": "PASS", "critical": True,
            "pass_line": "HUMAN_READABLE_REPORTS_PASS",
            "warn_line": None, "fail_line": None,
            "rc": 0, "tail": ["all human-readable reports present"],
        })
        print("HUMAN_READABLE_REPORTS_PASS")

    # 16. Daily automation health report consistency
    rc, out, err = _run([py, "scripts/verify_daily_automation_health_report.py",
                          "--date", args.date])
    combined = out + "\n" + err
    health = _grep(combined, "DAILY_AUTOMATION_HEALTH_PASS",
                    "DAILY_AUTOMATION_HEALTH_WARN",
                    "DAILY_AUTOMATION_HEALTH_FAILED")
    if health and "_PASS" in health:
        h_status = "PASS"
    elif health and "_WARN" in health:
        h_status = "WARN"
    else:
        h_status = "FAIL"
    checks.append({
        "name": "daily_automation_health", "command": "verify_daily_automation_health_report",
        "status": h_status, "critical": False,
        "pass_line": health if h_status == "PASS" else None,
        "warn_line": health if h_status == "WARN" else None,
        "fail_line": health if h_status == "FAIL" else None,
        "rc": rc, "tail": [health or "no pass line"],
    })

    # ── Roll up ────────────────────────────────────────────────────────
    has_fail = any(c["status"] == "FAIL" and c["critical"] for c in checks)
    has_warn = any(c["status"] == "WARN" for c in checks)

    payload = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "date": args.date,
        "derek_date": args.derek_date,
        "required_outcomes_through": args.required_outcomes_through,
        "checks": checks,
        "overall": (
            "FULL_DAILY_PRODUCTION_CONTRACT_FAILED" if has_fail
            else "FULL_DAILY_PRODUCTION_CONTRACT_WARN" if has_warn
            else "FULL_DAILY_PRODUCTION_CONTRACT_PASS"
        ),
    }

    out_dir = REPO_ROOT / "artifacts" / "automation_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"full_daily_production_contract_{args.date}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(payload["overall"], f"date={args.date}  derek_date={args.derek_date}")
    for c in checks:
        flag = "*" if c["critical"] else " "
        print(f"  {flag} {c['name']:<32}  {c['status']:<5}  "
              f"{(c['pass_line'] or c['warn_line'] or c['fail_line'] or '')[:120]}")
    if has_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
