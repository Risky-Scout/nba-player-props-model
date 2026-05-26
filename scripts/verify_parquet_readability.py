"""verify_parquet_readability.py — Fail-closed parquet readback validation.

Usage:
    python3 scripts/verify_parquet_readability.py \\
        --path predictions/all_props_2026-05-25.parquet \\
        --min-rows 1

Exits 0 only when the file:
  - is readable by pyarrow
  - has >= min_rows rows
  - (if --required-columns given) has all required columns

Exits 1 on any failure.

Failure codes emitted to stdout:
    PARQUET_READBACK_FAIL
    PARQUET_ZERO_ROWS_FAIL
    PARQUET_REQUIRED_COLUMNS_FAIL
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

ALL_PROPS_REQUIRED_COLUMNS: list[str] = [
    "player_id",
    "player_name",
    "stat",
    "side",
    "line",
]

ALL_PROPS_SOFT_COLUMNS: list[str] = [
    "model_prob",
    "pmf_mean",
]


def verify_parquet(
    path: Path,
    *,
    min_rows: int = 1,
    required_columns: Optional[list[str]] = None,
    soft_columns: Optional[list[str]] = None,
) -> tuple[bool, list[str]]:
    """Return (passed, list_of_failure_messages)."""
    failures: list[str] = []

    if not path.exists():
        failures.append(
            f"PARQUET_READBACK_FAIL  path={path}  reason=file_does_not_exist"
        )
        return False, failures

    # ── Primary read via pyarrow ────────────────────────────────────────────
    try:
        import pyarrow.parquet as pq
        tbl = pq.read_table(str(path))
        n_rows = tbl.num_rows
        col_names = set(tbl.schema.names)
    except Exception as e:
        failures.append(
            f"PARQUET_READBACK_FAIL  path={path}  reason={type(e).__name__}:{e}"
        )
        return False, failures

    print(
        f"PARQUET_READBACK_OK  path={path}  rows={n_rows}"
        f"  cols={len(col_names)}"
    )

    # ── Row count ───────────────────────────────────────────────────────────
    if n_rows < min_rows:
        failures.append(
            f"PARQUET_ZERO_ROWS_FAIL  path={path}"
            f"  rows={n_rows}  min_required={min_rows}"
        )

    # ── Required columns ────────────────────────────────────────────────────
    for col in required_columns or []:
        if col not in col_names:
            failures.append(
                f"PARQUET_REQUIRED_COLUMNS_FAIL  path={path}  missing_column={col}"
            )

    # ── Soft-warn columns ───────────────────────────────────────────────────
    for col in soft_columns or []:
        if col not in col_names:
            print(
                f"PARQUET_SOFT_COLUMN_MISSING  path={path}  column={col}"
                f"  (warn-only)"
            )

    return len(failures) == 0, failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", required=True, help="Path to parquet file")
    ap.add_argument(
        "--min-rows", type=int, default=1, help="Minimum required rows (default 1)"
    )
    ap.add_argument(
        "--required-columns",
        nargs="*",
        help="Column names that must be present (space-separated)",
    )
    ap.add_argument(
        "--all-props-columns",
        action="store_true",
        help=(
            "Apply the standard all_props required-column set: "
            f"{ALL_PROPS_REQUIRED_COLUMNS}"
        ),
    )
    args = ap.parse_args(argv)

    path = Path(args.path)
    required = args.required_columns or []
    soft: list[str] = []
    if args.all_props_columns:
        required = list(dict.fromkeys(required + ALL_PROPS_REQUIRED_COLUMNS))
        soft = ALL_PROPS_SOFT_COLUMNS

    print(f"PARQUET_VERIFY  path={path}  min_rows={args.min_rows}")

    ok, failures = verify_parquet(
        path,
        min_rows=args.min_rows,
        required_columns=required,
        soft_columns=soft,
    )

    if ok:
        print(f"PARQUET_VERIFY_PASS  path={path}")
        return 0

    print(f"PARQUET_VERIFY_FAIL  path={path}  failures={len(failures)}")
    for f in failures:
        print(f"  {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
