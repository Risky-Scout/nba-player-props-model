#!/usr/bin/env python3
"""Build the Wizard of Odds public export folder.

Phase 12B — assembles a clean, public-facing mirror of `deliveries/<date>/wizard_of_odds/`
for FTP upload to the WoO portal. Only model-only PMF artifacts and their manifests
are published. Internal Derek review packages, canonical source dumps, and after-game
scratch are intentionally excluded.

Phase 12D-amend — the public export is the **monetization** feed. It runs earlier in
the day than Derek's evaluation feed so users can see model predictions, click
affiliate odds buttons, and enter the sportsbook funnel before lineups confirm.
This script enriches each date with a `monetization_view` (csv / parquet / jsonl)
that joins market_comparison rows with optional affiliate links from
``config/wizardofodds_affiliate_links.json``. When the affiliate config is absent
or has no mapping for a book, ``monetization_status`` is set to
``needs_affiliate_mapping`` and ``affiliate_url`` / ``odds_button_url`` stay blank
— affiliate links are never fabricated.

CLI flags relevant to the monetization lifecycle:
    --snapshot-type-label     stamps every monetization_view row's snapshot_type
                              (e.g. ``woo_morning_monetization``); falls back to
                              the run_manifest snapshot_type when omitted.
    --finality-status-override
                              stamps every monetization_view row's finality_status
                              (e.g. ``PROVISIONAL_EARLY_MARKET``); falls back to the
                              run_manifest finality_status when omitted.
    --affiliate-config        path override; default
                              ``config/wizardofodds_affiliate_links.json``.

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
            monetization_view.{csv,parquet,jsonl}      # Phase 12D-amend
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
DEFAULT_AFFILIATE_CONFIG = REPO_ROOT / "config" / "wizardofodds_affiliate_links.json"

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

FINALITY_RANK = {
    "final": 3,
    "provisional": 2,
    "PROVISIONAL_EARLY_MARKET": 1,
}


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


def _load_affiliate_config(path: Path) -> dict:
    """Load the WoO affiliate-link config. Schema (all keys optional):

        {
          "version": 1,
          "default_button_label": "Bet at <book>",
          "books": {
            "draftkings": {
              "affiliate_url": "https://aff.example/dk?subid={market_key}",
              "odds_button_url": "https://aff.example/dk-odds?subid={market_key}",
              "active": true
            },
            ...
          }
        }

    The script never fabricates URLs — when a book has no entry (or the
    file is absent) ``monetization_status=needs_affiliate_mapping`` and
    both URL fields stay null."""
    if not path.exists():
        return {"_present": False, "books": {}}
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return {"_present": False, "_error": repr(e), "books": {}}
    if not isinstance(data, dict):
        return {"_present": False, "books": {}}
    data.setdefault("books", {})
    data["_present"] = True
    return data


def _affiliate_for_book(book: str, affiliate_cfg: dict) -> dict:
    """Return {affiliate_url, odds_button_url, monetization_status} for a
    book. Never fabricates URLs."""
    cfg_present = bool(affiliate_cfg.get("_present"))
    books = affiliate_cfg.get("books") or {}
    entry = books.get(book) if isinstance(books, dict) else None
    if (
        cfg_present
        and isinstance(entry, dict)
        and entry.get("active", True)
        and (entry.get("affiliate_url") or entry.get("odds_button_url"))
    ):
        return {
            "affiliate_url": entry.get("affiliate_url"),
            "odds_button_url": entry.get("odds_button_url"),
            "monetization_status": "active",
        }
    return {
        "affiliate_url": None,
        "odds_button_url": None,
        "monetization_status": "needs_affiliate_mapping",
    }


def _write_monetization_view(
    *,
    src_dir: Path,
    dst_dir: Path,
    run_manifest: dict,
    snapshot_type_label: str | None,
    finality_status_override: str | None,
    affiliate_cfg: dict,
) -> dict:
    """Emit `monetization_view.{csv,parquet,jsonl}` for the date.

    Source is the canonical `market_comparison.parquet`. Per-row enrichment:
    affiliate_url, odds_button_url, monetization_status, snapshot_type,
    snapshot_time_utc, finality_status, plus quality/freshness flags
    inherited from the run manifest. PMF columns are passed through
    unchanged — public output remains model-only."""
    import csv as _csv
    import pandas as pd

    src_path = src_dir / "market_comparison.parquet"
    if not src_path.exists():
        return {
            "rows": 0,
            "monetization_status_summary": {},
            "missing_source": "market_comparison.parquet",
        }
    df = pd.read_parquet(src_path).copy()

    snapshot_type_value = (
        snapshot_type_label or run_manifest.get("snapshot_type") or "unknown"
    )
    finality_value = (
        finality_status_override
        or run_manifest.get("finality_status")
        or "unknown"
    )
    snapshot_time_utc = run_manifest.get("snapshot_time_utc")
    qr = run_manifest.get("quality_rollup") or {}
    fm = run_manifest.get("freshness_manifest") or {}

    def _aff(book: str | None) -> dict:
        return _affiliate_for_book(str(book) if book else "", affiliate_cfg)

    aff_rows = [_aff(b) for b in df.get("book", pd.Series([None] * len(df)))]
    df["affiliate_url"] = [r["affiliate_url"] for r in aff_rows]
    df["odds_button_url"] = [r["odds_button_url"] for r in aff_rows]
    df["monetization_status"] = [r["monetization_status"] for r in aff_rows]
    df["snapshot_type_public"] = snapshot_type_value
    df["snapshot_time_utc_public"] = snapshot_time_utc
    df["finality_status_public"] = finality_value
    df["lineup_freshness_rollup"] = json.dumps(
        qr.get("lineup_freshness_status") or {}, sort_keys=True
    )
    df["availability_freshness_status"] = fm.get("availability_freshness_status")
    df["odds_freshness_status"] = (
        fm.get("odds_status")
        if isinstance(fm, dict)
        else None
    )

    csv_path = dst_dir / "monetization_view.csv"
    parquet_path = dst_dir / "monetization_view.parquet"
    jsonl_path = dst_dir / "monetization_view.jsonl"
    df.to_csv(csv_path, index=False, quoting=_csv.QUOTE_MINIMAL)
    df.to_parquet(parquet_path, index=False)
    with jsonl_path.open("w") as f:
        for r in df.to_dict(orient="records"):
            clean = {k: (None if (isinstance(v, float) and pd.isna(v)) else v) for k, v in r.items()}
            f.write(json.dumps(clean, default=str) + "\n")

    summary: dict[str, int] = {}
    for s in df["monetization_status"]:
        summary[s] = summary.get(s, 0) + 1
    return {
        "rows": int(len(df)),
        "monetization_status_summary": summary,
        "snapshot_type_public": snapshot_type_value,
        "finality_status_public": finality_value,
        "files": {
            "csv": csv_path.name,
            "parquet": parquet_path.name,
            "jsonl": jsonl_path.name,
        },
    }


def _date_summary(
    date: str,
    src_dir: Path,
    copy_result: dict,
    *,
    monetization: dict | None = None,
) -> dict:
    rm = _read_manifest(src_dir)
    out = {
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
    if monetization is not None:
        out["monetization"] = monetization
    return out


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
    *,
    snapshot_type_label: str | None = None,
    finality_status_override: str | None = None,
    affiliate_config_path: Path | None = None,
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

    affiliate_cfg = _load_affiliate_config(
        affiliate_config_path or DEFAULT_AFFILIATE_CONFIG
    )

    summaries: list[dict] = []
    for date in dates:
        src = deliveries_root / date / "wizard_of_odds"
        dst = out_dir / date
        copy_result = _copy_files(src, dst)
        rm = _read_manifest(src)
        # Phase 12F — do **not** swallow exceptions here. The previous
        # `except Exception` catch silently turned `ModuleNotFoundError:
        # pandas` into a "skipped" monetization_view, which produced
        # incomplete public exports in CI. The function already handles
        # the only expected no-op case (missing market_comparison.parquet)
        # via an early return; anything else is a real bug and must
        # surface.
        monet = _write_monetization_view(
            src_dir=src,
            dst_dir=dst,
            run_manifest=rm,
            snapshot_type_label=snapshot_type_label,
            finality_status_override=finality_status_override,
            affiliate_cfg=affiliate_cfg,
        )
        summaries.append(
            _date_summary(date, src, copy_result, monetization=monet)
        )

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
        "affiliate_config": {
            "path": str(
                (affiliate_config_path or DEFAULT_AFFILIATE_CONFIG)
                .relative_to(REPO_ROOT)
            ),
            "present": bool(affiliate_cfg.get("_present")),
            "books_mapped": (
                sorted(affiliate_cfg.get("books", {}).keys())
                if affiliate_cfg.get("_present")
                else []
            ),
        },
        "snapshot_type_label": snapshot_type_label,
        "finality_status_override": finality_status_override,
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
        "--all-available",
        action="store_true",
        help="build every date with a wizard_of_odds run_manifest.json. "
        "This is the default behaviour when --date is omitted; the flag is "
        "accepted explicitly so workflows and runbooks can spell out intent. "
        "Mutually exclusive with --date.",
    )
    ap.add_argument(
        "--keep-existing",
        action="store_true",
        help="do not wipe existing date dirs in out-dir before writing",
    )
    ap.add_argument(
        "--snapshot-type-label",
        default=None,
        help="stamp the public monetization_view's snapshot_type_public column "
        "(e.g. woo_morning_monetization). Falls back to the run_manifest "
        "snapshot_type when omitted.",
    )
    ap.add_argument(
        "--finality-status-override",
        default=None,
        help="stamp the public monetization_view's finality_status_public "
        "column (e.g. PROVISIONAL_EARLY_MARKET). Falls back to the "
        "run_manifest finality_status when omitted.",
    )
    ap.add_argument(
        "--affiliate-config",
        type=Path,
        default=None,
        help="path to wizardofodds_affiliate_links.json (default: "
        "config/wizardofodds_affiliate_links.json). Affiliate URLs are "
        "never fabricated: when the file is absent or a book has no "
        "mapping, monetization_status=needs_affiliate_mapping.",
    )
    args = ap.parse_args(argv)

    if args.all_available and args.date:
        ap.error("--all-available is mutually exclusive with --date")

    top = build(
        deliveries_root=args.deliveries_root.resolve(),
        out_dir=args.out_dir.resolve(),
        only_dates=args.date,
        keep_existing=args.keep_existing,
        snapshot_type_label=args.snapshot_type_label,
        finality_status_override=args.finality_status_override,
        affiliate_config_path=(
            args.affiliate_config.resolve()
            if args.affiliate_config else None
        ),
    )
    print(
        f"public_export wrote {len(top['dates'])} date(s); latest={top['latest_date']}; "
        f"out_dir={top['out_dir']}"
    )
    if top["dates"]:
        for s in top["dates"]:
            m = s.get("monetization") or {}
            ms = m.get("monetization_status_summary") or {}
            print(
                f"  {s['date']}: monetization rows={m.get('rows', 0)}  "
                f"snapshot_type_public={m.get('snapshot_type_public')}  "
                f"finality_status_public={m.get('finality_status_public')}  "
                f"status={ms}"
            )
    aff = top.get("affiliate_config") or {}
    print(
        f"  affiliate_config present={aff.get('present')} "
        f"books_mapped={aff.get('books_mapped')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
