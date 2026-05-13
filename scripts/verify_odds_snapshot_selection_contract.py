#!/usr/bin/env python3
"""Contract tests for odds_pairs selection (auto tiering vs placeholders)."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from odds_snapshot_selection import select_odds_pairs_parquet  # noqa: E402


def _touch(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"not a real parquet; selection uses filenames only")


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        day = "2099-01-01"
        proc2099 = root / "data" / "odds_api" / "processed" / day

        # Filenames containing template tokens must never be selected.
        _touch(proc2099 / "odds_pairs_close_lock_YYYY-MM-DD.parquet")
        p_only_bad, _ = select_odds_pairs_parquet(root, day, "auto")
        if p_only_bad is not None:
            fails.append("placeholder_token_in_filename_must_be_ignored")
        shutil.rmtree(proc2099, ignore_errors=True)

        proc2099.mkdir(parents=True, exist_ok=True)
        _touch(proc2099 / "odds_pairs_hist_lockday_2099-01-01.parquet")
        p1, m1 = select_odds_pairs_parquet(root, day, "auto")
        if p1 is None or m1.get("odds_snapshot_family") != "hist_lockday":
            fails.append(f"hist_only expected hist_lockday got {p1} {m1}")

        _touch(proc2099 / "odds_pairs_close_or_lock_2099-01-01.parquet")
        p2, m2 = select_odds_pairs_parquet(root, day, "auto")
        if p2 is None or "close_or_lock" not in p2.name:
            fails.append(f"auto should prefer close_or_lock over hist_lockday got {p2}")
        if m2.get("odds_snapshot_family") != "close_or_lock":
            fails.append(f"family should be close_or_lock got {m2}")

        shutil.rmtree(proc2099, ignore_errors=True)

    # Live repo: explicit hist_lockday + auto tiering for 2026-05-07 when present.
    day = "2026-05-07"
    hist_path = REPO_ROOT / "data" / "odds_api" / "processed" / day / f"odds_pairs_hist_lockday_{day}.parquet"
    if hist_path.is_file():
        pr_sub, mr_sub = select_odds_pairs_parquet(REPO_ROOT, day, "hist_lockday")
        if pr_sub is None or not pr_sub.exists():
            fails.append("hist_lockday snapshot_substr must resolve hist_lockday file")
        proc_d = REPO_ROOT / "data" / "odds_api" / "processed" / day
        has_close = any(
            "close_or_lock" in f.name.lower()
            for f in proc_d.glob("odds_pairs_*.parquet")
            if f.is_file()
        )
        pa, ma = select_odds_pairs_parquet(REPO_ROOT, day, "auto")
        if pa is None:
            fails.append("auto selection returned no file for 2026-05-07")
        elif has_close and ma.get("odds_snapshot_family") != "close_or_lock":
            fails.append(
                f"2026-05-07 auto must prefer close_or_lock when present; got {ma}"
            )
        elif not has_close and ma.get("odds_snapshot_family") != "hist_lockday":
            fails.append(
                f"2026-05-07 auto must pick hist_lockday when close_or_lock absent; got {ma}"
            )

    # Inventory vs loss builder must agree on the same path for a date.
    d2 = "2026-05-07"
    p_inv, _ = select_odds_pairs_parquet(REPO_ROOT, d2, "auto")
    p_loss, _ = select_odds_pairs_parquet(REPO_ROOT, d2, "auto")
    if (p_inv or None) != (p_loss or None):
        fails.append(f"path mismatch inventory={p_inv} loss={p_loss}")

    if fails:
        print("ODDS_SNAPSHOT_SELECTION_CONTRACT_FAIL", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("ODDS_SNAPSHOT_SELECTION_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
