#!/usr/bin/env python3
"""scripts/build_woo_dashboard.py

Build the two customer-facing HTML pages for Wizard of Odds NBA props:

  predictions/nba-props.html         — affiliate dashboard with bet sizing
  predictions/nba-pmf-research.html  — pure PMF distribution research page

Both files are SELF-CONTAINED: the JSON is embedded inline. The HTML never
fetches anything at runtime, so the dev.wizardofodds.com nginx 401 issue
on sibling JSON requests cannot break the page.

INPUT (read-only — produced by scripts/publish_woo_public_export.py):

  public_export/wizard_of_odds/<date>/affiliate_dashboard.json
  public_export/wizard_of_odds/<date>/pmf_research.json

  predictions/_template_nba_props.html
  predictions/_template_nba_pmf_research.html

OUTPUT:

  predictions/nba-props.html
  predictions/nba-pmf-research.html

This script does not modify any model artifact. It is a thin renderer.
It also prints an explicit audit of which stats appear in the JSON so
the operator can verify before uploading. Stats outside the supported
allowlist (pts/reb/ast/fg3m/tov) are filtered at render time by the
template's JS and reported here at build time.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys  # M8.1: defensive — already imported elsewhere is fine
sys.path.insert(0, str(REPO_ROOT / "src"))  # noqa: E402

from nba_props_model.targets import (  # noqa: E402
    MISSION_REQUIRED_TARGETS_CANONICAL,
)

PUBLIC_EXPORT = REPO_ROOT / "public_export" / "wizard_of_odds"
PREDICTIONS_DIR = REPO_ROOT / "predictions"

DASHBOARD_TEMPLATE = PREDICTIONS_DIR / "_template_nba_props.html"
PMF_TEMPLATE       = PREDICTIONS_DIR / "_template_nba_pmf_research.html"

DASHBOARD_OUTPUT   = PREDICTIONS_DIR / "nba-props.html"
PMF_OUTPUT         = PREDICTIONS_DIR / "nba-pmf-research.html"

DASHBOARD_MARKER   = "<!-- INJECT_DASHBOARD_DATA_HERE -->"
PMF_MARKER         = "<!-- INJECT_PMF_DATA_HERE -->"

# Mirrors SUPPORTED_SINGLE_STATS in both HTML templates. Used here only
# for the build-time audit print. Actual runtime filtering happens in
# the templates' JS so the JSON we embed remains the unmodified output
# of publish_woo_public_export.py.
SUPPORTED_SINGLE_STATS = set(MISSION_REQUIRED_TARGETS_CANONICAL)  # M8.1: was 5-stat literal


def _safe_json_for_inline_script(payload: dict) -> str:
    s = json.dumps(payload, default=str)
    return s.replace("</", "<\\/")


def _audit_dashboard_stats(rows: list) -> None:
    if not rows:
        print("  (audit) no rows to audit")
        return
    counts = Counter(str(r.get("stat") or "").lower() for r in rows)
    print("  (audit) affiliate_dashboard.json stats present:")
    for s, n in sorted(counts.items(), key=lambda x: -x[1]):
        marker = "WILL DISPLAY" if s in SUPPORTED_SINGLE_STATS else "filtered (not supported)"
        print(f"    {s:<10s} {n:>4d} rows  -> {marker}")
    displayed = sum(n for s, n in counts.items() if s in SUPPORTED_SINGLE_STATS)
    filtered  = sum(n for s, n in counts.items() if s not in SUPPORTED_SINGLE_STATS)
    print(f"  (audit) total dashboard rows that will display: {displayed}")
    if filtered:
        flt = {s for s in counts if s not in SUPPORTED_SINGLE_STATS}
        print(f"  (audit) total filtered:                          {filtered}  ({', '.join(sorted(flt))})")


def _audit_pmf_stats(players: list) -> None:
    if not players:
        print("  (audit) no players to audit")
        return
    counts = Counter()
    for p in players:
        for s in (p.get("stats") or {}).keys():
            counts[str(s).lower()] += 1
    print("  (audit) pmf_research.json stats present (across all players):")
    for s, n in sorted(counts.items(), key=lambda x: -x[1]):
        marker = "WILL DISPLAY" if s in SUPPORTED_SINGLE_STATS else "filtered (not supported)"
        print(f"    {s:<10s} {n:>4d} player-distributions  -> {marker}")
    will_display = sum(n for s, n in counts.items() if s in SUPPORTED_SINGLE_STATS)
    will_filter  = sum(n for s, n in counts.items() if s not in SUPPORTED_SINGLE_STATS)
    print(f"  (audit) total PMF distributions that will display: {will_display}")
    if will_filter:
        flt = {s for s in counts if s not in SUPPORTED_SINGLE_STATS}
        print(f"  (audit) total filtered:                            {will_filter}  ({', '.join(sorted(flt))})")


def render_dashboard(date: str, dry_run: bool = False) -> int:
    src = PUBLIC_EXPORT / date / "affiliate_dashboard.json"
    if not src.exists():
        print(f"FATAL: {src.relative_to(REPO_ROOT)} not found. "
              f"Run scripts/publish_woo_public_export.py --date {date} first.")
        return 2
    if not DASHBOARD_TEMPLATE.exists():
        print(f"FATAL: {DASHBOARD_TEMPLATE.relative_to(REPO_ROOT)} not found.")
        return 2

    with src.open() as f:
        payload = json.load(f)
    rows = payload.get("rows") or []
    print(f"  affiliate_dashboard.json: {len(rows)} rows, "
          f"date={payload.get('date')}, schema_version={payload.get('schema_version')}")
    _audit_dashboard_stats(rows)

    template = DASHBOARD_TEMPLATE.read_text()
    if DASHBOARD_MARKER not in template:
        print(f"FATAL: template missing marker {DASHBOARD_MARKER!r}.")
        return 2

    embedded = (
        '<script id="dashboard-embedded">\n'
        f'window.EMBEDDED_DATA = {_safe_json_for_inline_script(payload)};\n'
        '</script>'
    )
    html = template.replace(DASHBOARD_MARKER, embedded)
    if not dry_run:
        DASHBOARD_OUTPUT.write_text(html)
        print(f"  wrote {DASHBOARD_OUTPUT.relative_to(REPO_ROOT)}  "
              f"({len(html):,} chars)")
    return 0


def render_pmf_research(date: str, dry_run: bool = False) -> int:
    src_pmf = PUBLIC_EXPORT / date / "pmf_research.json"
    if not src_pmf.exists():
        print(f"FATAL: {src_pmf.relative_to(REPO_ROOT)} not found. "
              f"Run scripts/publish_woo_public_export.py --date {date} first.")
        return 2
    if not PMF_TEMPLATE.exists():
        print(f"FATAL: {PMF_TEMPLATE.relative_to(REPO_ROOT)} not found.")
        return 2

    with src_pmf.open() as f:
        pmf_payload = json.load(f)
    print(f"  pmf_research.json: {pmf_payload.get('count_players')} players, "
          f"{pmf_payload.get('count_props')} distributions, "
          f"convention='{pmf_payload.get('tail_bucket_convention', '')}'")
    _audit_pmf_stats(pmf_payload.get("players") or [])

    template = PMF_TEMPLATE.read_text()
    if PMF_MARKER not in template:
        print(f"FATAL: template missing marker {PMF_MARKER!r}.")
        return 2

    embedded = (
        '<script id="pmf-embedded">\n'
        f'window.EMBEDDED_PMF_DATA = {_safe_json_for_inline_script(pmf_payload)};\n'
        '</script>'
    )
    html = template.replace(PMF_MARKER, embedded)
    if not dry_run:
        PMF_OUTPUT.write_text(html)
        print(f"  wrote {PMF_OUTPUT.relative_to(REPO_ROOT)}  "
              f"({len(html):,} chars)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("=" * 72)
    print(f"build_woo_dashboard --date {args.date}")
    print("=" * 72)
    print()
    print(f"Allowlist: {sorted(SUPPORTED_SINGLE_STATS)}")
    # M8.1: allowlist is now the 11-stat mission canonical; the only filtered
    # tokens are non-mission stats like 'ra' and 'reb_ast'.
    print("Allowlist source: nba_props_model.targets.MISSION_REQUIRED_TARGETS_CANONICAL.")
    print("Anything outside the allowlist (e.g. 'ra', 'reb_ast') is filtered before render.")
    print()

    rc1 = render_dashboard(args.date, dry_run=args.dry_run)
    print()
    rc2 = render_pmf_research(args.date, dry_run=args.dry_run)

    if rc1 == 0 and rc2 == 0:
        print()
        print("WOO_DASHBOARD_BUILD_PASS  date=" + args.date)
        return 0
    print()
    print("WOO_DASHBOARD_BUILD_FAILED  date=" + args.date)
    return max(rc1, rc2)


if __name__ == "__main__":
    sys.exit(main())
