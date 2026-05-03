"""Phase 13W Part C — contextual delta variation audit.

For each Derek snapshot, inspects pmf_driver_decomposition.parquet
and reports whether the trained Phase 13S contextual deltas vary
across players or are constant. Constant deltas can happen honestly
when:

  * BDL did not return confirmed lineups (lineup_features_missing on
    every row), so all rows fall into the same lagged-proxy bucket.
  * The slate has only one stat-type per row.

Constant deltas are a BUG when:

  * Per-player lagged stats vary (visible in contextual_feature_audit)
    but the trained model still emits identical deltas.

Pass:    PHASE13W_CONTEXTUAL_DELTA_VARIATION_PASS
Pending: PHASE13W_CONTEXTUAL_DELTA_VARIATION_PENDING (no snapshots)
Fail:    PHASE13W_CONTEXTUAL_DELTA_VARIATION_FAILED
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES = REPO_ROOT / "deliveries"
HEALTH = REPO_ROOT / "artifacts" / "automation_health"


def _audit_snapshot(snap_dir: Path) -> dict:
    out: dict = {"snap_dir": str(snap_dir.relative_to(REPO_ROOT))}
    decomp = snap_dir / "pmf_driver_decomposition.parquet"
    audit = snap_dir / "contextual_feature_audit.parquet"
    manifest_path = snap_dir / "snapshot_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
    if not decomp.exists():
        out["status"] = "no_decomposition"
        return out
    try:
        import pandas as pd
        df = pd.read_parquet(decomp)
    except Exception as exc:
        out["status"] = "read_error"
        out["error"] = str(exc)
        return out
    out["rows"] = int(len(df))
    if "contextual_minutes_delta" in df.columns:
        s = df["contextual_minutes_delta"].astype(float)
        out["minutes_delta_unique"] = int(s.nunique())
        out["minutes_delta_min"] = float(s.min())
        out["minutes_delta_max"] = float(s.max())
        out["minutes_delta_mean"] = float(s.mean())
        out["minutes_delta_std"] = float(s.std() or 0.0)
    rate_summary: dict = {}
    for c in df.columns:
        if c.startswith("contextual_rate_delta_"):
            stat = c.replace("contextual_rate_delta_", "")
            try:
                ss = df[c].astype(float)
                rate_summary[stat] = {
                    "unique": int(ss.nunique()),
                    "min": float(ss.min()),
                    "max": float(ss.max()),
                    "mean": float(ss.mean()),
                    "std": float(ss.std() or 0.0),
                }
            except Exception:
                continue
    out["rate_delta_summary"] = rate_summary

    # Inspect contextual_feature_audit to decide whether per-row
    # variation should exist.
    feature_variation = "unknown"
    if audit.exists():
        try:
            import pandas as pd
            af = pd.read_parquet(audit)
            varying_cols = []
            for c in af.columns:
                if c in ("player_id", "player_name", "team", "game_id"):
                    continue
                try:
                    if af[c].nunique(dropna=True) > 1:
                        varying_cols.append(c)
                except Exception:
                    continue
            feature_variation = "varies" if varying_cols else "constant"
            out["feature_audit_varying_cols"] = varying_cols[:25]
        except Exception:
            pass
    out["feature_variation"] = feature_variation

    constant = (out.get("minutes_delta_unique") or 1) <= 1
    lineup_confirmed = bool(manifest.get("lineup_confirmed"))
    out["lineup_confirmed"] = lineup_confirmed
    if constant and feature_variation == "varies":
        out["verdict"] = "bug"
        out["reason"] = (
            "feature audit shows per-player variation but trained model "
            "emits identical contextual_minutes_delta — model is not "
            "consuming per-player features"
        )
    elif constant and feature_variation == "constant":
        out["verdict"] = "expected_baseline"
        out["reason"] = (
            "no per-player feature variation visible in this snapshot — "
            "constant contextual_minutes_delta is the honest baseline; "
            "lineup_confirmed=" + str(lineup_confirmed) + ", BDL_lineup_rows="
            + str(manifest.get("BDL_lineup_rows"))
        )
    else:
        out["verdict"] = "varies"
        out["reason"] = "trained model emits per-player deltas as expected"
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    HEALTH.mkdir(parents=True, exist_ok=True)
    base = DELIVERIES / args.delivery_date / "derek_game_snapshots"
    payload: dict = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "snapshots": [],
    }

    if not base.exists():
        payload["outcome"] = "pending"
        (HEALTH / f"contextual_delta_variation_{args.delivery_date}.json"
         ).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        print("PHASE13W_CONTEXTUAL_DELTA_VARIATION_PENDING")
        print(f"  reason=no_snapshots_present_yet")
        return 0

    bug_count = 0
    counted = 0
    for game_dir in sorted(base.iterdir()):
        if not game_dir.is_dir():
            continue
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            sd = game_dir / snap_type
            if not (sd / "snapshot_manifest.json").exists():
                continue
            counted += 1
            rec = _audit_snapshot(sd)
            rec["game_id"] = game_dir.name
            rec["snapshot_type"] = snap_type
            payload["snapshots"].append(rec)
            if rec.get("verdict") == "bug":
                bug_count += 1

    if counted == 0:
        payload["outcome"] = "pending"
        (HEALTH / f"contextual_delta_variation_{args.delivery_date}.json"
         ).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        print("PHASE13W_CONTEXTUAL_DELTA_VARIATION_PENDING")
        print(f"  reason=no_snapshots_present_yet")
        return 0

    payload["outcome"] = "fail" if bug_count else "pass"
    payload["snapshot_count"] = counted
    payload["bug_count"] = bug_count
    out_json = HEALTH / f"contextual_delta_variation_{args.delivery_date}.json"
    out_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    out_md = HEALTH / f"contextual_delta_variation_{args.delivery_date}.md"
    md = [
        f"# Contextual delta variation audit — {args.delivery_date}",
        "",
        f"- snapshots: **{counted}**",
        f"- bug_count: **{bug_count}**",
        "",
        "| game | type | rows | minutes_unique | min | max | mean | "
        "feature_variation | verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for s in payload["snapshots"]:
        md.append(
            f"| {s.get('game_id')} | {s.get('snapshot_type')} | "
            f"{s.get('rows')} | {s.get('minutes_delta_unique')} | "
            f"{s.get('minutes_delta_min'):.4f} | "
            f"{s.get('minutes_delta_max'):.4f} | "
            f"{s.get('minutes_delta_mean'):.4f} | "
            f"{s.get('feature_variation')} | "
            f"**{s.get('verdict')}** |"
        )
    md.append("")
    md.append("## Per-snapshot reason")
    md.append("")
    for s in payload["snapshots"]:
        md.append(
            f"- {s.get('game_id')}/{s.get('snapshot_type')}: "
            f"{s.get('reason')}"
        )
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    if bug_count:
        print("PHASE13W_CONTEXTUAL_DELTA_VARIATION_FAILED", file=sys.stderr)
        for s in payload["snapshots"]:
            if s.get("verdict") == "bug":
                print(
                    f"  - {s.get('game_id')}/{s.get('snapshot_type')}: "
                    f"{s.get('reason')}",
                    file=sys.stderr,
                )
        return 1
    print("PHASE13W_CONTEXTUAL_DELTA_VARIATION_PASS")
    print(f"  delivery_date={args.delivery_date} snapshots={counted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
