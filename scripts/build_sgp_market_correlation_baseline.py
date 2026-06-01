#!/usr/bin/env python3
"""SGP market correlation baseline builder.

When actual SGP book odds become available, this script ingests them and
computes the market-implied correlation factor for each SGP candidate.

Current status: VALID SKIP — no market SGP odds source is configured.

Usage
-----
  python3 scripts/build_sgp_market_correlation_baseline.py \\
    --date 2026-05-30 \\
    --repo-root .

The script exits 0 in all cases — it either writes data or valid-skips.

Future market odds schema (data/sgp_market_odds.parquet)
---------------------------------------------------------
Columns:
  snapshot_time_utc     ISO timestamp of odds snapshot
  game_id               Game identifier
  book                  Sportsbook name (e.g. DraftKings, FanDuel, NoVig)
  sgp_id                Matched SGP candidate identifier
  legs_json             JSON array of matched leg definitions
  market_decimal_odds   Book decimal odds (including vig)
  market_american_odds  American odds
  market_implied_probability       1 / market_decimal_odds
  no_vig_market_probability        Vig-removed market probability
  individual_leg_no_vig_probs_json JSON array of per-leg no-vig probs
  market_independence_probability  Product of individual leg no-vig probs
  market_corr_factor               no_vig_market_prob / market_independence_prob
  source                           Data vendor / method

Market correlation edge (once odds are available)
-------------------------------------------------
  model_corr_factor = calibrated_joint_probability / independent_probability
  corr_factor_delta_vs_market = model_corr_factor - market_corr_factor

  marginal_edge_component:
      product(model_leg_p) / product(market_leg_p) - 1

  correlation_edge_component:
      model_corr_factor / market_corr_factor - 1

  total_edge:
      calibrated_joint_probability / no_vig_market_probability - 1

When to ingest actual SGP odds
------------------------------
  1. Add market SGP odds source to data/sgp_market_odds.parquet.
  2. Set actual_sgp_market_odds_available = True in price grid.
  3. Set market_corr_factor_source = "market_book" (not "independence_placeholder").
  4. Enable Gate 5 (UCB95 market superiority) evaluation in gate reports.
  5. Only then allow CERTIFIED tier rows to appear.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--source", default=None, help="Market odds source file or API endpoint")
    ap.add_argument("--book", default=None,
                    help="Book name filter (e.g. DraftKings, FanDuel, NoVig)")
    ap.add_argument("--min-legs", type=int, default=2,
                    help="Min leg count to include (default: 2)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    slate_date = args.date
    out_dir = repo_root / "deliveries" / slate_date / "sgp_engine" / "market_comparison"

    # ── Check for market SGP odds source. ─────────────────────────────────────
    market_odds_path = repo_root / "data" / "sgp_market_odds.parquet"
    has_market_odds = market_odds_path.exists() or (args.source is not None)

    if not has_market_odds:
        status = {
            "status": "VALID_SKIP",
            "reason": (
                "No market SGP odds source configured. "
                "data/sgp_market_odds.parquet does not exist. "
                "market_corr_factor_source remains 'independence_placeholder'. "
                "actual_sgp_market_odds_available remains False."
            ),
            "slate_date": slate_date,
            "actual_sgp_market_odds_available": False,
            "market_corr_factor_source": "independence_placeholder",
            "gate5_market_superiority_applicable": False,
            "action_required": (
                "To enable market correlation baseline: "
                "populate data/sgp_market_odds.parquet with the schema documented "
                "in this script's docstring, then re-run."
            ),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "sgp_market_correlation_status.json").write_text(
            json.dumps(status, indent=2, sort_keys=True)
        )
        print(f"[SGP-MARKET] VALID_SKIP: No market SGP odds source.")
        print(f"  Status written: {out_dir / 'sgp_market_correlation_status.json'}")
        return 0

    # ── Future: ingest and process market odds. ───────────────────────────────
    # When market_odds_path exists, load it and compute:
    #   market_corr_factor = no_vig_market_prob / market_independence_prob
    #   model_corr_factor  = calibrated_joint_probability / independent_probability
    #   corr_factor_delta_vs_market = model_corr_factor - market_corr_factor
    #
    # For now, write a structured stub showing what will be computed.
    status = {
        "status": "VALID_SKIP",
        "reason": "Market odds source found but ingestion not yet implemented.",
        "market_odds_path": str(market_odds_path),
        "slate_date": slate_date,
        "actual_sgp_market_odds_available": False,
        "market_corr_factor_source": "independence_placeholder",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sgp_market_correlation_status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True)
    )
    print("[SGP-MARKET] VALID_SKIP: Ingestion not yet implemented for found source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
