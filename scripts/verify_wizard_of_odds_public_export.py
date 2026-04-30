#!/usr/bin/env python3
"""Verify the Wizard of Odds public export folder is publishable.

Phase 12E — pre-flight check before the FTP deploy. Exits non-zero on
the first failed gate so the deploy workflow short-circuits before any
upload attempt. Designed to be safe to run locally and in CI.

Gates (each is a separate failure with a specific message):

    1.  public_export/wizard_of_odds/index.html exists
    2.  public_export/wizard_of_odds/manifest.json exists and parses
    3.  manifest.json `latest_date` matches the date directory copied
        into latest/ (manifest is honest about the pointer)
    4.  latest/{fair_odds_board.csv, market_comparison.csv,
        publishable_edges.csv, monetization_view.csv, full_pmfs_wide.csv,
        full_pmfs_outcome_level.csv, run_manifest.json} exist
    5.  monetization_view + fair_odds_board have row counts > 0
        (publishable_edges can be 0 on future slates with no edges)
    6.  monetization_view has affiliate_url, odds_button_url, and
        monetization_status columns
    7.  No raw secrets are present in any text file under
        public_export/wizard_of_odds/ (env-var names are scanned)
    8.  No PMF corruption — pmf columns in full_pmfs_wide.csv sum to
        within 1e-6 of 1.0 (when the column set is present)

Exit codes:
    0   all gates passed
    1   gate failure (message printed to stderr)
    2   public export folder missing entirely

Usage:
    python3 scripts/verify_wizard_of_odds_public_export.py
    python3 scripts/verify_wizard_of_odds_public_export.py --out-dir path/
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "public_export" / "wizard_of_odds"

REQUIRED_LATEST_FILES = [
    "fair_odds_board.csv",
    "market_comparison.csv",
    "publishable_edges.csv",
    "monetization_view.csv",
    "full_pmfs_wide.csv",
    "full_pmfs_outcome_level.csv",
    "run_manifest.json",
]

# Env var names whose *values* must never appear in public output. We
# look up the live process env, then grep the public files for those
# values. Names alone are intentionally allowed (e.g. a runbook can
# reference "ODDS_API_KEY" by name).
SECRET_ENV_VARS = [
    "ODDS_API_KEY",
    "BDL_API_KEY",
    "DUNKS_API_KEY",
    "DUNKS_AND_THREES_API_KEY",
    "WOO_FTP_PASSWORD",
    "WOO_FTP_USER",
    "WOO_FTP_HOST",
    "WOO_FTP_REMOTE_DIR",
]

PMF_COLS = [f"p{i}" for i in range(0, 60)]


class GateFailure(Exception):
    """Raised when a verification gate fails."""


def _row_count_csv(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open() as f:
        reader = csv.reader(f)
        try:
            next(reader)  # header
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def _gate(label: str, ok: bool, detail: str = "") -> None:
    flag = "OK " if ok else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{flag}] {label}{suffix}")
    if not ok:
        raise GateFailure(label)


def _verify_no_secrets_leak(public_root: Path) -> None:
    """Scan every text file (csv/json/jsonl/html/md) under the public
    root for the *values* of known secret env vars. Returns silently
    when none are set (nothing to compare against). Filenames whose
    binary content is not text-decoded (e.g. *.parquet) are skipped."""
    secret_values: list[tuple[str, str]] = []
    for name in SECRET_ENV_VARS:
        v = os.environ.get(name)
        if v and len(v) >= 8:  # avoid trivial substrings
            secret_values.append((name, v))
    if not secret_values:
        print("  [OK ] no secret env vars set in this shell — leak scan skipped")
        return

    text_extensions = {".csv", ".json", ".jsonl", ".html", ".md", ".txt"}
    bad: list[tuple[Path, str]] = []
    for p in public_root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in text_extensions:
            continue
        try:
            content = p.read_text(errors="ignore")
        except Exception:
            continue
        for name, value in secret_values:
            if value in content:
                bad.append((p, name))
                break
    _gate(
        "no secret values present in public files",
        not bad,
        detail="; ".join(
            f"{p.relative_to(REPO_ROOT)} contains {name} value"
            for p, name in bad
        ),
    )


def _verify_pmf_sums(latest_dir: Path) -> None:
    """PMF sanity check. The canonical PMF lives in the ``pmf_json``
    column (one JSON object per row mapping outcome→probability); the
    spreadsheet view also exposes ``p0`` and tail probabilities
    ``p_ge_1, p_ge_2, …`` but does not enumerate every outcome. We
    parse pmf_json directly so the gate is robust to either layout."""
    path = latest_dir / "full_pmfs_wide.csv"
    if not path.exists():
        _gate("PMF sum sanity (full_pmfs_wide.csv)", False, "file missing")
        return
    try:
        import pandas as pd
        df = pd.read_csv(path)
    except Exception as e:
        _gate("PMF sum sanity (full_pmfs_wide.csv)", False, f"read failed: {e!r}")
        return

    if "pmf_json" in df.columns:
        bad_sum = 0
        bad_neg = 0
        bad_nonfin = 0
        bad_parse = 0
        sample_bad: list[float] = []
        for raw in df["pmf_json"].dropna():
            try:
                d = json.loads(raw)
            except Exception:
                bad_parse += 1
                continue
            total = 0.0
            ok = True
            for v in d.values():
                if not isinstance(v, (int, float)) or not math.isfinite(v):
                    bad_nonfin += 1
                    ok = False
                    break
                if v < 0:
                    bad_neg += 1
                    ok = False
                    break
                total += float(v)
            if ok and abs(total - 1.0) > 1e-6:
                bad_sum += 1
                if len(sample_bad) < 3:
                    sample_bad.append(round(total, 8))
        _gate(
            "PMF sum sanity (pmf_json sums to 1.0 within 1e-6)",
            (bad_sum == 0 and bad_neg == 0 and bad_nonfin == 0 and bad_parse == 0),
            (
                f"bad_sum={bad_sum} bad_neg={bad_neg} bad_nonfin={bad_nonfin} "
                f"bad_parse={bad_parse} sample={sample_bad}"
            ),
        )
        return

    pmf_cols = [c for c in PMF_COLS if c in df.columns]
    if not pmf_cols:
        _gate(
            "PMF sum sanity (full_pmfs_wide.csv)",
            True,
            "no pmf_json column and no p0..p59 columns — "
            "schema-tolerant pass",
        )
        return

    sums = df[pmf_cols].sum(axis=1).fillna(0.0)
    bad = sums[(sums - 1.0).abs() > 1e-6]
    _gate(
        "PMF sum sanity (p0..p59 columns)",
        bool(len(bad) == 0),
        f"{len(bad)} rows with |sum-1| > 1e-6 (sample sums: "
        f"{[round(float(x), 8) for x in bad.head(3).tolist()]})",
    )


def _verify_monetization_columns(latest_dir: Path) -> None:
    path = latest_dir / "monetization_view.csv"
    if not path.exists():
        _gate("monetization_view.csv columns", False, "file missing")
        return
    with path.open() as f:
        header = next(csv.reader(f))
    required = {"affiliate_url", "odds_button_url", "monetization_status"}
    missing = required - set(header)
    _gate(
        "monetization_view.csv has affiliate_url / odds_button_url / "
        "monetization_status columns",
        not missing,
        detail=("missing: " + ", ".join(sorted(missing))) if missing else "",
    )


def _verify_manifest_consistency(public_root: Path) -> dict:
    manifest_path = public_root / "manifest.json"
    if not manifest_path.exists():
        _gate("manifest.json present", False)
        return {}
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:
        _gate("manifest.json parses", False, f"{e!r}")
        return {}
    _gate("manifest.json present and parses", True)

    latest_date = manifest.get("latest_date")
    if not latest_date:
        _gate("manifest.latest_date present", False)
        return manifest
    date_dir = public_root / latest_date
    latest_dir = public_root / "latest"

    # latest_date must point to a real source folder
    _gate(
        f"manifest.latest_date={latest_date!r} has a corresponding date directory",
        date_dir.exists(),
        detail=str(date_dir.relative_to(REPO_ROOT)),
    )

    # latest/run_manifest.json should match the source date's manifest
    src_rm = date_dir / "run_manifest.json"
    dst_rm = latest_dir / "run_manifest.json"
    if src_rm.exists() and dst_rm.exists():
        _gate(
            "latest/run_manifest.json mirrors the source date",
            src_rm.read_bytes() == dst_rm.read_bytes(),
            detail=f"{src_rm.relative_to(REPO_ROOT)} <-> "
                   f"{dst_rm.relative_to(REPO_ROOT)}",
        )
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="public export root (default: public_export/wizard_of_odds)",
    )
    args = ap.parse_args()

    public_root = args.out_dir.resolve()
    print(f"verifying {public_root.relative_to(REPO_ROOT) if public_root.is_relative_to(REPO_ROOT) else public_root}")
    if not public_root.exists():
        print(f"  FATAL: {public_root} does not exist", file=sys.stderr)
        return 2

    try:
        _gate(
            "public_export/wizard_of_odds/index.html exists",
            (public_root / "index.html").exists(),
        )
        manifest = _verify_manifest_consistency(public_root)

        latest_dir = public_root / "latest"
        _gate(
            "public_export/wizard_of_odds/latest/ exists",
            latest_dir.exists() and latest_dir.is_dir(),
        )

        for fname in REQUIRED_LATEST_FILES:
            _gate(
                f"latest/{fname} exists",
                (latest_dir / fname).exists(),
            )

        # Row-count gates
        mon_rows = _row_count_csv(latest_dir / "monetization_view.csv")
        _gate(
            "monetization_view.csv has rows > 0",
            mon_rows > 0,
            detail=f"rows={mon_rows}",
        )
        fair_rows = _row_count_csv(latest_dir / "fair_odds_board.csv")
        _gate(
            "fair_odds_board.csv has rows > 0",
            fair_rows > 0,
            detail=f"rows={fair_rows}",
        )
        pub_rows = _row_count_csv(latest_dir / "publishable_edges.csv")
        # publishable_edges can be empty on future slates with no edges;
        # we only verify the file exists (above) and is readable.
        _gate(
            "publishable_edges.csv readable (rows >= 0)",
            pub_rows >= 0,
            detail=f"rows={pub_rows}",
        )

        _verify_monetization_columns(latest_dir)
        _verify_no_secrets_leak(public_root)
        _verify_pmf_sums(latest_dir)

    except GateFailure as e:
        print(f"\nVERIFICATION FAILED: {e}", file=sys.stderr)
        return 1

    print("\nVERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
