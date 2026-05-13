#!/usr/bin/env python3
"""Hard gate: predictions/stat_grid_{date}.parquet must cover all 12 mission stats with valid PMFs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

MISSION = tuple(str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL)
SUM_TOL = 1e-4


def _parse_pmf_cell(raw) -> np.ndarray | None:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        try:
            blob = json.loads(s)
        except json.JSONDecodeError:
            return None
    elif isinstance(raw, dict):
        blob = raw
    else:
        return None
    if not blob:
        return None
    try:
        keys = sorted(int(k) for k in blob.keys())
    except Exception:
        return None
    if not keys:
        return None
    kmax = max(keys)
    arr = np.zeros(kmax + 1, dtype=float)
    for k, v in blob.items():
        try:
            arr[int(k)] = float(v)
        except Exception:
            return None
    return arr


def _pmf_valid(arr: np.ndarray) -> tuple[bool, str]:
    if arr is None or arr.size == 0:
        return False, "empty_pmf"
    if not np.all(np.isfinite(arr)):
        return False, "nonfinite"
    if np.any(arr < -1e-12):
        return False, "negative_mass"
    s = float(arr.sum())
    if s <= 0:
        return False, "zero_sum"
    if abs(s - 1.0) > SUM_TOL:
        return False, f"sum_not_1 sum={s:.6f}"
    return True, "ok"


def verify_parquet(path: Path) -> tuple[bool, dict]:
    """Return (pass, detail dict)."""
    detail: dict = {
        "path": str(path),
        "missing_stats": [],
        "zero_row_stats": [],
        "row_counts": {},
        "pmf_invalid_sample": [],
    }
    if not path.is_file():
        detail["error"] = "file_missing"
        print("STAT_GRID_MISSION_STATS_CONTRACT_FAIL", detail)
        return False, detail

    df = pd.read_parquet(path)
    if "stat" not in df.columns:
        detail["error"] = "missing_stat_column"
        print("STAT_GRID_MISSION_STATS_CONTRACT_FAIL", detail)
        return False, detail

    vc = df["stat"].astype(str).str.lower().value_counts()
    counts = {str(k): int(v) for k, v in vc.items()}
    detail["row_counts"] = counts
    present = set(counts.keys())

    missing = [s for s in MISSION if s not in present]
    if missing:
        detail["missing_stats"] = missing

    zero_stats = [s for s in MISSION if counts.get(s, 0) == 0]
    if zero_stats:
        detail["zero_row_stats"] = zero_stats

    if missing or zero_stats:
        detail["error"] = "mission_stat_coverage"
        print("STAT_GRID_MISSION_STATS_CONTRACT_FAIL", json.dumps(detail, indent=2, default=str))
        return False, detail

    pmf_col = "pmf" if "pmf" in df.columns else None
    if pmf_col:
        bad = 0
        max_scan = min(len(df), 5000)
        for i, raw in enumerate(df[pmf_col].iloc[:max_scan]):
            arr = _parse_pmf_cell(raw)
            ok, why = _pmf_valid(arr) if arr is not None else (False, "unparseable")
            if not ok:
                bad += 1
                if len(detail["pmf_invalid_sample"]) < 12:
                    detail["pmf_invalid_sample"].append(
                        {"row_index": int(i), "reason": why}
                    )
        detail["pmf_rows_scanned"] = max_scan
        detail["pmf_invalid_rows_in_scan"] = bad
        if bad > 0:
            detail["error"] = "invalid_pmfs_in_sample"
            print("STAT_GRID_MISSION_STATS_CONTRACT_FAIL", json.dumps(detail, indent=2, default=str))
            return False, detail
    else:
        detail["error"] = "missing_pmf_column"
        print("STAT_GRID_MISSION_STATS_CONTRACT_FAIL", json.dumps(detail, indent=2, default=str))
        return False, detail

    print("STAT_GRID_MISSION_STATS_CONTRACT_PASS", json.dumps({"row_counts": counts}, default=str))
    return True, detail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--path", default=None)
    args = ap.parse_args()
    if args.path:
        path = Path(args.path)
    elif args.date:
        path = REPO_ROOT / "predictions" / f"stat_grid_{str(args.date).strip()[:10]}.parquet"
    else:
        print("FATAL: pass --date or --path", file=sys.stderr)
        return 2

    ok, detail = verify_parquet(path)
    if ok:
        py = sys.executable
        stats_s = " ".join(MISSION_REQUIRED_TARGETS_CANONICAL)
        print(
            "rebuild_command:",
            f"{py} scripts/build_stat_grid_pmfs.py --date <DATE> --stats {stats_s}",
        )
        return 0

    py = sys.executable
    d = args.date or path.stem.replace("stat_grid_", "")[:10]
    stats_s = " ".join(MISSION_REQUIRED_TARGETS_CANONICAL)
    print(
        "recommended_rebuild:",
        f"{py} {REPO_ROOT / 'scripts' / 'build_stat_grid_pmfs.py'} --date {d} --stats {stats_s}",
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
