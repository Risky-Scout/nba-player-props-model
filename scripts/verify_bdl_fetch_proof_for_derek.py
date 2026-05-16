#!/usr/bin/env python3
"""Emit a structured proof of the BDL /v2/lineups fetch state.

Writes ``artifacts/source_readiness/{date}/bdl_fetch_proof.json``.

States distinguished:

    bdl_key_missing
        ``BDL_API_KEY`` env var is unset; we never made a fetch attempt.
    bdl_request_failed
        BDL HTTP call raised; surface the exception.
    bdl_empty_pre_confirmation
        BDL responded but with zero rows. This is honest pre-confirmation
        state (most morning publishes) and must NOT permit a full-roster
        PMF publish — the M8.9 eligibility gate handles that.
    bdl_populated_confirmed_live
        BDL responded with one or more lineup rows.
    bdl_snapshot_missing
        We have no local snapshot under ``data/bdl_lineups/{date}/`` AND
        the run was operating in disk-only mode.
    bdl_snapshot_stale
        Local snapshot age exceeds ``--max-age-hours``.

The morning projected-mode pipeline does NOT require confirmed BDL
lineups — but it DOES require an explicit state representation so we
never silently fall back to publishing a full-roster.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _scan_local_snapshot(date: str) -> dict[str, Any]:
    """Look for previously-captured BDL snapshots under
    ``data/bdl_lineups/{date}/``. Returns metadata used to classify
    bdl_snapshot_missing / bdl_snapshot_stale."""
    d = REPO_ROOT / "data" / "bdl_lineups" / date
    if not d.exists():
        return {"present": False, "rows": 0, "files": [], "oldest_age_hours": None,
                "newest_age_hours": None}

    files = sorted(d.iterdir())
    if not files:
        return {"present": False, "rows": 0, "files": [], "oldest_age_hours": None,
                "newest_age_hours": None}

    rows = 0
    ages_hours: list[float] = []
    file_meta: list[dict[str, Any]] = []
    now = time.time()
    try:
        import pandas as pd
    except Exception:
        pd = None

    for f in files:
        try:
            mtime = f.stat().st_mtime
            age_h = (now - mtime) / 3600.0
            ages_hours.append(age_h)
            file_rows = 0
            if pd is not None and f.suffix == ".parquet":
                try:
                    file_rows = int(len(pd.read_parquet(f)))
                except Exception:
                    file_rows = 0
            elif f.suffix == ".json":
                try:
                    obj = json.loads(f.read_text())
                    if isinstance(obj, list):
                        file_rows = len(obj)
                    elif isinstance(obj, dict) and isinstance(obj.get("data"), list):
                        file_rows = len(obj["data"])
                except Exception:
                    file_rows = 0
            rows += file_rows
            file_meta.append({
                "path": str(f.relative_to(REPO_ROOT)),
                "rows": file_rows,
                "age_hours": age_h,
            })
        except Exception:
            continue

    return {
        "present": True,
        "rows": int(rows),
        "files": file_meta,
        "oldest_age_hours": max(ages_hours) if ages_hours else None,
        "newest_age_hours": min(ages_hours) if ages_hours else None,
    }


def _attempt_live_fetch(game_ids: list[int]) -> dict[str, Any]:
    """Optional live BDL /v2/lineups fetch. Returns success/error details
    without persisting state. Empty response is acceptable
    (pre-confirmation)."""
    result: dict[str, Any] = {
        "attempted": False,
        "ok": False,
        "rows": 0,
        "error": None,
    }
    if not game_ids:
        return result

    try:
        bdl = importlib.import_module("nba_props_model.data.bdl_client")
    except Exception as exc:
        result["error"] = f"import bdl_client failed: {exc}"
        return result

    if not callable(getattr(bdl, "get_lineups", None)):
        result["error"] = "bdl_client.get_lineups missing"
        return result

    result["attempted"] = True
    total = 0
    for gid in game_ids:
        try:
            resp = bdl.get_lineups(int(gid))
            if isinstance(resp, list):
                total += len(resp)
            elif isinstance(resp, dict) and isinstance(resp.get("data"), list):
                total += len(resp["data"])
        except Exception as exc:
            result["error"] = f"get_lineups({gid}) raised {type(exc).__name__}: {exc}"
            return result
    result["ok"] = True
    result["rows"] = int(total)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, help="YYYY-MM-DD slate date")
    ap.add_argument(
        "--max-age-hours",
        type=float,
        default=6.0,
        help="snapshot older than this is bdl_snapshot_stale",
    )
    ap.add_argument(
        "--smoke-game-id",
        type=int,
        nargs="*",
        default=None,
        help="optional list of game_ids to live-fetch /v2/lineups (no persistence)",
    )
    args = ap.parse_args(argv)

    bdl_key_present = bool(os.environ.get("BDL_API_KEY", "").strip())
    snap = _scan_local_snapshot(args.date)
    fetch = _attempt_live_fetch(args.smoke_game_id or []) if bdl_key_present else {
        "attempted": False, "ok": False, "rows": 0, "error": "BDL_API_KEY not set",
    }

    if not bdl_key_present:
        state = "bdl_key_missing"
    elif fetch["attempted"] and not fetch["ok"]:
        state = "bdl_request_failed"
    elif fetch["attempted"] and fetch["ok"] and fetch["rows"] == 0:
        state = "bdl_empty_pre_confirmation"
    elif fetch["attempted"] and fetch["ok"] and fetch["rows"] > 0:
        state = "bdl_populated_confirmed_live"
    elif not snap["present"]:
        state = "bdl_snapshot_missing"
    elif snap["present"] and snap.get("rows", 0) == 0:
        state = "bdl_empty_pre_confirmation"
    elif snap["present"] and (snap.get("oldest_age_hours") or 0.0) > float(args.max_age_hours):
        state = "bdl_snapshot_stale"
    else:
        state = "bdl_populated_confirmed_live"

    payload = {
        "delivery_date": args.date,
        "checked_at_utc": _now_utc_iso(),
        "bdl_key_present": bdl_key_present,
        "local_snapshot": snap,
        "live_fetch": fetch,
        "max_age_hours": float(args.max_age_hours),
        "state": state,
        "morning_projected_mode_allowed": state in {
            "bdl_empty_pre_confirmation",
            "bdl_populated_confirmed_live",
            "bdl_snapshot_missing",
        },
        "note": (
            "Morning projected mode does not require confirmed BDL lineups, "
            "but the M8.9 eligibility gate must run upstream so empty BDL "
            "never permits a full-roster PMF publish."
        ),
    }

    out_dir = REPO_ROOT / "artifacts" / "source_readiness" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bdl_fetch_proof.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"  wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"  state={state}")
    if state in {"bdl_key_missing", "bdl_request_failed"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
