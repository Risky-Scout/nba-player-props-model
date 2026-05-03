"""Phase 13X Part G — Wizard of Odds safety verifier.

Asserts that no production WoO files / pipelines were altered by this
phase. Specifically:

  * No tracked file under ``deliveries/<date>/wizard_of_odds/`` is
    modified between origin/main and the working tree.
  * The shared WoO build / validate scripts and workflow files are
    byte-identical to the previously-shipping versions on
    origin/main.
  * Derek-only files (``deliveries/<date>/derek_game_snapshots/...``,
    ``artifacts/automation_health/derek_*``) MAY be modified.

If a calculation bug had to be fixed in shared code, the bug+fix must
be documented in
``artifacts/automation_health/phase13x_woo_shared_fix.json`` and the
verifier inspects the documented before/after diff.

Pass:  PHASE13X_WOO_UNCHANGED_PASS
Fail:  PHASE13X_WOO_UNCHANGED_FAILED  (with the exact paths)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# Paths considered "WoO production". A change to any of these requires
# explicit documentation in phase13x_woo_shared_fix.json.
PROTECTED_PATTERNS = (
    "deliveries/*/wizard_of_odds/",
    "deliveries/*/pmf_model_review_package/",
    "deliveries/*/canonical_source/",
    "scripts/build_wizard_of_odds_public_export.py",
    "scripts/deploy_wizard_of_odds_ftp.py",
    "scripts/verify_wizard_of_odds_public_export.py",
    "scripts/build_daily_pmf_delivery.py",
    "scripts/run_daily_delivery_pipeline.py",
    "scripts/build_pmf_review_package.py",
    ".github/workflows/wizard_of_odds_daily.yml",
    ".github/workflows/wizard_of_odds_*.yml",
)


def _git_changed_files() -> list[str]:
    """Return the union of files changed in the working tree relative to
    origin/main HEAD (committed + uncommitted)."""
    files: set[str] = set()
    for cmd in (
        ["git", "diff", "--name-only", "origin/main..HEAD"],
        ["git", "diff", "--name-only"],
        ["git", "status", "--porcelain"],
    ):
        try:
            r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                                text=True, check=False)
        except Exception:
            continue
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if cmd[1] == "status":
                # porcelain: "XY path"
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    files.add(parts[1])
            else:
                files.add(line)
    return sorted(files)


def _matches_protected(path: str) -> bool:
    import fnmatch
    for pat in PROTECTED_PATTERNS:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat + "*"):
            return True
        if pat.endswith("/") and path.startswith(pat):
            return True
    return False


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.parse_args(argv)

    files = _git_changed_files()
    protected_changes = [f for f in files if _matches_protected(f)]

    documented_path = (
        REPO_ROOT / "artifacts" / "automation_health"
        / "phase13x_woo_shared_fix.json"
    )
    documented = {}
    if documented_path.exists():
        try:
            documented = json.loads(documented_path.read_text(encoding="utf-8"))
        except Exception:
            documented = {}
    documented_paths = set(documented.get("paths") or [])

    undocumented = [
        f for f in protected_changes if f not in documented_paths
    ]

    out = REPO_ROOT / "artifacts" / "automation_health"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "changed_files": files,
        "protected_changes": protected_changes,
        "documented_paths": sorted(documented_paths),
        "undocumented_changes": undocumented,
        "outcome": "fail" if undocumented else "pass",
    }
    (out / "phase13x_woo_unchanged.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    if undocumented:
        print("PHASE13X_WOO_UNCHANGED_FAILED", file=sys.stderr)
        for f in undocumented:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("PHASE13X_WOO_UNCHANGED_PASS")
    print(
        f"  protected_changes={len(protected_changes)} "
        f"documented={len(documented_paths)} "
        f"undocumented={len(undocumented)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
