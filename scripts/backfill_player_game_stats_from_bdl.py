#!/usr/bin/env python3
"""Phase 13AE — wrap ``scripts/refresh_bdl_player_game_stats.py`` with a
manifest output, idempotent dedupe verification, and the canonical
PLAYER_GAME_STATS_BACKFILL_PASS / _FAILED pass line.

The underlying refresh script already:
  - calls the BDL ``/nba/v1/stats`` endpoint
  - merges new rows into ``data/player_game_stats.parquet`` keyed on
    (game_id, player_id) — never fabricates outcomes
  - writes the merged table atomically
  - exits non-zero on API failure, missing key, or zero new rows

This wrapper:
  - takes ``--from-date`` / ``--to-date`` (inclusive)
  - runs the refresh
  - re-reads the parquet, validates dedup discipline, writes
    ``artifacts/automation_health/player_game_stats_freshness_<date>.json``
    and ``.md`` for the operator audit surface, where ``<date>`` is the
    ``--to-date``
  - emits a single PASS / FAIL line that captures the new max game_date,
    rows added, and any honest-fail reason
  - never fabricates rows; if BDL_API_KEY is missing or BDL returns
    zero rows, the parquet is left untouched and the script exits red

Hard rules (echoed):
  - No outcomes are invented.
  - No retraining is forced; this script is data-only.
  - When credentials are absent, the failure is loud and structured.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PARQUET = REPO_ROOT / "data" / "player_game_stats.parquet"
ART_DIR = REPO_ROOT / "artifacts" / "automation_health"
REFRESH_SCRIPT = REPO_ROOT / "scripts" / "refresh_bdl_player_game_stats.py"

DEDUP_KEY = ("game_id", "player_id")
REQUIRED_COLS = (
    "player_id", "player_name", "game_id", "game_date",
    "pts", "reb", "ast", "fg3m", "stl", "blk", "turnover", "min",
)


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _summarize(df: pd.DataFrame) -> dict:
    s = pd.to_datetime(df["game_date"], errors="coerce")
    duplicates = int(
        df.duplicated(subset=list(DEDUP_KEY), keep=False).sum()
    )
    null_keys = {
        c: int(df[c].isna().sum()) for c in REQUIRED_COLS if c in df.columns
    }
    return {
        "rows_total": int(len(df)),
        "min_game_date": str(s.min().date()) if not s.empty else None,
        "max_game_date": str(s.max().date()) if not s.empty else None,
        "duplicate_key_rows": duplicates,
        "null_counts": null_keys,
    }


def _write_freshness(date_label: str, payload: dict, out_md: Path,
                       out_json: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    md = [
        f"# Player game stats freshness — {date_label}",
        "",
        f"_Generated {payload.get('generated_at_utc')}._",
        "",
        f"- backfill window: **{payload.get('from_date')} → "
        f"{payload.get('to_date')}**",
        f"- status: **{payload.get('status')}**",
    ]
    summ = payload.get("summary") or {}
    if summ:
        md += [
            f"- total rows in parquet: **{summ.get('rows_total')}**",
            f"- min game_date: `{summ.get('min_game_date')}`",
            f"- max game_date: `{summ.get('max_game_date')}`",
            f"- duplicate (game_id, player_id) rows: "
            f"`{summ.get('duplicate_key_rows')}`",
        ]
    if payload.get("rows_added") is not None:
        md.append(f"- rows added by this run: **{payload.get('rows_added')}**")
    if payload.get("reason"):
        md += ["", f"## Reason", "", payload["reason"]]
    if payload.get("remediation"):
        md += ["", "## Remediation", "", payload["remediation"]]
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")


def _row_count_before() -> int:
    if not PARQUET.exists():
        return 0
    return int(len(pd.read_parquet(PARQUET, columns=["player_id"])))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-date", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--to-date", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--season", help="optional NBA season override (e.g. 2025)")
    args = ap.parse_args(argv)

    out_md = ART_DIR / f"player_game_stats_freshness_{args.to_date}.md"
    out_json = ART_DIR / f"player_game_stats_freshness_{args.to_date}.json"

    # Honest pre-flight: if BDL_API_KEY is absent we cannot fetch. Refuse
    # to run rather than emit a misleading PASS.
    api_key_set = bool(os.environ.get("BDL_API_KEY", "").strip())

    rows_before = _row_count_before()

    if not api_key_set:
        payload = {
            "schema_version": "1.0",
            "generated_at_utc": _utc_iso(),
            "from_date": args.from_date,
            "to_date": args.to_date,
            "status": "FAILED",
            "reason": "BDL_API_KEY environment variable is not set; refusing "
                       "to fabricate outcomes. The official refresh script "
                       "(scripts/refresh_bdl_player_game_stats.py) requires "
                       "this credential.",
            "remediation": "Run from CI where BDL_API_KEY is provisioned, "
                            "or export BDL_API_KEY locally before invoking "
                            "this script.",
            "summary": _summarize(pd.read_parquet(PARQUET)) if PARQUET.exists() else None,
            "rows_added": 0,
        }
        _write_freshness(args.to_date, payload, out_md, out_json)
        print(f"PLAYER_GAME_STATS_BACKFILL_FAILED  "
              f"from={args.from_date} to={args.to_date}  "
              f"reason=bdl_api_key_not_set", file=sys.stderr)
        return 1

    # Delegate to the canonical refresh script, restricted to the requested
    # window. The refresh script itself does idempotent (game_id, player_id)
    # merges and never fabricates rows.
    cmd = [
        sys.executable, str(REFRESH_SCRIPT),
        "--start-date", args.from_date,
        "--end-date", args.to_date,
    ]
    if args.season:
        cmd += ["--season", args.season]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    refresh_stdout = proc.stdout
    refresh_stderr = proc.stderr

    rows_after = _row_count_before()
    rows_added = max(0, rows_after - rows_before)

    if proc.returncode != 0:
        payload = {
            "schema_version": "1.0",
            "generated_at_utc": _utc_iso(),
            "from_date": args.from_date,
            "to_date": args.to_date,
            "status": "FAILED",
            "reason": (
                f"refresh_bdl_player_game_stats.py exited "
                f"{proc.returncode}: {(refresh_stderr or refresh_stdout)[-1000:]}"
            ),
            "rows_added": rows_added,
            "summary": _summarize(pd.read_parquet(PARQUET)) if PARQUET.exists() else None,
            "remediation": "Inspect refresh script log; common causes: rate "
                            "limit, transient API failure, season boundary "
                            "mismatch.",
        }
        _write_freshness(args.to_date, payload, out_md, out_json)
        print(f"PLAYER_GAME_STATS_BACKFILL_FAILED  "
              f"from={args.from_date} to={args.to_date}  "
              f"exit_code={proc.returncode}", file=sys.stderr)
        return 1

    df = pd.read_parquet(PARQUET)
    summary = _summarize(df)

    if summary["duplicate_key_rows"] > 0:
        payload = {
            "schema_version": "1.0",
            "generated_at_utc": _utc_iso(),
            "from_date": args.from_date,
            "to_date": args.to_date,
            "status": "FAILED",
            "reason": (
                f"parquet has {summary['duplicate_key_rows']} duplicate "
                f"(game_id, player_id) rows after refresh — dedup discipline "
                f"violated"
            ),
            "rows_added": rows_added,
            "summary": summary,
            "remediation": "Run scripts/refresh_bdl_player_game_stats.py with "
                            "--rebuild to rewrite the parquet from scratch.",
        }
        _write_freshness(args.to_date, payload, out_md, out_json)
        print(f"PLAYER_GAME_STATS_BACKFILL_FAILED  "
              f"reason=duplicate_keys count={summary['duplicate_key_rows']}",
              file=sys.stderr)
        return 1

    # SUCCESS — even when rows_added=0 because window had no NBA games.
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": _utc_iso(),
        "from_date": args.from_date,
        "to_date": args.to_date,
        "status": "PASS",
        "rows_added": rows_added,
        "summary": summary,
        "refresh_stdout_tail": refresh_stdout[-1000:],
    }
    _write_freshness(args.to_date, payload, out_md, out_json)
    print(f"PLAYER_GAME_STATS_BACKFILL_PASS  "
          f"from={args.from_date} to={args.to_date}  "
          f"rows_added={rows_added}  "
          f"max_game_date={summary['max_game_date']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
