"""Phase 13U Part D — enrich predictions/all_props_<date>.parquet with
real game_start_time metadata.

Reads the resolver output (from
``artifacts/live_schedule/<date>/game_start_times.json`` if present;
otherwise re-resolves) and writes back to
``predictions/all_props_<date>.parquet`` ONLY the metadata columns:

    game_start_time
    game_start_time_source
    game_start_time_resolution_confidence

A backup of the parquet file is written before mutation:

    predictions/all_props_<date>.pre_game_time_enrichment_backup.parquet

PMF / odds / probabilities / quantiles are not modified.

Pass / pending / fail lines:
    PREDICTION_GAME_START_TIME_ENRICHMENT_PASS
    PREDICTION_GAME_START_TIME_ENRICHMENT_PENDING
    PREDICTION_GAME_START_TIME_ENRICHMENT_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.schedule.game_start_times import (  # noqa: E402
    GameStartTimeResolver,
)


def _hash_file(p: Path) -> str:
    import hashlib
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    p.add_argument("--no-backup", action="store_true",
                   help="Skip the safety backup (used when the parquet is "
                        "checked in via git history).")
    args = p.parse_args(argv)

    pred = REPO_ROOT / "predictions" / f"all_props_{args.delivery_date}.parquet"
    out_dir = REPO_ROOT / "artifacts" / "live_schedule" / args.delivery_date
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pred.exists():
        report = {
            "schema_version": "1.0",
            "delivery_date": args.delivery_date,
            "outcome": "pending",
            "blocker": f"predictions parquet missing: {pred.relative_to(REPO_ROOT)}",
        }
        (out_dir / "prediction_game_time_enrichment.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print("PREDICTION_GAME_START_TIME_ENRICHMENT_PENDING")
        print(f"  reason={report['blocker']}")
        return 0

    import pandas as pd
    df = pd.read_parquet(pred)
    pre_hash = _hash_file(pred)
    pre_rows = int(len(df))
    pre_cols = list(df.columns)

    # Resolve.
    resolver = GameStartTimeResolver(repo_root=REPO_ROOT)
    records, telemetry = resolver.resolve(args.delivery_date)
    resolved_map = {
        r.game_id: r for r in records if r.resolved_game_start_time_utc
    }
    if not resolved_map:
        report = {
            "schema_version": "1.0",
            "delivery_date": args.delivery_date,
            "outcome": "pending",
            "blocker": (
                "no real source resolved any tip time; resolver telemetry "
                f"= {telemetry}"
            ),
            "telemetry": telemetry,
        }
        (out_dir / "prediction_game_time_enrichment.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, default=str),
            encoding="utf-8")
        print("PREDICTION_GAME_START_TIME_ENRICHMENT_PENDING")
        print(f"  reason={report['blocker']}")
        return 0

    if not args.no_backup:
        backup = REPO_ROOT / "predictions" / (
            f"all_props_{args.delivery_date}"
            ".pre_game_time_enrichment_backup.parquet"
        )
        if not backup.exists():
            shutil.copy2(pred, backup)

    # Add / overwrite the three metadata columns. PMF / model
    # probability / odds columns are NOT touched.
    gid_str = df["game_id"].astype(str)
    df["game_start_time"] = gid_str.map(
        lambda g: resolved_map[g].resolved_game_start_time_utc
        if g in resolved_map else None
    )
    df["game_start_time_source"] = gid_str.map(
        lambda g: resolved_map[g].source_used if g in resolved_map else "unresolved"
    )
    df["game_start_time_resolution_confidence"] = gid_str.map(
        lambda g: resolved_map[g].source_confidence
        if g in resolved_map else "unresolved"
    )

    df.to_parquet(pred, index=False)
    post_hash = _hash_file(pred)
    post_rows = int(len(df))
    post_cols = list(df.columns)

    report = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "outcome": "pass",
        "pre_hash": pre_hash,
        "post_hash": post_hash,
        "pre_rows": pre_rows,
        "post_rows": post_rows,
        "rows_changed": pre_rows != post_rows,
        "added_columns": [
            c for c in post_cols if c not in pre_cols
        ],
        "resolved_games": list(resolved_map.keys()),
        "resolved_count": len(resolved_map),
        "telemetry": telemetry,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0).isoformat() + "Z",
    }
    (out_dir / "prediction_game_time_enrichment.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8")
    md = [
        f"# Predictions enrichment — {args.delivery_date}",
        "",
        f"- generated_at_utc: {report['generated_at_utc']}",
        f"- pre_hash: `{pre_hash}`",
        f"- post_hash: `{post_hash}`",
        f"- pre_rows: {pre_rows}",
        f"- post_rows: {post_rows}",
        f"- rows_changed: **{report['rows_changed']}**",
        f"- added_columns: {report['added_columns']}",
        f"- resolved_games: {report['resolved_games']}",
    ]
    (out_dir / "prediction_game_time_enrichment.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    print("PREDICTION_GAME_START_TIME_ENRICHMENT_PASS")
    print(
        f"  delivery_date={args.delivery_date} "
        f"resolved={len(resolved_map)} pre_hash={pre_hash} post_hash={post_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
