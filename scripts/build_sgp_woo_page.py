#!/usr/bin/env python3
"""Build the Wizard of Odds SGP HTML page and associated export files.

Usage
-----
  python3 scripts/build_sgp_woo_page.py --date 2026-05-30 --repo-root .
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))


# ── HTML helpers ──────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: #f5f6fa;
  color: #222;
  padding: 24px 16px;
}
h1 { font-size: 1.9rem; font-weight: 700; color: #1a1a2e; }
h2 { font-size: 1.2rem; font-weight: 500; color: #444; margin-top: 4px; margin-bottom: 20px; }
h3 { font-size: 1rem; font-weight: 600; color: #1a1a2e; margin: 20px 0 10px; }
section { background: #fff; border-radius: 10px; padding: 20px 24px;
          box-shadow: 0 1px 6px rgba(0,0,0,.08); margin-bottom: 20px; }
.status-row { display: flex; flex-wrap: wrap; gap: 12px; }
.status-chip {
  display: inline-block; border-radius: 6px; padding: 5px 12px;
  font-size: .82rem; font-weight: 600; letter-spacing: .02em;
}
.chip-pass   { background: #d4edda; color: #155724; }
.chip-warn   { background: #fff3cd; color: #856404; }
.chip-fail   { background: #f8d7da; color: #721c24; }
.chip-info   { background: #d1ecf1; color: #0c5460; }
table { width: 100%; border-collapse: collapse; font-size: .88rem; }
thead th {
  background: #1a1a2e; color: #fff; padding: 10px 12px;
  text-align: left; font-weight: 600; position: sticky; top: 0;
}
tbody tr { border-bottom: 1px solid #eee; }
tbody tr:hover { background: #f0f4ff; }
tbody td { padding: 8px 12px; }
.tier-CERTIFIED   { color: #155724; font-weight: 700; }
.tier-MODEL_PRICE  { color: #004085; }
.tier-DIAGNOSTIC_ONLY { color: #856404; }
.tier-SUPPRESSED  { color: #999; }
.cert-badge { background: #28a745; color: #fff; border-radius: 4px; padding: 2px 7px; font-size:.75rem; }
.table-wrapper { overflow-x: auto; }
p.muted { color: #666; font-size: .85rem; margin-top: 6px; }
a { color: #0066cc; }
"""


def _chip(label: str, cls: str) -> str:
    return f'<span class="status-chip {cls}">{html.escape(str(label))}</span>'


def _tier_cell(tier: str) -> str:
    return f'<span class="tier-{html.escape(tier)}">{html.escape(tier)}</span>'


def _fmt_odds(val) -> str:
    try:
        v = int(val)
        return f"+{v}" if v > 0 else str(v)
    except Exception:
        return str(val)


def _fmt_prob(val) -> str:
    try:
        return f"{float(val) * 100:.1f}%"
    except Exception:
        return "—"


def _fmt_corr(val) -> str:
    try:
        return f"{float(val):.3f}"
    except Exception:
        return "—"


def _parse_legs_label(legs_json: str | None) -> str:
    if legs_json is None:
        return "—"
    try:
        legs = json.loads(legs_json)
        parts = []
        for leg in legs:
            pid = leg.get("label") or leg.get("player_id", "?")
            stat = leg.get("stat", "?").upper()
            line = leg.get("line", "?")
            side = leg.get("side", "over").capitalize()
            parts.append(f"{pid} {stat} {side} {line}")
        return " / ".join(parts)
    except Exception:
        return str(legs_json)[:80]


