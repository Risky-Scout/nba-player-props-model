#!/usr/bin/env python3
"""Static guardrail for corrected PMF production entrypoints.

This verifier checks that Derek/WoO production paths use the corrected PMF
delivery source instead of legacy all_props / broad-stat paths.

It intentionally does not forbid all legacy scripts from existing. It only
guards paths that can publish, commit, or deploy Derek/WoO-facing PMF outputs.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FAILURES: list[str] = []
WARNINGS: list[str] = []


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read(path: str) -> str:
    p = REPO_ROOT / path
    if not p.exists():
        FAILURES.append(f"missing required file: {path}")
        return ""
    return p.read_text(errors="replace")


def require(condition: bool, message: str) -> None:
    if not condition:
        FAILURES.append(message)


def warn(condition: bool, message: str) -> None:
    if not condition:
        WARNINGS.append(message)


def contains(path: str, needle: str) -> bool:
    return needle in read(path)


def ordered(path: str, first: str, second: str) -> bool:
    s = read(path)
    a = s.find(first)
    b = s.find(second)
    return a >= 0 and b >= 0 and a < b


def main() -> int:
    # No temporary workflow clutter.
    smoke = REPO_ROOT / ".github/workflows/derek_corrected_pmf_manual_smoke.yml"
    require(not smoke.exists(), f"temporary smoke workflow still exists: {rel(smoke)}")

    # Core corrected PMF delivery verifier must exist and enforce public/Derek contract.
    verifier = "scripts/verify_corrected_pmf_delivery.py"
    verifier_s = read(verifier)
    require("CORE_STATS" in verifier_s, f"{verifier} must define CORE_STATS")
    for stat in ["pts", "reb", "ast", "fg3m", "tov"]:
        require(stat in verifier_s, f"{verifier} missing core stat guard: {stat}")
    for bad in ["stl", "blk", "stocks"]:
        require(bad not in verifier_s or "extra" in verifier_s,
                f"{verifier} must reject broad/extra stat leakage including {bad}")
    require("affiliate_dashboard count must be > 0" in verifier_s,
            f"{verifier} must require affiliate_dashboard count > 0")
    require("false Derek no_games_today.json" in verifier_s,
            f"{verifier} must reject false Derek no_games_today.json")

    # WoO publisher must read dated corrected delivery, not predictions/all_props.
    woo_pub = "scripts/publish_woo_public_export.py"
    woo_s = read(woo_pub)
    require("full_pmfs_wide.parquet" in woo_s,
            f"{woo_pub} must read wizard_of_odds/full_pmfs_wide.parquet")
    require("_validate_delivery_wide" in woo_s,
            f"{woo_pub} must validate delivery wide file")
    require("predictions/all_props" not in woo_s,
            f"{woo_pub} must not publish public PMF from predictions/all_props")
    require("allow-empty-affiliate" in woo_s,
            f"{woo_pub} must refuse empty affiliate output by default")

    # Corrected Derek builder must source from WoO delivery.
    derek_builder = "scripts/build_derek_game_snapshots_from_delivery.py"
    derek_builder_s = read(derek_builder)
    require("full_pmfs_wide.parquet" in derek_builder_s,
            f"{derek_builder} must source corrected full_pmfs_wide.parquet")
    require("wizard_of_odds" in derek_builder_s,
            f"{derek_builder} must source from dated wizard_of_odds delivery")
    require("no_games_today.json is illegal" in derek_builder_s or "false_no_games" in derek_builder_s,
            f"{derek_builder} must remove/reject false no_games_today.json")
    for bad in ["stl", "blk", "stocks"]:
        require(bad in derek_builder_s,
                f"{derek_builder} should explicitly document/reject {bad} leakage")

    # Orchestrator must use stat-grid -> canonical -> delivery -> Derek/WoO -> verifier.
    orch = "scripts/run_daily_delivery_pipeline.py"
    orch_s = read(orch)
    for needle in [
        "build_stat_grid_pmfs.py",
        "build_model_only_canonical_from_stat_grid.py",
        "build_daily_pmf_delivery.py",
        "build_derek_game_snapshots_from_delivery.py",
        "publish_woo_public_export.py",
        "verify_corrected_pmf_delivery.py",
    ]:
        require(needle in orch_s, f"{orch} missing corrected production step: {needle}")
    require("CORRECTED_PMF_VERIFY" in orch_s and "_verify_corrected_pmf_delivery" in orch_s,
            f"{orch} must hard-gate corrected PMF delivery")

    # Daily PMF delivery workflow should route through orchestrator.
    daily_wf = ".github/workflows/daily_pmf_delivery.yml"
    daily_s = read(daily_wf)
    require("scripts/run_daily_delivery_pipeline.py" in daily_s,
            f"{daily_wf} must route production through orchestrator")
    require("scripts/publish_woo_public_export.py" in daily_s,
            f"{daily_wf} must use protected WoO publisher")
    warn("scripts/verify_corrected_pmf_delivery.py" in daily_s or "verify_corrected_pmf_delivery.py" in orch_s,
         f"{daily_wf} should expose corrected verifier directly or via orchestrator")

    # WoO after-game scoring must use corrected PMF delivery, not legacy all_props.
    daily_predictions_wf = ".github/workflows/daily_predictions.yml"
    daily_predictions_s = read(daily_predictions_wf)
    require("scripts/score_woo_after_game.py" not in daily_predictions_s,
            f"{daily_predictions_wf} must not call legacy all_props WoO scorer")
    require("scripts/score_daily_pmf_delivery_after_game.py" in daily_predictions_s,
            f"{daily_predictions_wf} must score corrected PMF delivery after game")

    full_contract = "scripts/verify_full_daily_production_contract.py"
    full_contract_s = read(full_contract)
    require("scripts/score_woo_after_game.py" not in full_contract_s,
            f"{full_contract} must not call legacy all_props WoO scorer")
    require("scripts/score_daily_pmf_delivery_after_game.py" in full_contract_s,
            f"{full_contract} must score corrected PMF delivery after game")

    # WoO FTP deploy must verify corrected PMF delivery before deploy.
    ftp_wf = ".github/workflows/wizard_of_odds_ftp_deploy.yml"
    ftp_s = read(ftp_wf)
    require("scripts/publish_woo_public_export.py" in ftp_s,
            f"{ftp_wf} must use protected public exporter")
    require("scripts/deploy_wizard_of_odds_ftp.py" in ftp_s,
            f"{ftp_wf} missing FTP deploy step")
    require("scripts/verify_corrected_pmf_delivery.py" in ftp_s,
            f"{ftp_wf} must run corrected PMF verifier before FTP deploy")
    if "scripts/verify_corrected_pmf_delivery.py" in ftp_s:
        require(ordered(ftp_wf, "scripts/verify_corrected_pmf_delivery.py", "scripts/deploy_wizard_of_odds_ftp.py"),
                f"{ftp_wf} must verify corrected PMF delivery before FTP deploy")

    # Existing Derek workflow must not keep old dispatcher/no-games path as production authority.
    derek_wf = ".github/workflows/derek_game_snapshots.yml"
    derek_wf_s = read(derek_wf)
    require("Build Derek snapshots from corrected PMF delivery" in derek_wf_s,
            f"{derek_wf} must build from corrected PMF delivery")
    require("Verify corrected PMF delivery contract" in derek_wf_s,
            f"{derek_wf} must verify corrected PMF delivery")
    require("scripts/build_derek_game_snapshots_from_delivery.py" in derek_wf_s,
            f"{derek_wf} must call corrected Derek builder")
    require("scripts/verify_corrected_pmf_delivery.py" in derek_wf_s,
            f"{derek_wf} must call corrected delivery verifier")
    require("scripts/dispatch_derek_live_game_snapshots.py" not in derek_wf_s,
            f"{derek_wf} still calls legacy dispatcher; retire or isolate it from production")
    require("no_games_today.json" not in derek_wf_s,
            f"{derek_wf} still has no_games_today sentinel logic; corrected builder/verifier must own this")

    # build_daily_pmf_delivery may still support all_props for legacy/backfill,
    # but production must reject stale broad packages.
    bdp = "scripts/build_daily_pmf_delivery.py"
    bdp_s = read(bdp)
    require("Block stale all_props" in bdp_s or "stale all_props" in bdp_s,
            f"{bdp} must explicitly reject stale broad all_props PMFs")
    require("extra_relative_to_supported" in bdp_s or "extra" in bdp_s,
            f"{bdp} must reject extra broad stats in production delivery")
    require("role_bucket" in bdp_s,
            f"{bdp} must propagate/validate role_bucket metadata")

    print("PRODUCTION_PMF_ENTRYPOINT_AUDIT")
    if WARNINGS:
        print("\nWARNINGS:")
        for w in WARNINGS:
            print(f"  - {w}")

    if FAILURES:
        print("\nFAILURES:")
        for f in FAILURES:
            print(f"  - {f}")
        raise SystemExit(1)

    print("\nPRODUCTION_PMF_ENTRYPOINT_VERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
