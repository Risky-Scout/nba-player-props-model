#!/usr/bin/env python3
"""Phase 13AI — WoO snapshot-schedule state machine.

For each (game, snapshot_type) pair on the requested date, classify into
one of:

  EXISTS                 — snapshot file present and parses
  PENDING_NOT_DUE        — target_time_utc is still in the future
                            (with a tolerance window); WARN/OK
  DUE_WINDOW_MISSING     — within +/- tolerance of target_time and the
                            file is missing; FAIL (publisher should
                            have run)
  MISSED_POST_TIP        — game has tipped, file is missing, and no
                            documented missed-marker exists; FAIL
  MISSED_DOCUMENTED      — file is missing but the matching folder
                            carries a missed_snapshot_manifest.json
                            (documented setup-day historical miss);
                            WARN

Snapshot-type target offsets relative to commence_time:
  morning      → target_time = commence_time - 8h  (a deterministic
                 anchor; not a hard schedule, just used for staleness
                 of the slate-level morning snapshot)
  t_minus_25   → target_time = commence_time - 25 min
  close_lock   → target_time = commence_time - 5 min

Tolerance: 5 min before target through 30 min after target = the
"due window".

Output:
  artifacts/automation_health/woo_snapshot_state_<date>.json
  artifacts/automation_health/woo_snapshot_state_<date>.md

Pass:  WOO_SNAPSHOT_STATE_MACHINE_PASS
Fail:  WOO_SNAPSHOT_STATE_MACHINE_FAILED  with exact game/snapshot reasons
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = REPO_ROOT / "predictions"
WOO_SNAP_ROOT = PRED_DIR / "woo_snapshots"
ART_DIR = REPO_ROOT / "artifacts" / "automation_health"

SNAPSHOT_OFFSETS_MIN = {
    "morning": -8 * 60,        # 8 hours before tip
    "t_minus_25": -25,
    "close_lock": -5,
}
TOLERANCE_BEFORE_MIN = 5
TOLERANCE_AFTER_MIN = 30


def _games_for_date(date: str) -> pd.DataFrame:
    """Pull (game_id, game, commence_time) for each game on the date.

    Phase 13AI: the predictions parquet does not always carry a
    commence_time column (older slates omit it), so fall back to the
    canonical ``artifacts/live_schedule/<date>/game_start_times.json``
    which records ``resolved_game_start_time_utc`` per game_id.
    """
    parquet = PRED_DIR / f"all_props_{date}.parquet"
    if not parquet.exists():
        return pd.DataFrame()
    df = pd.read_parquet(parquet)
    cols = ["game_id", "game"]
    optional = ("game_start_time", "commence_time")
    keep = [c for c in cols + list(optional) if c in df.columns]
    games = df[keep].drop_duplicates(subset=["game_id"]).reset_index(drop=True)

    # Schedule fallback.
    schedule_path = (REPO_ROOT / "artifacts" / "live_schedule" / date
                     / "game_start_times.json")
    if schedule_path.exists():
        try:
            sched = json.loads(schedule_path.read_text(encoding="utf-8"))
            tip_lookup = {
                str(r.get("game_id")): r.get("resolved_game_start_time_utc")
                for r in (sched.get("records") or [])
                if r.get("resolved_game_start_time_utc")
            }
            if tip_lookup:
                games["commence_time"] = games.get("commence_time")
                if "game_start_time" not in games.columns:
                    games["game_start_time"] = None
                for i, row in games.iterrows():
                    gid = str(int(row["game_id"]))
                    if (not row.get("game_start_time") and
                            not row.get("commence_time")):
                        games.at[i, "game_start_time"] = tip_lookup.get(gid)
        except Exception:
            pass

    return games


def _parse_ts(value) -> dt.datetime | None:
    if value is None or pd.isna(value):
        return None
    try:
        ts = pd.Timestamp(value)
    except Exception:
        return None
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.to_pydatetime()


def _snapshot_path(date: str, snap_type: str, scope: str) -> Path:
    return WOO_SNAP_ROOT / date / snap_type / scope / "nba_props_today.json"


def _missed_marker(date: str, snap_type: str, scope: str) -> Path:
    return WOO_SNAP_ROOT / date / snap_type / scope / "missed_snapshot_manifest.json"


def _classify(now_utc: dt.datetime, commence_time: dt.datetime | None,
                snap_type: str, file_present: bool, missed_marker: bool) -> tuple[str, str]:
    if file_present:
        return "EXISTS", "snapshot file present"
    if missed_marker:
        return "MISSED_DOCUMENTED", "documented historical miss"
    offset = SNAPSHOT_OFFSETS_MIN.get(snap_type)
    if offset is None or commence_time is None:
        return "PENDING_NOT_DUE", "no commence_time available — cannot classify"
    target = commence_time + dt.timedelta(minutes=offset)
    due_start = target - dt.timedelta(minutes=TOLERANCE_BEFORE_MIN)
    due_end = target + dt.timedelta(minutes=TOLERANCE_AFTER_MIN)
    tipped = now_utc >= commence_time
    if now_utc < due_start:
        return "PENDING_NOT_DUE", (
            f"target={target.strftime('%Y-%m-%dT%H:%M:%SZ')} "
            f"now={now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
    if due_start <= now_utc <= due_end:
        return "DUE_WINDOW_MISSING", (
            f"target={target.strftime('%Y-%m-%dT%H:%M:%SZ')} "
            f"in due window — publisher must produce file"
        )
    if tipped:
        return "MISSED_POST_TIP", (
            f"commence_time={commence_time.strftime('%Y-%m-%dT%H:%M:%SZ')} "
            "has passed and no file or missed marker present"
        )
    return "DUE_WINDOW_MISSING", (
        f"target={target.strftime('%Y-%m-%dT%H:%M:%SZ')} "
        f"now={now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')} after window"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--snapshot-types", default="morning,t_minus_25,close_lock")
    args = ap.parse_args(argv)
    date = args.date
    types = [s.strip() for s in args.snapshot_types.split(",") if s.strip()]
    now_utc = dt.datetime.now(dt.timezone.utc)

    games = _games_for_date(date)
    if games.empty:
        print(f"WOO_SNAPSHOT_STATE_MACHINE_FAILED  date={date}  "
              f"reason=no_predictions_parquet_for_date", file=sys.stderr)
        return 1

    states: list[dict] = []
    fails: list[str] = []
    for snap_type in types:
        if snap_type == "morning":
            scopes = [("slate", None)]  # slate scope; commence not used directly
        else:
            scopes = []
            for _, g in games.iterrows():
                gid = str(int(g["game_id"]))
                ct = _parse_ts(g.get("game_start_time") or g.get("commence_time"))
                scopes.append((gid, ct))
        for scope, commence in scopes:
            snap_path = _snapshot_path(date, snap_type, scope)
            marker = _missed_marker(date, snap_type, scope)
            file_present = snap_path.exists()
            marker_present = marker.exists()
            # Morning uses a date-level "due" anchor — treat as EXISTS / FAIL
            # only based on file presence.
            if snap_type == "morning":
                state = "EXISTS" if file_present else "DUE_WINDOW_MISSING"
                detail = ("morning slate snapshot present"
                          if file_present
                          else "morning slate snapshot file is missing — "
                               "must be published by daily_predictions workflow")
            else:
                state, detail = _classify(now_utc, commence, snap_type,
                                            file_present, marker_present)
            states.append({
                "snapshot_type": snap_type,
                "scope": scope,
                "commence_time_utc": (commence.strftime("%Y-%m-%dT%H:%M:%SZ")
                                       if commence else None),
                "file_path": str(snap_path.relative_to(REPO_ROOT)),
                "file_present": file_present,
                "missed_marker_present": marker_present,
                "state": state,
                "detail": detail,
            })
            if state in {"DUE_WINDOW_MISSING", "MISSED_POST_TIP"}:
                fails.append(
                    f"{snap_type}/{scope}: state={state} ({detail})"
                )

    payload = {
        "schema_version": "1.0",
        "date": date,
        "generated_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "snapshot_types_checked": types,
        "states": states,
        "fail_count": len(fails),
        "outcome": "fail" if fails else "pass",
    }
    ART_DIR.mkdir(parents=True, exist_ok=True)
    json_path = ART_DIR / f"woo_snapshot_state_{date}.json"
    md_path = ART_DIR / f"woo_snapshot_state_{date}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        f"# WoO snapshot schedule state — {date}",
        "",
        f"_Generated {payload['generated_at_utc']}._",
        "",
        f"- snapshot types checked: `{types}`",
        f"- outcome: **{payload['outcome']}**",
        f"- fail count: {payload['fail_count']}",
        "",
        "| snapshot_type | scope | commence_time | state | detail |",
        "|---|---|---|---|---|",
    ]
    for s in states:
        md_lines.append(
            f"| {s['snapshot_type']} | `{s['scope']}` | "
            f"`{s.get('commence_time_utc') or '—'}` | "
            f"**{s['state']}** | {s['detail']} |"
        )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if fails:
        print(f"WOO_SNAPSHOT_STATE_MACHINE_FAILED  date={date}  "
              f"failures={len(fails)}", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"WOO_SNAPSHOT_STATE_MACHINE_PASS  date={date}  "
          f"states_checked={len(states)}  "
          f"json={json_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
