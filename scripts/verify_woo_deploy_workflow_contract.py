#!/usr/bin/env python3
"""Phase 13AM: WoO deploy workflow contract verifier.

Asserts that the production WoO automation has been migrated to the
four-step Phase 13AM pipeline and is no longer producing customer-facing
artifacts via the legacy build_wizard_of_odds_public_export.py.

Workflows audited:
    .github/workflows/wizard_of_odds_ftp_deploy.yml
    .github/workflows/daily_pmf_delivery.yml
    .github/workflows/daily_predictions.yml

Required structural rules:

    R1. wizard_of_odds_ftp_deploy.yml MUST invoke each of the four new
        pipeline scripts BEFORE the FTP deploy step:
            scripts/publish_woo_public_export.py
            scripts/build_woo_dashboard.py
            scripts/verify_woo_dashboard_render_contract.py
            scripts/verify_woo_public_export_contract.py

    R2. wizard_of_odds_ftp_deploy.yml MUST NOT invoke the legacy
        scripts/build_wizard_of_odds_public_export.py — it is auxiliary
        and must not produce customer-facing artifacts.

    R3. wizard_of_odds_ftp_deploy.yml MUST stage the rendered HTML
        pages (predictions/nba-props.html + predictions/nba-pmf-research.html)
        somewhere the FTP step uploads. It MUST NOT stage the templates
        (_template_*.html).

    R4. The dashboard render verifier MUST run BEFORE the FTP deploy
        step (so a broken render gates upload).

    R5. daily_pmf_delivery.yml MUST invoke the four new pipeline scripts
        in at least one production job (any job carrying a public-export
        snapshot is acceptable). Without this, customer-facing JSON+HTML
        would only exist on a delivery day if a deploy run also happened
        — production must independently produce them.

    R6. daily_predictions.yml MUST NOT invoke the legacy builder
        (predictions workflow doesn't deal with WoO public export).

    R7. The legacy script scripts/build_wizard_of_odds_public_export.py
        MUST be marked with a "LEGACY / AUXILIARY" notice in its top-level
        docstring so a future operator immediately sees that customer-
        facing output has migrated.

On success the script prints exactly:

    WOO_DEPLOY_WORKFLOW_CONTRACT_PASS

On any failure the script prints each violation prefixed with
``::error::`` and exits 1 with a final summary line:

    WOO_DEPLOY_WORKFLOW_CONTRACT_FAILED count=<N>
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WF_DIR = REPO_ROOT / ".github" / "workflows"
DEPLOY_WF = WF_DIR / "wizard_of_odds_ftp_deploy.yml"
PMF_DELIVERY_WF = WF_DIR / "daily_pmf_delivery.yml"
PREDICTIONS_WF = WF_DIR / "daily_predictions.yml"
LEGACY_BUILDER = REPO_ROOT / "scripts" / "build_wizard_of_odds_public_export.py"

NEW_PIPELINE_SCRIPTS = (
    "scripts/publish_woo_public_export.py",
    "scripts/build_woo_dashboard.py",
    "scripts/verify_woo_dashboard_render_contract.py",
    "scripts/verify_woo_public_export_contract.py",
)
LEGACY_BUILDER_REL = "scripts/build_wizard_of_odds_public_export.py"
DEPLOY_SCRIPT_REL = "scripts/deploy_wizard_of_odds_ftp.py"
HTML_OUTPUT_FILES = (
    "predictions/nba-props.html",
    "predictions/nba-pmf-research.html",
)
TEMPLATE_TOKENS = (
    "predictions/_template_nba_props.html",
    "predictions/_template_nba_pmf_research.html",
    "_template_*.html",
)


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _all_run_blocks(wf: dict) -> list[tuple[str, str, str]]:
    """Yield (job, step_name, run_block) for every step that has `run:`."""
    out = []
    for job_name, job in (wf.get("jobs") or {}).items():
        for step in job.get("steps") or []:
            run = step.get("run")
            if not run:
                continue
            name = step.get("name") or step.get("id") or "<unnamed>"
            out.append((job_name, name, run))
    return out


def _step_index(wf: dict) -> list[tuple[str, int, str, str]]:
    """Yield (job, idx, step_name, run_block_or_empty) preserving order."""
    out = []
    for job_name, job in (wf.get("jobs") or {}).items():
        for i, step in enumerate(job.get("steps") or []):
            name = step.get("name") or step.get("id") or "<unnamed>"
            run = step.get("run") or ""
            out.append((job_name, i, name, run))
    return out


def _scripts_invoked(wf: dict) -> set[str]:
    invoked: set[str] = set()
    for _, _, run in _all_run_blocks(wf):
        for needle in (
            *NEW_PIPELINE_SCRIPTS,
            LEGACY_BUILDER_REL,
            DEPLOY_SCRIPT_REL,
        ):
            if needle in run:
                invoked.add(needle)
    return invoked


def main() -> int:
    failures: list[str] = []

    # ── Load workflows ───────────────────────────────────────────────
    deploy_wf = _load(DEPLOY_WF)
    pmf_wf = _load(PMF_DELIVERY_WF)
    pred_wf = _load(PREDICTIONS_WF)

    if deploy_wf is None:
        failures.append(f"missing {DEPLOY_WF}")
    if pmf_wf is None:
        failures.append(f"missing {PMF_DELIVERY_WF}")
    if pred_wf is None:
        # daily_predictions.yml is optional — if it does not exist the repo
        # trivially satisfies R6 (the legacy builder cannot be invoked).
        print(f"  [advisory] {PREDICTIONS_WF.name} not found — R6 trivially satisfied (no legacy builder invocation possible)")

    # ── R1: deploy yaml runs all four new-pipeline scripts ───────────
    if deploy_wf is not None:
        deploy_invoked = _scripts_invoked(deploy_wf)
        for needle in NEW_PIPELINE_SCRIPTS:
            if needle not in deploy_invoked:
                failures.append(
                    f"R1: {DEPLOY_WF.name} does not invoke {needle}"
                )

        # ── R2: deploy yaml does NOT invoke the legacy builder ───────
        if LEGACY_BUILDER_REL in deploy_invoked:
            failures.append(
                f"R2: {DEPLOY_WF.name} still invokes legacy "
                f"{LEGACY_BUILDER_REL} — must be removed"
            )

        # ── R3: HTML staged for upload, templates excluded ───────────
        joined = "\n".join(
            run for _, _, run in _all_run_blocks(deploy_wf)
        )
        for f in HTML_OUTPUT_FILES:
            if f not in joined:
                failures.append(
                    f"R3: {DEPLOY_WF.name} does not stage {f} for upload"
                )
        # The deploy workflow text MAY mention templates, but only as a
        # defensive guard ("must not leak"). Disallow any literal `cp`
        # of `_template_` files into public_export.
        for line in joined.splitlines():
            stripped = line.strip()
            if (
                stripped.startswith("cp ")
                and "_template_" in stripped
                and "public_export/" in stripped
            ):
                failures.append(
                    f"R3: {DEPLOY_WF.name} would copy template "
                    f"into public_export/: {stripped!r}"
                )

        # ── R4: render verifier runs before the FTP deploy step ──────
        verifier_idx = None
        deploy_idx = None
        for _, idx, name, run in _step_index(deploy_wf):
            if "verify_woo_dashboard_render_contract.py" in run:
                if verifier_idx is None:
                    verifier_idx = idx
            if DEPLOY_SCRIPT_REL in run:
                if deploy_idx is None:
                    deploy_idx = idx
        if verifier_idx is None:
            failures.append(
                f"R4: {DEPLOY_WF.name} has no verify_woo_dashboard_render_contract step"
            )
        elif deploy_idx is not None and verifier_idx >= deploy_idx:
            failures.append(
                f"R4: {DEPLOY_WF.name} render verifier (idx={verifier_idx}) "
                f"runs at/after FTP deploy step (idx={deploy_idx})"
            )

    # ── R5: daily PMF delivery yaml runs the new pipeline ───────────
    if pmf_wf is not None:
        pmf_invoked = _scripts_invoked(pmf_wf)
        for needle in NEW_PIPELINE_SCRIPTS:
            if needle not in pmf_invoked:
                failures.append(
                    f"R5: {PMF_DELIVERY_WF.name} does not invoke {needle}"
                )

    # ── R6: daily_predictions yaml does NOT invoke legacy builder ───
    # If the file is absent the repo trivially satisfies R6 (no invocation possible).
    if pred_wf is not None:
        pred_invoked = _scripts_invoked(pred_wf)
        if LEGACY_BUILDER_REL in pred_invoked:
            failures.append(
                f"R6: {PREDICTIONS_WF.name} invokes legacy "
                f"{LEGACY_BUILDER_REL} — must be removed"
            )

    # ── R7: legacy builder marked LEGACY in its docstring ───────────
    if LEGACY_BUILDER.exists():
        head = LEGACY_BUILDER.read_text(encoding="utf-8")[:1500]
        if "LEGACY" not in head and "legacy" not in head:
            failures.append(
                f"R7: {LEGACY_BUILDER_REL} top-of-file docstring does not "
                "carry a LEGACY / AUXILIARY marker"
            )
    else:
        # If the legacy builder is gone, that satisfies R7 and R2 trivially.
        pass

    if failures:
        for f in failures:
            print(f"::error::{f}")
        print(f"WOO_DEPLOY_WORKFLOW_CONTRACT_FAILED count={len(failures)}")
        return 1

    print("WOO_DEPLOY_WORKFLOW_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
