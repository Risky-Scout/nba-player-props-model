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

PMF_RESEARCH_PLAYER_LIST_KEYS = ("players", "rows", "data", "records", "items", "pmfs")


def _extract_pmf_research_players(payload):
    """Return a list of player records regardless of the producer's shape.

    The dashboard JSON has gone through two producer regimes:
      * legacy ``publish_woo_public_export.py`` writes
        ``{"players": [{...}, ...]}`` with each player's ``stats`` as a
        dict keyed by stat name.
      * the canonical ``build_woo_pmf_research_from_canonical.py`` writes
        ``{"players": [{...}], "pmfs": [...], "props": [...]}`` where
        each player's ``stats`` is a *list* of stat-atom dicts.

    Both shapes must parse without ever calling ``.items()`` on a list
    (run 25952350180 root-caused to exactly that). Unknown shapes fail
    explicitly with ``PMF_RESEARCH_JSON_SCHEMA_INVALID``.
    """
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, dict):
        for key in PMF_RESEARCH_PLAYER_LIST_KEYS:
            v = payload.get(key)
            if isinstance(v, list):
                return list(v)
        nested_values = [v for v in payload.values() if isinstance(v, dict)]
        if nested_values and all("stats" in v or "pmf" in v or "support" in v for v in nested_values):
            return nested_values
    type_name = type(payload).__name__
    keys = sorted(payload.keys()) if isinstance(payload, dict) else None
    raise ValueError(
        "PMF_RESEARCH_JSON_SCHEMA_INVALID "
        f"root_type={type_name} keys={keys}"
    )


def _iter_player_stats(player):
    """Yield ``(stat_name, stat_obj)`` pairs for either shape of
    ``player.stats``: dict keyed by stat name, or list of stat-atom
    dicts that themselves carry ``stat``/``stat_key``."""
    if not isinstance(player, dict):
        return
    stats = player.get("stats")
    if stats is None:
        return
    if isinstance(stats, dict):
        for stat_name, obj in stats.items():
            if isinstance(obj, dict):
                yield str(stat_name), obj
        return
    if isinstance(stats, list):
        for obj in stats:
            if not isinstance(obj, dict):
                continue
            name = obj.get("stat") or obj.get("stat_key") or obj.get("market")
            if not name:
                continue
            yield str(name), obj
        return
    # Unknown shape under ``stats`` — surface, don't silently swallow.
    raise ValueError(
        "PMF_RESEARCH_JSON_SCHEMA_INVALID "
        f"player_stats_type={type(stats).__name__}"
    )


def _stat_support_points(obj):
    """Return the renderable support points for a stat object.

    Legacy producers emit ``support_points: [{"k": 0, "p": 0.18,
    "label": "0", "is_tail": false}, ...]``. The canonical builder emits
    ``support`` + ``probs`` arrays. We accept either and project the
    new shape into the legacy ``support_points`` schema for downstream
    sum-to-1 / tail-label checks.
    """
    if not isinstance(obj, dict):
        return []
    sp = obj.get("support_points")
    if isinstance(sp, list):
        return [pt for pt in sp if isinstance(pt, dict)]
    support = obj.get("support")
    probs = obj.get("probs")
    if isinstance(support, list) and isinstance(probs, list) and len(support) == len(probs):
        return [
            {
                "k": int(k) if k is not None else None,
                "p": float(p) if p is not None else 0.0,
                "label": str(int(k)) if k is not None else "",
                "is_tail": False,
            }
            for k, p in zip(support, probs)
        ]
    return []


def _delivery_manifest_no_games_slate(repo: Path, date: str) -> bool:
    """Return True iff the dated delivery manifest carries the strict
    no-games-slate flag.

    The orchestrator's ``_short_circuit_if_no_games`` writes
    ``deliveries/<date>/manifest.json`` with ``no_games_slate: true``
    only after BOTH the predict no-games signal AND an independent
    BDL ``/games`` schedule lookup confirm zero games for the date.
    Any other manifest shape (missing flag, false flag, missing
    manifest, unparseable manifest, mismatched reason) returns False
    so a games-bearing slate still hard-fails on a zero-rows dashboard.
    """
    manifest_path = repo / "deliveries" / date / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("no_games_slate")) and payload.get("reason") == "no_games_slate"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    if _delivery_manifest_no_games_slate(repo, args.date):
        print(
            f"WOO_DASHBOARD_RENDER_CONTRACT_SOFT_SKIP_NO_GAMES_SLATE "
            f"date={args.date} "
            f"upstream_signal=deliveries/{args.date}/manifest.json:no_games_slate=true "
            f"reason=no_eligible_player_game_rows_expected"
        )
        return 0

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
            payload = json.loads(pmf_json.read_text())
            players = _extract_pmf_research_players(payload)
            if not players:
                fail("pmf_research.json has zero players")
            else:
                passed(f"pmf_research.json: {len(players)} players")
                bad_sums: list[str] = []
                bad_tails: list[str] = []
                for player in players:
                    try:
                        stat_iter = list(_iter_player_stats(player))
                    except ValueError as exc:
                        fail(str(exc))
                        continue
                    for stat, obj in stat_iter:
                        if stat.lower() not in SUPPORTED_STATS:
                            continue
                        sp = _stat_support_points(obj)
                        if not sp:
                            # No renderable support points for this stat — the
                            # canonical builder may emit support+probs but no
                            # support_points yet. Skip rather than spuriously
                            # failing the sum-to-1 check on an empty list.
                            continue
                        s = sum(float(pt.get("p", 0.0) or 0.0) for pt in sp)
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
