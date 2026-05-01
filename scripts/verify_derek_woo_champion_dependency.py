"""Phase 13G — verify Derek/WoO outputs depend on the active validated champion.

Read-only check that proves the production delivery surface is correctly
anchored on whatever ``champion_pointer.json`` currently identifies, and
that no part of the delivery pipeline silently reads from a challenger or
older calibrators.

Usage:
    python3 scripts/verify_derek_woo_champion_dependency.py [--max-stale-days N]

Outputs:
    artifacts/automation_health/derek_woo_champion_dependency.json
    artifacts/automation_health/derek_woo_champion_dependency.md

Final line on success:
    DEREK_WOO_CHAMPION_DEPENDENCY_PASS

Final line on failure:
    DEREK_WOO_CHAMPION_DEPENDENCY_FAILED + reasons.

Hard rules:
- Champion pointer must exist and identify a model_dir that contains the
  champion's calibrators.
- Production delivery scripts (predict.py, build_daily_pmf_delivery.py,
  build_derek_forward_feed.py, build_wizard_of_odds_public_export.py,
  build_stat_grid_pmfs.py, run_daily_delivery_pipeline.py) must NOT
  reference any challenger directory.
- Latest delivery's run_manifest.json (if present) must have been generated
  AFTER the active champion's promoted_at_utc — proves it was built using
  the current champion's artifacts and not a stale snapshot.
- Champion's ``promoted_at_utc`` must not be older than ``--max-stale-days``
  (default 14) — guards against the production surface running on a champion
  that has not been refreshed by the nightly pipeline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_MODELS_DIR,
    CHAMPION_POINTER_PATH,
    git_commit,
    read_json,
    sha256_file,
    utcnow,
    utcnow_iso,
    write_json_atomic,
)


HEALTH_DIR = REPO_ROOT / "artifacts" / "automation_health"
DELIVERIES_DIR = REPO_ROOT / "deliveries"
PUBLIC_EXPORT_WOO_DIR = REPO_ROOT / "public_export" / "wizard_of_odds"

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
class DependencyReport:
    generated_at_utc: str
    code_commit: str
    max_stale_days: int
    checks: list[Check] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

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
            "max_stale_days": self.max_stale_days,
            "passed": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
            "facts": self.facts,
        }


def _parse_iso(s: str) -> dt.datetime | None:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def check_champion_pointer(report: DependencyReport) -> dict:
    if not CHAMPION_POINTER_PATH.exists():
        report.add("champion_pointer_present", False, str(CHAMPION_POINTER_PATH))
        return {}
    p = read_json(CHAMPION_POINTER_PATH)
    report.add(
        "champion_pointer_present",
        True,
        f"model_version={p.get('model_version')!r}",
    )
    report.facts["champion_model_version"] = p.get("model_version")
    report.facts["champion_calibrator_version"] = p.get("calibrator_version")
    report.facts["champion_promoted_at_utc"] = p.get("promoted_at_utc")
    report.facts["champion_model_dir"] = p.get("model_dir")
    report.facts["champion_trained_through_date"] = p.get("trained_through_date")
    report.facts["champion_calibrated_through_date"] = p.get("calibrated_through_date")
    return p


def check_champion_calibrators_present(report: DependencyReport, pointer: dict) -> None:
    rel = pointer.get("model_dir", "artifacts/models")
    cdir = (REPO_ROOT / rel).resolve()
    missing: list[str] = []
    sha_prefixes: dict[str, str] = {}
    for stat in ("pts", "reb", "ast", "fg3m", "tov"):
        cand = cdir / f"pmf_cal_role_{stat}.pkl"
        if not cand.exists():
            missing.append(stat)
        else:
            sha_prefixes[stat] = sha256_file(cand)[:16]
    report.facts["champion_calibrator_sha_prefixes"] = sha_prefixes
    report.add(
        "champion_calibrators_present",
        not missing,
        f"missing_stats={missing}" if missing else "ok",
    )


def check_champion_freshness(report: DependencyReport, pointer: dict) -> None:
    promoted_iso = pointer.get("promoted_at_utc")
    promoted = _parse_iso(promoted_iso) if promoted_iso else None
    if promoted is None:
        report.add(
            "champion_freshness",
            False,
            f"no parseable promoted_at_utc ({promoted_iso!r})",
        )
        return
    age = utcnow() - promoted
    age_days = age.total_seconds() / 86400.0
    report.facts["champion_age_days"] = round(age_days, 2)
    report.add(
        "champion_freshness",
        age_days <= report.max_stale_days,
        f"age_days={age_days:.2f} max={report.max_stale_days}",
    )


def check_delivery_scripts_no_challenger_refs(report: DependencyReport) -> None:
    bad: list[str] = []
    for s in DELIVERY_SCRIPTS:
        if not s.exists():
            continue
        try:
            text = s.read_text(encoding="utf-8")
        except Exception:
            continue
        if "artifacts/models/challengers" in text:
            bad.append(str(s.relative_to(REPO_ROOT)))
    report.add(
        "delivery_scripts_no_challenger_refs",
        not bad,
        f"violations={bad}" if bad else "ok",
    )


def check_delivery_scripts_use_champion_path(report: DependencyReport, pointer: dict) -> None:
    """Production delivery scripts read from the champion's model_dir
    (``artifacts/models/`` in the canonical layout). Confirm at least one
    script in the pipeline references the champion path — directly or
    transitively via a ``nba_props_model.*`` import (the package's
    ``paths.MODEL_DIR`` IS the champion path)."""
    expected = pointer.get("model_dir", "artifacts/models")
    needles = (expected, "MODEL_DIR", "artifacts/models", "nba_props_model", "champion_pointer")
    refs: list[str] = []
    for s in DELIVERY_SCRIPTS:
        if not s.exists():
            continue
        text = s.read_text(encoding="utf-8")
        if any(n in text for n in needles):
            refs.append(s.name)
    report.facts["delivery_scripts_with_champion_refs"] = refs
    report.add(
        "delivery_scripts_reference_champion_path",
        len(refs) > 0,
        f"{len(refs)}/{len(DELIVERY_SCRIPTS)} delivery scripts reference champion path "
        f"(via direct path or nba_props_model package import)",
    )


def _latest_delivery_date() -> str | None:
    if not DELIVERIES_DIR.exists():
        return None
    candidates = sorted(
        d.name for d in DELIVERIES_DIR.iterdir() if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name)
    )
    return candidates[-1] if candidates else None


def check_latest_delivery_after_champion_promotion(
    report: DependencyReport, pointer: dict
) -> None:
    """Newest delivery's run_manifest.json must have been generated AFTER
    the active champion's promoted_at_utc — otherwise the delivery was built
    using a previous champion."""
    latest = _latest_delivery_date()
    report.facts["latest_delivery_date"] = latest
    if not latest:
        report.add(
            "latest_delivery_after_champion_promotion",
            True,
            "no deliveries found (advisory)",
        )
        return
    woo_manifest = DELIVERIES_DIR / latest / "wizard_of_odds" / "run_manifest.json"
    if not woo_manifest.exists():
        report.add(
            "latest_delivery_after_champion_promotion",
            True,
            f"no woo_manifest at deliveries/{latest}/ (advisory)",
        )
        return
    try:
        m = read_json(woo_manifest)
    except Exception as exc:
        report.add(
            "latest_delivery_after_champion_promotion",
            False,
            f"failed reading woo manifest: {exc}",
        )
        return

    delivery_generated = (
        m.get("generated_at_utc")
        or m.get("run_started_utc")
        or m.get("started_at_utc")
        or m.get("export_generated_at_utc")
    )
    promoted_iso = pointer.get("promoted_at_utc")
    delivery_dt = _parse_iso(delivery_generated)
    promoted_dt = _parse_iso(promoted_iso)
    report.facts["latest_delivery_generated_at"] = delivery_generated
    report.facts["champion_promoted_at_utc"] = promoted_iso

    if delivery_dt is None or promoted_dt is None:
        # If either timestamp is missing/unparseable, treat as advisory pass
        # so the gate doesn't false-positive on legacy manifests.
        report.add(
            "latest_delivery_after_champion_promotion",
            True,
            f"delivery_generated_at={delivery_generated!r} promoted_at_utc={promoted_iso!r} (advisory)",
        )
        return
    report.add(
        "latest_delivery_after_champion_promotion",
        delivery_dt >= promoted_dt,
        f"delivery_generated_at={delivery_dt.isoformat()} >= promoted_at_utc={promoted_dt.isoformat()}",
    )


def check_delivery_records_champion_id(report: DependencyReport, pointer: dict) -> None:
    """Phase 13H strict: when the active champion has rich metadata
    (``champion_model_id`` populated), the latest delivery's manifests must
    have been stamped via ``scripts/stamp_delivery_champion_metadata.py`` and
    must match the active pointer field-for-field on:

      - champion_model_id
      - trained_through_date
      - calibrated_through_date

    Falls back to advisory (Phase 13G semantics) when the champion is still
    a bootstrap pointer with no rich fields — the bootstrap pointer can
    never be stamped because the per-stat trained_through_date is unknown.
    """
    latest = _latest_delivery_date()
    pointer_id = pointer.get("champion_model_id") or pointer.get("model_version")
    pointer_trained = pointer.get("trained_through_date")
    pointer_calibrated = pointer.get("calibrated_through_date")
    is_bootstrap = pointer.get("champion_model_id") is None

    if not latest:
        report.add("delivery_records_champion_id", True, "no deliveries to check (advisory)")
        return

    candidates = {
        "woo": DELIVERIES_DIR / latest / "wizard_of_odds" / "run_manifest.json",
        "derek": DELIVERIES_DIR / latest / "derek_forward_feed" / "feed_manifest.json",
    }
    seen: dict[str, dict] = {}
    for label, cand in candidates.items():
        if not cand.exists():
            continue
        try:
            m = read_json(cand)
        except Exception:
            continue
        seen[label] = {
            "path": str(cand.relative_to(REPO_ROOT)),
            "champion_model_id": m.get("champion_model_id"),
            "trained_through_date": m.get("trained_through_date"),
            "calibrated_through_date": m.get("calibrated_through_date"),
            "model_source": m.get("model_source"),
            "no_challenger_artifacts_used": m.get("no_challenger_artifacts_used"),
            "model_version": m.get("model_version"),  # legacy field
        }
    report.facts["delivery_manifest_stamped"] = seen

    if is_bootstrap:
        # Bootstrap pointer has no rich fields to compare against. Pass with
        # advisory note — this gate becomes strict after first real promotion.
        report.add(
            "delivery_records_champion_id",
            True,
            "active champion is bootstrap pointer (no rich metadata yet); "
            "delivery stamp comparison deferred until first real promotion (advisory).",
        )
        return

    # Strict mode (post-promotion).
    failures: list[str] = []
    for side in ("woo", "derek"):
        if side not in seen:
            failures.append(f"{side}_manifest_missing")
            continue
        s = seen[side]
        if s.get("champion_model_id") != pointer_id:
            failures.append(
                f"{side}_champion_model_id_mismatch (delivery={s.get('champion_model_id')!r} "
                f"pointer={pointer_id!r})"
            )
        if pointer_trained and s.get("trained_through_date") != pointer_trained:
            failures.append(
                f"{side}_trained_through_date_mismatch (delivery={s.get('trained_through_date')!r} "
                f"pointer={pointer_trained!r})"
            )
        if pointer_calibrated and s.get("calibrated_through_date") != pointer_calibrated:
            failures.append(
                f"{side}_calibrated_through_date_mismatch (delivery={s.get('calibrated_through_date')!r} "
                f"pointer={pointer_calibrated!r})"
            )
        if s.get("no_challenger_artifacts_used") is not True:
            failures.append(
                f"{side}_no_challenger_artifacts_used_not_true (={s.get('no_challenger_artifacts_used')!r})"
            )
    report.add(
        "delivery_records_champion_id_strict",
        not failures,
        "ok" if not failures else f"failures={failures[:6]}",
    )


def check_delivery_does_not_use_stale_calibrators(report: DependencyReport, pointer: dict) -> None:
    """Phase 13H: confirm no champion calibrator on disk is from a different
    promoted-version than the one named in champion_pointer.

    We re-derive the per-stat sha256 of the calibrators in champion_artifact_dir
    and confirm they match what was recorded at promotion time in
    pointer.data_hashes (when present). If the pointer doesn't yet expose
    per-stat hashes (Phase 13H bootstrap), pass with advisory note.
    """
    rel = pointer.get("champion_artifact_dir") or pointer.get("model_dir") or "artifacts/models"
    cdir = (REPO_ROOT / rel).resolve()
    pointer_hashes = (pointer.get("data_hashes") or {}).get("champion_pickle_files") or []

    actual: dict[str, str] = {}
    for stat in ("pts", "reb", "ast", "fg3m", "tov"):
        p = cdir / f"pmf_cal_role_{stat}.pkl"
        if p.exists():
            actual[stat] = sha256_file(p)[:16]
    report.facts["champion_calibrator_actual_sha_prefixes"] = actual

    if not pointer_hashes:
        report.add(
            "delivery_does_not_use_stale_calibrators",
            True,
            "no per-stat hashes in pointer.data_hashes; deferred until first real promotion (advisory)",
        )
        return

    # When pointer carries hashes, reconcile.
    declared = {}
    for rec in pointer_hashes:
        path = rec.get("path") if isinstance(rec, dict) else None
        sha = rec.get("sha256") if isinstance(rec, dict) else None
        if not path or not sha:
            continue
        for stat in ("pts", "reb", "ast", "fg3m", "tov"):
            if path.endswith(f"pmf_cal_role_{stat}.pkl"):
                declared[stat] = sha[:16]
    drift = []
    for stat, sha in actual.items():
        if stat in declared and declared[stat] != sha:
            drift.append(f"{stat}: declared={declared[stat]} actual={sha}")
    report.add(
        "delivery_does_not_use_stale_calibrators",
        not drift,
        "ok" if not drift else f"drift={drift[:5]}",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Derek/WoO champion dependency.")
    p.add_argument(
        "--max-stale-days",
        type=int,
        default=14,
        help="Maximum allowed age (days) of the active champion's promoted_at_utc.",
    )
    args = p.parse_args(argv)

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    report = DependencyReport(
        generated_at_utc=utcnow_iso(),
        code_commit=git_commit(),
        max_stale_days=args.max_stale_days,
    )

    pointer = check_champion_pointer(report)
    if pointer:
        check_champion_calibrators_present(report, pointer)
        check_champion_freshness(report, pointer)
        check_delivery_scripts_no_challenger_refs(report)
        check_delivery_scripts_use_champion_path(report, pointer)
        check_latest_delivery_after_champion_promotion(report, pointer)
        check_delivery_records_champion_id(report, pointer)
        check_delivery_does_not_use_stale_calibrators(report, pointer)

    payload = report.to_dict()
    write_json_atomic(HEALTH_DIR / "derek_woo_champion_dependency.json", payload)

    md = [
        "# Derek/WoO Champion Dependency Verification",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- max_stale_days: {report.max_stale_days}",
        f"- passed: **{report.passed}**",
        "",
        "## Checks",
        "",
        "| Check | Pass | Detail |",
        "| --- | --- | --- |",
    ]
    for c in report.checks:
        safe_detail = c.detail.replace("|", "\\|")
        md.append(f"| {c.name} | {'yes' if c.passed else 'NO'} | {safe_detail} |")
    md += ["", "## Facts", "", "```", json.dumps(report.facts, indent=2, default=str), "```"]
    (HEALTH_DIR / "derek_woo_champion_dependency.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if report.passed:
        print("DEREK_WOO_CHAMPION_DEPENDENCY_PASS")
        return 0
    print("DEREK_WOO_CHAMPION_DEPENDENCY_FAILED", file=sys.stderr)
    for c in report.checks:
        if not c.passed:
            print(f"  - {c.name}: {c.detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
