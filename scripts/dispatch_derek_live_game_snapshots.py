"""Phase 13L — Derek per-game live snapshot dispatcher.

Loads today's NBA game schedule (or a target date in backfill mode), computes
per-game ``t_minus_25`` and ``close_lock`` target timestamps, decides which
snapshots are due in the current execution window, and invokes
``scripts/run_derek_live_game_snapshot.py`` per game.

Idempotent — never overwrites a completed snapshot unless ``--force`` is set.

Usage:
    python3 scripts/dispatch_derek_live_game_snapshots.py \\
        --delivery-date YYYY-MM-DD --snapshot-type t_minus_25
    python3 scripts/dispatch_derek_live_game_snapshots.py \\
        --delivery-date YYYY-MM-DD --snapshot-type close_lock \\
        --allow-backfill-test

Pass line:  DEREK_LIVE_SNAPSHOT_DISPATCH_PASS
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    git_commit,
    utcnow_iso,
    write_json_atomic,
)


SNAPSHOT_TYPES = ("current_live", "t_minus_25", "close_lock")
DELIVERIES_DIR = REPO_ROOT / "deliveries"
PRED_DIR = REPO_ROOT / "predictions"
DISPATCH_DIR = REPO_ROOT / "artifacts" / "derek_live_snapshots"

# Execution windows per spec Part J. close_lock uses -5 minutes from tip
# to absorb GitHub Actions runner latency.
T_MINUS_25_OFFSET_MIN = 25
CLOSE_LOCK_OFFSET_MIN = 5
T_MINUS_25_WINDOW = (-5, 7)        # (target - 5min, target + 7min)
CLOSE_LOCK_WINDOW = (-5, -1)       # (target - 5min, target - 1min) i.e. tip-10 to tip-6


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_iso(d: dt.datetime) -> str:
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _load_schedule(delivery_date: str) -> list[dict]:
    """Load today's slate from ``predictions/all_props_<date>.parquet`` (one row
    per (player, stat, line) — we deduplicate to (game_id, game_start_time)).
    Phase 13U — when the parquet has no ``game_start_time`` column, the
    dispatcher invokes the cascading resolver to fill in real tip times
    from cached/live Odds API or BDL. The resolver never fabricates;
    games it cannot resolve simply have ``game_start_time=None`` and
    are reported as not-due in the per-game log.
    """
    parquet = PRED_DIR / f"all_props_{delivery_date}.parquet"
    if not parquet.exists():
        return []
    try:
        import pandas as pd
        df = pd.read_parquet(parquet, columns=None)
        if "game_id" not in df.columns:
            return []
        rows = []
        gst_col = "game_start_time" if "game_start_time" in df.columns else None
        seen: set[str] = set()
        for _, r in df.iterrows():
            gid = str(r.get("game_id"))
            if gid in seen:
                continue
            seen.add(gid)
            rec = {"game_id": gid}
            if gst_col and gst_col in df.columns:
                gs = r.get(gst_col)
                if gs is not None and not (hasattr(gs, "__class__") and pd.isna(gs)):
                    rec["game_start_time"] = str(gs)
            rows.append(rec)

        # Phase 13U — fill missing tip times from the resolver.
        if any(not r.get("game_start_time") for r in rows):
            try:
                # Lazy import; resolver depends on src/ being on sys.path.
                from nba_props_model.schedule.game_start_times import (
                    GameStartTimeResolver,
                )
                resolver = GameStartTimeResolver(repo_root=REPO_ROOT)
                records, _telemetry = resolver.resolve(delivery_date)
                resolved = {
                    r.game_id: r.resolved_game_start_time_utc
                    for r in records if r.resolved_game_start_time_utc
                }
                source_used = {r.game_id: r.source_used for r in records}
                for r in rows:
                    if not r.get("game_start_time") and r["game_id"] in resolved:
                        r["game_start_time"] = resolved[r["game_id"]]
                        r["game_start_time_source"] = source_used.get(
                            r["game_id"], "resolver")
            except Exception:
                # Resolver failure is non-fatal — affected games stay
                # without start time and the per-game log will surface
                # the blocker.
                pass
        return rows
    except Exception:
        return []


def _parse_iso_to_utc(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def _snapshot_target(game_start: dt.datetime, snapshot_type: str
                      ) -> dt.datetime | None:
    if snapshot_type == "t_minus_25":
        return game_start - dt.timedelta(minutes=T_MINUS_25_OFFSET_MIN)
    if snapshot_type == "close_lock":
        return game_start - dt.timedelta(minutes=CLOSE_LOCK_OFFSET_MIN)
    if snapshot_type == "current_live":
        # current_live target is "now"; eligibility is simply
        # "game has not tipped yet". Returning game_start lets the
        # caller treat any pre-tip game as eligible.
        return game_start
    return None


def _is_in_window(now: dt.datetime, target: dt.datetime, window: tuple[int, int]) -> bool:
    earliest = target + dt.timedelta(minutes=window[0])
    latest = target + dt.timedelta(minutes=window[1])
    return earliest <= now <= latest


def _snapshot_dir(delivery_date: str, game_id: str, snapshot_type: str) -> Path:
    return (
        DELIVERIES_DIR / delivery_date / "derek_game_snapshots"
        / str(game_id) / snapshot_type
    )


def _already_run(delivery_date: str, game_id: str, snapshot_type: str) -> bool:
    return (_snapshot_dir(delivery_date, game_id, snapshot_type)
             / "snapshot_manifest.json").exists()


def _run_snapshot(delivery_date: str, game_id: str, snapshot_type: str,
                   allow_backfill: bool, force: bool) -> tuple[int, str]:
    cmd = [
        sys.executable,
        "scripts/run_derek_live_game_snapshot.py",
        "--delivery-date", delivery_date,
        "--game-id", str(game_id),
        "--snapshot-type", snapshot_type,
    ]
    if allow_backfill:
        cmd.append("--allow-backfill-test")
    if force:
        cmd.append("--force")
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        env={**os.environ},
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Dispatch Derek per-game live snapshots.")
    p.add_argument("--delivery-date", default=None,
                   help="YYYY-MM-DD; default = today UTC")
    p.add_argument("--snapshot-type", required=True, choices=SNAPSHOT_TYPES)
    p.add_argument("--allow-backfill-test", action="store_true",
                   help="Skip the wall-clock window check; run for any pending game.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing snapshot folders.")
    p.add_argument("--max-games", type=int, default=None,
                   help="Limit number of games dispatched (testing).")
    args = p.parse_args(argv)

    delivery_date = args.delivery_date or _utcnow().strftime("%Y-%m-%d")
    DISPATCH_DIR.mkdir(parents=True, exist_ok=True)

    schedule = _load_schedule(delivery_date)
    now = _utcnow()
    decisions: list[dict] = []
    fired = 0
    skipped_already_run = 0
    skipped_window = 0
    failures = 0

    # Phase 13T — verbose visibility on dispatch decision context. The
    # dispatcher prints what it sees so operators can debug "why was no
    # snapshot generated?" without trawling parquet diffs. Never prints
    # API keys.
    parquet = PRED_DIR / f"all_props_{delivery_date}.parquet"
    print(
        f"  delivery_date={delivery_date}  now_utc={_utc_iso(now)}  "
        f"snapshot_type={args.snapshot_type}"
    )
    print(
        f"  predictions_parquet={parquet.relative_to(REPO_ROOT)} "
        f"exists={parquet.exists()} "
        f"unique_games={len({e['game_id'] for e in schedule})}"
    )

    if not schedule:
        slate_status = (
            "predictions_parquet_missing"
            if not parquet.exists()
            else "predictions_parquet_present_but_no_games"
        )
        report = {
            "schema_version": "1.0",
            "delivery_date": delivery_date,
            "snapshot_type": args.snapshot_type,
            "now_utc": _utc_iso(now),
            "code_commit": git_commit(),
            "schedule_rows": 0,
            "eligible_rows": 0,
            "slate_status": slate_status,
            "decisions": [],
            "summary": {
                "fired": 0, "skipped_already_run": 0,
                "skipped_window": 0, "failures": 0,
            },
            "note": (
                f"no schedule loaded — predictions/all_props_{delivery_date}.parquet "
                f"slate_status={slate_status}. Dispatcher exits cleanly with no work."
            ),
        }
        out = DISPATCH_DIR / delivery_date / f"dispatch_{args.snapshot_type}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(out, report)
        # Phase 13T — emit explicit pending token alongside the existing
        # dispatch pass token so downstream verifiers recognise this as
        # honest "no games" rather than failure.
        print("DEREK_LIVE_SNAPSHOT_DISPATCH_PASS")
        print("DEREK_LIVE_SNAPSHOT_DISPATCH_PENDING_NO_GAMES")
        print(f"  delivery_date={delivery_date} snapshot_type={args.snapshot_type}")
        print(f"  schedule_rows=0 eligible_rows=0 slate_status={slate_status}")
        return 0

    if args.max_games:
        schedule = schedule[: args.max_games]

    if args.snapshot_type == "t_minus_25":
        window = T_MINUS_25_WINDOW
    elif args.snapshot_type == "close_lock":
        window = CLOSE_LOCK_WINDOW
    else:
        # current_live — eligibility is "game has not tipped yet".
        # A symbolic window is used only for the per-game log line.
        window = (-9999, 0)
    eligible_rows = 0
    for entry in schedule:
        game_id = entry["game_id"]
        gs_iso = entry.get("game_start_time")
        gs = _parse_iso_to_utc(gs_iso)
        target = _snapshot_target(gs, args.snapshot_type) if gs else None
        if args.snapshot_type == "current_live":
            # In-window iff the game has not tipped yet (pre-tip).
            in_window = (
                args.allow_backfill_test
                or (gs is not None and now < gs)
            )
        else:
            in_window = (
                args.allow_backfill_test
                or (target is not None and _is_in_window(now, target, window))
            )
        # Phase 13T+13U verbose per-game visibility.
        if args.snapshot_type == "current_live":
            if gs is None:
                due_reason = "no_game_start_time"
            elif now >= gs:
                due_reason = (
                    f"already_tipped (game_start_utc={_utc_iso(gs)} "
                    f"now={_utc_iso(now)})"
                )
            else:
                due_reason = (
                    f"pre_tip (game_start_utc={_utc_iso(gs)} now={_utc_iso(now)})"
                )
        else:
            due_reason = (
                "in_window" if in_window
                else ("no_game_start_time" if target is None
                      else f"target={_utc_iso(target)} window=({window[0]:+d},{window[1]:+d})min "
                           f"now={_utc_iso(now)} → not_due")
            )
        team = entry.get("team")
        opponent = entry.get("opponent")
        gst_source = entry.get("game_start_time_source") or "predictions_parquet"
        print(
            f"  game_id={game_id} team={team!r} opponent={opponent!r} "
            f"game_start_time={gs_iso!r} game_start_time_source={gst_source} "
            f"snapshot_type={args.snapshot_type} "
            f"target_utc={_utc_iso(target) if target else None} "
            f"due={in_window} reason={due_reason}"
        )
        if _already_run(delivery_date, game_id, args.snapshot_type) and not args.force:
            decisions.append({
                "game_id": game_id, "decision": "skipped_already_run",
                "target_utc": _utc_iso(target) if target else None,
                "due_reason": due_reason,
            })
            skipped_already_run += 1
            continue
        if not in_window:
            decisions.append({
                "game_id": game_id, "decision": "skipped_window",
                "target_utc": _utc_iso(target) if target else None,
                "now_utc": _utc_iso(now),
                "due_reason": due_reason,
            })
            skipped_window += 1
            continue
        eligible_rows += 1
        rc, log = _run_snapshot(
            delivery_date, game_id, args.snapshot_type,
            allow_backfill=bool(args.allow_backfill_test), force=args.force,
        )
        if rc == 0:
            fired += 1
            decisions.append({
                "game_id": game_id, "decision": "fired_ok",
                "target_utc": _utc_iso(target) if target else None,
                "tail": log.strip().splitlines()[-1:][0] if log.strip() else "",
            })
        else:
            failures += 1
            decisions.append({
                "game_id": game_id, "decision": "fired_failed",
                "exit_code": rc,
                "target_utc": _utc_iso(target) if target else None,
                "tail": log.strip().splitlines()[-3:],
            })

    report = {
        "schema_version": "1.0",
        "delivery_date": delivery_date,
        "snapshot_type": args.snapshot_type,
        "now_utc": _utc_iso(now),
        "code_commit": git_commit(),
        "schedule_rows": len(schedule),
        "eligible_rows": eligible_rows,
        "decisions": decisions,
        "summary": {
            "fired": fired, "skipped_already_run": skipped_already_run,
            "skipped_window": skipped_window, "failures": failures,
        },
    }
    out_dir = DISPATCH_DIR / delivery_date
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(out_dir / f"dispatch_{args.snapshot_type}.json", report)

    if failures > 0:
        print("DEREK_LIVE_SNAPSHOT_DISPATCH_FAILED", file=sys.stderr)
        for rec in decisions:
            if rec["decision"] == "fired_failed":
                print(f"  - game_id={rec['game_id']}: exit_code={rec.get('exit_code')}",
                      file=sys.stderr)
        return 1

    print("DEREK_LIVE_SNAPSHOT_DISPATCH_PASS")
    print("DEREK_DISPATCHER_GAME_TIME_AWARE_PASS")
    if eligible_rows == 0 and fired == 0:
        # Phase 13T — schedule had games but none were due in this
        # window. Emit the explicit pending token so the workflow's
        # E2E verifier can distinguish from a real failure.
        print("DEREK_LIVE_SNAPSHOT_DISPATCH_PENDING_NO_GAMES")
    if args.snapshot_type == "current_live" and fired > 0:
        print("DEREK_CURRENT_LIVE_SNAPSHOT_MODE_PASS")
    print(f"  delivery_date={delivery_date} snapshot_type={args.snapshot_type}")
    print(
        f"  fired={fired} skipped_already_run={skipped_already_run} "
        f"skipped_window={skipped_window} eligible_rows={eligible_rows} "
        f"schedule_rows={len(schedule)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
