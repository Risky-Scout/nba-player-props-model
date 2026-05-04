#!/usr/bin/env python3
"""Phase 13AD — verify the Wizard of Odds NBA props page is shippable
and never renders blank.

Checks:
  - ``predictions/nba-props.html`` exists and is > 5 KB
  - the HTML has a visible fallback / no-data state (``state``,
    ``static-banner``, or ``showState`` reference)
  - the HTML references a local JSON fallback (so it can render even
    when the deployed PHP endpoint is unavailable)
  - ``predictions/nba_props_today.json`` parses
  - its ``date`` matches the requested date
  - if ``count > 0``, a sample prop has the canonical fields
    (player_id/player, stat, line, model_prob_*, market_prob_*)
  - if ``count == 0``, the JSON has a ``reason`` field AND the HTML has
    a visible empty-state message
  - no stale json (date mismatch with no reason) is accepted

Pass:  WOO_NBA_PROPS_PAGE_PASS
Fail:  WOO_NBA_PROPS_PAGE_FAILED  with the exact reason
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = REPO_ROOT / "predictions" / "nba-props.html"
TODAY_JSON = REPO_ROOT / "predictions" / "nba_props_today.json"

REQUIRED_PROP_FIELDS = (
    ("player", "player_name"),
    ("stat",),
    ("line",),
    ("model_prob_over", "model_prob"),
    ("market_prob_over", "market_prob"),
)


def _has_any(d: dict, keys: tuple) -> bool:
    return any(k in d for k in keys)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    args = ap.parse_args(argv)
    date = args.date

    failures: list[str] = []

    if not HTML_PATH.exists():
        failures.append(f"missing {HTML_PATH.relative_to(REPO_ROOT)}")
    else:
        size = HTML_PATH.stat().st_size
        if size < 5 * 1024:
            failures.append(f"HTML too small ({size} bytes < 5 KB) — likely broken")
        html = HTML_PATH.read_text(encoding="utf-8")
        if "showState" not in html:
            failures.append("HTML missing showState() — no visible fallback "
                            "rendering for empty/error states")
        if "static-banner" not in html and "STATIC_FALLBACK" not in html:
            failures.append("HTML missing static-fallback wiring — page "
                            "will render blank when deployed PHP endpoint "
                            "is unreachable")
        if "nba_props_today.json" not in html:
            failures.append("HTML does not reference local JSON fallback "
                            "(./nba_props_today.json) — page has no offline "
                            "data source")

    if not TODAY_JSON.exists():
        failures.append(f"missing {TODAY_JSON.relative_to(REPO_ROOT)}")
    else:
        try:
            tj = json.loads(TODAY_JSON.read_text(encoding="utf-8"))
        except Exception as e:
            failures.append(f"nba_props_today.json parse error: {e}")
            tj = None
        if tj is not None:
            today_date = str(tj.get("date"))
            count = int(tj.get("count", len(tj.get("props", []))))
            reason = tj.get("reason")
            if today_date != date:
                failures.append(
                    f"nba_props_today.json date={today_date!r} is stale; "
                    f"expected {date!r}. Run scripts/publish_nba_props_today.py "
                    f"--date {date}."
                )
            if count == 0 and not reason:
                failures.append(
                    "nba_props_today.json has count=0 with no `reason` "
                    "field — front-end will render blank without explanation"
                )
            if count > 0:
                first = tj.get("props", [{}])[0]
                missing_field_groups: list[tuple] = []
                for grp in REQUIRED_PROP_FIELDS:
                    if not _has_any(first, grp):
                        missing_field_groups.append(grp)
                if missing_field_groups:
                    failures.append(
                        f"nba_props_today.json sample prop missing field "
                        f"groups: {missing_field_groups}"
                    )

    if failures:
        print(f"WOO_NBA_PROPS_PAGE_FAILED  date={date}  failures={len(failures)}",
              file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    sample = ""
    if TODAY_JSON.exists():
        try:
            tj = json.loads(TODAY_JSON.read_text(encoding="utf-8"))
            sample = (f"  count={tj.get('count')}  "
                      f"games={tj.get('games')}  "
                      f"date={tj.get('date')}")
        except Exception:
            pass
    print(f"WOO_NBA_PROPS_PAGE_PASS  date={date}{sample}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
