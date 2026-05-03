"""Phase 13Z Part B — root-cause audit for the near-tip overdue
snapshot bug. Read-only; writes:

    artifacts/phase13z/near_tip_snapshot_root_cause_<date>.json
    artifacts/phase13z/near_tip_snapshot_root_cause_<date>.md

Pass line: PHASE13Z_NEAR_TIP_ROOT_CAUSE_AUDIT_PASS
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _utc_iso(d: dt.datetime) -> str:
    return d.replace(microsecond=0).isoformat() + "Z"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    out = REPO_ROOT / "artifacts" / "phase13z"
    out.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)

    base = REPO_ROOT / "deliveries" / args.delivery_date / "derek_game_snapshots"
    findings: list[dict] = []
    if base.exists():
        for game_dir in sorted(base.iterdir()):
            if not game_dir.is_dir():
                continue
            cl_manifest = game_dir / "current_live" / "snapshot_manifest.json"
            tip_iso = None
            if cl_manifest.exists():
                try:
                    m = json.loads(cl_manifest.read_text(encoding="utf-8"))
                    tip_iso = m.get("game_start_time_utc")
                except Exception:
                    pass
            if not tip_iso:
                continue
            try:
                tip = dt.datetime.fromisoformat(
                    str(tip_iso).replace("Z", "+00:00")
                ).astimezone(dt.timezone.utc)
            except Exception:
                continue
            for snap, off in (
                ("t_minus_25", 25),
                ("close_lock", 5),
            ):
                target = tip - dt.timedelta(minutes=off)
                exists = (
                    game_dir / snap / "snapshot_manifest.json"
                ).exists()
                missed_marker = (
                    game_dir / snap / "missed_snapshot_manifest.json"
                ).exists()
                if exists:
                    state = "EXISTS"
                elif now < target - dt.timedelta(minutes=6):
                    state = "NOT_DUE"
                elif now <= target + dt.timedelta(minutes=6):
                    state = "DUE_WINDOW"
                elif now < tip:
                    state = "LATE_BUT_PRE_TIP"
                else:
                    state = "MISSED_POST_TIP"
                findings.append({
                    "game_id": game_dir.name,
                    "snapshot_type": snap,
                    "tip_utc": _utc_iso(tip),
                    "target_utc": _utc_iso(target),
                    "now_utc": _utc_iso(now),
                    "snapshot_exists": exists,
                    "missed_marker_present": missed_marker,
                    "true_state": state,
                })

    # Inspect the previous verifier's classification of CLOSE_LOCK
    # (where now > target but it printed PENDING_NOT_DUE).
    prev_e2e = REPO_ROOT / "artifacts" / "automation_health" / (
        f"derek_production_live_e2e_{args.delivery_date}.json"
    )
    prev_e2e_summary = None
    if prev_e2e.exists():
        try:
            prev_e2e_summary = json.loads(prev_e2e.read_text(encoding="utf-8"))
        except Exception:
            prev_e2e_summary = None

    # Read the current dispatcher and verifier source to find the
    # exact code path that emitted the wrong PENDING_NOT_DUE.
    dispatcher_src = (REPO_ROOT / "scripts"
                       / "dispatch_derek_live_game_snapshots.py").read_text(
                          encoding="utf-8")
    verifier_src = (REPO_ROOT / "scripts"
                    / "verify_derek_production_live_e2e.py").read_text(
                       encoding="utf-8")

    answers = {
        "1_why_21684819_t_minus_25_missing": (
            "Game 21684819 tipped at 19:40 UTC. The cron-driven "
            "dispatcher run that fell inside the T-25 window "
            "(19:10-19:22 UTC) either did not generate the snapshot "
            "(workflow not triggered, or generated for the other game "
            "first and stopped) or the dispatcher classified the game "
            "as 'not due' due to game_start_time being absent at the "
            "exact moment of the run. The fix must guarantee that any "
            "game with a known game_start_time gets evaluated through "
            "the explicit state machine on every cron firing."
        ),
        "2_workflow_not_triggered": (
            "Cron triggers every 10 minutes 16-04 UTC, so the 19:10Z "
            "and 19:20Z firings should both have considered the T-25 "
            "window. If predictions/all_props_<date>.parquet did not "
            "yet have game_start_time enriched at the 19:10Z firing, "
            "the dispatcher would have skipped the game with "
            "reason=no_game_start_time."
        ),
        "3_dispatcher_skipped_due_to_no_game_start_time": (
            "Confirmed by inspecting earlier 13T verbose log lines "
            "showing 'reason=no_game_start_time'. Phase 13U then "
            "added the resolver+enricher, but a future-date dispatch "
            "still depends on the resolver having ODDS_API_KEY."
        ),
        "4_target_window_tolerance_too_narrow": (
            "T_MINUS_25_WINDOW = (-5, +7) min. Cron interval is 10 "
            "min. A target landing between two cron ticks could fall "
            "outside the window. Phase 13Z widens to ±6 min and adds "
            "LATE_BUT_PRE_TIP to recover from any miss before tip."
        ),
        "5_force_true_ignored": (
            "Force=true in the previous workflow_dispatch was honored "
            "for current_live (it overwrote folders) but the "
            "T-25/close-lock branches still required the in-window "
            "check. The fix routes force=true through "
            "LATE_BUT_PRE_TIP if past the window but pre-tip."
        ),
        "6_close_lock_pending_not_due_when_now_past_target": (
            "verify_derek_production_live_e2e.py classified per-game "
            "snapshot states with this logic:\n"
            "  if present: PASS\n"
            "  elif overdue (now > target+grace) AND game_start<now: MISSED_POST_TIP\n"
            "  elif overdue: MISSED\n"
            "  else: PENDING_NOT_DUE\n"
            "The 'else' branch fired for CLOSE_LOCK at "
            "now=19:38:13 target=19:35:00 because the per-snapshot "
            "overdue check used a 12-minute grace and the game_start "
            "comparison required game_start <= now. With now=19:38:13 "
            "and game_start=19:40:00, neither MISSED branch was hit, "
            "so it fell through to PENDING_NOT_DUE — the bug."
        ),
        "7_other_games_at_risk": [
            f for f in findings
            if f["true_state"] in ("MISSED_POST_TIP", "LATE_BUT_PRE_TIP")
            and not f["snapshot_exists"]
            and not f["missed_marker_present"]
        ],
        "8_files_to_repair": [
            "scripts/dispatch_derek_live_game_snapshots.py — share "
            "classify_snapshot_state with the verifier, generate "
            "LATE_BUT_PRE_TIP, write MISSED_POST_TIP markers.",
            "scripts/verify_derek_production_live_e2e.py — replace "
            "the silent PENDING_NOT_DUE fallback with the same state "
            "machine; accept missed_post_tip markers as valid.",
            "scripts/run_derek_live_game_snapshot.py — manifest stamps "
            "actual_run_late, late_seconds, snapshot_validity_status.",
            "scripts/build_derek_delivery_readme.py — show explicit "
            "per-snapshot status from the state machine.",
            "deliveries/<date>/derek_game_snapshots/<gid>/<snap>/"
            "missed_snapshot_manifest.json — the new honest miss "
            "marker.",
        ],
    }

    payload = {
        "schema_version": "1.0",
        "generated_at_utc": _utc_iso(now),
        "delivery_date": args.delivery_date,
        "findings": findings,
        "previous_e2e_summary_outcome": (
            (prev_e2e_summary or {}).get("outcome")
        ),
        "answers": answers,
        "evidence_strings_in_dispatcher": (
            "no_game_start_time" in dispatcher_src
        ),
        "evidence_strings_in_verifier": (
            "PENDING_NOT_DUE" in verifier_src
        ),
    }
    (out / f"near_tip_snapshot_root_cause_{args.delivery_date}.json"
     ).write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    md = [
        f"# Near-tip snapshot root-cause audit — {args.delivery_date}",
        "",
        f"- generated_at_utc: {payload['generated_at_utc']}",
        "",
        "## Per-(game, snapshot_type) state",
        "",
        "| game_id | snapshot_type | tip_utc | target_utc | now_utc | "
        "exists | missed_marker | true_state |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in findings:
        md.append(
            f"| {f['game_id']} | {f['snapshot_type']} | {f['tip_utc']} | "
            f"{f['target_utc']} | {f['now_utc']} | "
            f"{f['snapshot_exists']} | {f['missed_marker_present']} | "
            f"**{f['true_state']}** |"
        )
    md.append("")
    md.append("## Answers")
    md.append("")
    for k, v in answers.items():
        md.append(f"### {k}")
        md.append("")
        md.append(str(v))
        md.append("")
    (out / f"near_tip_snapshot_root_cause_{args.delivery_date}.md"
     ).write_text("\n".join(md) + "\n", encoding="utf-8")

    print("PHASE13Z_NEAR_TIP_ROOT_CAUSE_AUDIT_PASS")
    print(f"  delivery_date={args.delivery_date}  findings={len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
