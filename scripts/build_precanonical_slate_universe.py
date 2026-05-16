#!/usr/bin/env python3
"""Materialize the pre-canonical slate universe seed parquet.

Breaks the historical circular dependency between ``feature_snapshot``
and canonical MODEL_ONLY on a clean slate by carrying ONLY the player
+ game slate identity grid required before feature population can
run:

  predict output (predictions/all_props_<date>.parquet)
    → pre-canonical seed (this script)
    → feature_snapshot
    → minutes_predictions
    → stat_grid (12 mission stats)
    → canonical MODEL_ONLY built from stat_grid
    → market_comparison
    → derek_forward_feed (downstream of canonical/stat-grid ONLY)

The seed is intentionally NOT canonical MODEL_ONLY, NOT a model PMF
surface, NOT market-edge data, and NOT a Derek-feed source. It only
contains identity columns (slate_date, player_id, player_name,
game_id, team/team_abbr, opponent, is_home, game_start_*). Strict
validation enforces:

  * rows > 0
  * non-null player_id / game_id
  * slate_date matches the requested delivery date
  * deduped on (player_id, game_id)

Failure markers (printed verbatim on stderr, exit 2):

  * ``PRECANNONICAL_SLATE_UNIVERSE_MISSING``
  * ``PRECANNONICAL_SLATE_UNIVERSE_EMPTY``
  * ``PRECANNONICAL_SLATE_UNIVERSE_KEYS_MISSING``
  * ``PRECANNONICAL_SLATE_UNIVERSE_DATE_MISMATCH``

See :mod:`nba_props_model.features.precanonical_slate_universe` for
the contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.precanonical_slate_universe import (  # noqa: E402
    NoGamesSlateSoftSkip,
    PrecanonicalSlateUniverseError,
    materialize_precanonical_slate_universe,
    precanonical_seed_path,
    predictions_all_props_path,
)


def _write_no_games_seed_audit(repo_root: Path, date: str, run_mode: str, marker_line: str) -> Path:
    """Persist a small audit artifact alongside the BDL no-games audit.

    The pre-canonical seed soft-skip and the BDL lineups soft-skip both
    surface a real no-games slate. Co-locating the audit under
    ``artifacts/live_lineups/<date>/`` keeps on-call review in one
    place when the morning delivery is force-run against an empty
    slate.
    """
    out_dir = repo_root / "artifacts" / "live_lineups" / date
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_path = out_dir / "precanonical_seed_no_games_soft_skip.json"
    payload = {
        "delivery_date": date,
        "run_mode": run_mode,
        "marker": "PRECANNONICAL_SLATE_UNIVERSE_SOFT_SKIP_NO_GAMES",
        "marker_line": marker_line,
        "reason": "predict_no_games_placeholder",
        "source": "predictions/all_props_<date>.parquet + predictions/singles_<date>.json reason=no_games_slate",
    }
    import json as _json
    audit_path.write_text(_json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return audit_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Build the pre-canonical slate universe seed parquet from "
            "predictions/all_props_<date>.parquet. Strictly validates "
            "player_id/game_id/slate_date integrity."
        )
    )
    ap.add_argument("--date", required=True, help="Delivery date (YYYY-MM-DD)")
    ap.add_argument(
        "--run-mode",
        required=True,
        help="Run-mode stamp (e.g. morning_expected, t25, t5).",
    )
    ap.add_argument(
        "--source",
        default=None,
        help=(
            "Optional override of the source parquet "
            "(default: predictions/all_props_<date>.parquet)."
        ),
    )
    ap.add_argument(
        "--out",
        default=None,
        help=(
            "Optional override of the seed output parquet "
            "(default: data/features/precanonical_slate_universe_<date>_<run_mode>.parquet)."
        ),
    )
    args = ap.parse_args(argv)

    source = Path(args.source) if args.source else predictions_all_props_path(REPO_ROOT, args.date)
    target = Path(args.out) if args.out else precanonical_seed_path(REPO_ROOT, args.date, args.run_mode)

    try:
        out_path = materialize_precanonical_slate_universe(
            REPO_ROOT,
            date=args.date,
            run_mode=args.run_mode,
            source_path=source,
            out_path=target,
        )
    except NoGamesSlateSoftSkip as exc:
        marker = str(exc)
        audit = _write_no_games_seed_audit(REPO_ROOT, args.date, args.run_mode, marker)
        try:
            audit_rel = audit.relative_to(REPO_ROOT)
        except ValueError:
            audit_rel = audit
        print(f"{marker} audit={audit_rel}")
        return 0
    except PrecanonicalSlateUniverseError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        rel = out_path.relative_to(REPO_ROOT)
    except ValueError:
        rel = out_path
    print("PRECANNONICAL_SLATE_UNIVERSE_BUILT")
    print(f"  date={args.date} run_mode={args.run_mode}")
    print(f"  source={source}")
    print(f"  out={rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
