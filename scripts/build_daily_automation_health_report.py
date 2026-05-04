#!/usr/bin/env python3
"""Phase 13AD — single-page daily automation health report.

Aggregates state from training, predictions, Derek snapshots, Wizard of
Odds, and after-game scoring into one JSON + markdown so the operator
can audit the entire daily chain at a glance.

Inputs:
  --date YYYY-MM-DD

Outputs:
  artifacts/automation_health/daily_automation_health_<date>.json
  artifacts/automation_health/daily_automation_health_<date>.md

Sections:
  1. Nightly training / recalibration
  2. Daily prediction generation
  3. Derek snapshots
  4. Wizard of Odds
  5. After-game scoring
  6. Overall (PASS / WARN / FAIL)

Hard rules:
  - Section statuses come from the actual artifacts on disk; we do NOT
    invent green pass lines for missing data.
  - Critical-path failures (training failed without halted_reason,
    missing prediction outputs, blank WoO page, broken Derek verifier
    after snapshot windows are due) drive OVERALL_FAIL.
  - Honest skipped-with-reason states do not block OVERALL_PASS, but
    they downgrade to WARN where appropriate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ART_DIR = REPO_ROOT / "artifacts" / "automation_health"


def _run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return -1, "", str(e)


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _section_training(date: str) -> dict:
    """Training section keyed on the latest completed training cutoff.

    Phase 13AI: training is keyed on the last day with complete settled
    outcomes (= ``training_cutoff_date``), not on ``run_date``. For
    ``run_date=2026-05-04`` the ``training_cutoff_date`` is 2026-05-03
    (yesterday's settled stats). The status field reflects whether the
    cutoff training actually completed:

    - PASS: the most-recent challenger ``<cutoff>`` directory carries
      a non-dry-run train_manifest.json + calibration_manifest.json +
      validation_report.json + promotion_decision.json AND the
      cutoff <= max(player_game_stats.game_date).
    - NO_PROMOTE_PASS: same as PASS but promotion_decision says
      no-promote with a documented reason.
    - HALTED_PENDING_UPSTREAM_DATA: NO completed cutoff training exists
      AND today's same-day run halted because settled stats are stale.
    - FAIL: completed cutoff training is missing AND outcomes ARE
      already settled through the required date — i.e. the workflow
      never ran or crashed.

    A historical halted report at ``artifacts/model_daily_reports/<date>/
    daily_model_training_report.json`` written when settled stats were
    stale is reclassified as ``historical_failed_attempt`` once the
    settled outcomes catch up; it is no longer surfaced as the current
    status.
    """
    pointer = _read_json(REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json")

    # 1) Determine the required training cutoff for this run_date.
    #    Default = yesterday in UTC (which is approximately previous-day-ET).
    try:
        cutoff = (dt.date.fromisoformat(date) - dt.timedelta(days=1)).isoformat()
    except Exception:
        cutoff = date

    # 2) Determine the latest completed challenger directory at or before
    #    cutoff. The "completed" predicate requires a non-dry-run
    #    train_manifest.json with status=ok and calibration + validation +
    #    promotion artifacts present.
    challengers_root = REPO_ROOT / "artifacts" / "models" / "challengers"
    completed_cutoff: str | None = None
    completed_tm: dict = {}
    if challengers_root.exists():
        for child in sorted(challengers_root.iterdir(), reverse=True):
            if not child.is_dir():
                continue
            name = child.name
            if not (len(name) == 10 and name[4] == "-" and name[7] == "-"):
                continue
            if name > cutoff:
                continue
            tm_path = child / "train_manifest.json"
            tm = _read_json(tm_path)
            if not tm or tm.get("dry_run") is not False or tm.get("status") not in {"ok", None}:
                continue
            calib = child / "calibration_manifest.json"
            valid = child / "validation_report.json"
            promo = child / "promotion_decision.json"
            if not (calib.exists() and valid.exists() and promo.exists()):
                continue
            completed_cutoff = name
            completed_tm = tm
            break

    # 3) Same-run-day halted artifacts (the 13AD honest-pending writers).
    same_run_manifest = REPO_ROOT / "artifacts" / "nightly_training" / date / "run_manifest.json"
    same_daily_md = REPO_ROOT / "artifacts" / "model_daily_reports" / date / "daily_model_training_report.md"
    same_daily_json = REPO_ROOT / "artifacts" / "model_daily_reports" / date / "daily_model_training_report.json"
    same_readiness = REPO_ROOT / "artifacts" / "training_readiness" / date / "readiness_report.json"
    same_rm = _read_json(same_run_manifest) or {}
    same_daily = _read_json(same_daily_json) or {}
    same_halted = (same_rm.get("halted_reason")
                    or same_daily.get("halted_reason"))
    same_halted_status = same_daily.get("status")

    # 4) Required-outcomes-through is what the cutoff says we needed.
    required_outcomes_through = cutoff

    # 5) Determine settled-outcome max date for context.
    settled_max = None
    stats_path = REPO_ROOT / "data" / "player_game_stats.parquet"
    if stats_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(stats_path, columns=["game_date"])
            settled_max = str(pd.to_datetime(df["game_date"]).dt.date.max())
        except Exception:
            settled_max = None

    # Pick the canonical paths for the section. When a completed cutoff
    # training exists, point at THAT artifact set (clearly labeled by
    # training_cutoff_date). When it doesn't, point at the same-day halted
    # artifacts so the operator audit surface still has somewhere to read.
    primary_cutoff = completed_cutoff or cutoff
    pri_run_manifest = REPO_ROOT / "artifacts" / "nightly_training" / primary_cutoff / "run_manifest.json"
    pri_daily_md = REPO_ROOT / "artifacts" / "model_daily_reports" / primary_cutoff / "daily_model_training_report.md"
    pri_daily_json = REPO_ROOT / "artifacts" / "model_daily_reports" / primary_cutoff / "daily_model_training_report.json"
    pri_readiness = REPO_ROOT / "artifacts" / "training_readiness" / primary_cutoff / "readiness_report.json"
    pri_rm = _read_json(pri_run_manifest) or same_rm
    pri_daily = _read_json(pri_daily_json) or same_daily
    promotion = _read_json(REPO_ROOT / "artifacts" / "models" / "challengers" / primary_cutoff / "promotion_decision.json") or {}

    out: dict = {
        "section": "nightly_training_recalibration",
        "run_date": date,
        "prediction_date": date,
        "training_cutoff_date": primary_cutoff,
        "required_outcomes_through": required_outcomes_through,
        "settled_outcomes_max_date": settled_max,
        "training_cutoff_satisfied_by_settled_outcomes": bool(
            settled_max and settled_max >= required_outcomes_through
        ),
        "completed_cutoff_training_dir": (
            f"artifacts/models/challengers/{completed_cutoff}" if completed_cutoff else None
        ),
        "run_manifest_path": str(pri_run_manifest.relative_to(REPO_ROOT)),
        "daily_report_md_path": str(pri_daily_md.relative_to(REPO_ROOT)),
        "daily_report_json_path": str(pri_daily_json.relative_to(REPO_ROOT)),
        "readiness_report_path": str(pri_readiness.relative_to(REPO_ROOT)),
        "champion_model_id": (pointer or {}).get("champion_model_id"),
        "trained_through_date": (pointer or {}).get("trained_through_date"),
        "calibrated_through_date": (pointer or {}).get("calibrated_through_date"),
        "feature_set_id": (pointer or {}).get("feature_set_id"),
        "promoted": promotion.get("promoted"),
        "promotion_reason": promotion.get("reason"),
        "halted_reason": pri_rm.get("halted_reason"),
        "halted_workflow_run_url": (
            (pri_rm.get("halted_workflow_run") or {}).get("url")
            or (pri_daily.get("halted_workflow_run") or {}).get("url")
        ),
        "same_day_run_status": same_daily.get("status"),
        "same_day_run_classified_as": (
            "historical_failed_attempt"
            if (same_halted_status == "halted_pending_upstream_data" and completed_cutoff)
            else None
        ),
        "note": (
            "Training artifacts are keyed by latest settled outcome date "
            "(training_cutoff_date), not by slate / run date. Same-day "
            "outcomes (e.g. tonight's games) may still be pending for "
            "postgame scoring; that does not affect today's training "
            "status."
        ),
        "root_cause": None,
        "status": "PENDING",
    }

    # ── Status decision ───
    if completed_cutoff:
        # Real training has completed for the required cutoff.
        promoted = promotion.get("promoted")
        promo_reason = promotion.get("reason")
        if promoted is True:
            out["status"] = "PASS"
        elif promoted is False or (promoted is None and promo_reason):
            out["status"] = "NO_PROMOTE_PASS"
            out["root_cause"] = (
                f"training completed for cutoff={completed_cutoff} "
                f"but promotion withheld: {promo_reason}. champion "
                "pointer unchanged."
            )
        else:
            out["status"] = "PASS"
        return out

    # No completed cutoff training. Decide between honest skipped vs FAIL
    # based on whether outcomes are already settled (=> the workflow
    # SHOULD have run successfully and didn't => FAIL) or are still
    # legitimately stale (=> HALTED_PENDING_UPSTREAM_DATA).
    if (settled_max is None or settled_max < required_outcomes_through):
        out["status"] = "HALTED_PENDING_UPSTREAM_DATA"
        out["root_cause"] = (
            f"training_cutoff_date={required_outcomes_through} requires "
            f"settled outcomes through that date; player_game_stats.parquet "
            f"max_game_date={settled_max!r} is still behind. Strict "
            "resolver correctly halted; training will resume automatically "
            "once BDL backfill catches up."
        )
        return out

    out["status"] = "FAIL"
    out["root_cause"] = (
        f"settled outcomes are present through {settled_max!r} (>= "
        f"required {required_outcomes_through!r}) but no completed "
        f"training run exists at artifacts/models/challengers/"
        f"{required_outcomes_through}/. Workflow should have succeeded "
        "and did not — investigate the most recent CI run."
    )
    return out


def _section_predictions(date: str) -> dict:
    pred_dir = REPO_ROOT / "predictions"
    parquet = pred_dir / f"all_props_{date}.parquet"
    singles = pred_dir / f"singles_{date}.json"
    pmf_display = pred_dir / f"pmf_display_{date}.json"
    today = pred_dir / "nba_props_today.json"

    out: dict = {
        "section": "daily_prediction_generation",
        "all_props_path": str(parquet.relative_to(REPO_ROOT)),
        "singles_path": str(singles.relative_to(REPO_ROOT)),
        "pmf_display_path": str(pmf_display.relative_to(REPO_ROOT)),
        "nba_props_today_path": str(today.relative_to(REPO_ROOT)),
        "all_props_rows": None,
        "all_props_games": None,
        "singles_count": None,
        "pmf_display_count": None,
        "today_count": None,
        "today_date": None,
        "no_data_reason": None,
        "verifier_pass_line": None,
        "status": "PENDING",
    }

    rc, stdout, stderr = _run(
        [sys.executable, "scripts/verify_daily_prediction_outputs.py", "--date", date]
    )
    pass_line = next(
        (line for line in (stdout + stderr).splitlines()
         if line.startswith("DAILY_PREDICTION_OUTPUTS_")),
        None,
    )
    out["verifier_pass_line"] = pass_line

    sj = _read_json(singles)
    pj = _read_json(pmf_display)
    tj = _read_json(today)

    try:
        import pandas as pd
        if parquet.exists():
            df = pd.read_parquet(parquet)
            out["all_props_rows"] = int(len(df))
            out["all_props_games"] = int(df["game_id"].nunique()) if "game_id" in df.columns else 0
    except Exception:
        pass

    if sj is not None:
        out["singles_count"] = len(sj.get("picks", sj.get("singles", [])))
    if pj is not None:
        out["pmf_display_count"] = len(pj.get("props", []))
    if tj is not None:
        out["today_count"] = int(tj.get("count", len(tj.get("props", []))))
        out["today_date"] = tj.get("date")
        out["no_data_reason"] = tj.get("reason")

    if rc == 0 and pass_line and pass_line.startswith("DAILY_PREDICTION_OUTPUTS_PASS"):
        out["status"] = "PASS"
    else:
        out["status"] = "FAIL"
        out["root_cause"] = (
            f"verify_daily_prediction_outputs failed: {pass_line or stderr.strip()[-300:]}"
        )

    return out


def _section_derek(date: str) -> dict:
    out: dict = {
        "section": "derek_snapshots",
        "requested_date": date,
        "delivery_date": date,
        "latest_verified_date": None,
        "current_live_count": 0,
        "t_minus_25_missed": 0,
        "t_minus_25_present": 0,
        "close_lock_missed": 0,
        "close_lock_present": 0,
        "verifier_pass_lines": {},
        "status": "PENDING",
    }
    base = REPO_ROOT / "deliveries" / date / "derek_game_snapshots"
    if not base.exists():
        # Fall back to the most-recent delivery date that has a Derek
        # snapshot folder. The daily Derek workflow runs throughout the
        # day; on early-morning runs the date's snapshots may not exist
        # yet, but the verifier should still report on the last one.
        deliveries = REPO_ROOT / "deliveries"
        candidates = sorted(
            (p.parent.name for p in deliveries.glob("*/derek_game_snapshots")),
            reverse=True,
        )
        if candidates:
            out["delivery_date"] = candidates[0]
            out["latest_verified_date"] = candidates[0]
            base = deliveries / candidates[0] / "derek_game_snapshots"
        else:
            out["status"] = "PENDING"
            out["root_cause"] = (
                f"no Derek delivery folder under deliveries/{date}/ or any "
                "earlier date — Derek workflow has not run yet"
            )
            return out
    else:
        out["latest_verified_date"] = date
    for game_dir in base.iterdir():
        if not game_dir.is_dir():
            continue
        for snap in ("current_live", "t_minus_25", "close_lock"):
            sd = game_dir / snap
            if not sd.exists():
                continue
            has_market = (sd / "market_comparison.csv").exists()
            has_missed = (sd / "missed_snapshot_manifest.json").exists()
            if snap == "current_live" and has_market:
                out["current_live_count"] += 1
            elif snap == "t_minus_25":
                if has_missed:
                    out["t_minus_25_missed"] += 1
                elif has_market:
                    out["t_minus_25_present"] += 1
            elif snap == "close_lock":
                if has_missed:
                    out["close_lock_missed"] += 1
                elif has_market:
                    out["close_lock_present"] += 1

    verify_date = out["delivery_date"]
    pass_lines: dict = {}
    for label, cmd in (
        ("DEREK_LIVE_SNAPSHOTS",
         [sys.executable, "scripts/verify_derek_live_snapshots.py",
          "--delivery-date", verify_date]),
        ("DEREK_PRODUCTION_LIVE_E2E",
         [sys.executable, "scripts/verify_derek_production_live_e2e.py",
          "--delivery-date", verify_date]),
        ("DEREK_OUTCOME_LEVEL_PROBABILITIES",
         [sys.executable, "scripts/verify_derek_outcome_level_probabilities.py",
          "--delivery-date", verify_date]),
    ):
        rc, stdout, stderr = _run(cmd)
        line = next(
            (l for l in (stdout + stderr).splitlines() if l.startswith(label)),
            None,
        )
        pass_lines[label] = {
            "pass_line": line,
            "exit_code": rc,
            "passed": (rc == 0 and (line or "").endswith("_PASS")
                       or (line is not None and "_PASS" in line)),
        }
    out["verifier_pass_lines"] = pass_lines
    if all(v.get("passed") for v in pass_lines.values()):
        out["status"] = "PASS"
    else:
        out["status"] = "FAIL"
        out["root_cause"] = "one or more Derek verifiers did not emit a PASS line"
    return out


def _section_woo(date: str) -> dict:
    html = REPO_ROOT / "predictions" / "nba-props.html"
    today = REPO_ROOT / "predictions" / "nba_props_today.json"
    out: dict = {
        "section": "wizard_of_odds",
        "html_path": str(html.relative_to(REPO_ROOT)),
        "data_path": str(today.relative_to(REPO_ROOT)),
        "html_size_bytes": html.stat().st_size if html.exists() else 0,
        "verifier_pass_line": None,
        "status": "PENDING",
        "blank_page_prevention": False,
    }
    rc, stdout, stderr = _run(
        [sys.executable, "scripts/verify_woo_nba_props_page.py", "--date", date]
    )
    line = next(
        (l for l in (stdout + stderr).splitlines() if l.startswith("WOO_NBA_PROPS_PAGE_")),
        None,
    )
    out["verifier_pass_line"] = line
    if html.exists():
        h = html.read_text(encoding="utf-8")
        out["blank_page_prevention"] = (
            "showState" in h and "static-banner" in h and "nba_props_today.json" in h
        )
    if rc == 0 and line and line.startswith("WOO_NBA_PROPS_PAGE_PASS"):
        out["status"] = "PASS"
    else:
        out["status"] = "FAIL"
        out["root_cause"] = (
            f"verify_woo_nba_props_page failed: {line or stderr.strip()[-300:]}"
        )
    return out


def _section_after_game(date: str) -> dict:
    out: dict = {
        "section": "after_game_scoring",
        "latest_settled_date": None,
        "outcomes_available": False,
        "scoring_report_path": None,
        "status": "PENDING",
    }
    # Use player_game_stats to find latest settled date.
    stats = REPO_ROOT / "data" / "player_game_stats.parquet"
    if stats.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(stats, columns=["game_date"])
            latest = str(df["game_date"].max())
            out["latest_settled_date"] = latest
            out["outcomes_available"] = latest >= date
        except Exception:
            pass

    # If after_game_scoring artifacts exist for this date, point to them.
    p = REPO_ROOT / "deliveries" / date / "after_game_scoring" / "after_game_status.json"
    if p.exists():
        out["scoring_report_path"] = str(p.relative_to(REPO_ROOT))
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            if payload.get("scored"):
                out["status"] = "PASS"
            else:
                out["status"] = "PENDING"
                out["root_cause"] = payload.get("reason") or "scored=false"
        except Exception:
            out["status"] = "WARN"
            out["root_cause"] = "after_game_status.json present but not parseable"
    else:
        if out["latest_settled_date"] and out["latest_settled_date"] < date:
            out["status"] = "PENDING"
            out["root_cause"] = (
                f"settled stats only through {out['latest_settled_date']}; "
                f"after-game scoring for {date} pending upstream backfill"
            )
        else:
            out["status"] = "PENDING"
            out["root_cause"] = "no after_game_scoring artifacts for this date yet"
    return out


def _overall(sections: dict) -> tuple[str, str]:
    statuses = {k: v.get("status") for k, v in sections.items()}
    # Critical path = predictions + derek + woo. Training and after-game can
    # honestly skip when upstream data is not ready.
    critical = ("predictions", "derek", "woo")
    if any(statuses[k] == "FAIL" for k in critical):
        bad = [k for k in critical if statuses[k] == "FAIL"]
        return "OVERALL_FAIL", f"critical path failure: {bad}"
    if statuses.get("training") == "FAIL":
        return "OVERALL_FAIL", "training failed without honest skipped-with-reason"
    pass_like = {"PASS", "NO_PROMOTE_PASS"}
    # NO_PROMOTE_PASS counts as PASS for overall classification.
    if all(s in pass_like for s in statuses.values()):
        return "OVERALL_PASS", "all critical sections pass; no warnings"
    if any(s == "WARN" for s in statuses.values()):
        return "OVERALL_WARN", "one or more sections in WARN"
    if any(s == "PENDING" for s in statuses.values()):
        return "OVERALL_WARN", "one or more sections pending honest upstream data"
    if any(s == "SKIPPED_WITH_REASON" for s in statuses.values()):
        return "OVERALL_WARN", "training skipped pending upstream data"
    if any(s == "HALTED_PENDING_UPSTREAM_DATA" for s in statuses.values()):
        return "OVERALL_WARN", (
            "training halted pending upstream data — same-day cycle did not "
            "run; no_promote remains in effect"
        )
    return "OVERALL_PASS", "all critical sections pass; no warnings"


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _markdown(payload: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Daily automation health — {payload['date']}")
    lines.append("")
    lines.append(f"_Generated {payload['generated_at_utc']}._")
    lines.append("")
    lines.append(f"## Overall: **{payload['overall']['status']}**")
    lines.append("")
    lines.append(f"- summary: {payload['overall']['summary']}")
    lines.append("")
    sections = payload["sections"]

    def _emit(title: str, sec_key: str, fields: list[tuple[str, str]]):
        s = sections[sec_key]
        lines.append(f"## {title} — `{s['status']}`")
        lines.append("")
        for label, key in fields:
            v = s.get(key)
            lines.append(f"- **{label}:** `{v}`")
        if s.get("root_cause"):
            lines.append(f"- **root_cause:** {s['root_cause']}")
        lines.append("")

    _emit("1. Nightly training / recalibration", "training", [
        ("status", "status"),
        ("run_date", "run_date"),
        ("prediction_date", "prediction_date"),
        ("training_cutoff_date", "training_cutoff_date"),
        ("required_outcomes_through", "required_outcomes_through"),
        ("settled_outcomes_max_date", "settled_outcomes_max_date"),
        ("training_cutoff_satisfied_by_settled_outcomes",
         "training_cutoff_satisfied_by_settled_outcomes"),
        ("completed_cutoff_training_dir", "completed_cutoff_training_dir"),
        ("promoted", "promoted"),
        ("promotion_reason", "promotion_reason"),
        ("halted_reason", "halted_reason"),
        ("halted_workflow_run_url", "halted_workflow_run_url"),
        ("champion_model_id", "champion_model_id"),
        ("trained_through_date", "trained_through_date"),
        ("calibrated_through_date", "calibrated_through_date"),
        ("daily_report_md_path", "daily_report_md_path"),
        ("readiness_report_path", "readiness_report_path"),
        ("same_day_run_status", "same_day_run_status"),
        ("same_day_run_classified_as", "same_day_run_classified_as"),
    ])
    note = sections["training"].get("note")
    if note:
        lines.append(f"_{note}_")
        lines.append("")

    _emit("2. Daily prediction generation", "predictions", [
        ("status", "status"),
        ("verifier_pass_line", "verifier_pass_line"),
        ("all_props_rows", "all_props_rows"),
        ("all_props_games", "all_props_games"),
        ("singles_count", "singles_count"),
        ("pmf_display_count", "pmf_display_count"),
        ("today_count", "today_count"),
        ("today_date", "today_date"),
    ])

    _emit("3. Derek snapshots", "derek", [
        ("status", "status"),
        ("delivery_date", "delivery_date"),
        ("current_live_count", "current_live_count"),
        ("t_minus_25_missed", "t_minus_25_missed"),
        ("t_minus_25_present", "t_minus_25_present"),
        ("close_lock_missed", "close_lock_missed"),
        ("close_lock_present", "close_lock_present"),
    ])
    derek_lines = sections["derek"].get("verifier_pass_lines", {})
    for label, info in derek_lines.items():
        lines.append(f"- {label}: `{info.get('pass_line')}`")
    lines.append("")

    _emit("4. Wizard of Odds", "woo", [
        ("status", "status"),
        ("verifier_pass_line", "verifier_pass_line"),
        ("html_path", "html_path"),
        ("data_path", "data_path"),
        ("html_size_bytes", "html_size_bytes"),
        ("blank_page_prevention", "blank_page_prevention"),
    ])

    _emit("5. After-game scoring", "after_game", [
        ("status", "status"),
        ("latest_settled_date", "latest_settled_date"),
        ("outcomes_available", "outcomes_available"),
        ("scoring_report_path", "scoring_report_path"),
    ])

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date

    sections = {
        "training": _section_training(date),
        "predictions": _section_predictions(date),
        "derek": _section_derek(date),
        "woo": _section_woo(date),
        "after_game": _section_after_game(date),
    }
    status, summary = _overall(sections)

    payload = {
        "schema_version": "1.0",
        "date": date,
        "generated_at_utc": _utc_iso(),
        "overall": {"status": status, "summary": summary},
        "sections": sections,
    }
    ART_DIR.mkdir(parents=True, exist_ok=True)
    json_out = ART_DIR / f"daily_automation_health_{date}.json"
    md_out = ART_DIR / f"daily_automation_health_{date}.md"
    json_out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md_out.write_text(_markdown(payload), encoding="utf-8")

    print(status, f"date={date}")
    print(f"  summary={summary}")
    print(f"  json={json_out.relative_to(REPO_ROOT)}")
    print(f"  md={md_out.relative_to(REPO_ROOT)}")
    for name, sec in sections.items():
        print(f"  {name}={sec['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
