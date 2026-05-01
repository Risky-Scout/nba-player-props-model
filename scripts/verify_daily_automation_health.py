"""Phase 13B — daily automation health probe.

Confirms that every production delivery surface is intact, that the nightly
training surface is non-interfering, and that no secrets or raw data have
leaked into committed paths. Independent of whether real retraining is wired:
this is the operator's "is the system still healthy?" check.

Usage:
    python3 scripts/verify_daily_automation_health.py
    python3 scripts/verify_daily_automation_health.py --as-of-date YYYY-MM-DD

Outputs:
    artifacts/automation_health/latest_health_report.json
    artifacts/automation_health/latest_health_summary.md

Final line on success:
    DAILY_AUTOMATION_HEALTH_PASS

Hard rules echoed:
- Delivery jobs read only champion_pointer.json; they never reference
  challenger directories.
- No tracked production files are dirty in `git diff`.
- No secrets in public_export, deliveries, or model manifests.
- Training cron does not overlap any delivery cron.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit,
    looks_like_secret,
    read_json,
    utcnow_iso,
    write_json_atomic,
)

WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
DELIVERIES_DIR = REPO_ROOT / "deliveries"
PUBLIC_EXPORT_WOO_DIR = REPO_ROOT / "public_export" / "wizard_of_odds"
HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"

DELIVERY_SCRIPTS = (
    REPO_ROOT / "scripts" / "build_daily_pmf_delivery.py",
    REPO_ROOT / "scripts" / "build_derek_forward_feed.py",
    REPO_ROOT / "scripts" / "build_wizard_of_odds_public_export.py",
    REPO_ROOT / "scripts" / "run_daily_delivery_pipeline.py",
    REPO_ROOT / "scripts" / "predict.py",
    REPO_ROOT / "scripts" / "build_stat_grid_pmfs.py",
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class HealthReport:
    generated_at_utc: str
    code_commit: str
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(Check(name, passed, detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "overall_pass": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
        }


def _latest_delivery_date() -> str | None:
    if not DELIVERIES_DIR.exists():
        return None
    candidates = sorted(
        d.name for d in DELIVERIES_DIR.iterdir() if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name)
    )
    return candidates[-1] if candidates else None


def _read_workflow_text(name: str) -> str | None:
    p = WORKFLOWS_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else None


def _extract_cron_lines(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- cron:"):
            # remove leading '- cron:' and trim quotes
            v = s[len("- cron:"):].strip().strip("'\"")
            if v:
                out.append(v)
    return out


def _cron_minutes(cron: str) -> set[tuple[int, int]]:
    """Return the (hour, minute) UTC slots a 5-field cron expression fires.

    Only handles the field shapes used in this repo: literal numbers, comma
    lists, and "*". Days-of-month / month / dow are assumed daily.
    """
    parts = cron.split()
    if len(parts) < 2:
        return set()
    minute_part, hour_part = parts[0], parts[1]

    def expand(field: str, lo: int, hi: int) -> list[int]:
        if field == "*":
            return list(range(lo, hi + 1))
        out: list[int] = []
        for tok in field.split(","):
            if tok.isdigit():
                out.append(int(tok))
        return out

    minutes = expand(minute_part, 0, 59)
    hours = expand(hour_part, 0, 23)
    return {(h, m) for h in hours for m in minutes}


def check_woo_export(report: HealthReport, latest_date: str | None) -> None:
    latest_dir = PUBLIC_EXPORT_WOO_DIR / "latest"
    if not latest_dir.exists():
        report.add("woo_latest_export_present", False, str(latest_dir))
        return
    must_have = ("fair_odds_board.parquet", "full_pmfs_wide.parquet", "monetization_view.parquet", "run_manifest.json")
    missing = [m for m in must_have if not (latest_dir / m).exists()]
    report.add(
        "woo_latest_export_present",
        not missing,
        f"missing={missing}" if missing else "all required files present",
    )
    # Also: the date stamp inside the manifest should agree with the latest delivery date.
    manifest = latest_dir / "run_manifest.json"
    if manifest.exists():
        try:
            m = read_json(manifest)
            d = m.get("delivery_date") or m.get("date") or m.get("as_of_date")
            agree = (latest_date is None) or (d == latest_date)
            report.add(
                "woo_latest_manifest_date_matches_latest_delivery",
                bool(agree),
                f"manifest_date={d!r} latest_delivery_date={latest_date!r}",
            )
        except Exception as exc:
            report.add("woo_latest_manifest_date_matches_latest_delivery", False, str(exc))


def check_woo_export_verifier(report: HealthReport) -> None:
    """If a WoO public-export verifier script exists, treat its presence as a
    health signal. We do not run it here — the daily pipeline already does.
    """
    candidates = list(REPO_ROOT.glob("scripts/verify_wizard_of_odds*.py")) + list(
        REPO_ROOT.glob("scripts/wizard_of_odds_*verify*.py")
    )
    report.add(
        "woo_export_verifier_present",
        bool(candidates),
        f"candidates={[str(c.relative_to(REPO_ROOT)) for c in candidates]}",
    )


def check_workflows_present(report: HealthReport) -> None:
    expected = {
        "wizard_of_odds_ftp_deploy.yml": "WoO FTP deploy workflow",
        "daily_pmf_delivery.yml": "Daily delivery workflow",
        "nightly_training_calibration.yml": "Nightly training workflow",
    }
    for fname, desc in expected.items():
        report.add(
            f"workflow_present_{fname}",
            (WORKFLOWS_DIR / fname).exists(),
            desc,
        )


def check_derek_builder_present(report: HealthReport) -> None:
    p = REPO_ROOT / "scripts" / "build_derek_forward_feed.py"
    report.add("derek_forward_feed_builder_present", p.exists(), str(p.relative_to(REPO_ROOT)) if p.exists() else "missing")


def check_daily_workflow_references(report: HealthReport) -> None:
    text = _read_workflow_text("daily_pmf_delivery.yml") or ""
    report.add(
        "daily_workflow_references_derek",
        "derek_near_lineup" in text or "build_derek_forward_feed" in text,
        "daily_pmf_delivery.yml references Derek",
    )
    report.add(
        "daily_workflow_references_woo_modes",
        ("woo_morning_monetization" in text) and ("woo_afternoon_refresh" in text),
        "daily_pmf_delivery.yml references both WoO modes",
    )


def check_champion_pointer(report: HealthReport) -> None:
    if not CHAMPION_POINTER_PATH.exists():
        report.add("champion_pointer_present", False, str(CHAMPION_POINTER_PATH))
        return
    pointer = read_json(CHAMPION_POINTER_PATH)
    needed = {"model_version", "calibrator_version", "model_dir", "schema_version"}
    missing = needed - set(pointer.keys())
    report.add(
        "champion_pointer_present",
        not missing,
        f"missing_fields={missing}" if missing else "well-formed",
    )


def check_training_cron_does_not_overlap_delivery(report: HealthReport) -> None:
    nightly = _read_workflow_text("nightly_training_calibration.yml")
    delivery = _read_workflow_text("daily_pmf_delivery.yml")
    if not nightly or not delivery:
        report.add(
            "training_cron_no_overlap_with_delivery",
            False,
            "missing nightly_training_calibration.yml or daily_pmf_delivery.yml",
        )
        return
    n_slots: set[tuple[int, int]] = set()
    for cron in _extract_cron_lines(nightly):
        n_slots |= _cron_minutes(cron)
    d_slots: set[tuple[int, int]] = set()
    for cron in _extract_cron_lines(delivery):
        d_slots |= _cron_minutes(cron)
    overlap = n_slots & d_slots
    # Also: nightly's training window (09:30 → 14:30 UTC promotion cutoff) must
    # not overlap the 15:00 UTC WoO publish — confirm 14:30 cutoff is enforced
    # in code by checking the constant in the helper module.
    helper = REPO_ROOT / "src" / "nba_props_model" / "training_automation.py"
    helper_text = helper.read_text(encoding="utf-8") if helper.exists() else ""
    cutoff_present = (
        "PROMOTION_CUTOFF_HOUR = 14" in helper_text
        and "PROMOTION_CUTOFF_MINUTE = 30" in helper_text
    )
    report.add(
        "training_cron_no_overlap_with_delivery",
        (not overlap) and cutoff_present,
        f"overlap_slots={sorted(overlap)} cutoff_constants_present={cutoff_present}",
    )


def check_no_dirty_production_files(report: HealthReport) -> None:
    """Ensure no tracked production paths are uncommitted (working-tree dirty)."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        dirty = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except Exception as exc:
        report.add("no_dirty_production_files", False, f"git error: {exc}")
        return
    prod_prefixes = (
        "scripts/predict.py",
        "scripts/build_daily_pmf_delivery.py",
        "scripts/build_derek_forward_feed.py",
        "scripts/build_wizard_of_odds_public_export.py",
        "scripts/run_daily_delivery_pipeline.py",
        "scripts/build_stat_grid_pmfs.py",
        ".github/workflows/daily_pmf_delivery.yml",
        ".github/workflows/wizard_of_odds_ftp_deploy.yml",
        "src/nba_props_model/pipelines/predict.py",
        "src/nba_props_model/pipelines/train.py",
        "src/nba_props_model/calibration/pmf_calibration.py",
        "artifacts/models/registry/champion_pointer.json",
    )
    bad = [f for f in dirty if any(f == p or f.startswith(p) for p in prod_prefixes)]
    report.add(
        "no_dirty_production_files",
        not bad,
        f"dirty={bad[:10]}" if bad else "clean",
    )


