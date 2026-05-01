"""Phase 13F — resolve the latest safe as-of-date for nightly challenger training.

Reads ``data/player_game_stats.parquet`` (tracked in git, available on every
checkout) and identifies the most recent game date with finalized outcomes.
Rejects today (UTC) if games are still in progress, and rejects any date with
sparse outcome coverage (fewer player-game rows than a per-day floor).

Usage:
    python3 scripts/resolve_latest_safe_training_date.py [--floor-rows N]

Outputs:
    artifacts/nightly_training/latest_safe_training_date.json

Hard rules:
- No future leakage. The resolved as_of_date is strictly the latest
  finalized-outcome date, never inferred or fabricated.
- Today (UTC) is always rejected — games may still be in progress.
- The default floor (50 player-game rows) is conservative; an NBA slate
  produces ~250-400 rows on a busy day. Days below the floor are likely
  partial / still-arriving.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    NIGHTLY_TRAINING_DIR,
    git_commit,
    utcnow,
    utcnow_iso,
    write_json_atomic,
)

PLAYER_GAME_STATS = REPO_ROOT / "data" / "player_game_stats.parquet"
DEFAULT_FLOOR_ROWS = 50  # below this, outcomes for the date are likely partial


def resolve(floor_rows: int = DEFAULT_FLOOR_ROWS) -> dict:
    today_utc = utcnow().date()
    out: dict = {
        "schema_version": "1.0",
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "today_utc": today_utc.isoformat(),
        "floor_rows": floor_rows,
        "input_path": str(PLAYER_GAME_STATS.relative_to(REPO_ROOT)),
        "input_present": PLAYER_GAME_STATS.exists(),
        "rejected_dates": [],
        "no_future_leakage_precheck": False,
        "resolved_as_of_date": None,
        "max_outcome_date": None,
    }
    if not PLAYER_GAME_STATS.exists():
        out["error"] = f"missing {out['input_path']}"
        return out
    try:
        import pandas as pd
    except ImportError:
        out["error"] = "pandas not installed"
        return out

    df = pd.read_parquet(PLAYER_GAME_STATS, columns=["game_date"])
    if df.empty:
        out["error"] = "player_game_stats.parquet is empty"
        return out

    counts = df.groupby(df["game_date"].astype(str).str[:10]).size().sort_index(ascending=False)
    out["max_outcome_date"] = str(counts.index.max())

    rejected: list[dict] = []
    chosen: str | None = None
    for date_str, n_rows in counts.items():
        d = dt.date.fromisoformat(str(date_str))
        if d >= today_utc:
            rejected.append({"date": date_str, "rows": int(n_rows), "reason": "today_or_future_utc"})
            continue
        if int(n_rows) < floor_rows:
            rejected.append(
                {"date": date_str, "rows": int(n_rows), "reason": f"rows<{floor_rows}_likely_partial"}
            )
            continue
        chosen = date_str
        break

    out["rejected_dates"] = rejected[:10]
    out["resolved_as_of_date"] = chosen
    out["no_future_leakage_precheck"] = chosen is not None and dt.date.fromisoformat(chosen) < today_utc
    if chosen is None:
        out["error"] = "no_safe_date_found"
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Resolve latest safe training date.")
    p.add_argument("--floor-rows", type=int, default=DEFAULT_FLOOR_ROWS)
    args = p.parse_args(argv)

    NIGHTLY_TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = NIGHTLY_TRAINING_DIR / "latest_safe_training_date.json"
    payload = resolve(floor_rows=args.floor_rows)
    write_json_atomic(out_path, payload)

    if payload.get("resolved_as_of_date"):
        print(payload["resolved_as_of_date"])
        return 0
    print(f"NO_SAFE_DATE: {payload.get('error', 'unknown')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
