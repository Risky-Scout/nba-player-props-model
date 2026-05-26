"""Phase 13U Part E — Derek slate completeness verifier.

For ``--delivery-date``, compare:

  * the real game slate (Odds API live events / cached / BDL)
  * games present in ``predictions/all_props_<date>.parquet``
  * games present under ``deliveries/<date>/derek_game_snapshots/``

and write:

    artifacts/automation_health/derek_slate_completeness_<date>.json
    artifacts/automation_health/derek_slate_completeness_<date>.md

Pass / pending / fail lines:
    DEREK_SLATE_COMPLETENESS_PASS
    DEREK_SLATE_COMPLETENESS_PENDING
    DEREK_SLATE_COMPLETENESS_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.schedule.game_start_times import (  # noqa: E402
    GameStartTimeResolver,
    NBA_TEAM_NAME_TO_ABBR,
)
from nba_props_model.derek.snapshot_state import CLOSE_LOCK_OFFSET_MIN  # noqa: E402


T_MINUS_25_OFFSET_MIN = 25
T_MINUS_25_WINDOW = (-5, 7)
CLOSE_LOCK_WINDOW = (-5, -1)


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_iso_to_utc(s):
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def _utc_iso(d):
    if d is None:
        return None
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    out_dir = REPO_ROOT / "artifacts" / "automation_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    now = _utcnow()

    pred_parquet = REPO_ROOT / "predictions" / f"all_props_{args.delivery_date}.parquet"
    pred_games_with_props: dict[str, dict] = {}
    if pred_parquet.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(pred_parquet)
            if "game_id" in df.columns:
                for gid, sub in df.groupby(df["game_id"].astype(str)):
                    pred_games_with_props[gid] = {
                        "game_id": gid,
                        "rows": int(len(sub)),
                        "team_ids": sorted({
                            int(t) for t in sub["team_id"].dropna().unique()
                            if "team_id" in sub.columns
                        }),
                        "game_start_time": (
                            str(sub["game_start_time"].dropna().iloc[0])
                            if "game_start_time" in sub.columns
                            and not sub["game_start_time"].dropna().empty
                            else None
                        ),
                    }
        except Exception as exc:
            pass

    # Real schedule via resolver.
    resolver = GameStartTimeResolver(repo_root=REPO_ROOT)
    records, telemetry = resolver.resolve(args.delivery_date)
    schedule_by_gid = {r.game_id: r for r in records}

    # Derek snapshot folders.
    derek_root = REPO_ROOT / "deliveries" / args.delivery_date / "derek_game_snapshots"
    derek_games: dict[str, list[str]] = {}
    if derek_root.exists():
        for gd in sorted(derek_root.iterdir()):
            if not gd.is_dir():
                continue
            types = sorted(
                d.name for d in gd.iterdir() if d.is_dir()
                and (d / "snapshot_manifest.json").exists()
            )
            derek_games[gd.name] = types

    games_in_real_slate = set(schedule_by_gid.keys()) | set(pred_games_with_props.keys())
    games_in_predictions = set(pred_games_with_props.keys())
    games_with_no_props = sorted(set(schedule_by_gid.keys()) - games_in_predictions)
    games_missing_from_predictions = list(games_with_no_props)
    games_with_null_start_time = sorted(
        gid for gid, r in pred_games_with_props.items()
        if not r.get("game_start_time")
    )

    # Eligibility per snapshot type.
    eligible_t25: list[str] = []
    eligible_cl: list[str] = []
    eligible_current_live: list[str] = []
    games_already_tipped: list[str] = []
    games_missed_t25: list[str] = []
    for gid in sorted(games_in_predictions):
        rec = schedule_by_gid.get(gid)
        gs = _parse_iso_to_utc(
            rec.resolved_game_start_time_utc if rec else None
        )
        if gs is None:
            continue
        if gs < now:
            games_already_tipped.append(gid)
            continue
        # Available for current_live (any pre-tip game).
        eligible_current_live.append(gid)
        t25_target = gs - dt.timedelta(minutes=T_MINUS_25_OFFSET_MIN)
        cl_target = gs - dt.timedelta(minutes=CLOSE_LOCK_OFFSET_MIN)
        if (t25_target + dt.timedelta(minutes=T_MINUS_25_WINDOW[0])
            <= now <=
            t25_target + dt.timedelta(minutes=T_MINUS_25_WINDOW[1])):
            eligible_t25.append(gid)
        if (cl_target + dt.timedelta(minutes=CLOSE_LOCK_WINDOW[0])
            <= now <=
            cl_target + dt.timedelta(minutes=CLOSE_LOCK_WINDOW[1])):
            eligible_cl.append(gid)
        # Missed T-25 if we're more than 12 minutes past the close.
        if now > t25_target + dt.timedelta(
            minutes=T_MINUS_25_WINDOW[1] + 12
        ):
            games_missed_t25.append(gid)

    payload = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "now_utc": _utc_iso(now),
        "telemetry": telemetry,
        "games_in_real_slate": sorted(games_in_real_slate),
        "games_in_predictions": sorted(games_in_predictions),
        "games_missing_from_predictions": games_missing_from_predictions,
        "games_with_no_props": games_with_no_props,
        "games_with_null_start_time": games_with_null_start_time,
        "eligible_current_live": eligible_current_live,
        "eligible_t_minus_25": eligible_t25,
        "eligible_close_lock": eligible_cl,
        "games_already_tipped": games_already_tipped,
        "games_missed_t_minus_25": games_missed_t25,
        "derek_game_folders": derek_games,
        "predictions_parquet_present": pred_parquet.exists(),
    }
    (out_dir / f"derek_slate_completeness_{args.delivery_date}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8")

    md = [
        f"# Derek slate completeness — {args.delivery_date}",
        "",
        f"- now_utc: {_utc_iso(now)}",
        f"- predictions_parquet_present: {pred_parquet.exists()}",
        f"- games_in_real_slate: **{len(games_in_real_slate)}**",
        f"- games_in_predictions: **{len(games_in_predictions)}**",
        f"- games_missing_from_predictions: {games_missing_from_predictions}",
        f"- games_with_null_start_time: {games_with_null_start_time}",
        f"- eligible_current_live: {eligible_current_live}",
        f"- eligible_t_minus_25: {eligible_t25}",
        f"- eligible_close_lock: {eligible_cl}",
        f"- games_already_tipped: {games_already_tipped}",
        f"- games_missed_t_minus_25: {games_missed_t25}",
        f"- derek_game_folders: {derek_games}",
    ]
    (out_dir / f"derek_slate_completeness_{args.delivery_date}.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    # PASS/PENDING/FAILED decision.
    if not pred_parquet.exists():
        print("DEREK_SLATE_COMPLETENESS_PENDING")
        print(f"  reason=no_predictions_parquet")
        return 0
    if not games_in_predictions:
        print("DEREK_SLATE_COMPLETENESS_PENDING")
        print(f"  reason=predictions_have_zero_games")
        return 0
    # Hard fail when predictions exist but rows missing real start times AND
    # the resolver had a real schedule available (cached or live).
    if (games_with_null_start_time and
        (telemetry.get("odds_api_live_events", 0) > 0
         or telemetry.get("odds_api_cached_events", 0) > 0
         or telemetry.get("bdl_live_games", 0) > 0)
        and not all(
            schedule_by_gid.get(gid)
            and not schedule_by_gid[gid].resolved_game_start_time_utc
            for gid in games_with_null_start_time
        )):
        print("DEREK_SLATE_COMPLETENESS_FAILED", file=sys.stderr)
        print(
            f"  delivery_date={args.delivery_date} "
            f"games_with_null_start_time={games_with_null_start_time}",
            file=sys.stderr,
        )
        return 1
    print("DEREK_SLATE_COMPLETENESS_PASS")
    print(
        f"  delivery_date={args.delivery_date} "
        f"slate={len(games_in_real_slate)} predictions={len(games_in_predictions)} "
        f"current_live_eligible={len(eligible_current_live)} "
        f"t25_eligible={len(eligible_t25)} cl_eligible={len(eligible_cl)} "
        f"already_tipped={len(games_already_tipped)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