_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|bearer|token|password)\s*[=:]\s*['\"]?([A-Za-z0-9_\-+/=]{20,})['\"]?",
    re.IGNORECASE,
)


def _scan_text_for_secrets(text: str) -> list[str]:
    hits: list[str] = []
    for m in _SECRET_KEY_RE.finditer(text):
        # Skip obvious env-var references / GitHub Actions context tokens.
        full = m.group(0)
        if "${{" in full or "secrets." in full or "$BDL_API_KEY" in full or "$ODDS_API_KEY" in full:
            continue
        hits.append(full[:80])
        if len(hits) >= 5:
            break
    return hits


def check_no_secrets_in_outputs(report: HealthReport) -> None:
    """Walk every JSON / MD / CSV in public_export, deliveries, and model
    manifests and look for plausible API-key shapes. We do not slurp parquet
    bytes (too large + structured)."""
    scan_dirs: list[Path] = []
    if PUBLIC_EXPORT_WOO_DIR.exists():
        scan_dirs.append(PUBLIC_EXPORT_WOO_DIR)
    if DELIVERIES_DIR.exists():
        scan_dirs.append(DELIVERIES_DIR)
    scan_dirs.append(REPO_ROOT / "artifacts" / "models" / "registry")
    scan_dirs.append(REPO_ROOT / "artifacts" / "models" / "challengers")
    scan_dirs.append(REPO_ROOT / "artifacts" / "nightly_training")

    text_exts = {".json", ".md", ".csv", ".jsonl", ".yml", ".yaml", ".html"}
    hits: list[str] = []
    files_scanned = 0
    file_cap = 2000  # safety: don't scan more than this many files in one health probe
    for d in scan_dirs:
        if not d.exists():
            continue
        for path in d.rglob("*"):
            if files_scanned >= file_cap:
                break
            if not path.is_file():
                continue
            if path.suffix.lower() not in text_exts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files_scanned += 1
            local = _scan_text_for_secrets(text)
            for h in local:
                # Final guard: only count if the value chunk also passes the
                # heuristic from training_automation.looks_like_secret. That
                # eliminates ID-shaped strings like player_ids that match the
                # length floor.
                if looks_like_secret(h):
                    hits.append(f"{path.relative_to(REPO_ROOT)}: {h}")
            if len(hits) >= 5:
                break
        if len(hits) >= 5:
            break
    report.add(
        "no_secrets_in_outputs",
        not hits,
        f"files_scanned={files_scanned} hits={hits[:5]}",
    )


