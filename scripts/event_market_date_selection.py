"""Shared date selection for M8.6 event-market tooling (inventory / fingerprint)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def dates_fingerprint(dates: list[str]) -> str:
    u = sorted({str(d).strip() for d in dates if str(d).strip()})
    return hashlib.sha256(",".join(u).encode("utf-8")).hexdigest()[:12]


def dates_label_from_fingerprint(fp: str) -> str:
    return f"dates_{fp}"


def load_dates_from_inventory_csv(
    path: Path,
    *,
    eligible_only: bool,
) -> tuple[list[str], pd.DataFrame]:
    """Return sorted unique dates and the full inventory frame (filtered rows used)."""
    df = pd.read_csv(path)
    if "date" not in df.columns:
        print(f"FATAL: inventory missing 'date' column: {path}", file=sys.stderr)
        raise SystemExit(2)
    work = df.copy()
    work["date"] = work["date"].astype(str).str.slice(0, 10)
    if eligible_only and "eligible_for_event_market_backtest" in work.columns:
        ev = work["eligible_for_event_market_backtest"]
        if ev.dtype == object:
            ev = ev.astype(str).str.lower().isin(("1", "true", "t", "yes"))
        work = work[ev == True]  # noqa: E712
    dates = sorted(work["date"].dropna().unique().tolist())
    return dates, work


def resolve_event_market_label(
    *,
    date: str | None,
    start_date: str | None,
    end_date: str | None,
    dates_file: str | None,
    include_ineligible: bool,
) -> tuple[list[str], str, dict]:
    """Return (dates_used, label, meta)."""
    from datetime import date as dt_date, timedelta

    modes = sum(bool(x) for x in (date, (start_date and end_date), dates_file))
    if modes > 1:
        print("FATAL: use only one of --date, --start-date/--end-date, --dates-file", file=sys.stderr)
        raise SystemExit(2)
    if (start_date or end_date) and not (start_date and end_date):
        print("FATAL: --start-date and --end-date together", file=sys.stderr)
        raise SystemExit(2)

    meta: dict = {"mode": None, "dates_fingerprint": None}
    if dates_file:
        dates, _inv = load_dates_from_inventory_csv(
            Path(dates_file),
            eligible_only=not include_ineligible,
        )
        if not dates:
            print("FATAL: no dates after inventory filter", file=sys.stderr)
            raise SystemExit(2)
        fp = dates_fingerprint(dates)
        meta.update({"mode": "dates_file", "dates_fingerprint": fp, "inventory_path": dates_file})
        return dates, dates_label_from_fingerprint(fp), meta
    if date:
        meta["mode"] = "single_date"
        return [date], date, meta
    if start_date and end_date:
        s = dt_date.fromisoformat(start_date)
        e = dt_date.fromisoformat(end_date)
        dlist: list[str] = []
        while s <= e:
            dlist.append(s.isoformat())
            s += timedelta(days=1)
        meta["mode"] = "date_range"
        meta["start_date"] = start_date
        meta["end_date"] = end_date
        return dlist, f"{start_date}_{end_date}", meta
    print("FATAL: pass --date, --start-date/--end-date, or --dates-file", file=sys.stderr)
    raise SystemExit(2)


def latest_oof_verification_summary(repo_root: Path | None = None) -> dict | None:
    """Newest verification_summary.json under optimizer verification trees."""
    root = repo_root or REPO_ROOT
    cand = sorted(
        root.glob("_stat_grid_delivery_calibration_optimizer/verification/before_after_oof_*/verification_summary.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not cand:
        return None
    try:
        return json.loads(cand[0].read_text(encoding="utf-8"))
    except Exception:
        return None


def model_only_calibration_claim_allowed(repo_root: Path | None = None) -> bool:
    """True only if latest OOF verification reports zero failed supported stat-role cells."""
    summ = latest_oof_verification_summary(repo_root)
    if not summ:
        return False
    failed = summ.get("failed_supported_stat_role_cells_after")
    try:
        return int(failed) == 0
    except Exception:
        return False
