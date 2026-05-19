#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd

TARGET_FOLDERS = [
    "canonical_source",
    "wizard_of_odds",
    "derek_forward_feed",
    "derek_game_snapshots",
    "pmf_model_review_package",
    "after_game_scoring",
]

TABLE_SUFFIXES = {".csv", ".parquet", ".jsonl"}

PREFERRED_COLS = [
    "player_name", "player_id", "team", "opponent", "game_id", "stat",
    "role_bucket", "pmf_source", "calibration_source", "cal_source",
    "minutes_mean", "minutes_q50", "p_inactive_used",
    "mean", "pmf_mean", "median", "mode", "p0",
    "k", "p_k", "line", "market_line", "book",
    "model_p_over", "p_over", "model_p_under", "p_under",
    "market_over_odds", "market_under_odds", "market_no_vig_over_prob",
    "edge", "edge_over",
    "injury_freshness_status", "injury_context_source",
    "expected_lineup_status", "official_lineup_status",
    "lineup_source", "lineup_freshness_status",
    "snapshot_type", "snapshot_time_utc",
]

def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return pd.DataFrame(rows)
    raise ValueError(path)

def compact(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in PREFERRED_COLS if c in df.columns]
    if not cols:
        cols = list(df.columns[:20])
    return df[cols].copy()

def write_previews(date: str) -> None:
    root = Path("deliveries") / date
    if not root.exists():
        raise SystemExit(f"FAIL: missing {root}")

    for folder_name in TARGET_FOLDERS:
        folder = root / folder_name
        if not folder.exists():
            continue

        files = sorted(
            p for p in folder.rglob("*")
            if p.is_file()
            and p.suffix.lower() in TABLE_SUFFIXES
            and not p.name.startswith("00_")
        )

        md_lines = [
            f"# Reviewable Delivery Preview — {date} — {folder_name}",
            "",
            "GitHub may refuse to render large CSV files. This file is intentionally small.",
            "",
        ]

        for p in files:
            rel = p.relative_to(root)
            try:
                df = read_table(p)
                view = compact(df).head(30)
            except Exception as exc:
                md_lines += [
                    f"## `{rel}`",
                    "",
                    f"FAILED_TO_READ: `{type(exc).__name__}: {exc}`",
                    "",
                ]
                continue

            md_lines += [
                "---",
                "",
                f"## `{rel}`",
                "",
                f"- bytes: `{p.stat().st_size:,}`",
                f"- rows: `{len(df):,}`",
                f"- columns: `{len(df.columns):,}`",
                "",
                "Compact first 30 rows:",
                "",
                "```csv",
                view.to_csv(index=False),
                "```",
                "",
            ]

        out_md = folder / "00_REVIEW_FIRST_ROWS.md"
        out_md.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"WROTE {out_md}")

    print("DELIVERY_REVIEW_PREVIEWS_PASS")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    write_previews(args.date)

if __name__ == "__main__":
    main()
