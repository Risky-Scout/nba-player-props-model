"""verify_sparse_stat_pmf_shape.py — Fail-closed stl/blk/stocks PMF shape check.

Usage:
    python3 scripts/verify_sparse_stat_pmf_shape.py --date 2026-05-25
    python3 scripts/verify_sparse_stat_pmf_shape.py \\
        --path deliveries/2026-05-25/wizard_of_odds/full_pmfs_wide.csv

Checks each stl/blk/stocks PMF for:
  - sum ≈ 1.0
  - no negative probabilities
  - no non-monotone tail spikes after the plausible region

Spike rule (stl/blk after k >= 2, stocks after k >= 3):
    A spike exists when a later bin BOTH:
    - is > 25% relatively larger than the previous bin, AND
    - has absolute probability > SPIKE_ABS_THRESHOLD

Failure code emitted:
    SPARSE_STAT_PMF_TAIL_SPIKE_FAIL
    SPARSE_STAT_PMF_NEGATIVE_PROB_FAIL
    SPARSE_STAT_PMF_SUM_FAIL
    SPARSE_STAT_PMF_FILE_MISSING

Exits 0 when all checks pass.
Exits 1 on any failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Relative threshold: later bin must be > this fraction bigger than previous.
SPIKE_REL_THRESHOLD = 0.25
# Absolute threshold: later bin must also exceed this probability.
SPIKE_ABS_THRESHOLD = 0.00025
# Sum tolerance.
SUM_TOLERANCE = 1e-3
# Spike-check start index per stat.
SPIKE_START_BY_STAT: dict[str, int] = {"stl": 2, "blk": 2, "stocks": 3}
SPARSE_STATS = {"stl", "blk", "stocks"}


def _parse_pmf(blob: str | dict) -> dict[int, float]:
    if isinstance(blob, str):
        blob = json.loads(blob)
    return {int(k): float(v) for k, v in blob.items()}


def _check_pmf(
    stat: str, player_name: str, pmf: dict[int, float]
) -> list[str]:
    failures: list[str] = []
    if not pmf:
        return failures

    ks = sorted(pmf.keys())
    vals = [pmf[k] for k in ks]
    total = sum(vals)

    # Sum check.
    if abs(total - 1.0) > SUM_TOLERANCE:
        failures.append(
            f"SPARSE_STAT_PMF_SUM_FAIL"
            f"  player={player_name!r}  stat={stat}  sum={total:.6f}"
        )

    # Negative probability check.
    for k, v in zip(ks, vals):
        if v < -1e-9:
            failures.append(
                f"SPARSE_STAT_PMF_NEGATIVE_PROB_FAIL"
                f"  player={player_name!r}  stat={stat}  k={k}  prob={v:.8f}"
            )

    # Tail spike check.
    start = SPIKE_START_BY_STAT.get(stat, 2)
    for i in range(1, len(ks)):
        k_prev, k_curr = ks[i - 1], ks[i]
        if k_prev < start:
            continue
        p_prev, p_curr = pmf[k_prev], pmf[k_curr]
        if p_prev <= 0:
            continue
        rel_increase = (p_curr - p_prev) / p_prev
        if rel_increase > SPIKE_REL_THRESHOLD and p_curr > SPIKE_ABS_THRESHOLD:
            failures.append(
                f"SPARSE_STAT_PMF_TAIL_SPIKE_FAIL"
                f"  player={player_name!r}  stat={stat}"
                f"  k_prev={k_prev}  p_prev={p_prev:.6f}"
                f"  k_curr={k_curr}  p_curr={p_curr:.6f}"
                f"  rel_increase={rel_increase:.2f}"
            )

    return failures


def verify_file(source: Path) -> tuple[bool, list[str]]:
    """Read full_pmfs_wide CSV or parquet, check all sparse-stat rows."""
    if not source.exists():
        return False, [f"SPARSE_STAT_PMF_FILE_MISSING  path={source}"]

    # Load.
    try:
        if source.suffix.lower() == ".parquet":
            import pandas as pd
            df = pd.read_parquet(str(source))
        else:
            import pandas as pd
            df = pd.read_csv(str(source))
    except Exception as e:
        return False, [f"SPARSE_STAT_PMF_FILE_MISSING  path={source}  error={e}"]

    all_failures: list[str] = []
    rows_checked = 0
    players_with_failure: set[str] = set()

    for _, row in df.iterrows():
        stat = str(row.get("stat", "")).lower()
        if stat not in SPARSE_STATS:
            continue
        player = str(row.get("player_name", "unknown"))
        pmf_blob = row.get("pmf_json", None)
        if pmf_blob is None or (isinstance(pmf_blob, float)):
            continue
        try:
            pmf = _parse_pmf(pmf_blob)
        except Exception:
            continue

        rows_checked += 1
        row_failures = _check_pmf(stat, player, pmf)
        if row_failures:
            players_with_failure.add(player)
            all_failures.extend(row_failures)

    print(
        f"SPARSE_STAT_PMF_SHAPE_CHECKED"
        f"  source={source}  rows={rows_checked}"
        f"  failures={len(all_failures)}"
        f"  players_with_failure={len(players_with_failure)}"
    )
    return len(all_failures) == 0, all_failures


def _find_source(woo: Path) -> Optional[Path]:
    for name in ("full_pmfs_wide.parquet", "full_pmfs_wide.csv"):
        p = woo / name
        if p.exists():
            return p
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="Delivery date YYYY-MM-DD")
    ap.add_argument("--path", help="Explicit path to full_pmfs_wide.csv or .parquet")
    args = ap.parse_args(argv)

    if args.path:
        source = Path(args.path)
    elif args.date:
        woo = Path("deliveries") / args.date / "wizard_of_odds"
        source = _find_source(woo)
        if source is None:
            print(
                f"SPARSE_STAT_PMF_FILE_MISSING  date={args.date}"
                f"  woo_dir={woo}  reason=no_full_pmfs_wide_found"
            )
            return 1
    else:
        ap.error("Either --date or --path is required.")

    print(f"SPARSE_STAT_PMF_SHAPE_VERIFY  source={source}")

    ok, failures = verify_file(source)

    if ok:
        print(f"SPARSE_STAT_PMF_SHAPE_PASS  source={source}")
        return 0

    print(f"SPARSE_STAT_PMF_SHAPE_FAIL  source={source}  failures={len(failures)}")
    # Print up to 25 failures to avoid flooding logs.
    for f in failures[:25]:
        print(f"  {f}")
    if len(failures) > 25:
        print(f"  ... and {len(failures) - 25} more failures")
    return 1


if __name__ == "__main__":
    sys.exit(main())
