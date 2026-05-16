#!/usr/bin/env python3
"""Check expected morning delivery folder layout for a slate date."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = (
    "canonical_source",
    "wizard_of_odds",
    "pmf_model_review_package",
    "after_game_scoring",
    "derek_forward_feed",
)


def _delivery_manifest_confirmed_no_games_slate(date: str) -> bool:
    """Strict 4-flag no-games gate for the morning completeness verifier.

    Returns True if and only if the dated delivery manifest declares
    ALL of:

      * ``no_games_slate == True``
      * ``confirmed_no_games_slate == True``
      * ``reason == "no_games_slate"``
      * ``market_superiority_evaluated == False``
      * ``derek_forward_feed_expected == False``

    These four fields are stamped together only by the orchestrator's
    ``_emit_no_games_delivery_package`` after BOTH the predict
    no-games signal AND an independent BDL ``/games`` schedule lookup
    have confirmed zero games for the date. Any partial / missing /
    corrupt manifest returns False so a games-bearing slate with
    missing subdirs (pmf_model_review_package, derek_forward_feed,
    after_game_scoring) still hard-fails — that's a real regression,
    not a no-games soft-skip.
    """
    manifest_path = REPO_ROOT / "deliveries" / date / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("no_games_slate") is True
        and payload.get("confirmed_no_games_slate") is True
        and payload.get("reason") == "no_games_slate"
        and payload.get("market_superiority_evaluated") is False
        and payload.get("derek_forward_feed_expected") is False
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    if _delivery_manifest_confirmed_no_games_slate(args.date):
        print(
            f"VERIFY_MORNING_DELIVERY_COMPLETENESS_SOFT_SKIP_NO_GAMES "
            f"date={args.date} "
            f"manifest=deliveries/{args.date}/manifest.json "
            f"gate=no_games_slate+confirmed_no_games_slate+"
            f"market_superiority_evaluated=false+derek_forward_feed_expected=false "
            f"reason=no_eligible_player_game_rows_expected"
        )
        return 0

    root = REPO_ROOT / "deliveries" / args.date
    fails: list[str] = []
    if not root.is_dir():
        fails.append(f"missing_delivery_root:{root}")

    for d in REQUIRED_DIRS:
        p = root / d
        if not p.is_dir():
            fails.append(f"missing_dir:{d}")
        elif d == "after_game_scoring":
            ag = root / "after_game_scoring"
            placeholder = ag / "after_game_scoring_placeholder_manifest.json"
            status_json = ag / "after_game_status.json"
            has_scoring = (ag / "after_game_scoring.parquet").exists() or (
                ag / "after_game_scoring.csv"
            ).exists()
            pending = False
            if placeholder.is_file():
                try:
                    pm = json.loads(placeholder.read_text(encoding="utf-8"))
                    pending = str(pm.get("after_game_scoring_status", "")) == "pending_actuals"
                except Exception:
                    fails.append("invalid_after_game_scoring_placeholder_manifest_json")
            elif status_json.is_file():
                try:
                    sm = json.loads(status_json.read_text(encoding="utf-8"))
                    st = str(sm.get("after_game_status", ""))
                    pending = st in ("pending_outcomes", "pending_actuals")
                except Exception:
                    fails.append("invalid_after_game_status_json")
            if not has_scoring and not pending:
                fails.append(
                    "after_game_scoring_missing_scoring_and_no_pending_placeholder"
                )

    woo = root / "wizard_of_odds" / "run_manifest.json"
    if woo.is_file():
        try:
            m = json.loads(woo.read_text(encoding="utf-8"))
            if m.get("market_superiority_claim_allowed") is True:
                fails.append("market_superiority_claim_allowed_true_without_external_verifier")
        except Exception:
            fails.append("invalid_run_manifest_json")

    if fails:
        print("MORNING_DELIVERY_COMPLETENESS_FAIL")
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("MORNING_DELIVERY_COMPLETENESS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
