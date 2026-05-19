#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd


def is_empty_col(s: pd.Series) -> bool:
    if s.isna().all():
        return True
    nonnull = s.dropna()
    if nonnull.empty:
        return True
    return nonnull.astype(str).str.strip().eq("").all()


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
    raise ValueError(f"unsupported file type: {path}")


def write_table(path: Path, df: pd.DataFrame) -> None:
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
    elif path.suffix.lower() == ".parquet":
        df.to_parquet(path, index=False)
    elif path.suffix.lower() == ".jsonl":
        with path.open("w", encoding="utf-8") as f:
            for row in df.to_dict(orient="records"):
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    else:
        raise ValueError(f"unsupported file type: {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", required=True)
    ap.add_argument("--root", default="deliveries")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    out_dir = Path("artifacts/automation_health")
    out_dir.mkdir(parents=True, exist_ok=True)

    total_files_checked = 0
    total_files_changed = 0
    total_cols_removed = 0
    all_changes = []

    for date in args.date:
        delivery_dir = Path(args.root) / date
        if not delivery_dir.exists():
            raise SystemExit(f"FAIL: missing delivery folder: {delivery_dir}")

        files = sorted(
            p for p in delivery_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".csv", ".parquet", ".jsonl"}
        )

        for path in files:
            total_files_checked += 1
            df = read_table(path)

            if df.empty or len(df.columns) == 0:
                continue

            preserve_cols = set()
        if "derek_forward_feed" in path.as_posix():
            preserve_cols.update({
                "model_artifact_hash",
                "event_id",
                "role_mixture_weights_json",
                "role_entropy",
                "role_bucket_confidence",
                "minutes_q10",
                "minutes_q90",
                "unavailable_reason",
            })

        empty_cols = [c for c in df.columns if c not in preserve_cols and is_empty_col(df[c])]
            if not empty_cols:
                continue

            clean = df.drop(columns=empty_cols)

            if args.write:
                write_table(path, clean)

            total_files_changed += 1
            total_cols_removed += len(empty_cols)
            all_changes.append({
                "date": date,
                "file": str(path),
                "rows": int(len(df)),
                "cols_before": int(len(df.columns)),
                "cols_after": int(len(clean.columns)),
                "removed_columns": [str(c) for c in empty_cols],
            })

    report = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "write": args.write,
        "dates": args.date,
        "files_checked": total_files_checked,
        "files_changed": total_files_changed,
        "columns_removed_total": total_cols_removed,
        "changes": all_changes,
    }

    tag = "_".join(args.date)
    json_path = out_dir / f"delivery_empty_column_hygiene_{tag}.json"
    md_path = out_dir / f"delivery_empty_column_hygiene_{tag}.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        f"# Delivery Empty Column Hygiene — {tag}",
        "",
        f"- write: `{args.write}`",
        f"- files checked: `{total_files_checked}`",
        f"- files changed: `{total_files_changed}`",
        f"- columns removed total: `{total_cols_removed}`",
        "",
    ]

    for ch in all_changes:
        lines.append(f"## `{ch['file']}`")
        lines.append(f"- rows: `{ch['rows']}`")
        lines.append(f"- cols before: `{ch['cols_before']}`")
        lines.append(f"- cols after: `{ch['cols_after']}`")
        lines.append(f"- removed columns: `{', '.join(ch['removed_columns'])}`")
        lines.append("")

    md_path.write_text("\n".join(lines) + "\n")

    print("DELIVERY_EMPTY_COLUMN_HYGIENE_COMPLETE")
    print(f"files_checked={total_files_checked}")
    print(f"files_changed={total_files_changed}")
    print(f"columns_removed_total={total_cols_removed}")
    print(f"report_json={json_path}")
    print(f"report_md={md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
