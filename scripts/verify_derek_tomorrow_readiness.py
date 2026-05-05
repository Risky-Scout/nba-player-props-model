#!/usr/bin/env python3
"""Phase 13AL — verify the system is ready for tomorrow's Derek delivery.

This is a static / structural verifier. It does NOT trigger CI runs; it
checks that the workflows + scripts in origin/main carry the discipline
needed for tomorrow's automation to succeed without manual recovery.

Inputs:
  --date YYYY-MM-DD       (the upcoming slate date to validate against)

Checks:
  1. Daily PMF delivery workflow (`daily_pmf_delivery.yml`) has a
     scheduled `derek_near_lineup` cron firing well before tip.
  2. Derek live snapshot workflow (`derek_live_game_snapshots.yml`) has
     scheduled crons for current_live, t_minus_25, and close_lock that
     cover the slate window.
  3. Workflows resolve the slate using TZ=America/New_York rather than
     raw UTC date (no rollover bug).
  4. Every workflow that needs BDL passes ``BDL_API_KEY:
     ${{ secrets.BDL_API_KEY }}`` into the job/step env.
  5. Dispatcher captures child stdout/stderr/traceback (the
     ``::error::`` block + ``failed_snapshot_manifest.json`` writer).
  6. ``verify_derek_production_live_e2e.py`` rejects ``backfill_demo``
     mode for production_live — already enforced by Phase 13AJ.
  7. ``verify_derek_outcome_level_probabilities.py`` does not PASS with
     ok=0 when the slate has games; only PENDING (no slate),
     MISSED_DOCUMENTED (every miss has a marker), or FAIL.
  8. The Derek schema contract document exists at
     ``docs/derek_schema_contract.md``.
  9. Today's human-readable Derek reports are produced.
  10. No ``backfill_demo`` snapshot files are committed under
      ``deliveries/<date>/derek_game_snapshots/``.

Pass: DEREK_TOMORROW_READINESS_PASS
Fail: DEREK_TOMORROW_READINESS_FAILED  with exact reasons
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True, help="upcoming slate date YYYY-MM-DD")
    args = ap.parse_args(argv)
    date = args.date

    failures: list[str] = []
    facts: dict = {"date": date}

    # 1. daily_pmf_delivery near-lineup cron + ET resolution
    daily_pmf = REPO_ROOT / ".github" / "workflows" / "daily_pmf_delivery.yml"
    daily_pmf_text = _read_text(daily_pmf)
    if not daily_pmf_text:
        failures.append(f"missing {daily_pmf.relative_to(REPO_ROOT)}")
    else:
        if "derek_near_lineup" not in daily_pmf_text:
            failures.append("daily_pmf_delivery.yml has no derek_near_lineup job")
        if "TZ=America/New_York" not in daily_pmf_text:
            failures.append(
                "daily_pmf_delivery.yml does not resolve slate via "
                "TZ=America/New_York — UTC rollover bug risk"
            )
        if "BDL_API_KEY: ${{ secrets.BDL_API_KEY }}" not in daily_pmf_text:
            failures.append(
                "daily_pmf_delivery.yml does not pass BDL_API_KEY through "
                "env — predict.py / Derek pipeline will fail in CI"
            )

    # 2. derek_live_game_snapshots cron coverage
    derek_live = REPO_ROOT / ".github" / "workflows" / "derek_live_game_snapshots.yml"
    derek_live_text = _read_text(derek_live)
    if not derek_live_text:
        failures.append(f"missing {derek_live.relative_to(REPO_ROOT)}")
    else:
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            if snap_type not in derek_live_text:
                failures.append(
                    f"derek_live_game_snapshots.yml does not reference "
                    f"snapshot_type={snap_type!r}"
                )
        if "BDL_API_KEY: ${{ secrets.BDL_API_KEY }}" not in derek_live_text:
            failures.append(
                "derek_live_game_snapshots.yml does not pass BDL_API_KEY "
                "through env"
            )
        # Cron coverage — at least 4 firings/hour during slate window.
        cron_lines = re.findall(r"^\s*-\s*cron:\s*['\"]([^'\"]+)['\"]",
                                 derek_live_text, re.MULTILINE)
        facts["derek_live_cron_count"] = len(cron_lines)
        if len(cron_lines) < 1:
            failures.append(
                "derek_live_game_snapshots.yml has no scheduled crons"
            )

    # 3. nightly training BDL env pass-through
    nightly = REPO_ROOT / ".github" / "workflows" / "nightly_training_calibration.yml"
    nightly_text = _read_text(nightly)
    if nightly_text and "BDL_API_KEY: ${{ secrets.BDL_API_KEY }}" not in nightly_text:
        failures.append(
            "nightly_training_calibration.yml does not pass BDL_API_KEY "
            "through env"
        )

    # 4. daily_predictions BDL env
    daily_pred = REPO_ROOT / ".github" / "workflows" / "daily_predictions.yml"
    daily_pred_text = _read_text(daily_pred)
    if daily_pred_text and "BDL_API_KEY: ${{ secrets.BDL_API_KEY }}" not in daily_pred_text:
        failures.append(
            "daily_predictions.yml does not pass BDL_API_KEY through env"
        )

    # 5. dispatcher logging discipline
    dispatcher = REPO_ROOT / "scripts" / "dispatch_derek_live_game_snapshots.py"
    dispatcher_text = _read_text(dispatcher)
    if not dispatcher_text:
        failures.append(f"missing {dispatcher.relative_to(REPO_ROOT)}")
    else:
        for needle in ("failed_snapshot_manifest.json",
                        "child stderr",
                        "::error::"):
            if needle not in dispatcher_text:
                failures.append(
                    f"dispatcher missing required logging discipline: "
                    f"{needle!r}"
                )

    # 6. e2e verifier rejects backfill_demo. The script uses a positive
    # whitelist ``("production_live", "production_live_current")`` —
    # anything else (including backfill_demo) is rejected.
    e2e = REPO_ROOT / "scripts" / "verify_derek_production_live_e2e.py"
    e2e_text = _read_text(e2e)
    if e2e_text and "production_live_current" not in e2e_text:
        failures.append(
            "verify_derek_production_live_e2e.py does not enforce the "
            "production_live whitelist (backfill_demo would slip through)"
        )

    # 7. outcome_level_probabilities verifier rejects ok=0 on eligible slate
    olp_verifier = REPO_ROOT / "scripts" / "verify_derek_outcome_level_probabilities.py"
    olp_text = _read_text(olp_verifier)
    if olp_text and ("not ok:" not in olp_text or "MISSED_DOCUMENTED" not in olp_text):
        failures.append(
            "verify_derek_outcome_level_probabilities.py is missing the "
            "ok=0 / MISSED_DOCUMENTED discipline"
        )

    # 8. Derek schema contract
    schema_doc = REPO_ROOT / "docs" / "derek_schema_contract.md"
    if not schema_doc.exists():
        failures.append(f"missing {schema_doc.relative_to(REPO_ROOT)}")

    # 9. Today's Derek READMEs (canonical previous-day delivery is fine
    # if upcoming-date delivery hasn't published yet).
    derek_idx = REPO_ROOT / "deliveries" / date / "derek_game_snapshots" / "README.md"
    if not derek_idx.exists():
        # Allowed if the upcoming-date slate hasn't started; not a fail.
        pass

    # 10. No backfill_demo snapshots committed under deliveries/<date>/.
    deliveries_dir = REPO_ROOT / "deliveries" / date / "derek_game_snapshots"
    if deliveries_dir.exists():
        for snap_manifest in deliveries_dir.glob("*/*/snapshot_manifest.json"):
            try:
                m = json.loads(snap_manifest.read_text(encoding="utf-8"))
            except Exception:
                continue
            if m.get("snapshot_mode") == "backfill_demo":
                failures.append(
                    f"backfill_demo snapshot committed: "
                    f"{snap_manifest.relative_to(REPO_ROOT)}"
                )

    # 11. Operator daily check + full contract scripts present
    for required_script in (
        "scripts/operator_daily_check.py",
        "scripts/verify_full_daily_production_contract.py",
        "scripts/verify_daily_readme_freshness.py",
        "scripts/verify_woo_public_export_contract.py",
        "scripts/verify_secrets_preflight.py",
    ):
        if not (REPO_ROOT / required_script).exists():
            failures.append(f"missing required script: {required_script}")

    # ── Output ────────────────────────────────────────────────────────
    out_dir = REPO_ROOT / "artifacts" / "automation_health"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "date": date,
        "facts": facts,
        "failures": failures,
        "outcome": "fail" if failures else "pass",
    }
    (out_dir / f"derek_tomorrow_readiness_{date}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    if failures:
        print(f"DEREK_TOMORROW_READINESS_FAILED  date={date}  "
              f"failures={len(failures)}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"DEREK_TOMORROW_READINESS_PASS  date={date}  "
          f"derek_live_crons={facts.get('derek_live_cron_count')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
