"""Phase 13X Part E — append "Edge reasonability / publishability"
section + tables to every Derek snapshot's snapshot_report.md (and
the three impact reports), using the already-applied publishability
columns in market_comparison.parquet plus the calibration audit
findings.

Pass:  PHASE13X_DEREK_EDGE_REPORTS_PASS
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES = REPO_ROOT / "deliveries"
HEALTH = REPO_ROOT / "artifacts" / "automation_health"


def _load_calibration_summary(delivery_date: str) -> dict:
    p = HEALTH / f"derek_edge_calibration_{delivery_date}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _build_edge_section(df, snap_audit_lineup_confirmed: bool,
                         snapshot_type: str, calib_summary: dict) -> list[str]:
    import pandas as pd
    md: list[str] = []
    md.append("## Edge reasonability / publishability")
    md.append("")
    if snapshot_type == "current_live" and not snap_audit_lineup_confirmed:
        md.append(
            "Current-live edges are **model-vs-market disagreements** "
            "from the best-available baseline. BDL did not return "
            "confirmed lineup rows at this timestamp, so these rows "
            "are **watchlist / review signals**, not confirmed-lineup "
            "recommendations. Large edges are flagged for review. "
            "Push / integer lines are audited separately. Calibration "
            "support is checked by stat / side / edge bucket where "
            "settled samples exist. **T-minus-25 and close-lock are "
            "the more important near-tip confirmed-lineup snapshots.**"
        )
    else:
        md.append(
            "Edges below were re-derived from the PMF (push-excluded "
            "win-prob convention), recomputed against no-vig market "
            "probabilities, and EV is reported both with and without "
            "push handling on integer lines."
        )
    md.append("")

    # Top edges with publishability status (top 20 by abs edge).
    if "raw_edge" in df.columns:
        df = df.copy()
        df["_abs"] = df["raw_edge"].abs()
        top = df.sort_values("_abs", ascending=False).head(20)
        cols = [c for c in (
            "player_name", "stat", "side", "line", "bet_vendor",
            "model_prob", "market_prob", "raw_edge", "ev",
            "edge_publish_status", "root_cause_label",
            "calibration_support_status", "edge_reasonability_notes",
        ) if c in top.columns]
        md.append("### Top edges with publishability status")
        md.append("")
        md.append("| " + " | ".join(cols) + " |")
        md.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, r in top.iterrows():
            row = []
            for c in cols:
                v = r.get(c)
                if isinstance(v, float):
                    row.append(f"{v:+.3f}" if c in (
                        "raw_edge", "ev"
                    ) else f"{v:.3f}")
                else:
                    row.append(str(v))
            md.append("| " + " | ".join(row) + " |")
        md.append("")

    # Push-line audit table.
    if "push_line" in df.columns:
        push_rows = df[df["push_line"] == True]
        if not push_rows.empty:
            md.append("### Push-line audit rows")
            md.append("")
            md.append(
                "| player | stat | side | line | push_prob | ev | "
                "ev_recomputed | ev_recomputed_pushinc | "
                "edge_publish_status |"
            )
            md.append(
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"
            )
            for _, r in push_rows.iterrows():
                md.append(
                    f"| {r.get('player_name')} | {r.get('stat')} | "
                    f"{r.get('side')} | {r.get('line')} | "
                    f"{float(r.get('push_prob') or 0):.3f} | "
                    f"{float(r.get('ev') or 0):+.3f} | "
                    f"{float(r.get('ev_recomputed') or 0):+.3f} | "
                    f"{float(r.get('ev_recomputed_pushinc') or 0):+.3f} | "
                    f"{r.get('edge_publish_status')} |"
                )
            md.append("")

    # Calibration bucket summary from the calibration audit.
    if calib_summary.get("stat_summary"):
        md.append("### Calibration bucket summary (historical corpus)")
        md.append("")
        md.append("| stat/side | n | model_logloss | market_logloss | Δll |")
        md.append("| --- | ---: | ---: | ---: | ---: |")
        for k, s in sorted(calib_summary["stat_summary"].items()):
            md.append(
                f"| {k} | {s['n']} | {s['model_ll_mean']:.3f} | "
                f"{s['market_ll_mean']:.3f} | {s['delta_ll_mean']:+.3f} |"
            )
        md.append("")
    return md


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    base = DELIVERIES / args.delivery_date / "derek_game_snapshots"
    if not base.exists():
        print("PHASE13X_DEREK_EDGE_REPORTS_PASS")
        print("  no derek_game_snapshots dir")
        return 0
    calib_summary = _load_calibration_summary(args.delivery_date)
    import pandas as pd

    files_updated = 0
    for game_dir in sorted(base.iterdir()):
        if not game_dir.is_dir():
            continue
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            sd = game_dir / snap_type
            mc = sd / "market_comparison.parquet"
            manifest_path = sd / "snapshot_manifest.json"
            if not mc.exists() or not manifest_path.exists():
                continue
            try:
                df = pd.read_parquet(mc)
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            section = _build_edge_section(
                df,
                snap_audit_lineup_confirmed=bool(m.get("lineup_confirmed")),
                snapshot_type=str(m.get("snapshot_type") or snap_type),
                calib_summary=calib_summary,
            )
            for fname in (
                "snapshot_report.md", "pmf_driver_decomposition.md",
                "lineup_injury_impact_report.md",
                "direct_lineup_impact_report.md",
            ):
                target = sd / fname
                if not target.exists():
                    continue
                txt = target.read_text(encoding="utf-8")
                marker = "## Edge reasonability / publishability"
                if marker in txt:
                    # Strip existing section to before the marker.
                    txt = txt.split(marker)[0].rstrip() + "\n\n"
                target.write_text(
                    txt + "\n".join(section) + "\n", encoding="utf-8"
                )
                files_updated += 1

    print("PHASE13X_DEREK_EDGE_REPORTS_PASS")
    print(
        f"  delivery_date={args.delivery_date} files_updated={files_updated}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
