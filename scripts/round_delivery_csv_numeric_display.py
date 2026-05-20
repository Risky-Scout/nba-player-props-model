#!/usr/bin/env python3
"""Round float-typed display columns in user-facing delivery CSVs.

This post-processing step normalizes display precision for CSVs under
``<delivery-root>/<date>/`` so that user-facing tables show at most
``--places`` decimal places. Parquet, JSON, model artifacts, calibration
sources, training artifacts, and any non-``.csv`` file are NEVER opened
or modified — they retain full precision.

Protective guarantees (mirrors conventions used by
``scripts/enforce_delivery_csv_size_contract.py``):

- Skips generated split parts (any path under ``*_csv_parts/``). They are
  regenerated downstream from the rounded source CSV, so processing them
  directly would either be redundant or interact badly with the size
  contract's re-shard step.
- Skips any ``--preserve`` relative path. ``derek_unique_props_summary.csv``
  is preserved by the production workflow via this flag.
- Skips ID-like columns. A column is considered an ID when its lowercase
  name matches any of ``{id, season, year, count, rows}`` exactly, or ends
  with ``_id``, or starts with ``id_``, or contains ``_id_``.
- Skips JSON / weights columns. A column whose lowercase name contains
  ``json`` or ``weights`` (e.g. ``role_mixture_weights_json``) is never
  rounded — its byte content is preserved through the pandas CSV round
  trip.
- Skips non-float columns. Only columns where
  ``pandas.api.types.is_float_dtype(...)`` is True are rounded. Integer
  columns are left untouched (no ``.0000`` suffix), and numeric ``object``
  columns are not coerced.

Markers:

- ``DELIVERY_CSV_NUMERIC_ROUNDING_PASS date=<date> files_checked=<N> ``
  ``files_changed=<N> places=<places>`` on success (also for the dry-run
  ``--write``-less invocation).
- ``DELIVERY_CSV_NUMERIC_ROUNDING_SKIP_NO_DATE date=<date>`` when the
  delivery folder does not exist (treated as a clean valid-skip; the
  caller may run this before the delivery is built).
- ``DELIVERY_CSV_ROUNDING_ZERO_COLUMNS_FAIL path=<rel>`` to stderr with a
  non-zero exit when an input CSV has zero columns (empty file or no
  parseable header). Header-only CSVs (>=1 column, 0 rows) are valid.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pandas as pd


PART_DIR_SUFFIX = "_csv_parts"
ID_EXACT_LOWER = {"id", "season", "year", "count", "rows"}


def _is_generated_csv_part(path: Path) -> bool:
    """Generated split parts live under any directory whose name ends in
    ``_csv_parts``. They are regenerated downstream from the source CSV,
    so the top-level scan must NOT treat them as independent CSVs."""
    return any(part.endswith(PART_DIR_SUFFIX) for part in path.parts)


def _is_id_column(col: object) -> bool:
    name = str(col).lower()
    if name in ID_EXACT_LOWER:
        return True
    if name.endswith("_id"):
        return True
    if name.startswith("id_"):
        return True
    if "_id_" in name:
        return True
    return False


def _is_json_or_weights_column(col: object) -> bool:
    name = str(col).lower()
    return "json" in name or "weights" in name


def _column_is_eligible(col: object, series: pd.Series) -> bool:
    if _is_id_column(col):
        return False
    if _is_json_or_weights_column(col):
        return False
    if not pd.api.types.is_float_dtype(series):
        return False
    return True


def _serialize(df: pd.DataFrame, places: int) -> bytes:
    buf = io.StringIO()
    df.to_csv(
        buf,
        index=False,
        float_format=f"%.{places}f",
        lineterminator="\n",
    )
    return buf.getvalue().encode("utf-8")


def _process_one(path: Path, places: int) -> tuple[bytes, bytes, bool]:
    """Return ``(original_bytes, new_bytes, would_change)``.

    Raises :class:`ValueError` when the CSV has zero columns (empty file
    or no parseable header). Files without any eligible (rounding-target)
    column are returned with ``new_bytes == original_bytes`` and
    ``would_change=False`` so the on-disk file is never rewritten — this
    avoids reformatting unrelated float columns (e.g. float-typed IDs)
    when nothing would actually be rounded.
    """

    original = path.read_bytes()
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("zero columns") from exc

    if len(df.columns) == 0:
        raise ValueError("zero columns")

    rounded_any = False
    for col in df.columns:
        if _column_is_eligible(col, df[col]):
            df[col] = df[col].round(places)
            rounded_any = True

    if not rounded_any:
        return original, original, False

    new_bytes = _serialize(df, places)
    return original, new_bytes, original != new_bytes


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Round float-typed display columns in user-facing delivery "
            "CSVs to <= --places decimal places."
        )
    )
    ap.add_argument("--date", required=True, help="Delivery date (YYYY-MM-DD).")
    ap.add_argument(
        "--places",
        type=int,
        default=4,
        help="Maximum decimal places (default: 4).",
    )
    ap.add_argument(
        "--delivery-root",
        default="deliveries",
        help="Root that contains <date>/ (default: deliveries).",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write rewritten files to disk. Without this flag, the script "
        "is a dry-run and only counts files that would change.",
    )
    ap.add_argument(
        "--preserve",
        action="append",
        default=[],
        help="Repeatable. Relative path under <delivery-root>/<date>/ that "
        "must never be modified (e.g. "
        "derek_forward_feed/derek_unique_props_summary.csv).",
    )
    args = ap.parse_args()

    target = Path(args.delivery_root) / args.date
    if not target.exists():
        print(
            f"DELIVERY_CSV_NUMERIC_ROUNDING_SKIP_NO_DATE date={args.date}"
        )
        return 0

    preserve_set = {Path(p).as_posix() for p in args.preserve}

    files_checked = 0
    files_changed = 0

    for path in sorted(target.rglob("*.csv")):
        if _is_generated_csv_part(path):
            continue
        rel = path.relative_to(target).as_posix()
        if rel in preserve_set:
            continue
        files_checked += 1

        try:
            original, new_bytes, would_change = _process_one(path, args.places)
        except ValueError:
            print(
                f"DELIVERY_CSV_ROUNDING_ZERO_COLUMNS_FAIL path={rel}",
                file=sys.stderr,
            )
            return 2

        if not would_change:
            continue

        files_changed += 1
        if args.write:
            path.write_bytes(new_bytes)

    print(
        f"DELIVERY_CSV_NUMERIC_ROUNDING_PASS date={args.date} "
        f"files_checked={files_checked} files_changed={files_changed} "
        f"places={args.places}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
