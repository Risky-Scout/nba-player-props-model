#!/usr/bin/env python3
"""M8.8 — static audit of injury/lineup behaviour vs run modes."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _must(path: Path, needle: str) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"missing_file:{path.name}"
    t = path.read_text(encoding="utf-8")
    if needle not in t:
        return False, f"missing_sentinel:{needle!r}_in_{path.name}"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--latest-completed-date", required=True)
    args = ap.parse_args()

    out = REPO_ROOT / "artifacts" / "model_diagnostics" / "injury_lineup_run_modes"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    ok_all = True

    rdp = REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py"
    ok, msg = _must(rdp, "run_mode_stamp")
    rows.append({"check": "pipeline_passes_run_mode_stamp_to_derek", "ok": ok, "detail": msg})
    ok_all &= ok

    ok, msg = _must(rdp, "morning_expected")
    rows.append({"check": "pipeline_documents_morning_expected", "ok": ok, "detail": msg})
    ok_all &= ok

    bdp = REPO_ROOT / "scripts" / "build_daily_pmf_delivery.py"
    ok, msg = _must(bdp, "injury_freshness_status")
    rows.append({"check": "delivery_emits_injury_freshness", "ok": ok, "detail": msg})
    ok_all &= ok

    ok, msg = _must(bdp, "lineup_freshness_status")
    rows.append({"check": "delivery_emits_lineup_freshness", "ok": ok, "detail": msg})
    ok_all &= ok

    bdf = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
    ok, msg = _must(bdf, "lineup_snapshot_status.json")
    rows.append({"check": "derek_writes_lineup_status_json", "ok": ok, "detail": msg})
    ok_all &= ok

    ok, msg = _must(bdf, "fabricates lineup data")
    rows.append({"check": "derek_docstrings_reject_fabrication", "ok": ok, "detail": msg})
    ok_all &= ok

    av = REPO_ROOT / "data" / "player_availability_asof.parquet"
    rows.append(
        {
            "check": "availability_table_exists",
            "ok": av.is_file(),
            "detail": "" if av.is_file() else "missing_data/player_availability_asof.parquet",
        }
    )
    ok_all &= av.is_file()

    with (out / "source_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "ok", "detail"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    modes = [
        ("morning_expected", "expected_lineup", "official_not_required"),
        ("t25", "injury_refresh", "official_lineup_attempt"),
        ("t5", "final_pregame", "official_lineup_attempt"),
        ("final_after_game", "actuals", "box_score"),
    ]
    with (out / "run_mode_contract.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_mode", "lineup_policy", "official_lineup_policy"])
        for m in modes:
            w.writerow(m)

    (out / "stale_availability_risks.csv").write_text("check,detail\n", encoding="utf-8")

    summ = {
        "date": args.date,
        "latest_completed_date": args.latest_completed_date,
        "pass_all": ok_all,
    }
    (out / "summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")
    md = [
        f"# Injury / lineup run-mode audit ({args.date})",
        "",
        f"- **pass_all**: `{ok_all}`",
        "",
    ]
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if ok_all:
        print("INJURY_LINEUP_RUN_MODE_AUDIT_PASS")
    else:
        print("INJURY_LINEUP_RUN_MODE_AUDIT_FAIL")
    return 0 if ok_all else 2


if __name__ == "__main__":
    raise SystemExit(main())