def _build_engine_status_html(
    bundle_manifest: dict | None,
    gate_status: dict | None,
    n_prices: int,
    slate_date: str,
) -> str:
    chips = []
    if bundle_manifest:
        status = bundle_manifest.get("bundle_status", "UNKNOWN")
        cls = "chip-pass" if status == "PASS" else "chip-fail"
        chips.append(_chip(f"Bundle: {status}", cls))
        n_games = bundle_manifest.get("n_games", "?")
        n_players = bundle_manifest.get("n_players", "?")
        chips.append(_chip(f"{n_games} games / {n_players} players", "chip-info"))
        trained = bundle_manifest.get("trained_through_date") or "?"
        chips.append(_chip(f"Model through: {trained}", "chip-info"))
    else:
        chips.append(_chip("Bundle: UNAVAILABLE", "chip-fail"))

    chips.append(_chip(f"{n_prices} tickets priced", "chip-info"))

    if gate_status:
        gs = gate_status.get("gate_status", "UNKNOWN")
        cls = "chip-pass" if gs == "CERTIFIED" else ("chip-warn" if gs == "MODEL_PRICE" else "chip-info")
        chips.append(_chip(f"Gate: {gs}", cls))
        sup = gate_status.get("market_superiority_certified", False)
        if sup:
            chips.append(_chip("Market Superiority CERTIFIED", "chip-pass"))
        if gate_status.get("ece") is not None:
            chips.append(_chip(f"ECE: {gate_status['ece']:.4f}", "chip-info"))

    rows_html = "\n".join(f"      {c}" for c in chips)
    return f"""
    <div class="status-row">
{rows_html}
    </div>
    <p class="muted">Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
"""


def _build_price_table_html(df: pd.DataFrame) -> str:
    visible = df[df["tier"] != "SUPPRESSED"] if "tier" in df.columns else df
    if visible.empty:
        return "<p class='muted'>No prices available for this slate.</p>"

    headers = ["Ticket", "Legs", "Fair Odds", "Joint Prob.", "Corr. Factor", "Tier"]
    thead = "".join(f"<th>{h}</th>" for h in headers)

    rows_html_parts = []
    for _, row in visible.iterrows():
        tier = str(row.get("tier", "MODEL_PRICE"))
        legs_label = _parse_legs_label(row.get("legs_json"))
        odds = _fmt_odds(row.get("fair_american_odds"))
        prob = _fmt_prob(row.get("calibrated_joint_probability"))
        corr = _fmt_corr(row.get("correlation_factor_vs_pmf_independence"))
        ticket_id = str(row.get("ticket_id", ""))
        tier_html = _tier_cell(tier)
        if tier == "CERTIFIED":
            tier_html += ' <span class="cert-badge">CERTIFIED</span>'
        note = ""
        if tier == "DIAGNOSTIC_ONLY":
            note = ' <span class="muted">(diagnostic)</span>'

        rows_html_parts.append(
            f"<tr>"
            f"<td>{html.escape(ticket_id)}</td>"
            f"<td>{html.escape(legs_label)}</td>"
            f"<td><strong>{html.escape(odds)}</strong></td>"
            f"<td>{html.escape(prob)}</td>"
            f"<td>{html.escape(corr)}</td>"
            f"<td>{tier_html}{note}</td>"
            f"</tr>"
        )

    rows_html = "\n".join(rows_html_parts)
    return f"""
    <div class="table-wrapper">
      <table>
        <thead><tr>{thead}</tr></thead>
        <tbody>
{rows_html}
        </tbody>
      </table>
    </div>
    <p class="muted">{len(visible)} tickets shown (SUPPRESSED rows hidden).</p>
"""


def _build_diagnostic_banner_html(gate_status: dict | None) -> str:
    """Return a prominent diagnostic/warning banner when calibration is not yet certified."""
    if gate_status is None:
        gs = "UNAVAILABLE"
    else:
        gs = gate_status.get("gate_status", "UNKNOWN")

    if gs == "CERTIFIED":
        # Calibration gates passed — no banner needed
        return ""

    if gs == "INSUFFICIENT_SAMPLE":
        msg = "Joint calibration pending historical SGP backtest sample."
        detail = (
            "The SGP Engine has not yet accumulated enough out-of-sample backtest rows "
            "to fit reliable joint probability calibrators. Prices shown are model fair values "
            "computed from the correlated simulation. <strong>No market-superiority claim is made.</strong>"
        )
    elif gs in ("MODEL_PRICE", "DIAGNOSTIC_ONLY"):
        msg = "SGP Engine — Model Price Mode."
        detail = (
            "Calibration gates have not yet passed. Prices are raw model estimates. "
            "<strong>No market-superiority claim is made.</strong>"
        )
    else:
        msg = f"SGP Engine Diagnostic Mode (gate_status={gs})."
        detail = (
            "Calibration readiness gates have not passed. "
            "<strong>No market-superiority claim is made.</strong>"
        )

    return f"""
  <section id="diagnostic-banner" style="background:#fff3cd;border:2px solid #ffc107;border-radius:10px;padding:16px 24px;margin-bottom:20px;">
    <h3 style="color:#856404;font-size:1rem;">⚠ {html.escape(msg)}</h3>
    <p style="color:#856404;font-size:.88rem;margin-top:8px;">{detail}</p>
    <p style="color:#856404;font-size:.82rem;margin-top:6px;">
      This page is for diagnostic and research purposes only.
      SGP Engine outputs are isolated from the main PMF delivery pipeline
      and are not published as certified market recommendations until
      all readiness gates (docs/SGP_ENGINE_BUILD_PLAN.md §0C) pass.
    </p>
  </section>
"""


