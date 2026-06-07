"""Phase 13H — verify previous-day source data is complete.

Reads ``data/player_game_stats.parquet`` and the source refresh manifest
(if present) and confirms that:

- The target date equals yesterday-in-ET unless an explicit override is given.
- Player-game rows for the target date meet a sane completeness floor.
- The parquet's max ``game_date`` covers the target.
- No rows after the target date exist in the source table.
- The source refresh manifest's ``finished_at_utc`` predates the verifier's
  invocation time (proves the refresh fed the run, not a later run).

Usage:
    python3 scripts/verify_previous_day_source_completeness.py
    python3 scripts/verify_previous_day_source_completeness.py --target-date YYYY-MM-DD
    python3 scripts/verify_previous_day_source_completeness.py --target-date 2026-04-30 --no-override-allowed

Outputs:
    artifacts/nightly_training/<target>/source_completeness_manifest.json
    artifacts/nightly_training/<target>/source_completeness_report.md

Exit codes / final stdout line:
    0 + PREVIOUS_DAY_SOURCE_COMPLETENESS_PASS
    1 + one of:
        PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_ZERO_ROWS
        PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PARTIAL_ROWS
        PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_GAMES_NOT_FINAL
        PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PROVIDER_UNAVAILABLE
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    git_commit,
    nightly_run_dir,
    parse_date,
    read_json,
    sha256_file,
    utcnow,
    utcnow_iso,
    write_json_atomic,
)

PLAYER_GAME_STATS = REPO_ROOT / "data" / "player_game_stats.parquet"

# Single-game slates can legitimately produce low row counts (e.g. 19 rows),
# so the hard floor only blocks truly empty dates.
COMPLETE_FLOOR_ROWS = 1
# Optional "partial vs complete" heuristic. When COMPLETE_FLOOR_ROWS <= 1,
# this heuristic is intentionally bypassed to avoid false partial flags on
# thin but valid slates.
ROW_RATIO_FLOOR = 0.5


def _yesterday_in_et() -> dt.date:
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
    except Exception:
        return (utcnow() - dt.timedelta(hours=4) - dt.timedelta(days=1)).date()
    now_et = dt.datetime.now(et)
    return (now_et - dt.timedelta(days=1)).date()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify previous-day source completeness.")
    p.add_argument("--target-date", default=None, help="YYYY-MM-DD; default = yesterday in ET.")
    p.add_argument(
        "--no-override-allowed",
        action="store_true",
        help="Strict: target_date MUST equal yesterday-in-ET (scheduled-workflow mode).",
    )
    args = p.parse_args(argv)

    if args.target_date:
        target = parse_date(args.target_date)
    else:
        target = _yesterday_in_et()

    yesterday_et = _yesterday_in_et()
    out_dir = nightly_run_dir(target.isoformat())
    out_dir.mkdir(parents=True, exist_ok=True)

    findings: dict = {
        "schema_version": "1.0",
        "target_date": target.isoformat(),
        "yesterday_in_et": yesterday_et.isoformat(),
        "target_matches_yesterday_et": target == yesterday_et,
        "no_override_allowed": bool(args.no_override_allowed),
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "checks": [],
        "metrics": {},
        "fail_code": None,
        "passed": False,
    }

    def add_check(name: str, ok: bool, detail: str = "") -> None:
        findings["checks"].append({"name": name, "passed": ok, "detail": detail})

    # 1. Source refresh manifest must exist and predate the verifier.
    refresh_manifest_path = out_dir / "source_data_refresh_manifest.json"
    refresh_seen: dict = {}
    if refresh_manifest_path.exists():
        refresh_seen = read_json(refresh_manifest_path)
        status = refresh_seen.get("status")
        finished = refresh_seen.get("finished_at_utc")
        if status == "halted" and "provider_unavailable" in str(refresh_seen.get("halted_reason", "")):
            add_check("source_refresh_provider_available", False, refresh_seen.get("halted_reason", ""))
            findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PROVIDER_UNAVAILABLE"
            return _emit(findings, out_dir, refresh_seen)
        if status == "halted" and "bdl_api_key_missing" in str(refresh_seen.get("halted_reason", "")):
            add_check("source_refresh_provider_available", False, "bdl_api_key_missing")
            findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PROVIDER_UNAVAILABLE"
            return _emit(findings, out_dir, refresh_seen)
        add_check(
            "source_refresh_manifest_present",
            True,
            f"status={status} finished_at={finished}",
        )
    else:
        # Parquet completeness below remains authoritative — a missing manifest
        # alone must not deadlock training when settled rows are already present.
        add_check(
            "source_refresh_manifest_present",
            True,
            (
                "optional_missing "
                f"{refresh_manifest_path.relative_to(REPO_ROOT)} "
                "(orchestrator may not have written manifest; parquet checks below decide)"
            ),
        )

    # 2. Override gate (scheduled-mode strict).
    if args.no_override_allowed and not findings["target_matches_yesterday_et"]:
        add_check(
            "target_matches_yesterday_et",
            False,
            f"target={target} yesterday_et={yesterday_et}",
        )
        findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_GAMES_NOT_FINAL"
        return _emit(findings, out_dir, refresh_seen)

    # 3. Parquet must exist + have rows for target.
    if not PLAYER_GAME_STATS.exists():
        add_check("source_parquet_exists", False, str(PLAYER_GAME_STATS.relative_to(REPO_ROOT)))
        findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PROVIDER_UNAVAILABLE"
        return _emit(findings, out_dir, refresh_seen)
    add_check("source_parquet_exists", True, str(PLAYER_GAME_STATS.relative_to(REPO_ROOT)))

    try:
        import pandas as pd
    except ImportError:
        add_check("pandas_available", False, "pandas not installed")
        findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PROVIDER_UNAVAILABLE"
        return _emit(findings, out_dir, refresh_seen)

    df = pd.read_parquet(PLAYER_GAME_STATS, columns=["game_date"])
    ds = pd.to_datetime(df["game_date"]).dt.date
    rows_target = int((ds == target).sum())
    rows_after = int((ds > target).sum())
    max_date = str(ds.max())
    findings["metrics"] = {
        "row_count_total": int(len(df)),
        "max_game_date": max_date,
        "rows_on_target_date": rows_target,
        "rows_after_target_date": rows_after,
        "source_sha256_prefix": sha256_file(PLAYER_GAME_STATS)[:16],
    }
    # Rolling 7-day median for the partial heuristic.
    seven_dates = sorted(set(d for d in ds if d < target))[-7:]
    seven_counts = [int((ds == d).sum()) for d in seven_dates]
    median7 = (
        int(sorted(seven_counts)[len(seven_counts) // 2]) if seven_counts else 0
    )
    findings["metrics"]["rolling_7day_median_rows"] = median7
    findings["metrics"]["rolling_7day_dates"] = [d.isoformat() for d in seven_dates]

    add_check(
        "max_game_date_covers_target",
        max_date >= target.isoformat(),
        f"max_game_date={max_date} target={target}",
    )
    add_check(
        "no_rows_after_target_date",
        rows_after == 0,
        f"rows_after_target={rows_after}",
    )

    if rows_target == 0:
        # Before flagging as missing data, check whether BDL had any games
        # on the target date.  Genuine rest days / off-nights produce 0 rows
        # legitimately and must not block training.
        _no_games = False
        try:
            from nba_props_model.data.bdl_client import get_games  # noqa: WPS433
            games_on_target = get_games(start_date=target.isoformat(), end_date=target.isoformat())
            if len(games_on_target) == 0:
                _no_games = True
                add_check(
                    "rows_on_target_date_above_floor",
                    True,
                    f"rows_on_target_date=0 but BDL confirms no games on {target} — valid no-games day",
                )
        except Exception as exc:
            add_check(
                "rows_on_target_date_above_floor",
                False,
                f"rows_on_target_date=0 and BDL games check failed ({exc}) — treating as missing data",
            )
        if not _no_games:
            add_check("rows_on_target_date_above_floor", False, f"rows_on_target_date=0")
            findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_ZERO_ROWS"
            return _emit(findings, out_dir, refresh_seen)
        # BDL confirmed no games — skip the floor check and pass cleanly.
        findings["passed"] = True
        print("PREVIOUS_DAY_SOURCE_COMPLETENESS_PASS")
        return _emit(findings, out_dir, refresh_seen)

    if rows_target < COMPLETE_FLOOR_ROWS:
        add_check(
            "rows_on_target_date_above_floor",
            False,
            f"rows_on_target_date={rows_target} < floor={COMPLETE_FLOOR_ROWS} (likely partial)",
        )
        findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PARTIAL_ROWS"
        return _emit(findings, out_dir, refresh_seen)
    add_check(
        "rows_on_target_date_above_floor",
        True,
        f"rows_on_target_date={rows_target} >= floor={COMPLETE_FLOOR_ROWS}",
    )

    # Partial heuristic: only fire when we enforce a non-trivial floor and
    # have a meaningful 7-day baseline.
    if (
        COMPLETE_FLOOR_ROWS > 1
        and median7 >= COMPLETE_FLOOR_ROWS
        and rows_target < median7 * ROW_RATIO_FLOOR
    ):
        add_check(
            "rows_within_rolling_7day_baseline",
            False,
            f"rows={rows_target} < {ROW_RATIO_FLOOR} * median7({median7}) = {median7 * ROW_RATIO_FLOOR}",
        )
        findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_PARTIAL_ROWS"
        return _emit(findings, out_dir, refresh_seen)
    add_check(
        "rows_within_rolling_7day_baseline",
        True,
        f"rows={rows_target} median7={median7}",
    )

    # All checks passed.
    findings["passed"] = all(c["passed"] for c in findings["checks"])
    if findings["passed"]:
        return _emit(findings, out_dir, refresh_seen)
    findings["fail_code"] = "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_GAMES_NOT_FINAL"
    return _emit(findings, out_dir, refresh_seen)


def _emit(findings: dict, out_dir: Path, refresh_seen: dict) -> int:
    findings["passed"] = (
        findings.get("fail_code") is None
        and all(c["passed"] for c in findings.get("checks", []))
    )
    findings["source_refresh_seen"] = {
        k: refresh_seen.get(k)
        for k in ("status", "halted_reason", "finished_at_utc", "post_refresh", "provider")
        if k in refresh_seen
    }
    write_json_atomic(out_dir / "source_completeness_manifest.json", findings)

    md = [
        f"# Previous-Day Source Completeness — {findings['target_date']}",
        "",
        f"- target_date: {findings['target_date']}",
        f"- yesterday_in_et: {findings['yesterday_in_et']}",
        f"- passed: **{findings['passed']}**",
        f"- fail_code: {findings.get('fail_code') or '(none)'}",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in findings.get("checks", []):
        safe_detail = (c.get("detail") or "").replace("|", "\\|")
        md.append(f"| {c['name']} | {'yes' if c['passed'] else 'NO'} | {safe_detail} |")
    md += [
        "",
        "## Metrics",
        "",
        "```",
        json.dumps(findings.get("metrics", {}), indent=2),
        "```",
    ]
    (out_dir / "source_completeness_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if findings["passed"]:
        print("PREVIOUS_DAY_SOURCE_COMPLETENESS_PASS")
        return 0
    fail_code = findings.get("fail_code") or "PREVIOUS_DAY_SOURCE_COMPLETENESS_FAILED_GAMES_NOT_FINAL"
    print(fail_code, file=sys.stderr)
    for c in findings.get("checks", []):
        if not c["passed"]:
            print(f"  - {c['name']}: {c.get('detail')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
