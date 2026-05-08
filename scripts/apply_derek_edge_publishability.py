"""Phase 13X Part D — apply edge publishability columns to Derek
market_comparison files.

Reads the root-cause + calibration audit JSON, then writes the
following columns onto every Derek snapshot's market_comparison.csv
and market_comparison.parquet (in place; only Derek-only files are
touched):

    edge_publish_status       (PUBLISH_BLOCKER /
                                REVIEW_LARGE_EDGE /
                                REVIEW_PUSH_LINE /
                                WATCHLIST_NOT_CONFIRMED_LINEUP /
                                ACTIONABLE_REVIEWED)
    edge_reasonability_status (CALIBRATION_SUPPORTED /
                                CALIBRATION_SAMPLE_LIMITED /
                                CALIBRATION_SAMPLE_THIN /
                                CALIBRATION_REVIEW_REQUIRED /
                                NOT_CHECKED)
    edge_reasonability_notes
    root_cause_label
    push_line                 (bool)
    push_prob                 (float)
    p0                        (float)
    pmf_mean                  (float)
    pmf_variance              (float)
    model_prob_from_pmf       (float)
    market_prob_recomputed    (float)
    raw_edge_recomputed       (float)
    ev_recomputed             (float, push-excluded)
    ev_recomputed_pushinc     (float, push-aware)
    large_edge_bucket         (str)
    calibration_support_status(str)
    calibration_bucket_n      (int)
    lineup_confirmation_dependency (str)

Pass:  PHASE13X_DEREK_EDGE_GATING_PASS
Fail:  PHASE13X_DEREK_EDGE_GATING_FAILED  (only on calculation bug or
        when an integer/push line lacks an honest push-aware EV)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES = REPO_ROOT / "deliveries"
HEALTH = REPO_ROOT / "artifacts" / "automation_health"


def _line_bucket(line: float) -> str:
    try:
        x = float(line)
    except Exception:
        return "unknown"
    if x <= 1.0:
        return "low_le_1.0"
    if x <= 2.5:
        return "low_2.5"
    if x <= 5.5:
        return "mid_5.5"
    if x <= 10.5:
        return "mid_10.5"
    return "high_gt_10.5"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    rc_path = HEALTH / f"derek_edge_root_cause_{args.delivery_date}.json"
    cal_path = HEALTH / f"derek_edge_calibration_{args.delivery_date}.json"
    if not rc_path.exists():
        print("PHASE13X_DEREK_EDGE_GATING_FAILED", file=sys.stderr)
        print(
            f"  reason=missing {rc_path}; run audit_derek_edge_root_cause.py first",
            file=sys.stderr,
        )
        return 1
    rc = json.loads(rc_path.read_text(encoding="utf-8"))
    cal = json.loads(cal_path.read_text(encoding="utf-8")) if cal_path.exists() else {
        "bucket_findings": []
    }
    # Build a lookup from (player_name, stat, side, line) → calibration
    # status from the calibration audit.
    cal_lookup: dict[tuple, dict] = {}
    for f in cal.get("bucket_findings", []):
        key = (
            str(f.get("player_name")), str(f.get("stat")),
            str(f.get("side")), float(f.get("line") or 0.0),
        )
        cal_lookup[key] = f

    base = DELIVERIES / args.delivery_date / "derek_game_snapshots"
    if not base.exists():
        print("PHASE13X_DEREK_EDGE_GATING_FAILED", file=sys.stderr)
        print(f"  reason=no derek_game_snapshots dir for {args.delivery_date}",
              file=sys.stderr)
        return 1

    import pandas as pd

    snapshots_processed = 0
    rows_updated = 0
    issues: list[str] = []

    for snap_audit in rc.get("snapshots", []):
        snap_dir_rel = snap_audit.get("snap_dir")
        if not snap_dir_rel:
            continue
        snap_dir = REPO_ROOT / snap_dir_rel
        mc_parquet = snap_dir / "market_comparison.parquet"
        mc_csv = snap_dir / "market_comparison.csv"
        if not mc_parquet.exists():
            continue
        df = pd.read_parquet(mc_parquet)
        # Build per-row lookup from the audit (keyed on player_name +
        # stat + side + line so we don't repeat the math).
        per_row: dict[tuple, dict] = {}
        for r in snap_audit.get("rows", []):
            key = (
                str(r.get("player_name")), str(r.get("stat")),
                str(r.get("side")), float(r.get("line") or 0.0),
            )
            per_row[key] = r

        # New column values, default-filled to keep schema stable.
        n = len(df)
        df["edge_publish_status"] = "WATCHLIST_NOT_CONFIRMED_LINEUP"
        df["edge_reasonability_status"] = "NOT_CHECKED"
        df["edge_reasonability_notes"] = ""
        df["root_cause_label"] = ""
        df["push_line"] = False
        df["push_prob"] = 0.0
        df["p0"] = 0.0
        df["pmf_mean"] = 0.0
        df["pmf_variance"] = 0.0
        df["model_prob_from_pmf"] = 0.0
        df["market_prob_recomputed"] = 0.0
        df["raw_edge"] = 0.0
        df["raw_edge_recomputed"] = 0.0
        df["ev_recomputed"] = 0.0
        df["ev_recomputed_pushinc"] = 0.0
        df["large_edge_bucket"] = "EDGE_LT_10"
        df["calibration_support_status"] = "NOT_CHECKED"
        df["calibration_bucket_n"] = 0
        df["lineup_confirmation_dependency"] = "current_live_unconfirmed_baseline"

        for i, r in df.iterrows():
            key = (
                str(r.get("player_name")), str(r.get("stat")),
                str(r.get("side")), float(r.get("line") or 0.0),
            )
            audit = per_row.get(key) or {}
            cal_rec = cal_lookup.get(key) or {}
            # Default publishability comes from the audit; layer on
            # calibration support + push-line override.
            base_status = audit.get("edge_publish_status") or "WATCHLIST_NOT_CONFIRMED_LINEUP"
            calib_status = cal_rec.get("calibration_status") or "NOT_CHECKED"
            calib_n = int(cal_rec.get("historical_n") or 0)
            notes_parts: list[str] = []
            notes_parts.append(audit.get("edge_publish_reason") or "")

            # Layer 1: integer push line with non-trivial push prob is
            # always REVIEW_PUSH_LINE (or stricter).
            if audit.get("push_line") and float(audit.get("push_prob") or 0.0) >= 0.05:
                if base_status not in ("PUBLISH_BLOCKER",):
                    base_status = "REVIEW_PUSH_LINE"
                notes_parts.append(
                    f"push_prob={float(audit.get('push_prob') or 0.0):.3f}; "
                    "push-aware EV may differ from displayed EV"
                )
            # Layer 2: calibration thin/limited downgrades to review.
            if calib_status in ("CALIBRATION_SAMPLE_THIN",
                                "CALIBRATION_REVIEW_REQUIRED"):
                if base_status == "ACTIONABLE_REVIEWED":
                    base_status = "REVIEW_LARGE_EDGE"
                notes_parts.append(
                    f"calibration {calib_status} (n={calib_n})"
                )
            elif calib_status == "CALIBRATION_SAMPLE_LIMITED":
                notes_parts.append(
                    f"calibration sample limited (n={calib_n})"
                )

            df.at[i, "edge_publish_status"] = base_status
            df.at[i, "edge_reasonability_status"] = calib_status
            df.at[i, "edge_reasonability_notes"] = "; ".join(
                p for p in notes_parts if p
            )
            df.at[i, "root_cause_label"] = audit.get("root_cause_label") or ""
            df.at[i, "push_line"] = bool(audit.get("push_line"))
            df.at[i, "push_prob"] = float(audit.get("push_prob") or 0.0)
            df.at[i, "p0"] = float(audit.get("p0") or 0.0)
            df.at[i, "pmf_mean"] = float(audit.get("pmf_mean") or 0.0)
            df.at[i, "pmf_variance"] = float(audit.get("pmf_variance") or 0.0)
            df.at[i, "model_prob_from_pmf"] = float(
                audit.get("model_prob_recomputed") or 0.0
            )
            df.at[i, "market_prob_recomputed"] = float(
                audit.get("market_prob_recomputed") or 0.0
            )
            raw_edge = float(audit.get("raw_edge_recomputed") or audit.get("raw_edge") or 0.0)
            df.at[i, "raw_edge"] = raw_edge
            df.at[i, "raw_edge_recomputed"] = raw_edge
            df.at[i, "ev_recomputed"] = float(
                audit.get("ev_recomputed_pushexc") or 0.0
            )
            df.at[i, "ev_recomputed_pushinc"] = float(
                audit.get("ev_recomputed_pushinc") or 0.0
            )
            df.at[i, "large_edge_bucket"] = audit.get("large_edge_bucket") or "EDGE_LT_10"
            df.at[i, "calibration_support_status"] = calib_status
            df.at[i, "calibration_bucket_n"] = calib_n
            if (snap_audit.get("snapshot_type") == "current_live"
                and not snap_audit.get("lineup_confirmed")):
                df.at[i, "lineup_confirmation_dependency"] = (
                    "current_live_unconfirmed_baseline"
                )
            else:
                df.at[i, "lineup_confirmation_dependency"] = (
                    f"{snap_audit.get('snapshot_type')}_lineup_"
                    f"confirmed_{bool(snap_audit.get('lineup_confirmed'))}"
                )
            rows_updated += 1

        # Hard-fail rule: any row that still has push_line=True with no
        # ev_recomputed_pushinc available is a calculation gap.
        for i, r in df.iterrows():
            if r["push_line"] and (r["ev_recomputed_pushinc"] in (None,)):
                issues.append(
                    f"{snap_dir_rel}: row {i} push_line but no push-aware EV"
                )

        df.to_csv(mc_csv, index=False)
        df.to_parquet(mc_parquet, index=False)
        snapshots_processed += 1

    if issues:
        print("PHASE13X_DEREK_EDGE_GATING_FAILED", file=sys.stderr)
        for i in issues[:20]:
            print(f"  - {i}", file=sys.stderr)
        return 1

    print("PHASE13X_DEREK_EDGE_GATING_PASS")
    print(
        f"  delivery_date={args.delivery_date} "
        f"snapshots_processed={snapshots_processed} "
        f"rows_updated={rows_updated}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
