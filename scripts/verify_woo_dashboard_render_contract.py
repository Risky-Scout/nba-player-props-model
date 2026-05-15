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
                def _row_has_model_prob(r: dict) -> bool:
                    for key in ("model_prob", "model_probability_for_side",
                                "model_prob_over", "model_p_over"):
                        v = r.get(key)
                        if v is None:
                            continue
                        try:
                            return float(v) == float(v)
                        except Exception:
                            continue
                    return False

                bad = [r for r in rows if not _row_has_model_prob(r)]
                if bad:
                    fail(f"{len(bad)} rows have null model_prob")
                else:
                    passed("every row has a non-null model probability "
                           "(model_prob / model_probability_for_side / model_prob_over)")
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

                def _iter_stat_blocks(player_obj: dict):
                    stats_field = player_obj.get("stats")
                    if isinstance(stats_field, dict):
                        for stat_name, block in stats_field.items():
                            yield stat_name, block
                    elif isinstance(stats_field, list):
                        for block in stats_field:
                            if isinstance(block, dict):
                                yield str(block.get("stat") or block.get("stat_key") or ""), block

                for player in players:
                    for stat, obj in _iter_stat_blocks(player):
                        if stat and stat not in SUPPORTED_STATS:
                            continue
                        if not isinstance(obj, dict):
                            continue
                        sp = obj.get("support_points")
                        if isinstance(sp, list) and sp:
                            s = sum(pt.get("p", 0.0) for pt in sp if isinstance(pt, dict))
                            if not (0.99 <= s <= 1.01):
                                bad_sums.append(f"{player.get('player')} {stat}: sum={s:.4f}")
                            for pt in sp:
                                if isinstance(pt, dict) and pt.get("is_tail") \
                                        and not str(pt.get("label", "")).endswith("+"):
                                    bad_tails.append(
                                        f"{player.get('player')} {stat}: '{pt.get('label')}'"
                                    )
                            continue

                        probs = obj.get("probs") or []
                        if isinstance(probs, list) and probs:
                            try:
                                s = float(sum(float(p) for p in probs))
                            except Exception:
                                s = 0.0
                            if not (0.99 <= s <= 1.01):
                                bad_sums.append(f"{player.get('player')} {stat}: sum={s:.4f}")
                if bad_sums:
                    fail(f"support_points don't sum to 1.0: {bad_sums[:3]}")
                else:
                    passed("all supported-stat distributions sum to 1.0 (±0.01)")
                if bad_tails:
                    fail(f"tail labels missing '+': {bad_tails[:3]}")
                else:
                    passed("tail labels OK (or schema has no tail-bucket field)")
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
