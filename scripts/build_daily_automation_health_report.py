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
    """Same-day training section.

    Phase 13AG: status is governed by the SAME-DAY artifacts only —
    artifacts/{nightly_training,model_daily_reports,training_readiness}/
    <date>/. A previous-day successful training run does NOT upgrade
    today's status. The previous-day artifacts are surfaced as
    ``most_recent_completed_training`` facts for visibility, never as
    primary status.

    The earlier 13AF behavior (preferring previous-day-ET artifacts)
    produced a same-day/previous-day path mismatch: 2026-05-04 health
    said PASS while pointing at the 2026-05-03 daily report, despite
    the same-day 2026-05-04 daily report explicitly saying
    HALTED_PENDING_UPSTREAM_DATA. That is now caught by the verifier.
    """
    same_run_manifest = REPO_ROOT / "artifacts" / "nightly_training" / date / "run_manifest.json"
    same_daily_md = REPO_ROOT / "artifacts" / "model_daily_reports" / date / "daily_model_training_report.md"
    same_daily_json = REPO_ROOT / "artifacts" / "model_daily_reports" / date / "daily_model_training_report.json"
    same_readiness = REPO_ROOT / "artifacts" / "training_readiness" / date / "readiness_report.json"

    rm = _read_json(same_run_manifest)
    daily_payload = _read_json(same_daily_json)
    pointer = _read_json(REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json")

    out: dict = {
        "section": "nightly_training_recalibration",
        "training_cutoff_date": date,
        "run_manifest_path": str(same_run_manifest.relative_to(REPO_ROOT)),
        "daily_report_md_path": str(same_daily_md.relative_to(REPO_ROOT)),
        "daily_report_json_path": str(same_daily_json.relative_to(REPO_ROOT)),
        "readiness_report_path": str(same_readiness.relative_to(REPO_ROOT)),
        "same_day_artifacts_present": bool(rm or daily_payload),
        "champion_model_id": (pointer or {}).get("champion_model_id"),
        "trained_through_date": (pointer or {}).get("trained_through_date"),
        "calibrated_through_date": (pointer or {}).get("calibrated_through_date"),
        "feature_set_id": (pointer or {}).get("feature_set_id"),
        "halted_reason": None,
        "halted_workflow_run_url": None,
        "same_day_report_status": (daily_payload or {}).get("status"),
        "root_cause": None,
        "status": "PENDING",
    }

    # Surface most-recent-completed training as supplementary facts. This is
    # the previous-day-ET training that may have succeeded earlier; it does
    # NOT govern today's status. The top-level `status` field is driven by
    # SAME-DAY artifacts only.
    most_recent: dict | None = None
    challengers_root = REPO_ROOT / "artifacts" / "models" / "challengers"
    if challengers_root.exists():
        # Look at challenger directories that have a non-dry-run train_manifest.
        best: tuple[str, dict] | None = None
        for child in sorted(challengers_root.iterdir(), reverse=True):
            if not child.is_dir():
                continue
            name = child.name
            # Skip prior-named historical dirs and per-flavor subdirs (e.g.
            # _direct_lineup_contextual). Prefer the canonical YYYY-MM-DD form.
            if not (len(name) == 10 and name[4] == "-" and name[7] == "-"):
                continue
            # Don't surface today's same-day dir as "most recent completed."
            if name >= date:
                continue
            tm_path = child / "train_manifest.json"
            tm = _read_json(tm_path)
            if not tm or tm.get("dry_run") is not False or tm.get("status") not in {"ok", None}:
                continue
            best = (name, tm)
            break
        if best is not None:
            mr_date, mr_tm = best
            mr_run_manifest = _read_json(REPO_ROOT / "artifacts" / "nightly_training" / mr_date / "run_manifest.json") or {}
            mr_daily = _read_json(REPO_ROOT / "artifacts" / "model_daily_reports" / mr_date / "daily_model_training_report.json") or {}
            mr_promotion = _read_json(REPO_ROOT / "artifacts" / "models" / "challengers" / mr_date / "promotion_decision.json") or {}
            most_recent = {
                "training_cutoff_date": mr_date,
                "final_status": mr_run_manifest.get("final_status"),
                "halted_reason": mr_run_manifest.get("halted_reason"),
                "challenger_artifact_dir": f"artifacts/models/challengers/{mr_date}",
                "daily_report_md_path": f"artifacts/model_daily_reports/{mr_date}/daily_model_training_report.md",
                "promoted": mr_promotion.get("promoted"),
                "promotion_reason": mr_promotion.get("reason"),
                "label": (
                    "previous champion state — not today's training run; "
                    "do not infer same-day status from this"
                ),
            }
    out["most_recent_completed_training"] = most_recent

    if not (rm or daily_payload):
        out["status"] = "FAIL"
        out["root_cause"] = (
            f"No run_manifest.json or daily_model_training_report.json for "
            f"same-day {date} under artifacts/nightly_training/{date}/ or "
            f"artifacts/model_daily_reports/{date}/. Nightly workflow either "
            "never ran or did not upload artifacts."
        )
        return out

    halted = (rm or {}).get("halted_reason") or (daily_payload or {}).get("halted_reason")
    out["halted_reason"] = halted
    if (rm or {}).get("halted_workflow_run"):
        out["halted_workflow_run_url"] = rm["halted_workflow_run"].get("url")
    elif (daily_payload or {}).get("halted_workflow_run"):
        out["halted_workflow_run_url"] = daily_payload["halted_workflow_run"].get("url")

    same_day_report_status = (daily_payload or {}).get("status")
    final_status = (rm or {}).get("final_status")

    # Same-day daily report explicitly halted → mirror the halt. Never PASS.
    if same_day_report_status == "halted_pending_upstream_data" or \
       final_status == "halted_pending_upstream_data" or \
       halted == "previous_day_data_not_ready":
        out["status"] = "HALTED_PENDING_UPSTREAM_DATA"
        out["root_cause"] = (
            (daily_payload or {}).get("remediation")
            or "Strict resolver halted: previous-day-ET data not ready in "
               "data/player_game_stats.parquet. Correct safe behavior. "
               "Training will resume automatically when BDL backfills "
               "settled stats."
        )
        return out

    if final_status == "ok":
        out["status"] = "PASS"
        return out

    if halted in {"training_inputs_missing", "training_inputs_prepare_failed",
                  "readiness_failed", "training_failed", "calibration_failed"}:
        out["status"] = "FAIL"
        out["root_cause"] = (
            f"halted_reason={halted}. See run_manifest.json + the failed "
            "GitHub Actions run for the full error log."
        )
        return out

    # Same-day artifacts exist but final_status is unset/unknown — surface
    # honestly rather than silently passing.
    out["status"] = "SKIPPED_WITH_REASON"
    out["root_cause"] = (
        (daily_payload or {}).get("remediation")
        or f"final_status={final_status!r} same_day_report_status="
           f"{same_day_report_status!r} — same-day training did not "
           "complete; manual review required"
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
    if any(s == "WARN" for s in statuses.values()):
        return "OVERALL_WARN", "one or more sections in WARN"
    if any(s == "PENDING" for s in statuses.values()):
        # Pending after_game or training-skipped-with-reason are acceptable.
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
        ("training_cutoff_date", "training_cutoff_date"),
        ("same_day_artifacts_present", "same_day_artifacts_present"),
        ("same_day_report_status", "same_day_report_status"),
        ("halted_reason", "halted_reason"),
        ("halted_workflow_run_url", "halted_workflow_run_url"),
        ("champion_model_id", "champion_model_id"),
        ("trained_through_date", "trained_through_date"),
        ("calibrated_through_date", "calibrated_through_date"),
        ("daily_report_md_path", "daily_report_md_path"),
        ("readiness_report_path", "readiness_report_path"),
    ])
    mr = sections["training"].get("most_recent_completed_training")
    if mr:
        lines.append("**Most-recent-completed training (supplementary, not "
                     "today's status):**")
        lines.append("")
        for k, v in mr.items():
            lines.append(f"- `{k}`: `{v}`")
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
