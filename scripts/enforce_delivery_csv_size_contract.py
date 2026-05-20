#!/usr/bin/env python3
"""
Enforce GitHub-viewable CSV files inside deliveries/<date>.

Policy:
- No CSV under deliveries/<date> may exceed --max-bytes.
- Oversized CSVs are preserved as parquet and split into small CSV parts.
- The original CSV path is replaced with a small first-rows preview.
- Explicit --preserve files are never modified; if oversized, the script fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PART_DIR_SUFFIX = "_csv_parts"


def _is_generated_csv_part(path: Path) -> bool:
    """Generated split parts live under any directory whose name ends in
    ``_csv_parts``. They are produced/regenerated from a source CSV
    elsewhere in the delivery tree, so the top-level source scan must
    NOT treat them as independent source CSVs (doing so re-processes
    files that get removed mid-run during a re-split, which crashes
    with FileNotFoundError)."""
    return any(part.endswith(PART_DIR_SUFFIX) for part in path.parts)


def _csv_header_column_count(path: Path) -> int:
    """Return number of columns in the CSV header. Zero if the file is
    truly empty or pandas raises EmptyDataError. Zero rows WITH columns
    returns the header count."""
    try:
        df = pd.read_csv(path, nrows=0)
    except pd.errors.EmptyDataError:
        return 0
    return int(len(df.columns))


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_size_bytes(df: pd.DataFrame, n_rows: int) -> int:
    return len(df.head(n_rows).to_csv(index=False).encode("utf-8"))


def largest_preview_rows(df: pd.DataFrame, max_bytes: int) -> int:
    if len(df) == 0:
        return 0

    lo, hi, best = 0, len(df), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        size = csv_size_bytes(df, mid)
        if size <= max_bytes:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def write_shards(df: pd.DataFrame, part_dir: Path, stem: str, max_bytes: int) -> list[dict[str, Any]]:
    if part_dir.exists():
        shutil.rmtree(part_dir)
    part_dir.mkdir(parents=True, exist_ok=True)

    if len(df) == 0:
        part = part_dir / f"{stem}_part_000.csv"
        df.to_csv(part, index=False)
        return [{
            "part": part.name,
            "rows": 0,
            "bytes": part.stat().st_size,
        }]

    sample_n = min(len(df), 100)
    sample_bytes = max(1, len(df.head(sample_n).to_csv(index=False).encode("utf-8")))
    avg_row_bytes = max(1.0, sample_bytes / max(1, sample_n))
    rows_per_part = max(1, int((max_bytes * 0.82) / avg_row_bytes))

    parts: list[dict[str, Any]] = []
    i = 0
    part_idx = 0

    while i < len(df):
        n = min(rows_per_part, len(df) - i)

        while n >= 1:
            tmp = part_dir / f".{stem}_part_{part_idx:03d}.tmp.csv"
            final = part_dir / f"{stem}_part_{part_idx:03d}.csv"

            df.iloc[i:i + n].to_csv(tmp, index=False)
            size = tmp.stat().st_size

            if size <= max_bytes:
                tmp.replace(final)
                parts.append({
                    "part": final.name,
                    "rows": int(n),
                    "bytes": int(size),
                    "start_row": int(i),
                    "end_row_exclusive": int(i + n),
                })
                i += n
                part_idx += 1
                break

            tmp.unlink(missing_ok=True)
            n = n // 2

        if n < 1:
            raise RuntimeError(
                f"Cannot shard {stem}: one row is too large for max_bytes={max_bytes}"
            )

    return parts


def write_readme(
    csv_path: Path,
    rel: str,
    original_rows: int,
    original_cols: int,
    original_bytes: int,
    preview_rows: int,
    parquet_path: Path,
    part_dir: Path,
    parts: list[dict[str, Any]],
    max_bytes: int,
) -> None:
    readme = csv_path.with_name(f"{csv_path.stem}_README.md")
    lines = [
        f"# {csv_path.name}",
        "",
        "This CSV was larger than the GitHub CSV rendering limit used by this repository.",
        "",
        f"- Original relative path: `{rel}`",
        f"- Original rows: `{original_rows}`",
        f"- Original columns: `{original_cols}`",
        f"- Original bytes: `{original_bytes}`",
        f"- Current CSV preview rows: `{preview_rows}`",
        f"- Max allowed CSV bytes: `{max_bytes}`",
        f"- Full machine-readable parquet: `{parquet_path.name}`",
        f"- CSV parts folder: `{part_dir.name}/`",
        "",
        "## CSV parts",
        "",
        "| part | rows | bytes |",
        "|---|---:|---:|",
    ]
    for p in parts:
        lines.append(f"| `{part_dir.name}/{p['part']}` | {p['rows']} | {p['bytes']} |")
    lines.append("")
    readme.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--max-bytes", type=int, default=512 * 1024)
    ap.add_argument("--write", action="store_true")
    ap.add_argument(
        "--preserve",
        action="append",
        default=[],
        help="Path relative to deliveries/<date> that must never be modified.",
    )
    ap.add_argument(
        "--delivery-root",
        default=None,
        help="Override the delivery root for tests. Defaults to "
        "<repo>/deliveries/<date>.",
    )
    ap.add_argument(
        "--artifacts-dir",
        default=None,
        help="Override the artifacts/automation_health output dir for tests. "
        "Defaults to <repo>/artifacts/automation_health.",
    )
    args = ap.parse_args()

    if args.delivery_root:
        delivery_root = Path(args.delivery_root).resolve()
    else:
        delivery_root = (REPO_ROOT / "deliveries" / args.date).resolve()
    if not delivery_root.exists():
        raise SystemExit(f"delivery root not found: {delivery_root}")

    if args.artifacts_dir:
        artifacts_dir = Path(args.artifacts_dir).resolve()
    elif args.delivery_root:
        artifacts_dir = (delivery_root.parent.parent / "artifacts" / "automation_health").resolve()
    else:
        artifacts_dir = REPO_ROOT / "artifacts" / "automation_health"

    preserve = {str(p).strip("/") for p in args.preserve}
    records: list[dict[str, Any]] = []
    failures: list[str] = []

    csv_paths = sorted(
        p for p in delivery_root.rglob("*.csv")
        if not _is_generated_csv_part(p)
    )

    for csv_path in csv_paths:
        rel = csv_path.relative_to(delivery_root).as_posix()
        size = csv_path.stat().st_size

        rec: dict[str, Any] = {
            "path": rel,
            "bytes_before": int(size),
            "max_bytes": int(args.max_bytes),
            "action": "ok",
        }

        if size <= args.max_bytes:
            cols = _csv_header_column_count(csv_path)
            if cols <= 0:
                rec["action"] = "zero_columns_fail"
                marker = f"DELIVERY_CSV_SCHEMA_ZERO_COLUMNS_FAIL path={rel}"
                failures.append(marker)
                records.append(rec)
                continue
            rec["columns"] = int(cols)
            records.append(rec)
            continue

        if rel in preserve:
            rec["action"] = "preserve_oversized_fail"
            failures.append(
                f"DELIVERY_CSV_SIZE_CONTRACT_PROTECTED_FILE_OVERSIZED "
                f"path={rel} bytes={size} max_bytes={args.max_bytes}"
            )
            records.append(rec)
            continue

        if not args.write:
            rec["action"] = "oversized_fail_dry_run"
            failures.append(f"oversized CSV: {rel} ({size} bytes)")
            records.append(rec)
            continue

        before_hash = sha256_path(csv_path)

        try:
            df = pd.read_csv(csv_path, low_memory=False)
        except Exception as exc:
            rec["action"] = "read_fail"
            rec["error"] = repr(exc)
            failures.append(f"could not read oversized CSV {rel}: {exc!r}")
            records.append(rec)
            continue

        parquet_path = csv_path.with_suffix(".parquet")
        if not parquet_path.exists():
            try:
                df.to_parquet(parquet_path, index=False)
            except Exception as exc:
                rec["parquet_write_error"] = repr(exc)
                failures.append(f"could not preserve parquet for {rel}: {exc!r}")
                records.append(rec)
                continue

        if len(df.columns) <= 0:
            rec["action"] = "zero_columns_fail"
            failures.append(f"DELIVERY_CSV_SCHEMA_ZERO_COLUMNS_FAIL path={rel}")
            records.append(rec)
            continue

        part_dir = csv_path.with_name(f"{csv_path.stem}{PART_DIR_SUFFIX}")
        try:
            parts = write_shards(df, part_dir, csv_path.stem, args.max_bytes)
        except Exception as exc:
            rec["shard_error"] = repr(exc)
            failures.append(f"could not shard {rel}: {exc!r}")
            records.append(rec)
            continue

        on_disk_parts = sorted(part_dir.glob("*.csv"))
        on_disk_part_names = [p.name for p in on_disk_parts]
        if len(df) > 0 and not on_disk_parts:
            failures.append(
                f"DELIVERY_CSV_SPLIT_NO_PARTS_GENERATED source={rel}"
            )
            records.append(rec)
            continue
        for part in on_disk_parts:
            if not part.is_file():
                failures.append(
                    f"DELIVERY_CSV_SPLIT_NO_PARTS_GENERATED source={rel} "
                    f"missing={part.name}"
                )
                continue
            part_cols = _csv_header_column_count(part)
            if part_cols <= 0:
                failures.append(
                    f"DELIVERY_CSV_SCHEMA_ZERO_COLUMNS_FAIL "
                    f"path={part.relative_to(delivery_root).as_posix()}"
                )
        print(
            f"DELIVERY_CSV_SPLIT_PARTS_VALIDATED source={rel} "
            f"parts={len(on_disk_parts)}"
        )

        preview_rows = largest_preview_rows(df, args.max_bytes)
        preview = df.head(preview_rows).copy()
        preview.to_csv(csv_path, index=False)

        if csv_path.stat().st_size > args.max_bytes and preview_rows > 0:
            preview_rows = 0
            df.head(0).to_csv(csv_path, index=False)

        write_readme(
            csv_path=csv_path,
            rel=rel,
            original_rows=int(len(df)),
            original_cols=int(len(df.columns)),
            original_bytes=int(size),
            preview_rows=int(preview_rows),
            parquet_path=parquet_path,
            part_dir=part_dir,
            parts=parts,
            max_bytes=args.max_bytes,
        )

        rec.update({
            "action": "split_and_previewed",
            "rows_original": int(len(df)),
            "cols_original": int(len(df.columns)),
            "preview_rows": int(preview_rows),
            "bytes_after": int(csv_path.stat().st_size),
            "sha256_before": before_hash,
            "sha256_after": sha256_path(csv_path),
            "parquet": parquet_path.relative_to(delivery_root).as_posix(),
            "parts_dir": part_dir.relative_to(delivery_root).as_posix(),
            "parts_count": len(on_disk_part_names),
            "parts": [
                (part_dir.relative_to(delivery_root) / name).as_posix()
                for name in on_disk_part_names
            ],
        })
        records.append(rec)

    oversized_after = []
    for p in sorted(delivery_root.rglob("*.csv")):
        if _is_generated_csv_part(p):
            continue
        if not p.exists():
            continue
        s = p.stat().st_size
        rel_after = p.relative_to(delivery_root).as_posix()
        if rel_after in preserve:
            continue
        if s > args.max_bytes:
            oversized_after.append({
                "path": rel_after,
                "bytes": int(s),
            })

    if oversized_after:
        failures.extend(
            f"still oversized after enforcement: {x['path']} ({x['bytes']} bytes)"
            for x in oversized_after
        )

    out_dir = artifacts_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "date": args.date,
        "max_bytes": args.max_bytes,
        "write": bool(args.write),
        "preserve": sorted(preserve),
        "records": records,
        "oversized_after": oversized_after,
        "pass": not failures,
        "failures": failures,
    }

    json_path = out_dir / f"delivery_csv_size_contract_{args.date}.json"
    md_path = out_dir / f"delivery_csv_size_contract_{args.date}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = [
        f"# Delivery CSV size contract — {args.date}",
        "",
        f"- max_bytes: `{args.max_bytes}`",
        f"- pass: `{not failures}`",
        "",
        "| path | before bytes | action | after bytes |",
        "|---|---:|---|---:|",
    ]
    for r in records:
        md.append(
            f"| `{r['path']}` | {r.get('bytes_before', '')} | "
            f"{r.get('action', '')} | {r.get('bytes_after', '')} |"
        )

    if failures:
        md.extend(["", "## Failures", ""])
        for f in failures:
            md.append(f"- {f}")

    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    try:
        print(f"WROTE {json_path.relative_to(REPO_ROOT)}")
        print(f"WROTE {md_path.relative_to(REPO_ROOT)}")
    except ValueError:
        print(f"WROTE {json_path}")
        print(f"WROTE {md_path}")

    if failures:
        print("DELIVERY_CSV_SIZE_CONTRACT_FAIL")
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("DELIVERY_CSV_SIZE_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
