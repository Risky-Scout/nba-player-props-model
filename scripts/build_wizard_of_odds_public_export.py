#!/usr/bin/env python3
"""Build the Wizard of Odds public export folder.

Phase 12B — assembles a clean, public-facing mirror of `deliveries/<date>/wizard_of_odds/`
for FTP upload to the WoO portal. Only model-only PMF artifacts and their manifests
are published. Internal Derek review packages, canonical source dumps, and after-game
scratch are intentionally excluded.

Layout produced under ``public_export/wizard_of_odds/`` (configurable via --out-dir):

    public_export/wizard_of_odds/
        manifest.json                # top-level: dates available + latest pointer
        index.html                   # browseable directory page
        latest/                      # mirror of the most recent date with WoO files
            ...
        <YYYY-MM-DD>/
            fair_odds_board.{csv,parquet,jsonl}
            full_pmfs_wide.{csv,parquet}
            full_pmfs_outcome_level.{csv,parquet}
            market_comparison.{csv,parquet}
            publishable_edges.{csv,parquet}
            run_manifest.json
            README.md

A delivery date is included only if its `wizard_of_odds/run_manifest.json` exists. The
"latest" pointer prefers `final` over `provisional` over the newest available date.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DELIVERIES = REPO_ROOT / "deliveries"
DEFAULT_OUT = REPO_ROOT / "public_export" / "wizard_of_odds"

PUBLIC_FILES = [
    "fair_odds_board.csv",
    "fair_odds_board.parquet",
    "fair_odds_board.jsonl",
    "full_pmfs_wide.csv",
    "full_pmfs_wide.parquet",
    "full_pmfs_outcome_level.csv",
    "full_pmfs_outcome_level.parquet",
    "market_comparison.csv",
    "market_comparison.parquet",
    "publishable_edges.csv",
    "publishable_edges.parquet",
    "run_manifest.json",
    "README.md",
]

FINALITY_RANK = {"final": 2, "provisional": 1}


def _iso_utc(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _list_delivery_dates(deliveries_root: Path) -> list[str]:
    if not deliveries_root.exists():
        return []
    out = []
    for child in sorted(deliveries_root.iterdir()):
        if not child.is_dir():
            continue
        # accept YYYY-MM-DD
        try:
            datetime.strptime(child.name, "%Y-%m-%d")
        except ValueError:
            continue
        if (child / "wizard_of_odds" / "run_manifest.json").exists():
            out.append(child.name)
    return out


def _copy_files(src_dir: Path, dst_dir: Path) -> dict:
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []
    missing: list[str] = []
    for name in PUBLIC_FILES:
        src = src_dir / name
        if not src.exists():
            missing.append(name)
            continue
        dst = dst_dir / name
        shutil.copy2(src, dst)
        copied.append({"name": name, "size_bytes": dst.stat().st_size})
    return {"copied": copied, "missing": missing}


def _read_manifest(src_dir: Path) -> dict:
    p = src_dir / "run_manifest.json"
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _date_summary(date: str, src_dir: Path, copy_result: dict) -> dict:
    rm = _read_manifest(src_dir)
    return {
        "date": date,
        "snapshot_type": rm.get("snapshot_type"),
        "snapshot_time_utc": rm.get("snapshot_time_utc"),
        "model_version": rm.get("model_version"),
        "finality_status": rm.get("finality_status"),
        "finality_blocker_codes": rm.get("finality_blocker_codes", []),
        "row_counts": rm.get("row_counts", {}),
        "books_seen": rm.get("sources", {})
        .get("odds_snapshot", {})
        .get("books_seen", []),
        "tov_status": rm.get("tov_status"),
        "files": copy_result["copied"],
        "missing_files": copy_result["missing"],
    }


def _pick_latest(summaries: list[dict]) -> str | None:
    if not summaries:
        return None
    # prefer highest finality rank, then most recent date
    def key(s: dict):
        rank = FINALITY_RANK.get(s.get("finality_status") or "", 0)
        return (rank, s["date"])

    return max(summaries, key=key)["date"]


def _render_index_html(top: dict) -> str:
    rows = []
    for s in top["dates"]:
        cls = {
            "final": "cls-final",
            "provisional": "cls-prov",
        }.get(s.get("finality_status") or "", "")
        blockers = ", ".join(s.get("finality_blocker_codes") or []) or "&mdash;"
        rc = s.get("row_counts") or {}
        rows.append(
            f"<tr class='{cls}'>"
            f"<td><a href='{s['date']}/'>{s['date']}</a></td>"
            f"<td><code>{s.get('finality_status') or '&mdash;'}</code></td>"
            f"<td><code>{s.get('snapshot_type') or '&mdash;'}</code></td>"
            f"<td class=right>{rc.get('fair_odds_board', '&mdash;')}</td>"
            f"<td class=right>{rc.get('full_pmfs_wide', '&mdash;')}</td>"
            f"<td class=right>{rc.get('publishable_edges', '&mdash;')}</td>"
            f"<td><code>{s.get('model_version') or '&mdash;'}</code></td>"
            f"<td>{blockers}</td>"
            "</tr>"
        )
    latest = top.get("latest_date") or "&mdash;"
    built = top.get("built_at_utc")
    return (
        "<!doctype html><html><head><meta charset=utf-8>"
        "<title>Wizard of Odds — public PMF export</title><style>"
        "body{font-family:system-ui;max-width:1200px;margin:1.5rem auto;padding:0 1rem;color:#222}"
        "h1{margin-top:0}table{border-collapse:collapse;width:100%;font-size:0.92em}"
        "th,td{padding:0.35rem 0.55rem;border:1px solid #ddd;text-align:left}"
        "th{background:#f0f0f0}td.right{text-align:right}"
        ".cls-final{background:#dff5dd}.cls-prov{background:#fff7d6}"
        "code{background:#f3f3f3;padding:0.05em 0.3em;border-radius:3px;font-size:0.9em}"
        ".note{background:#fff8d6;border-left:4px solid #d4a900;padding:0.5rem 0.9rem;margin:0.8rem 0}"
        "</style></head><body>"
        "<h1>Wizard of Odds — public PMF export</h1>"
        f"<p>Built {built}. Latest: <a href='latest/'><code>{latest}</code></a> "
        "(mirror of the most recent FINAL, then PROVISIONAL, then newest date).</p>"
        "<div class='note'>All published PMFs are <b>model-only</b>. Market columns are reference; "
        "no probability has been adjusted to a book line. TOV PMFs come from the Phase 8 calibrators "
        "with no Phase 10D / 10D.2 overlay.</div>"
        "<table><tr><th>date</th><th>finality</th><th>snapshot</th>"
        "<th>fair_odds</th><th>full_pmfs_wide</th><th>publishable_edges</th>"
        "<th>model_version</th><th>blockers</th></tr>"
        + "".join(rows)
        + "</table></body></html>"
    )


def build(
    deliveries_root: Path,
    out_dir: Path,
    only_dates: list[str] | None,
    keep_existing: bool,
) -> dict:
    dates = _list_delivery_dates(deliveries_root)
    if only_dates:
        dates = [d for d in dates if d in set(only_dates)]
    if not dates:
        raise SystemExit(
            f"No deliveries with wizard_of_odds/run_manifest.json found under {deliveries_root}"
        )

    if out_dir.exists() and not keep_existing:
        # only wipe directories we own (date subdirs + latest); leave unrelated files alone
        for child in out_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            elif child.name in {"index.html", "manifest.json"}:
                child.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict] = []
    for date in dates:
        src = deliveries_root / date / "wizard_of_odds"
        dst = out_dir / date
        copy_result = _copy_files(src, dst)
        summaries.append(_date_summary(date, src, copy_result))

    latest_date = _pick_latest(summaries)
    latest_dir = out_dir / "latest"
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    if latest_date:
        shutil.copytree(out_dir / latest_date, latest_dir)

    top = {
        "built_at_utc": _iso_utc(),
        "deliveries_root": str(deliveries_root.relative_to(REPO_ROOT)),
        "out_dir": str(out_dir.relative_to(REPO_ROOT)),
        "latest_date": latest_date,
        "dates": summaries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(top, indent=2) + "\n")
    (out_dir / "index.html").write_text(_render_index_html(top))
    return top


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--deliveries-root",
        type=Path,
        default=DEFAULT_DELIVERIES,
        help="path to deliveries/ root (default: repo deliveries/)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="output directory (default: public_export/wizard_of_odds)",
    )
    ap.add_argument(
        "--date",
        action="append",
        default=None,
        help="restrict to specific date(s); repeatable. Default: all dates with WoO manifest.",
    )
    ap.add_argument(
        "--keep-existing",
        action="store_true",
        help="do not wipe existing date dirs in out-dir before writing",
    )
    args = ap.parse_args(argv)

    top = build(
        deliveries_root=args.deliveries_root.resolve(),
        out_dir=args.out_dir.resolve(),
        only_dates=args.date,
        keep_existing=args.keep_existing,
    )
    print(
        f"public_export wrote {len(top['dates'])} date(s); latest={top['latest_date']}; "
        f"out_dir={top['out_dir']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
