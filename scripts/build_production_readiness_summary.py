#!/usr/bin/env python3
"""Aggregate M8.8 audit outputs into a single production-readiness summary."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(p: Path) -> dict:
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of-date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    args = ap.parse_args()
    art = REPO_ROOT / "artifacts" / "model_diagnostics"
    comp = _read_json(art / "daily_delivery_completeness_last_run" / "summary.json")
    inj = _read_json(art / "injury_lineup_run_modes" / "summary.json")
    gh = _read_json(art / "github_delivery_automation" / "summary.json")
    payload = {
        "as_of_date": args.as_of_date,
        "delivery_completeness_pass": comp.get("pass_all"),
        "injury_lineup_audit_pass": inj.get("pass_all"),
        "github_automation_pass": gh.get("pass_all"),
        "notes": (
            "This file is generated locally from audit artifacts; it is not committed "
            "unless explicitly requested."
        ),
    }
    outd = art
    outd.mkdir(parents=True, exist_ok=True)
    stem = f"production_readiness_summary_{args.as_of_date}"
    (outd / f"{stem}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Production readiness summary ({args.as_of_date})",
        "",
        f"- Delivery completeness pass: **{payload['delivery_completeness_pass']}**",
        f"- Injury/lineup audit pass: **{payload['injury_lineup_audit_pass']}**",
        f"- GitHub automation audit pass: **{payload['github_automation_pass']}**",
        "",
        "See nested bullets in mission M8.8 Phase 7 for narrative answers once audits are green.",
        "",
    ]
    (outd / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {outd.relative_to(REPO_ROOT)}/{stem}.{{json,md}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
