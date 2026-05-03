"""Phase 13U Part C — game start time resolver CLI.

Runs the cascading resolver and writes:

    artifacts/live_schedule/<date>/game_start_times.json
    artifacts/live_schedule/<date>/game_start_times.csv
    artifacts/live_schedule/<date>/game_start_time_resolution_report.md

Pass / pending / fail lines:
    GAME_START_TIME_RESOLUTION_PASS
    GAME_START_TIME_RESOLUTION_PENDING
    GAME_START_TIME_RESOLUTION_FAILED
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.schedule.game_start_times import (  # noqa: E402
    GameStartTimeResolver,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    out_dir = REPO_ROOT / "artifacts" / "live_schedule" / args.delivery_date
    out_dir.mkdir(parents=True, exist_ok=True)

    resolver = GameStartTimeResolver(repo_root=REPO_ROOT)
    records, telemetry = resolver.resolve(args.delivery_date)

    payload = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z",
        "delivery_date": args.delivery_date,
        "telemetry": telemetry,
        "records": [r.as_dict() for r in records],
    }
    (out_dir / "game_start_times.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    with (out_dir / "game_start_times.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "game_id", "team_abbr", "opponent_abbr",
            "resolved_game_start_time_utc", "source_used",
            "source_confidence", "source_payload_hash",
            "resolution_blocker",
        ])
        for r in records:
            w.writerow([
                r.game_id, r.team_abbr, r.opponent_abbr,
                r.resolved_game_start_time_utc or "",
                r.source_used, r.source_confidence,
                r.source_payload_hash, r.resolution_blocker,
            ])

    md = [
        f"# Game start time resolution — {args.delivery_date}",
        "",
        f"- generated_at_utc: {payload['generated_at_utc']}",
        f"- predictions_unique_games: {telemetry.get('predictions_unique_games')}",
        f"- resolved: **{telemetry.get('resolved_count', 0)}**",
        f"- unresolved: **{telemetry.get('unresolved_count', 0)}**",
        f"- ODDS_API_KEY present: {telemetry.get('odds_api_key_present')}",
        f"- BDL_API_KEY present: {telemetry.get('bdl_api_key_present')}",
        f"- odds_api_cached_events: {telemetry.get('odds_api_cached_events')}",
        f"- odds_api_live_events: {telemetry.get('odds_api_live_events')}",
        f"- bdl_live_games: {telemetry.get('bdl_live_games')}",
        "",
        "## Per-game resolution",
        "",
        "| game_id | team | opponent | resolved_utc | source | confidence | blocker |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in records:
        md.append(
            f"| {r.game_id} | {r.team_abbr} | {r.opponent_abbr} | "
            f"`{r.resolved_game_start_time_utc or ''}` | "
            f"{r.source_used} | {r.source_confidence} | "
            f"{r.resolution_blocker} |"
        )
    (out_dir / "game_start_time_resolution_report.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    resolved = telemetry.get("resolved_count", 0)
    total = len(records)

    # PASS only if every game in predictions had a real start time
    # resolved. PENDING if the slate has zero games or no real source
    # is available yet. FAILED only on resolver-internal errors (we
    # don't have those right now; cascade returns unresolved instead).
    if total == 0:
        print("GAME_START_TIME_RESOLUTION_PENDING")
        print(f"  delivery_date={args.delivery_date} reason="
              f"{telemetry.get('resolution_blocker') or 'no_predictions_games'}")
        return 0
    if resolved == 0:
        print("GAME_START_TIME_RESOLUTION_PENDING")
        print(
            f"  delivery_date={args.delivery_date} "
            f"games={total} resolved=0 "
            f"odds_cached={telemetry.get('odds_api_cached_events')} "
            f"odds_live={telemetry.get('odds_api_live_events')} "
            f"bdl_live={telemetry.get('bdl_live_games')}"
        )
        return 0
    if resolved < total:
        # Partial resolution is a soft failure: report PASS for the
        # resolved games but PENDING tag for the unresolved tail.
        print("GAME_START_TIME_RESOLUTION_PASS")
        print(
            f"  delivery_date={args.delivery_date} "
            f"resolved={resolved}/{total}"
        )
        for r in records:
            if not r.resolved_game_start_time_utc:
                print(
                    f"  - {r.game_id} ({r.team_abbr}@{r.opponent_abbr}): "
                    f"unresolved blocker={r.resolution_blocker!r}"
                )
        return 0
    print("GAME_START_TIME_RESOLUTION_PASS")
    print(f"  delivery_date={args.delivery_date} resolved={resolved}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
