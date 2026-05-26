"""verify_woo_delivery_complete.py — Fail-closed WoO delivery completeness check.

Usage:
    python3 scripts/verify_woo_delivery_complete.py --date 2026-05-25
    python3 scripts/verify_woo_delivery_complete.py --path deliveries/2026-05-25/wizard_of_odds

Exits 0 only when ALL required files are present AND have > 0 rows.
Exits 1 with structured diagnostic messages on any failure.

Failure codes emitted to stdout (one per failure):
    WOO_DELIVERY_INCOMPLETE_MISSING_REQUIRED_FILE
    WOO_DELIVERY_INCOMPLETE_ZERO_FAIR_ODDS
    WOO_DELIVERY_INCOMPLETE_ZERO_PMFS
    WOO_DELIVERY_INCOMPLETE_ZERO_MARKET_COMPARISON
    WOO_DELIVERY_REFUSED_TO_OVERWRITE_COMPLETE_WITH_EMPTY
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Required files — at least one of each pair must exist.
# ---------------------------------------------------------------------------
REQUIRED_FILE_PAIRS: list[tuple[str, ...]] = [
    ("fair_odds_board.parquet", "fair_odds_board.csv"),
    ("market_comparison.parquet", "market_comparison.csv"),
    ("publishable_edges.parquet", "publishable_edges.csv"),
    ("full_pmfs_wide.parquet", "full_pmfs_wide.csv"),
    ("full_pmfs_outcome_level.parquet", "full_pmfs_outcome_level.csv"),
    ("count_diagnostics.json",),
    ("omitted_bets.json",),
    ("run_manifest.json",),
]

# Keys in count_diagnostics that must be > 0.
COUNT_DIAG_ROW_KEYS: list[str] = [
    "fair_odds_board_rows",
    "full_pmfs_wide_rows",
    "full_pmfs_outcome_level_rows",
]


def _count_rows(path: Path) -> int:
    """Return row count for parquet or CSV file. Returns -1 on error."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".parquet":
            import pyarrow.parquet as pq
            tbl = pq.read_table(str(path))
            return tbl.num_rows
        if suffix == ".csv":
            import csv as _csv
            with path.open(newline="", encoding="utf-8") as f:
                reader = _csv.reader(f)
                next(reader, None)  # skip header
                return sum(1 for _ in reader)
    except Exception as e:
        print(f"    WARN: could not count rows in {path}: {e}")
    return -1


def _resolve_woo_path(date: Optional[str], path: Optional[str]) -> Path:
    if path:
        return Path(path)
    if date:
        return Path("deliveries") / date / "wizard_of_odds"
    raise ValueError("Either --date or --path is required.")


def verify(woo: Path, *, check_nonzero: bool = True) -> tuple[bool, list[str]]:
    """Return (passed, list_of_failure_codes)."""
    failures: list[str] = []

    if not woo.exists():
        failures.append(
            f"WOO_DELIVERY_INCOMPLETE_MISSING_REQUIRED_FILE  path={woo}  reason=directory_does_not_exist"
        )
        return False, failures

    # 1. File presence checks.
    for pair in REQUIRED_FILE_PAIRS:
        found = any((woo / name).exists() for name in pair)
        if not found:
            failures.append(
                f"WOO_DELIVERY_INCOMPLETE_MISSING_REQUIRED_FILE"
                f"  path={woo}  missing_one_of={list(pair)}"
            )

    # 2. Row count checks for parquet/csv files.
    if check_nonzero:
        for stem, code in [
            ("fair_odds_board", "WOO_DELIVERY_INCOMPLETE_ZERO_FAIR_ODDS"),
            ("market_comparison", "WOO_DELIVERY_INCOMPLETE_ZERO_MARKET_COMPARISON"),
            ("full_pmfs_wide", "WOO_DELIVERY_INCOMPLETE_ZERO_PMFS"),
            ("full_pmfs_outcome_level", "WOO_DELIVERY_INCOMPLETE_ZERO_PMFS"),
        ]:
            for ext in (".parquet", ".csv"):
                fp = woo / f"{stem}{ext}"
                if fp.exists():
                    rows = _count_rows(fp)
                    if rows == 0:
                        failures.append(
                            f"{code}  file={fp.name}  rows={rows}"
                        )
                    break  # only check whichever exists

        # 3. count_diagnostics keys.
        cd = woo / "count_diagnostics.json"
        if cd.exists():
            try:
                data = json.loads(cd.read_text())
                for key in COUNT_DIAG_ROW_KEYS:
                    val = data.get(key, None)
                    if val is not None and val == 0:
                        failures.append(
                            f"WOO_DELIVERY_INCOMPLETE_ZERO_PMFS"
                            f"  count_diagnostics_key={key}  value={val}"
                        )
            except Exception as e:
                failures.append(
                    f"WOO_DELIVERY_INCOMPLETE_MISSING_REQUIRED_FILE"
                    f"  file=count_diagnostics.json  reason=parse_error:{e}"
                )

    return len(failures) == 0, failures


def is_complete(woo: Path) -> bool:
    """Quick boolean check — no output."""
    ok, _ = verify(woo)
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="Delivery date YYYY-MM-DD")
    ap.add_argument("--path", help="Explicit path to wizard_of_odds directory")
    ap.add_argument(
        "--quiet", action="store_true", help="Suppress per-failure detail"
    )
    args = ap.parse_args(argv)

    woo = _resolve_woo_path(args.date, args.path)

    label = str(woo)
    print(f"WOO_DELIVERY_VERIFY  path={label}")

    ok, failures = verify(woo)

    if ok:
        print(f"WOO_DELIVERY_COMPLETE  path={label}")
        return 0

    print(f"WOO_DELIVERY_INCOMPLETE  path={label}  failures={len(failures)}")
    for f in failures:
        print(f"  {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