def _build_full_html(
    slate_date: str,
    price_df: pd.DataFrame | None,
    bundle_manifest: dict | None,
    gate_status: dict | None,
) -> str:
    n_prices = len(price_df) if price_df is not None else 0
    status_html = _build_engine_status_html(bundle_manifest, gate_status, n_prices, slate_date)
    table_html = _build_price_table_html(price_df) if price_df is not None else (
        "<p class='muted'>No price data available.</p>"
    )
    banner_html = _build_diagnostic_banner_html(gate_status)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SGP Engine — Wizard of Odds — {html.escape(slate_date)}</title>
  <style>
{_CSS}
  </style>
</head>
<body>
  <h1>NBA Same-Game Parlay Engine</h1>
  <h2>Wizard of Odds &mdash; Slate: {html.escape(slate_date)}</h2>
{banner_html}
  <section id="engine-status">
    <h3>Engine Status</h3>
{status_html}
  </section>

  <section id="sgp-prices">
    <h3>SGP Fair Price Grid</h3>
{table_html}
  </section>

  <section id="methodology">
    <h3>Methodology</h3>
    <p>
      The SGP Engine prices Same-Game Parlays using a full-discrete PMF joint probability
      framework. Each player-stat outcome is modeled as a calibrated probability mass function
      (PMF) delivered by the production NBA model. A factor-based correlated simulation
      (marginal-anchored, mechanism-factor v1) generates <strong>joint</strong> outcome
      distributions across all players in the same game, respecting within-game correlations
      via shared pace, total, team offense/defense, and player usage/minutes factors.
    </p>
    <p style="margin-top:10px">
      All prices are <strong>fair prices</strong> (no vig applied). Market odds are included
      where available. <strong>CERTIFIED</strong> prices have passed statistical market
      superiority gates (UCB95 log-loss and Brier score). <strong>MODEL_PRICE</strong> prices
      are our best estimate without certification. <strong>DIAGNOSTIC_ONLY</strong> prices
      have wide confidence intervals and should not be acted upon directly.
    </p>
    <p style="margin-top:10px">
      Engine: NBA SGP Engine v1 — factor-based marginal-anchored simulation<br>
      Data: <a href="https://www.balldontlie.io/">BDL API</a> + internal model outputs
    </p>
  </section>