def check_latest_derek_and_woo_for_latest_date(report: HealthReport, latest_date: str | None) -> None:
    if not latest_date:
        report.add("latest_derek_for_latest_date", False, "no delivery dirs found")
        report.add("latest_woo_for_latest_date", False, "no delivery dirs found")
        return
    derek_dir = DELIVERIES_DIR / latest_date / "derek_forward_feed"
    woo_dir = DELIVERIES_DIR / latest_date / "wizard_of_odds"
    report.add(
        "latest_derek_for_latest_date",
        derek_dir.exists() and any(derek_dir.iterdir()),
        f"{derek_dir.relative_to(REPO_ROOT)} exists={derek_dir.exists()}",
    )
    report.add(
        "latest_woo_for_latest_date",
        woo_dir.exists() and any(woo_dir.iterdir()),
        f"{woo_dir.relative_to(REPO_ROOT)} exists={woo_dir.exists()}",
    )


def check_delivery_does_not_reference_challengers(report: HealthReport) -> None:
    bad: list[str] = []
    for s in DELIVERY_SCRIPTS:
        if not s.exists():
            continue
        if "artifacts/models/challengers" in s.read_text(encoding="utf-8"):
            bad.append(str(s.relative_to(REPO_ROOT)))
    report.add(
        "delivery_does_not_reference_challengers",
        not bad,
        f"violations={bad}" if bad else "ok",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Daily automation health probe.")
    p.add_argument("--as-of-date", help="Override latest date for date-specific checks")
    args = p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    latest_date = args.as_of_date or _latest_delivery_date()

    report = HealthReport(generated_at_utc=utcnow_iso(), code_commit=git_commit())

    check_woo_export(report, latest_date)
    check_woo_export_verifier(report)
    check_workflows_present(report)
    check_derek_builder_present(report)
    check_daily_workflow_references(report)
    check_champion_pointer(report)
    check_training_cron_does_not_overlap_delivery(report)
    check_no_dirty_production_files(report)
    check_no_secrets_in_outputs(report)
    check_latest_derek_and_woo_for_latest_date(report, latest_date)
    check_delivery_does_not_reference_challengers(report)

    write_json_atomic(HEALTH_DIR / "latest_health_report.json", report.to_dict())

    md = [
        "# Daily Automation Health Probe",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- code_commit: {report.code_commit[:12]}",
        f"- latest_delivery_date_seen: {latest_date}",
        f"- overall_pass: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe_detail = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe_detail} |")
    (HEALTH_DIR / "latest_health_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if report.passed:
        print("DAILY_AUTOMATION_HEALTH_PASS")
        return 0
    print("HEALTH CHECK FAILED")
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
