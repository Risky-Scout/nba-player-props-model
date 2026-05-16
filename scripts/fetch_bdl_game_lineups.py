"""Phase 13M — fetch BDL confirmed lineups for one or more games.

Wraps ``nba_props_model.data.bdl_client.get_lineups_status`` which hits
the BDL v1 lineups endpoint with the ``game_ids[]`` array query param:

    GET https://api.balldontlie.io/v1/lineups?game_ids[]=<id>

The previous implementation called ``/nba/v2/lineups?game_id=<id>`` which
BDL responds to with ``404 Route not found``.  The v2-path mistake was
silently swallowed and reported as "no rows returned (lineups not posted
yet)", producing false ``BDL_LINEUPS_FETCH_PASS`` lines on disk.  The
corrected fetcher writes a structured ``bdl_fetch_status`` field that
distinguishes endpoint misconfiguration from a legitimate empty
pre-confirmation response.

Per-game artifacts written under ``artifacts/live_lineups/<date>/<gid>/``:

    bdl_lineups_raw.json
    bdl_lineups_normalized.csv
    bdl_lineups_normalized.parquet
    lineup_status.json   (now carries ``bdl_fetch_status``)
    lineup_status.md

``bdl_fetch_status`` enum (set by ``bdl_client.get_lineups_status``):

    lineups_available                    HTTP 200 + non-empty data array
    confirmed_lineups_not_available_yet  HTTP 200 + empty data array
    endpoint_misconfigured               HTTP 404 (wrong URL/route)
    auth_failed                          HTTP 401 / 403
    request_failed                       network exception / 5xx

``lineup_confirmed=True`` only when ``bdl_fetch_status="lineups_available"``
AND both teams are present AND each team has exactly 5 ``starter=True``
rows AND the fetch occurred before ``game_start_time_utc`` (when known).
In every other case ``lineup_confirmed=False`` and ``lineup_blocker``
records the exact reason.

Usage:
    python3 scripts/fetch_bdl_game_lineups.py --delivery-date YYYY-MM-DD --game-id 21681995
    python3 scripts/fetch_bdl_game_lineups.py --delivery-date YYYY-MM-DD \\
        --game-ids 21681995,21681996

Pass line:  BDL_LINEUPS_FETCH_PASS
            Printed only when every game returned HTTP 200 (mix of
            ``lineups_available`` and ``confirmed_lineups_not_available_yet``
            is allowed).
Fail line:  BDL_LINEUPS_FETCH_FAILED
            Printed when ANY game returned ``endpoint_misconfigured``,
            ``auth_failed``, or ``request_failed``.

Modeling-rule reminder: an empty BDL pre-confirmation response is NOT a
projected-lineup source.  The morning player universe must come from the
internal projected rotation/minutes artifact; empty BDL must NOT cause
full-roster PMFs.  See the player-game eligibility gate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.data.bdl_client import (  # noqa: E402
    get_lineups,
    get_lineups_status,
)


LIVE_LINEUPS_DIR = REPO_ROOT / "artifacts" / "live_lineups"
PRED_DIR = REPO_ROOT / "predictions"
SOURCE_TAG = "balldontlie_v1_lineups"  # canonical source tag matching the
                                        # actual v1 endpoint hit by
                                        # get_lineups_status() — keep this
                                        # stable across endpoint version
                                        # bumps so downstream consumers don't
                                        # re-key on minor URL changes.

# Fetch-status enum values returned by bdl_client.get_lineups_status().
# Any value other than the two HTTP-200 cases is a hard failure.
BDL_FETCH_STATUS_OK = {
    "lineups_available",
    "confirmed_lineups_not_available_yet",
}
BDL_FETCH_STATUS_FAIL = {
    "endpoint_misconfigured",
    "auth_failed",
    "request_failed",
}


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_iso(d: dt.datetime) -> str:
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _normalize_row(raw: dict, game_id: str, fetched_at_utc: str) -> dict:
    player = raw.get("player") or {}
    team = raw.get("team") or {}
    return {
        "game_id": str(game_id),
        "team_id": team.get("id"),
        "team_abbreviation": team.get("abbreviation") or team.get("triCode")
            or team.get("name"),
        "player_id": player.get("id"),
        "player_name": (
            (player.get("first_name") or "") + " " + (player.get("last_name") or "")
        ).strip() or player.get("name"),
        "starter": bool(raw.get("starter")),
        "lineup_position": raw.get("position") or raw.get("lineup_position"),
        "player_position": player.get("position"),
        "source": SOURCE_TAG,
        "fetched_at_utc": fetched_at_utc,
    }


def _hash_lineup(rows: list[dict]) -> str:
    if not rows:
        return ""
    payload = json.dumps(
        sorted(
            (
                {
                    "team_id": r["team_id"],
                    "player_id": r["player_id"],
                    "starter": r["starter"],
                    "lineup_position": r["lineup_position"],
                }
                for r in rows
            ),
            key=lambda r: (r.get("team_id") or 0, r.get("player_id") or 0),
        ),
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _load_game_start_time(delivery_date: str, game_id: str) -> str | None:
    parquet = PRED_DIR / f"all_props_{delivery_date}.parquet"
    if not parquet.exists():
        return None
    try:
        import pandas as pd
        df = pd.read_parquet(parquet, columns=None)
        if "game_id" not in df.columns or "game_start_time" not in df.columns:
            return None
        sub = df[df["game_id"].astype(str) == str(game_id)]
        if sub.empty:
            return None
        gs = sub["game_start_time"].dropna()
        return str(gs.iloc[0]) if not gs.empty else None
    except Exception:
        return None


def _classify(status_rows: list[dict], game_start_time: str | None,
               fetched_at: dt.datetime) -> tuple[bool, str, str]:
    """Return (lineup_confirmed, lineup_complete_status, lineup_blocker)."""
    if not status_rows:
        return False, "unavailable", (
            "no rows returned by BDL lineups endpoint (lineups not posted yet)"
        )
    teams = sorted({r.get("team_id") for r in status_rows if r.get("team_id")})
    if len(teams) < 2:
        return False, "partial", (
            f"only {len(teams)} team(s) present in lineup response; expected 2"
        )
    starters_per_team = Counter(
        r["team_id"] for r in status_rows if r.get("starter") is True
    )
    bad = {
        tid: starters_per_team.get(tid, 0)
        for tid in teams
        if starters_per_team.get(tid, 0) != 5
    }
    if bad:
        return False, "partial", (
            f"each team must have 5 starter=True rows; observed counts: "
            f"{dict(starters_per_team)}"
        )
    # Must have been fetched before game start when start time is known.
    if game_start_time:
        try:
            gs = dt.datetime.fromisoformat(game_start_time.replace("Z", "+00:00"))
            if gs.tzinfo is None:
                gs = gs.replace(tzinfo=dt.timezone.utc)
            if fetched_at >= gs:
                return False, "stale", (
                    f"fetched_at_utc={_utc_iso(fetched_at)} is at-or-after "
                    f"game_start_time_utc={game_start_time}; refusing to claim "
                    "confirmed lineup with post-tip data"
                )
        except Exception:
            # If we can't parse the start time we don't downgrade — the
            # missing-fetch-time case should have already been classified
            # by an upstream check.
            pass
    return True, "complete", ""


def _write_status_md(out_dir: Path, status: dict) -> None:
    md = [
        f"# BDL Lineup Status — game {status['game_id']} ({status['delivery_date']})",
        "",
        f"- source: `{status['source']}`",
        f"- fetched_at_utc: `{status['fetched_at_utc']}`",
        f"- lineup_confirmed: **{status['lineup_confirmed']}**",
        f"- lineup_complete: **{status['lineup_complete']}**",
        f"- lineup_blocker: {status['lineup_blocker']!r}",
        f"- teams_present: {status['teams_present']}",
        f"- starter_count_by_team: {status['starter_count_by_team']}",
        f"- bench_count_by_team: {status['bench_count_by_team']}",
        f"- total_rows: {status['total_rows']}",
        f"- lineup_hash: `{status['lineup_hash']}`",
        "",
        "## Starters",
        "",
        "| team_id | player_id | player_name | position |",
        "| --- | --- | --- | --- |",
    ]
    for s in status["starters"]:
        md.append(
            f"| {s.get('team_id')} | {s.get('player_id')} | "
            f"{s.get('player_name')} | {s.get('lineup_position')} |"
        )
    md += [
        "",
        "## Bench",
        "",
        "| team_id | player_id | player_name | position |",
        "| --- | --- | --- | --- |",
    ]
    for b in status["bench_players"]:
        md.append(
            f"| {b.get('team_id')} | {b.get('player_id')} | "
            f"{b.get('player_name')} | {b.get('lineup_position')} |"
        )
    (out_dir / "lineup_status.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _status_from_fetch_failure(
    *,
    delivery_date: str,
    game_id: str,
    fetched_at_iso: str,
    bdl_fetch_status: str,
    http_status: int | None,
    error: str | None,
) -> dict:
    """Build the on-disk lineup_status payload for a fetch-failure outcome.

    Covers ``endpoint_misconfigured`` / ``auth_failed`` / ``request_failed``.
    The structured ``bdl_fetch_status`` lets downstream consumers
    distinguish a real BDL routing problem from a legitimate
    "lineups_not_posted_yet" empty response.
    """
    if bdl_fetch_status == "endpoint_misconfigured":
        blocker = "endpoint_misconfigured: HTTP 404 from BDL /v1/lineups"
    elif bdl_fetch_status == "auth_failed":
        blocker = f"auth_failed: HTTP {http_status}"
    else:
        blocker = f"request_failed: {error}"
    return {
        "schema_version": "1.1",
        "delivery_date": delivery_date,
        "game_id": str(game_id),
        "source": SOURCE_TAG,
        "fetched_at_utc": fetched_at_iso,
        "bdl_fetch_status": bdl_fetch_status,
        "bdl_http_status": http_status,
        "bdl_fetch_error": error,
        "lineup_confirmed": False,
        "lineup_complete": "fetch_failed",
        "lineup_blocker": blocker,
        "teams_present": [],
        "starter_count_by_team": {},
        "bench_count_by_team": {},
        "total_rows": 0,
        "starters": [],
        "bench_players": [],
        "unmapped_players": [],
        "lineup_hash": "",
    }


def fetch_one(delivery_date: str, game_id: str) -> dict:
    """Fetch + persist lineup artifacts for a single game; returns status dict.

    Calls ``bdl_client.get_lineups_status([game_id])`` and maps the
    structured ``status`` field to the on-disk ``bdl_fetch_status`` /
    ``lineup_complete`` / ``lineup_blocker`` triple.  HTTP-200 outcomes
    proceed through the existing ``_classify`` flow; non-200 outcomes
    short-circuit with an explicit fetch-failure status payload.
    """
    out_dir = LIVE_LINEUPS_DIR / delivery_date / str(game_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    fetched_at = _utcnow()
    fetched_at_iso = _utc_iso(fetched_at)

    fetch_result = get_lineups_status([int(game_id)])
    bdl_fetch_status = fetch_result.get("status") or "request_failed"
    http_status = fetch_result.get("http_status")
    error_text = fetch_result.get("error")
    raw = fetch_result.get("rows") or []

    (out_dir / "bdl_lineups_raw.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    if bdl_fetch_status in BDL_FETCH_STATUS_FAIL:
        status = _status_from_fetch_failure(
            delivery_date=delivery_date,
            game_id=game_id,
            fetched_at_iso=fetched_at_iso,
            bdl_fetch_status=bdl_fetch_status,
            http_status=http_status,
            error=error_text,
        )
        (out_dir / "lineup_status.json").write_text(
            json.dumps(status, indent=2, sort_keys=True), encoding="utf-8"
        )
        _write_status_md(out_dir, status)
        return status

    # HTTP 200 path — empty array is a legitimate pre-confirmation outcome.
    norm = [_normalize_row(r, game_id, fetched_at_iso) for r in raw]
    try:
        import pandas as pd
        df = pd.DataFrame(norm)
        df.to_csv(out_dir / "bdl_lineups_normalized.csv", index=False)
        df.to_parquet(out_dir / "bdl_lineups_normalized.parquet", index=False)
    except Exception:
        # Even if pandas is unavailable, JSON and status remain authoritative.
        pass

    starters = [r for r in norm if r.get("starter") is True]
    bench = [r for r in norm if r.get("starter") is False]
    starter_counts = Counter(r["team_id"] for r in starters)
    bench_counts = Counter(r["team_id"] for r in bench)
    teams_present = sorted({r.get("team_id") for r in norm if r.get("team_id")})

    game_start = _load_game_start_time(delivery_date, game_id)
    confirmed, complete, blocker = _classify(norm, game_start, fetched_at)

    if bdl_fetch_status == "confirmed_lineups_not_available_yet":
        # Override the legacy "no rows returned ... lineups not posted yet"
        # string with the canonical bdl_fetch_status token so downstream
        # consumers don't have to string-match a humanized sentence.
        blocker = "confirmed_lineups_not_available_yet"

    status = {
        "schema_version": "1.1",
        "delivery_date": delivery_date,
        "game_id": str(game_id),
        "source": SOURCE_TAG,
        "fetched_at_utc": fetched_at_iso,
        "bdl_fetch_status": bdl_fetch_status,
        "bdl_http_status": http_status,
        "bdl_fetch_error": error_text,
        "game_start_time_utc": game_start,
        "lineup_confirmed": confirmed,
        "lineup_complete": complete,
        "lineup_blocker": blocker,
        "teams_present": teams_present,
        "starter_count_by_team": {str(k): int(v) for k, v in starter_counts.items()},
        "bench_count_by_team": {str(k): int(v) for k, v in bench_counts.items()},
        "total_rows": len(norm),
        "starters": [
            {k: r.get(k) for k in (
                "team_id", "team_abbreviation", "player_id", "player_name",
                "lineup_position", "player_position",
            )} for r in starters
        ],
        "bench_players": [
            {k: r.get(k) for k in (
                "team_id", "team_abbreviation", "player_id", "player_name",
                "lineup_position", "player_position",
            )} for r in bench
        ],
        # Phase 13M does not wire BDL→model player_id mapping (BDL ids are
        # the native model id universe per Phase 13M scout).  If a future
        # phase introduces a mapping this list captures unmapped ids.
        "unmapped_players": [],
        "lineup_hash": _hash_lineup(norm),
    }
    (out_dir / "lineup_status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True), encoding="utf-8"
    )
    _write_status_md(out_dir, status)
    return status


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fetch BDL confirmed lineups.")
    p.add_argument("--delivery-date", required=True, help="YYYY-MM-DD")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--game-id", help="Single BDL game_id")
    g.add_argument("--game-ids", help="Comma-separated BDL game_ids")
    args = p.parse_args(argv)

    if not os.environ.get("BDL_API_KEY", "").strip():
        print("BDL_LINEUPS_FETCH_FAILED", file=sys.stderr)
        print("  reason: BDL_API_KEY env var is not set", file=sys.stderr)
        return 1

    if args.game_id:
        ids = [args.game_id.strip()]
    else:
        ids = [s.strip() for s in args.game_ids.split(",") if s.strip()]

    statuses: list[dict] = []
    for gid in ids:
        try:
            statuses.append(fetch_one(args.delivery_date, gid))
        except Exception as exc:
            print("BDL_LINEUPS_FETCH_FAILED", file=sys.stderr)
            print(f"  reason: game_id={gid} fetch raised: {exc}", file=sys.stderr)
            return 1

    # Any HTTP non-200 outcome (endpoint_misconfigured / auth_failed /
    # request_failed) is a hard failure.  Mixed HTTP-200 outcomes of
    # `lineups_available` and `confirmed_lineups_not_available_yet` are
    # both legitimate pass states (the latter is normal for a morning run
    # before lineups are posted).
    failing = [
        st for st in statuses if st.get("bdl_fetch_status") in BDL_FETCH_STATUS_FAIL
    ]
    if failing:
        print("BDL_LINEUPS_FETCH_FAILED", file=sys.stderr)
        for st in failing:
            print(
                f"  - game_id={st['game_id']}  "
                f"bdl_fetch_status={st['bdl_fetch_status']}  "
                f"http_status={st.get('bdl_http_status')}  "
                f"blocker={st['lineup_blocker']}",
                file=sys.stderr,
            )
        return 1

    print("BDL_LINEUPS_FETCH_PASS")
    print(f"  delivery_date={args.delivery_date} games_fetched={len(statuses)}")
    for st in statuses:
        print(
            f"  - game_id={st['game_id']}  "
            f"bdl_fetch_status={st.get('bdl_fetch_status')}  "
            f"lineup_confirmed={st['lineup_confirmed']}  "
            f"complete={st['lineup_complete']}  total_rows={st['total_rows']}  "
            f"hash={st['lineup_hash'] or '(empty)'}"
        )
        if not st["lineup_confirmed"]:
            print(f"    blocker: {st['lineup_blocker']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