</body>
</html>
"""


# ── Calibration summary ───────────────────────────────────────────────────────

def _build_calibration_summary(
    slate_date: str,
    price_df: pd.DataFrame | None,
    gate_status: dict | None,
) -> dict:
    tier_counts: dict[str, int] = {}
    if price_df is not None and "tier" in price_df.columns:
        for t, g in price_df.groupby("tier", dropna=False):
            tier_counts[str(t)] = int(len(g))

    gs = gate_status or {}
    cal_status = gs.get("gate_status", "INSUFFICIENT_SAMPLE")

    return {
        "slate_date": slate_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "calibration_status": cal_status,
        "n_prices": int(len(price_df)) if price_df is not None else 0,
        "n_certified": tier_counts.get("CERTIFIED", 0),
        "n_model_price": tier_counts.get("MODEL_PRICE", 0),
        "n_diagnostic": tier_counts.get("DIAGNOSTIC_ONLY", 0),
        "n_suppressed": tier_counts.get("SUPPRESSED", 0),
        "gate_status": gs,
        "methodology": "NBA SGP Engine v1 — factor-based marginal-anchored simulation",
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="Slate date YYYY-MM-DD")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    slate_date = args.date
    sgp_root = repo_root / "deliveries" / slate_date / "sgp_engine"

    print(f"[WoO SGP] date={slate_date}", flush=True)

    # ── Load inputs (all graceful) ────────────────────────────────────────────

    # Price grid
    price_df: pd.DataFrame | None = None
    price_csv = sgp_root / "prices" / "sgp_price_grid.csv"
    price_parquet = sgp_root / "prices" / "sgp_price_grid.parquet"
    if price_parquet.exists():
        try:
            price_df = pd.read_parquet(price_parquet)
            print(f"  Loaded price grid from parquet: {len(price_df)} rows", flush=True)
        except Exception as exc:
            print(f"  WARNING: Could not load price parquet: {exc}", file=sys.stderr)
    if price_df is None and price_csv.exists():
        try:
            price_df = pd.read_csv(price_csv)
            print(f"  Loaded price grid from CSV: {len(price_df)} rows", flush=True)
        except Exception as exc:
            print(f"  WARNING: Could not load price CSV: {exc}", file=sys.stderr)
    if price_df is None:
        print("  No price grid found — building empty export.", file=sys.stderr)

    # Bundle manifest
    bundle_manifest: dict | None = None
    manifest_path = sgp_root / "slate_state_bundle_v1" / "bundle_manifest.json"
    if manifest_path.exists():
        try:
            bundle_manifest = json.loads(manifest_path.read_text())
        except Exception as exc:
            print(f"  WARNING: Could not parse bundle manifest: {exc}", file=sys.stderr)

    # Gate status (calibration)
    gate_status: dict | None = None
    gate_path = sgp_root / "calibration" / "sgp_gate_status.json"
    cal_report_path = sgp_root / "calibration" / "sgp_calibration_report.json"
    for gp in [gate_path, cal_report_path]:
        if gp.exists():
            try:
                raw = json.loads(gp.read_text())
                gate_status = raw.get("gate", raw)
                break
            except Exception:
                pass

    # ── Build HTML ────────────────────────────────────────────────────────────
    html_content = _build_full_html(slate_date, price_df, bundle_manifest, gate_status)

    # ── Build calibration summary ─────────────────────────────────────────────
    cal_summary = _build_calibration_summary(slate_date, price_df, gate_status)

    # ── Publishable edges CSV ─────────────────────────────────────────────────
    if price_df is not None and not price_df.empty and "tier" in price_df.columns:
        edges_df = price_df[price_df["tier"].isin({"MODEL_PRICE", "CERTIFIED"})].copy()
    else:
        edges_df = pd.DataFrame()

    # ── Write WoO export outputs ───────────────────────────────────────────────
    woo_dir = sgp_root / "woo_export"
    woo_dir.mkdir(parents=True, exist_ok=True)

    (woo_dir / "sgp_index.html").write_text(html_content, encoding="utf-8")
    if price_df is not None:
        price_df.to_csv(woo_dir / "sgp_price_grid.csv", index=False)
    else:
        pd.DataFrame().to_csv(woo_dir / "sgp_price_grid.csv", index=False)
    edges_df.to_csv(woo_dir / "sgp_publishable_edges.csv", index=False)
    (woo_dir / "sgp_calibration_summary.json").write_text(
        json.dumps(cal_summary, indent=2, sort_keys=True)
    )
    print(f"  WoO export written: {woo_dir}", flush=True)

    # ── Write public_export ───────────────────────────────────────────────────
    pub_dir = repo_root / "public_export" / "wizard_of_odds" / "sgp"
    pub_dir.mkdir(parents=True, exist_ok=True)

    (pub_dir / "index.html").write_text(html_content, encoding="utf-8")
    if price_df is not None:
        price_df.to_csv(pub_dir / "sgp_price_grid.csv", index=False)
    else:
        pd.DataFrame().to_csv(pub_dir / "sgp_price_grid.csv", index=False)
    edges_df.to_csv(pub_dir / "sgp_publishable_edges.csv", index=False)
    (pub_dir / "sgp_calibration_summary.json").write_text(
        json.dumps(cal_summary, indent=2, sort_keys=True)
    )
    print(f"  Public export written: {pub_dir}", flush=True)

    print("[WoO SGP] Done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
