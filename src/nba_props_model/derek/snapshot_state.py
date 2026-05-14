"""Phase 13Z — shared snapshot state machine for Derek dispatcher /
verifier / runner.

The single source of truth for whether a per-(game, snapshot_type)
folder is in one of these states:

    EXISTS              snapshot_manifest.json present and valid
    NOT_DUE             now < target - early_tolerance
    DUE_WINDOW          target - early_tolerance <= now <= target +
                        late_tolerance
    LATE_BUT_PRE_TIP    now > target + late_tolerance and now <
                        game_start_time
    MISSED_POST_TIP     now >= game_start_time and snapshot missing
    INVALID_NO_START    game_start_time is missing/unparseable

Tolerances default to ±6 minutes so a target landing between cron
ticks (cron fires every 10 min) does not silently skip the window.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


EARLY_TOLERANCE_MIN = 6   # legacy fallback for current_live / unknown types
LATE_TOLERANCE_MIN = 6
T_MINUS_25_OFFSET_MIN = 25
CLOSE_LOCK_OFFSET_MIN = 6

# Per-snapshot-type firing tolerances (spec Part J):
#   t_minus_25 must fire 20-30 min before tip  -> +/-5 around target=(tip-25)
#   close_lock must fire  3- 9 min before tip  -> +/-3 around target=(tip-6)
TOLERANCES_BY_TYPE = {
    "t_minus_25": (5, 5),
    "close_lock": (3, 3),
    "current_live": (180, 0),
}


@dataclass(frozen=True)
class SnapshotStateResult:
    state: str
    target_time_utc: Optional[dt.datetime]
    game_start_time_utc: Optional[dt.datetime]
    now_utc: dt.datetime
    snapshot_exists: bool
    missed_marker_exists: bool
    seconds_to_target: Optional[float]
    seconds_late_vs_target: Optional[float]
    detail: str


def _parse_iso_to_utc(s) -> Optional[dt.datetime]:
    if s is None:
        return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def snapshot_target(game_start: dt.datetime, snapshot_type: str
                     ) -> Optional[dt.datetime]:
    if snapshot_type == "t_minus_25":
        return game_start - dt.timedelta(minutes=T_MINUS_25_OFFSET_MIN)
    if snapshot_type == "close_lock":
        return game_start - dt.timedelta(minutes=CLOSE_LOCK_OFFSET_MIN)
    if snapshot_type == "current_live":
        return game_start
    return None


def classify_snapshot_state(
    *,
    now_utc: dt.datetime,
    game_start_time_utc,
    snapshot_type: str,
    snapshot_exists: bool,
    missed_marker_exists: bool = False,
    early_tolerance_min: Optional[int] = None,
    late_tolerance_min: Optional[int] = None,
) -> SnapshotStateResult:
    _type_tol = TOLERANCES_BY_TYPE.get(
        snapshot_type, (EARLY_TOLERANCE_MIN, LATE_TOLERANCE_MIN))
    if early_tolerance_min is None:
        early_tolerance_min = _type_tol[0]
    if late_tolerance_min is None:
        late_tolerance_min = _type_tol[1]
    if snapshot_exists:
        gs = _parse_iso_to_utc(game_start_time_utc)
        target = snapshot_target(gs, snapshot_type) if gs else None
        return SnapshotStateResult(
            state="EXISTS", target_time_utc=target,
            game_start_time_utc=gs, now_utc=now_utc,
            snapshot_exists=True, missed_marker_exists=missed_marker_exists,
            seconds_to_target=(
                (target - now_utc).total_seconds() if target else None
            ),
            seconds_late_vs_target=(
                (now_utc - target).total_seconds() if target else None
            ),
            detail="snapshot_manifest.json present",
        )
    gs = _parse_iso_to_utc(game_start_time_utc)
    if gs is None:
        return SnapshotStateResult(
            state="INVALID_NO_START",
            target_time_utc=None, game_start_time_utc=None,
            now_utc=now_utc,
            snapshot_exists=False,
            missed_marker_exists=missed_marker_exists,
            seconds_to_target=None,
            seconds_late_vs_target=None,
            detail="game_start_time_utc missing or unparseable",
        )
    target = snapshot_target(gs, snapshot_type)
    if target is None:
        return SnapshotStateResult(
            state="INVALID_NO_START",
            target_time_utc=None, game_start_time_utc=gs,
            now_utc=now_utc,
            snapshot_exists=False,
            missed_marker_exists=missed_marker_exists,
            seconds_to_target=None,
            seconds_late_vs_target=None,
            detail=f"unknown snapshot_type {snapshot_type!r}",
        )
    early = target - dt.timedelta(minutes=early_tolerance_min)
    late = target + dt.timedelta(minutes=late_tolerance_min)
    if now_utc < early:
        return SnapshotStateResult(
            state="NOT_DUE",
            target_time_utc=target, game_start_time_utc=gs,
            now_utc=now_utc, snapshot_exists=False,
            missed_marker_exists=missed_marker_exists,
            seconds_to_target=(target - now_utc).total_seconds(),
            seconds_late_vs_target=None,
            detail=(
                f"now < target - {early_tolerance_min}min; will fire "
                f"during the cron window starting at {early.isoformat()}"
            ),
        )
    if now_utc <= late:
        return SnapshotStateResult(
            state="DUE_WINDOW",
            target_time_utc=target, game_start_time_utc=gs,
            now_utc=now_utc, snapshot_exists=False,
            missed_marker_exists=missed_marker_exists,
            seconds_to_target=(target - now_utc).total_seconds(),
            seconds_late_vs_target=(now_utc - target).total_seconds(),
            detail=(
                f"target {target.isoformat()} ± "
                f"{late_tolerance_min}min — generate now"
            ),
        )
    if now_utc < gs:
        return SnapshotStateResult(
            state="LATE_BUT_PRE_TIP",
            target_time_utc=target, game_start_time_utc=gs,
            now_utc=now_utc, snapshot_exists=False,
            missed_marker_exists=missed_marker_exists,
            seconds_to_target=(target - now_utc).total_seconds(),
            seconds_late_vs_target=(now_utc - target).total_seconds(),
            detail=(
                f"now is past target+{late_tolerance_min}min but "
                f"before tip {gs.isoformat()} — recover by generating "
                "immediately, manifest must record actual_run_late=true"
            ),
        )
    return SnapshotStateResult(
        state="MISSED_POST_TIP",
        target_time_utc=target, game_start_time_utc=gs,
        now_utc=now_utc, snapshot_exists=False,
        missed_marker_exists=missed_marker_exists,
        seconds_to_target=(target - now_utc).total_seconds(),
        seconds_late_vs_target=(now_utc - target).total_seconds(),
        detail=(
            f"game already tipped at {gs.isoformat()}; do not "
            "fabricate pre-tip data — write missed_snapshot_manifest.json"
        ),
    )


def write_missed_marker(
    *,
    snapshot_dir: Path,
    delivery_date: str,
    game_id: str,
    snapshot_type: str,
    state_result: SnapshotStateResult,
    missed_reason: str = "post_tip_no_pretip_snapshot_was_generated",
) -> dict:
    """Phase 13Z — write the explicit MISSED_POST_TIP marker for a
    snapshot folder. Never produces fake PMFs. Idempotent."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "snapshot_type": snapshot_type,
        "game_id": str(game_id),
        "delivery_date": delivery_date,
        "game_start_time_utc": (
            state_result.game_start_time_utc.isoformat() + "Z"
            if state_result.game_start_time_utc
            and state_result.game_start_time_utc.tzinfo is None is False
            else (
                state_result.game_start_time_utc.replace(microsecond=0)
                .isoformat().replace("+00:00", "Z")
                if state_result.game_start_time_utc else None
            )
        ),
        "snapshot_target_time_utc": (
            state_result.target_time_utc.replace(microsecond=0)
            .isoformat().replace("+00:00", "Z")
            if state_result.target_time_utc else None
        ),
        "now_utc": (
            state_result.now_utc.replace(microsecond=0)
            .isoformat().replace("+00:00", "Z")
        ),
        "missed_reason": missed_reason,
        "no_fake_pretip_snapshot": True,
        "production_fix_applied": True,
        "next_automation_status": (
            "next-day cron will resume normal scheduling; this miss is "
            "documented for the audit trail."
        ),
        "state": state_result.state,
        "detail": state_result.detail,
    }
    marker = snapshot_dir / "missed_snapshot_manifest.json"
    marker.write_text(
        __import__("json").dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md = [
        f"# Missed snapshot — {snapshot_type} ({game_id}) {delivery_date}",
        "",
        f"- snapshot_type: **{snapshot_type}**",
        f"- game_id: `{game_id}`",
        f"- delivery_date: {delivery_date}",
        f"- game_start_time_utc: `{payload['game_start_time_utc']}`",
        f"- snapshot_target_time_utc: `{payload['snapshot_target_time_utc']}`",
        f"- now_utc: `{payload['now_utc']}`",
        f"- missed_reason: `{missed_reason}`",
        "",
        "## Why a marker, not a fake snapshot",
        "",
        "The game has already tipped. We do **not** fabricate a "
        "pre-tip snapshot after the fact — pre-tip lineups, injury "
        "status, and odds at this moment in history can no longer be "
        "reconstructed without leakage from in-game data. Instead, "
        "this marker file records the miss honestly so downstream "
        "verifiers and Derek's index can label the snapshot as "
        "MISSED_POST_TIP rather than silently treating it as pending.",
        "",
        "- `no_fake_pretip_snapshot: true`",
        "- `production_fix_applied: true`",
    ]
    (snapshot_dir / "missed_snapshot_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )
    return payload
