#!/usr/bin/env python3
"""Audit predictions/stat_grid_{date}.parquet for mission-stat coverage and legacy TOV-only artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

MISSION_SET = frozenset(str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _classify(
    *,
    present: set[str],
    tov_only: bool,
    require_mission: bool,
) -> tuple[str, str, str]:
    """Return (possible_origin, recommended_action, pass_fail)."""
    if not present:
        return "unknown", "rebuild_with_full_mission_stats", "fail"
    if tov_only:
        return "legacy_tov_supplement", "rebuild_with_full_mission_stats", "fail"
    missing = sorted(MISSION_SET - present)
    if missing:
        if require_mission:
            return "partial_mission_grid", "rebuild_with_full_mission_stats", "fail"
        return "partial_mission_grid", "rebuild_with_full_mission_stats", "warn"
    return "full_mission_grid", "accept", "pass"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (used with default path)")
    ap.add_argument("--path", default=None, help="Override parquet path")
    ap.add_argument(
        "--require-mission-stats",
        action="store_true",
        help="Treat missing mission stats as diagnostic failure.",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / "model_diagnostics",
    )
    args = ap.parse_args()

    if args.path:
        p = Path(args.path)
        date_key = args.date or p.stem.replace("stat_grid_", "")[:10]
    elif args.date:
        date_key = str(args.date).strip()[:10]
        p = REPO_ROOT / "predictions" / f"stat_grid_{date_key}.parquet"
    else:
        print("FATAL: pass --date and/or --path", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"stat_grid_integrity_{date_key}"

    row: dict = {
        "date": date_key,
        "path": str(p),
        "file_exists": p.is_file(),
        "parquet_mtime_utc": None,
        "row_count": 0,
        "stat_counts": {},
        "mission_stats_present": [],
        "mission_stats_missing": [],
        "player_count_by_stat": {},
        "pairs_by_stat": {},
        "tov_only_artifact": False,
        "possible_origin": "unknown",
        "recommended_action": "fail",
        "require_mission_stats": bool(args.require_mission_stats),
        "diagnosed_at_utc": _iso_now(),
    }

    per_stat_rows: list[dict] = []

    if not p.is_file():
        row["possible_origin"] = "unknown"
        row["recommended_action"] = "rebuild_with_full_mission_stats"
        origin, action, pf = _classify(present=set(), tov_only=False, require_mission=args.require_mission_stats)
        row["possible_origin"] = origin
        row["recommended_action"] = action
        row["contract_hint"] = pf
    else:
        st = p.stat()
        row["parquet_mtime_utc"] = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
        df = pd.read_parquet(p)
        row["row_count"] = int(len(df))
        if "stat" not in df.columns:
            print("FATAL: stat column missing", file=sys.stderr)
            return 2
        vc = df["stat"].astype(str).str.lower().value_counts()
        counts = {str(k): int(v) for k, v in vc.items()}
        row["stat_counts"] = counts
        present = set(counts.keys())
        tov_only = present == {"tov"} and counts.get("tov", 0) > 0
        row["tov_only_artifact"] = bool(tov_only)
        miss = sorted(MISSION_SET - present)
        row["mission_stats_present"] = sorted(MISSION_SET & present)
        row["mission_stats_missing"] = miss
        key_cols = [c for c in ("player_id", "game_id") if c in df.columns]
        if key_cols:
            for stat, sub in df.groupby(df["stat"].astype(str).str.lower()):
                row["player_count_by_stat"][stat] = int(sub["player_id"].nunique()) if "player_id" in sub.columns else 0
                row["pairs_by_stat"][stat] = int(
                    sub[key_cols].drop_duplicates().shape[0]
                )
        origin, action, pf = _classify(
            present=present,
            tov_only=tov_only,
            require_mission=args.require_mission_stats,
        )
        row["possible_origin"] = origin
        row["recommended_action"] = action
        row["contract_hint"] = pf
        for stat in sorted(MISSION_SET | present):
            per_stat_rows.append(
                {
                    "date": date_key,
                    "stat": stat,
                    "row_count": int(counts.get(stat, 0)),
                    "is_mission": stat in MISSION_SET,
                    "n_players": row["player_count_by_stat"].get(stat, 0),
                    "n_pairs": row["pairs_by_stat"].get(stat, 0),
                }
            )

    json_path = base.with_suffix(".json")
    json_path.write_text(json.dumps(row, indent=2, default=str) + "\n", encoding="utf-8")

    pd.DataFrame(per_stat_rows if per_stat_rows else [{"date": date_key, "note": "no_per_stat_breakdown"}]).to_csv(
        base.with_suffix(".csv"), index=False
    )

    md_lines = [
        f"# Stat grid integrity — {date_key}",
        "",
        f"- **File**: `{row['path']}`",
        f"- **Exists**: {row['file_exists']}",
        f"- **Rows**: {row['row_count']}",
        f"- **TOV-only artifact**: {row['tov_only_artifact']}",
        f"- **Mission missing**: `{row['mission_stats_missing']}`",
        f"- **Origin (heuristic)**: `{row['possible_origin']}`",
        f"- **Recommended action**: `{row['recommended_action']}`",
        f"- **mtime (UTC)**: {row['parquet_mtime_utc']}",
        "",
        "## Stat counts",
        "",
        "```",
        json.dumps(row.get("stat_counts") or {}, indent=2),
        "```",
        "",
    ]
    base.with_suffix(".md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"STAT_GRID_INTEGRITY_DIAG wrote {json_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
