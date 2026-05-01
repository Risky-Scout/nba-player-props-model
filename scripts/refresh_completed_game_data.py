"""Phase 13H — refresh completed-game source data through a target date.

Wraps ``scripts/refresh_bdl_player_game_stats.py`` with manifest output and
strict failure semantics so the nightly orchestrator can:

  1. Identify the target date (yesterday in America/New_York by default).
  2. Refresh ``data/player_game_stats.parquet`` from the BDL API up through
     that date.
  3. Record the refresh provenance (provider, fetch timestamps, row counts,
     date coverage, file hash).
  4. Halt with ``source_data_refresh_failed`` if BDL credentials are
     unavailable or the refresh subprocess fails.

Usage:
    python3 scripts/refresh_completed_game_data.py
    python3 scripts/refresh_completed_game_data.py --target-date YYYY-MM-DD

Outputs:
    artifacts/nightly_training/<target_date>/source_data_refresh_manifest.json
    artifacts/nightly_training/<target_date>/source_data_refresh_report.md

Hard rules:
- Never marks partial games as complete (the BDL refresh script appends
  finalized rows only).
- Never overwrites the production ``data/player_game_stats.parquet`` outside
  this single explicit append-and-merge step.
- Records a SHA256 over the resulting parquet so downstream gates can prove
  what they consumed.
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
    nightly_run_dir,
    parse_date,
    sha256_file,
    utcnow,
    utcnow_iso,
    write_json_atomic,
)

PLAYER_GAME_STATS = REPO_ROOT / "data" / "player_game_stats.parquet"
BDL_REFRESH_SCRIPT = REPO_ROOT / "scripts" / "refresh_bdl_player_game_stats.py"


def _yesterday_in_et() -> dt.date:
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
    except Exception:
        return (utcnow() - dt.timedelta(hours=4) - dt.timedelta(days=1)).date()
    now_et = dt.datetime.now(et)
    return (now_et - dt.timedelta(days=1)).date()


def _stat_parquet(target: dt.date) -> dict:
    out: dict = {
        "path": str(PLAYER_GAME_STATS.relative_to(REPO_ROOT)),
        "exists": PLAYER_GAME_STATS.exists(),
    }
    if not PLAYER_GAME_STATS.exists():
        return out
    out["size_bytes"] = PLAYER_GAME_STATS.stat().st_size
    out["mtime_utc"] = (
        dt.datetime.fromtimestamp(PLAYER_GAME_STATS.stat().st_mtime, tz=dt.timezone.utc).isoformat()
    )
    out["sha256_prefix"] = sha256_file(PLAYER_GAME_STATS)[:16]
    try:
        import pandas as pd
        df = pd.read_parquet(PLAYER_GAME_STATS, columns=["game_date"])
        ds = pd.to_datetime(df["game_date"]).dt.date
        out["row_count"] = int(len(df))
        out["max_game_date"] = str(ds.max())
        out["rows_on_target_date"] = int((ds == target).sum())
        out["rows_after_target_date"] = int((ds > target).sum())
        # Last 5 dates for visibility.
        last = ds.value_counts().sort_index(ascending=False).head(5).to_dict()
        out["recent_date_row_counts"] = {str(k): int(v) for k, v in last.items()}
    except Exception as exc:
        out["error_inspecting"] = str(exc)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Refresh completed-game source data.")
    p.add_argument(
        "--target-date",
        default=None,
        help="YYYY-MM-DD; default = yesterday in America/New_York.",
    )
    p.add_argument(
        "--skip-if-fresh",
        action="store_true",
        help="Skip the BDL fetch if the parquet's max_game_date already covers target.",
    )
    args = p.parse_args(argv)

    if args.target_date:
        target = parse_date(args.target_date)
    else:
        target = _yesterday_in_et()

    out_dir = nightly_run_dir(target.isoformat())
    out_dir.mkdir(parents=True, exist_ok=True)

    started_at = utcnow_iso()
    pre_state = _stat_parquet(target)

    manifest: dict = {
        "schema_version": "1.0",
        "target_date": target.isoformat(),
        "target_policy": "yesterday_america_new_york",
        "started_at_utc": started_at,
        "code_commit": git_commit(),
        "provider": "balldontlie.io",
        "fetcher": str(BDL_REFRESH_SCRIPT.relative_to(REPO_ROOT)),
        "pre_refresh": pre_state,
        "post_refresh": None,
        "subprocess": None,
        "status": "ok",
        "halted_reason": None,
    }

    api_key = os.environ.get("BDL_API_KEY")
    if not api_key:
        manifest["status"] = "halted"
        manifest["halted_reason"] = "source_data_refresh_failed:bdl_api_key_missing"
        manifest["finished_at_utc"] = utcnow_iso()
        write_json_atomic(out_dir / "source_data_refresh_manifest.json", manifest)
        _write_md(out_dir, manifest)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "halted_reason": manifest["halted_reason"],
                    "target_date": target.isoformat(),
                }
            ),
            file=sys.stderr,
        )
        return 1

    if not BDL_REFRESH_SCRIPT.exists():
        manifest["status"] = "halted"
        manifest["halted_reason"] = "source_data_refresh_failed:fetcher_script_missing"
        manifest["finished_at_utc"] = utcnow_iso()
        write_json_atomic(out_dir / "source_data_refresh_manifest.json", manifest)
        _write_md(out_dir, manifest)
        return 1

    if args.skip_if_fresh:
        max_date = pre_state.get("max_game_date")
        if max_date and max_date >= target.isoformat() and pre_state.get("rows_on_target_date", 0) > 0:
            manifest["status"] = "skipped_already_fresh"
            manifest["post_refresh"] = pre_state
            manifest["finished_at_utc"] = utcnow_iso()
            write_json_atomic(out_dir / "source_data_refresh_manifest.json", manifest)
            _write_md(out_dir, manifest)
            print(json.dumps({"status": "skipped_already_fresh", "target_date": target.isoformat()}))
            return 0

    cmd = [
        sys.executable,
        str(BDL_REFRESH_SCRIPT.relative_to(REPO_ROOT)),
        "--end-date",
        target.isoformat(),
    ]
    log_path = out_dir / "source_data_refresh.log"
    t0 = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"$ {' '.join(cmd)}\n\n")
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            stdout=f,
            stderr=subprocess.STDOUT,
            check=False,
            env={**os.environ},
        )
    elapsed = time.perf_counter() - t0
    manifest["subprocess"] = {
        "command": cmd,
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 1),
        "log_path": str(log_path.relative_to(REPO_ROOT)),
    }

    if proc.returncode != 0:
        manifest["status"] = "halted"
        manifest["halted_reason"] = f"source_data_refresh_failed:fetcher_exit_{proc.returncode}"
        manifest["finished_at_utc"] = utcnow_iso()
        write_json_atomic(out_dir / "source_data_refresh_manifest.json", manifest)
        _write_md(out_dir, manifest)
        print(
            json.dumps({"status": "halted", "halted_reason": manifest["halted_reason"]}),
            file=sys.stderr,
        )
        return 1

    post_state = _stat_parquet(target)
    manifest["post_refresh"] = post_state
    manifest["finished_at_utc"] = utcnow_iso()

    # Strict-mode flag (if the orchestrator told us to fail-on-zero-rows).
    if post_state.get("rows_on_target_date", 0) == 0:
        manifest["status"] = "halted"
        manifest["halted_reason"] = "source_data_refresh_failed:zero_rows_for_target_after_refresh"
        write_json_atomic(out_dir / "source_data_refresh_manifest.json", manifest)
        _write_md(out_dir, manifest)
        print(
            json.dumps(
                {
                    "status": "halted",
                    "halted_reason": manifest["halted_reason"],
                    "target_date": target.isoformat(),
                }
            ),
            file=sys.stderr,
        )
        return 1

    write_json_atomic(out_dir / "source_data_refresh_manifest.json", manifest)
    _write_md(out_dir, manifest)
    print(
        json.dumps(
            {
                "status": "ok",
                "target_date": target.isoformat(),
                "rows_on_target_date": post_state.get("rows_on_target_date"),
                "max_game_date": post_state.get("max_game_date"),
            }
        )
    )
    return 0


def _write_md(out_dir: Path, manifest: dict) -> None:
    pre = manifest.get("pre_refresh") or {}
    post = manifest.get("post_refresh") or {}
    md = [
        f"# Source Data Refresh — {manifest['target_date']}",
        "",
        f"- status: **{manifest['status']}**",
        f"- halted_reason: {manifest.get('halted_reason') or '(none)'}",
        f"- provider: {manifest['provider']}",
        f"- started_at_utc: {manifest['started_at_utc']}",
        f"- finished_at_utc: {manifest.get('finished_at_utc')}",
        "",
        "## Parquet pre/post",
        "",
        "| Field | Pre | Post |",
        "| --- | --- | --- |",
        f"| row_count | {pre.get('row_count')} | {post.get('row_count')} |",
        f"| max_game_date | {pre.get('max_game_date')} | {post.get('max_game_date')} |",
        f"| rows_on_target_date | {pre.get('rows_on_target_date')} | {post.get('rows_on_target_date')} |",
        f"| sha256_prefix | {pre.get('sha256_prefix')} | {post.get('sha256_prefix')} |",
    ]
    (out_dir / "source_data_refresh_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
