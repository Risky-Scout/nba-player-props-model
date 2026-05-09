#!/usr/bin/env python3
"""
Render-contract verifier for the WoO dashboard HTML files.

Run AFTER `build_woo_dashboard.py` to gate the upload. Static checks only —
no headless browser needed; uses Python stdlib only.

Usage:
    python3 scripts/verify_woo_dashboard_render_contract.py --date 2026-05-04

On success, prints exactly:
    WOO_DASHBOARD_RENDER_CONTRACT_PASS  date=<date>

On any failure, prints each failed check and exits 1.
"""
import argparse
import json
import sys
from pathlib import Path

REQUIRED_PROPS_PRESENT = [
    "window.EMBEDDED_DATA",
    "function finiteOrNull",
    "function probOrNull",
    "Number.isFinite(b.ev)",
    "Number.isFinite(b.odds)",
    "kellyDisplayPct = 'Review'",
    "SUPPORTED_SINGLE_STATS",
    "playerKey",
    "gameKey",
    "sideUpper",
    "pickBestBook",
]
FORBIDDEN_PROPS = [
    "${r.player_id}|${stat}|${r.side}|${r.line}",
    "pickBestAffiliate",
    "AFFILIATE_DISPLAY[bk].label",
]

REQUIRED_PMF_PRESENT = [
    "window.EMBEDDED_PMF_DATA",
    "summaryStatsFromSupport",
    "lastVisibleK",
    "tailGapSlots",
    "renderHistogram(support, modeVal",
    "hist-bar tail",
]
FORBIDDEN_PMF = [
    "lastNonTailK",
    "(statObj.mean ?? 0)",
    "renderHistogram(support, statObj.mode",
    "Affiliate Book Lines",
    "offered-line",
    "isMode ? 'hist-bar mode' : 'hist-bar tail'",
]
from nba_props_model.targets import BASE_STATS_FULL  # noqa: E402

SUPPORTED_STATS = set(BASE_STATS_FULL)  # M4A2: was 5-stat set literal


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    props_html = repo / "predictions" / "nba-props.html"
    pmf_html = repo / "predictions" / "nba-pmf-research.html"
    aff_json = repo / "public_export" / "wizard_of_odds" / args.date / "affiliate_dashboard.json"
    pmf_json = repo / "public_export" / "wizard_of_odds" / args.date / "pmf_research.json"

    failures: list[str] = []

    def fail(msg: str) -> None:
        failures.append(msg)
        print(f"  [FAIL] {msg}")

    def passed(msg: str) -> None:
        print(f"  [PASS] {msg}")

    print("PROPS HTML — required content:")
    if not props_html.exists():
        fail(f"props HTML missing at {props_html}")
    else:
        text = props_html.read_text()
        for needle in REQUIRED_PROPS_PRESENT:
            (passed if needle in text else fail)(f"contains: {needle}")
        for needle in FORBIDDEN_PROPS:
            (fail if needle in text else passed)(f"absent: {needle!r}")

    print("\nPMF HTML — required content:")
    if not pmf_html.exists():
        fail(f"PMF HTML missing at {pmf_html}")
    else:
        text = pmf_html.read_text()
        for needle in REQUIRED_PMF_PRESENT:
            (passed if needle in text else fail)(f"contains: {needle}")
        for needle in FORBIDDEN_PMF:
            (fail if needle in text else passed)(f"absent: {needle!r}")

    print("\nJSON shape:")
    if not aff_json.exists():
        fail(f"affiliate_dashboard.json missing at {aff_json}")
    else:
        try:
            d = json.loads(aff_json.read_text())
            rows = d.get("rows", [])
            if not rows:
                fail("affiliate_dashboard.json has zero rows")
            else:
                passed(f"affiliate_dashboard.json: {len(rows)} rows")
                bad = [r for r in rows if r.get("model_prob") is None]
                if bad:
                    fail(f"{len(bad)} rows have null model_prob")
                else:
                    passed("every row has a non-null model_prob")
        except Exception as e:
            fail(f"affiliate_dashboard.json parse error: {e}")

    if not pmf_json.exists():
        fail(f"pmf_research.json missing at {pmf_json}")
    else:
        try:
            d = json.loads(pmf_json.read_text())
            players = d.get("players", [])
            if not players:
                fail("pmf_research.json has zero players")
            else:
                passed(f"pmf_research.json: {len(players)} players")
                bad_sums: list[str] = []
                bad_tails: list[str] = []
                for player in players:
                    for stat, obj in (player.get("stats") or {}).items():
                        if stat not in SUPPORTED_STATS:
                            continue
                        sp = obj.get("support_points", [])
                        s = sum(pt.get("p", 0.0) for pt in sp)
                        if not (0.99 <= s <= 1.01):
                            bad_sums.append(f"{player.get('player')} {stat}: sum={s:.4f}")
                        for pt in sp:
                            if pt.get("is_tail") and not str(pt.get("label", "")).endswith("+"):
                                bad_tails.append(f"{player.get('player')} {stat}: '{pt.get('label')}'")
                if bad_sums:
                    fail(f"support_points don't sum to 1.0: {bad_sums[:3]}")
                else:
                    passed("all supported-stat support_points sum to 1.0 (±0.01)")
                if bad_tails:
                    fail(f"tail labels missing '+': {bad_tails[:3]}")
                else:
                    passed("all tail labels end with '+'")
        except Exception as e:
            fail(f"pmf_research.json parse error: {e}")

    print()
    if failures:
        print(f"WOO_DASHBOARD_RENDER_CONTRACT_FAIL  date={args.date}  failures={len(failures)}")
        return 1
    print(f"WOO_DASHBOARD_RENDER_CONTRACT_PASS  date={args.date}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
