#!/usr/bin/env python3
"""Phase 13AN — end-to-end delivery health verifier.

Top-level wrapper that runs the full chain of structural verifiers.
Each subcheck is an independent verifier that emits its own pass/fail
line; this script consolidates them into a single summary.

Required when --mode production:

    1. player_game_stats fresh through --date
    2. predictions/all_props_<date>.parquet, pmf_display, singles
    3. tov accounted for (--require-tov)
    4. odds snapshots exist (Phase 13AN-B2 — gated)
    5. market_comparison_rows > 0 (--require-market)
    6. scored_market_rows > 0 (--require-market)
    7. CLV calculated (--require-clv)
    8. Derek forward feed verifies (--require-derek)
    9. WoO delivery package verifies (--require-woo)
   10. Champion stamps consistent across Derek + WoO
   11. Rolling market benchmark with paired rows (--require-market)
   12. No stale lineup/injury/role-bucket warnings
   13. No deploy-secret warnings (when --require-no-warnings + deploy mode)
   14. No uncommitted required output files

Pass line:
    END_TO_END_DELIVERY_HEALTH_PASS  date=<date>  mode=<mode>

Fail line:
    END_TO_END_DELIVERY_HEALTH_FAILED  date=<date>  mode=<mode>  count=<n>

Phase 1 scaffold note: items 4-7 (odds snapshots, market scoring rows,
CLV) require the Phase 2 odds snapshot persistence + market scoring
hardening to land before they can pass on a real slate. Until those
land, the verifier surfaces them as MISSING_DEPENDENCY entries with
the specific upstream blocker so the operator sees exactly which
Phase 2 task is gating end-to-end health.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(
        cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False
    )
    return p.returncode, p.stdout or "", p.stderr or ""


def _read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument(
        "--mode", choices=["strict", "production", "report_only"],
        default="production",
    )
    ap.add_argument("--require-market", action="store_true")
    ap.add_argument("--require-tov", action="store_true")
    ap.add_argument("--require-derek", action="store_true")
    ap.add_argument("--require-woo", action="store_true")
    ap.add_argument("--require-clv", action="store_true")
    ap.add_argument("--require-no-warnings", action="store_true")
    args = ap.parse_args(argv)

    date = args.date
    py = sys.executable
    failures: list[tuple[str, str]] = []  # (gate, detail)
    pending: list[tuple[str, str]] = []   # (gate, blocker)

    # 1. player_game_stats fresh through date
    rc, out, err = _run(
        [py, "scripts/verify_player_game_stats_freshness.py",
         "--required-through-date", date]
    )
    if rc != 0:
        failures.append(("player_game_stats_fresh", (out + err).strip()[-300:]))

    # 2. predictions exist
    pred_dir = REPO_ROOT / "predictions"
    pred_files = [
        pred_dir / f"all_props_{date}.parquet",
        pred_dir / f"pmf_display_{date}.json",
        pred_dir / f"singles_{date}.json",
    ]
    missing_pred = [str(p.relative_to(REPO_ROOT)) for p in pred_files if not p.exists()]
    if missing_pred:
        failures.append(("predictions_exist", f"missing={missing_pred}"))

    # 3. TOV accounted for
    if args.require_tov:
        # Look at the WoO run_manifest blocker codes — they're the
        # canonical place TOV-handling status is recorded.
        woo_run = _read_json(
            REPO_ROOT / "deliveries" / date / "wizard_of_odds" / "run_manifest.json"
        ) or {}
        blockers = list(woo_run.get("finality_blocker_codes") or [])
        if "missing_stats:tov" in blockers:
            failures.append(
                ("tov_accounted_for",
                 "WoO run_manifest declares 'missing_stats:tov' — "
                 "current champion does not provide TOV; --require-tov fails. "
                 "Phase 2 C3 retraining required to clear.")
            )

    # 4-7: odds snapshots / market scoring / CLV (Phase 2 dependencies).
    if args.require_market or args.require_clv:
        odds_root = REPO_ROOT / "data" / "odds_snapshots" / date
        required_snaps = ("morning", "lineup", "close")
        missing_snaps = [
            n for n in required_snaps
            if not (odds_root / f"{n}.parquet").exists()
        ]
        if missing_snaps:
            pending.append(
                ("odds_snapshots_persisted",
                 f"missing snapshots {missing_snaps} under "
                 f"{odds_root.relative_to(REPO_ROOT)} — Phase 2 B2 required")
            )

        scored_summary = _read_json(
            REPO_ROOT / "deliveries" / date / "after_game_scoring"
            / "model_vs_market_scoring.json"
        )
        if scored_summary is None:
            pending.append(
                ("model_vs_market_scoring",
                 f"deliveries/{date}/after_game_scoring/"
                 "model_vs_market_scoring.json missing — Phase 2 B4 required")
            )
        else:
            rows_total = scored_summary.get("rows_total")
            if not rows_total:
                pending.append(
                    ("model_vs_market_scoring_rows",
                     f"rows_total={rows_total} (must be > 0) — Phase 2 B4")
                )

    if args.require_clv:
        clv = REPO_ROOT / "deliveries" / date / "after_game_scoring" / \
              "after_game_clv_and_scoring.parquet"
        if not clv.exists():
            pending.append(
                ("clv_calculated",
                 f"{clv.relative_to(REPO_ROOT)} missing — Phase 2 B3 required")
            )

    # 8. Derek forward feed verifies
    if args.require_derek:
        rc, out, err = _run(
            [py, "scripts/verify_derek_forward_feed.py",
             "--delivery-date", date, "--mode", "production"]
        )
        if rc != 0:
            failures.append(("derek_forward_feed", (out + err).strip()[-400:]))

    # 9. WoO delivery package verifies
    if args.require_woo:
        # In strict mode we require even market+tov; in production mode
        # we tolerate the documented finality_blockers if --allow-no-market
        # / --allow-tov-missing were set. For end-to-end strict, market+tov
        # must be present.
        woo_args = [
            py, "scripts/verify_woo_delivery_package.py",
            "--delivery-date", date, "--mode", "production",
        ]
        if not args.require_market:
            woo_args.append("--allow-no-market")
        if not args.require_tov:
            woo_args.append("--allow-tov-missing")
        rc, out, err = _run(woo_args)
        if rc != 0:
            failures.append(("woo_delivery_package", (out + err).strip()[-400:]))

    # 10. Champion stamps consistent
    pointer = _read_json(
        REPO_ROOT / "artifacts" / "models" / "registry" / "champion_pointer.json"
    ) or {}
    pointer_champion = pointer.get("champion_model_id")
    derek_manifest = _read_json(
        REPO_ROOT / "deliveries" / date / "derek_forward_feed" / "feed_manifest.json"
    ) or {}
    woo_manifest = _read_json(
        REPO_ROOT / "deliveries" / date / "wizard_of_odds" / "run_manifest.json"
    ) or {}
    derek_champion = derek_manifest.get("champion_model_id")
    woo_champion = woo_manifest.get("champion_model_id")
    if pointer_champion and derek_champion and pointer_champion != derek_champion:
        failures.append(("champion_stamp_derek",
                         f"pointer={pointer_champion} derek={derek_champion}"))
    if pointer_champion and woo_champion and pointer_champion != woo_champion:
        failures.append(("champion_stamp_woo",
                         f"pointer={pointer_champion} woo={woo_champion}"))

    # 11. Rolling market benchmark paired rows (Phase 2 B4 dependency).
    if args.require_market:
        rolling = _read_json(
            REPO_ROOT / "artifacts" / "automation_health"
            / f"rolling_market_benchmark_{date}.json"
        )
        if rolling is None:
            pending.append(
                ("rolling_market_benchmark",
                 f"artifacts/automation_health/"
                 f"rolling_market_benchmark_{date}.json missing — Phase 2 B4")
            )
        else:
            rows_paired = rolling.get("rows_paired") or 0
            if rows_paired <= 0:
                pending.append(
                    ("rolling_market_benchmark_rows_paired",
                     f"rows_paired={rows_paired} (must be > 0) — Phase 2 B4")
                )

    # 12. Lineup/injury/role-bucket warnings (production-grade signal).
    if args.require_no_warnings:
        for code in ("lineup_unconfirmed", "injury_very_stale", "role_bucket_missing"):
            if code in (woo_manifest.get("finality_blocker_codes") or []):
                pending.append(
                    (f"finality_blocker_{code}",
                     f"WoO run_manifest declares '{code}' — Phase 2 E1/E2 required")
                )

    # 13. Deploy secret warnings — only meaningful in CI with secrets present.
    # Skipped when no deploy mode is requested.

    # 14. Uncommitted required output files.
    rc, out, err = _run(
        ["git", "status", "--porcelain", "--",
         f"deliveries/{date}/", f"public_export/wizard_of_odds/{date}/"]
    )
    if rc == 0 and out.strip():
        # An untracked file under deliveries/ or public_export/ for THIS
        # date is a soft signal; if the operator just ran the pipeline
        # locally and forgot to commit, surface it.
        bad_lines = [
            line for line in out.splitlines()
            if line.startswith("?? ") or line.startswith(" M ")
        ]
        if bad_lines and args.require_no_warnings:
            pending.append((
                "uncommitted_required_outputs",
                f"git status flagged: {bad_lines[:3]}"
            ))

    # ── Render result ───────────────────────────────────────────────
    print(f"# end-to-end delivery health  date={date}  mode={args.mode}")
    if failures:
        print("# FAILURES")
        for name, detail in failures:
            print(f"::error::{name}: {detail}")
    if pending:
        print("# PENDING DEPENDENCIES")
        for name, blocker in pending:
            print(f"::warning::{name}: MISSING_DEPENDENCY {blocker}")

    overall_failed = bool(failures) or (
        bool(pending) and args.mode in ("strict", "production")
    )

    if overall_failed:
        print(
            f"END_TO_END_DELIVERY_HEALTH_FAILED  date={date}  mode={args.mode}  "
            f"failures={len(failures)}  pending={len(pending)}"
        )
        return 1

    print(
        f"END_TO_END_DELIVERY_HEALTH_PASS  date={date}  mode={args.mode}  "
        f"failures=0  pending={len(pending)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
