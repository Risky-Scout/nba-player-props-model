#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


TABLE_SUFFIXES = {".csv", ".parquet", ".jsonl"}

PRESERVE_BY_PATH_SUBSTRING = {
    "derek_forward_feed/derek_forward_feed": {
        "model_artifact_hash",
        "event_id",
        "role_mixture_weights_json",
        "role_entropy",
        "role_bucket_confidence",
        "minutes_q10",
        "minutes_q90",
        "unavailable_reason",
        # contract-required by DEREK_UNIFIED_REQUIRED_COLUMNS; legitimately null in projected/morning mode
        "lineup_last_updated_utc",
    }
}


def is_empty_col(s: pd.Series) -> bool:
    if s.isna().all():
        return True
    nonnull = s.dropna()
    if nonnull.empty:
        return True
    return nonnull.astype(str).str.strip().eq("").all()


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path, low_memory=False)

    if suffix == ".parquet":
        return pd.read_parquet(path)

    if suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        return pd.DataFrame(rows)

    raise ValueError(f"unsupported table type: {path}")


def write_table(path: Path, df: pd.DataFrame) -> None:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(path, index=False)
        return

    if suffix == ".parquet":
        df.to_parquet(path, index=False)
        return

    if suffix == ".jsonl":
        with path.open("w", encoding="utf-8") as f:
            for rec in df.to_dict(orient="records"):
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        return

    raise ValueError(f"unsupported table type: {path}")


def preserve_cols_for(path: Path) -> set[str]:
    rel = path.as_posix()
    keep = set()

    for needle, cols in PRESERVE_BY_PATH_SUBSTRING.items():
        if needle in rel:
            keep.update(cols)

    return keep


def audit_date(root: Path, date: str, write: bool) -> dict:
    delivery_dir = root / date

    if not delivery_dir.exists():
        raise SystemExit(f"FAIL: missing delivery folder: {delivery_dir}")

    report = {
        "date": date,
        "delivery_dir": str(delivery_dir),
        "write": write,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files_checked": 0,
        "files_changed": 0,
        "columns_removed_total": 0,
        "changes": [],
        "errors": [],
    }

    table_files = sorted(
        p for p in delivery_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in TABLE_SUFFIXES
    )

    for path in table_files:
        report["files_checked"] += 1

        try:
            df = read_table(path)
        except Exception as exc:
            report["errors"].append({
                "file": path.as_posix(),
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue

        if df.empty or len(df.columns) == 0:
            continue

        preserve_cols = preserve_cols_for(path)
        empty_cols = [
            c for c in df.columns
            if c not in preserve_cols and is_empty_col(df[c])
        ]

        if not empty_cols:
            continue

        clean = df.drop(columns=empty_cols)

        report["files_changed"] += 1
        report["columns_removed_total"] += len(empty_cols)
        report["changes"].append({
            "file": path.as_posix(),
            "rows": int(len(df)),
            "cols_before": int(len(df.columns)),
            "cols_after": int(len(clean.columns)),
            "preserved_columns": sorted(preserve_cols),
            "removed_columns": [str(c) for c in empty_cols],
        })

        if write:
            write_table(path, clean)

    return report


def write_report(reports: list[dict]) -> None:
    out_dir = Path("artifacts/automation_health")
    out_dir.mkdir(parents=True, exist_ok=True)

    tag = "_".join(r["date"] for r in reports)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reports": reports,
        "files_checked": sum(r["files_checked"] for r in reports),
        "files_changed": sum(r["files_changed"] for r in reports),
        "columns_removed_total": sum(r["columns_removed_total"] for r in reports),
        "errors": [err for r in reports for err in r["errors"]],
    }

    json_path = out_dir / f"delivery_empty_column_hygiene_{tag}.json"
    md_path = out_dir / f"delivery_empty_column_hygiene_{tag}.md"

    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        f"# Delivery Empty Column Hygiene — {tag}",
        "",
        f"- files checked: `{payload['files_checked']}`",
        f"- files changed: `{payload['files_changed']}`",
        f"- columns removed total: `{payload['columns_removed_total']}`",
        f"- errors: `{len(payload['errors'])}`",
        "",
    ]

    for r in reports:
        lines.append(f"## {r['date']}")
        lines.append("")
        for ch in r["changes"]:
            lines.append(f"### `{ch['file']}`")
            lines.append(f"- rows: `{ch['rows']}`")
            lines.append(f"- cols before: `{ch['cols_before']}`")
            lines.append(f"- cols after: `{ch['cols_after']}`")
            lines.append(f"- preserved columns: `{', '.join(ch['preserved_columns'])}`")
            lines.append(f"- removed columns: `{', '.join(ch['removed_columns'])}`")
            lines.append("")

    if payload["errors"]:
        lines.append("## Errors")
        for err in payload["errors"]:
            lines.append(f"- `{err['file']}`: {err['error']}")

    md_path.write_text("\n".join(lines) + "\n")

    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", required=True)
    ap.add_argument("--root", default="deliveries")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)

    reports = []
    for date in args.date:
        report = audit_date(root, date, args.write)
        reports.append(report)

        print(f"DELIVERY_EMPTY_COLUMN_HYGIENE date={date}")
        print(f"  files_checked={report['files_checked']}")
        print(f"  files_changed={report['files_changed']}")
        print(f"  columns_removed_total={report['columns_removed_total']}")
        print(f"  errors={len(report['errors'])}")

    write_report(reports)

    errors = [err for r in reports for err in r["errors"]]
    if errors:
        raise SystemExit(f"FAIL: {len(errors)} table read/write errors")

    print("DELIVERY_EMPTY_COLUMN_HYGIENE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
