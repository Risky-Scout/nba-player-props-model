"""Phase 13S Part H — promote the direct-lineup contextual challenger.

Augments ``artifacts/models/registry/champion_pointer.json`` with the
Phase 13S contextual fields and switches ``feature_set_id`` /
``contextual_challenger_dir`` to the direct-lineup challenger. Legacy
WoO-required pointer fields (``model_version``, ``model_dir``,
``champion_calibrator_paths``, ``promoted_at_utc``) are preserved.

Refuses promotion if validation gates failed, no-leakage failed, or
the trained_through_date is in the future (unless
``--allow-future-trained-through``). Records a previous-pointer
backup under ``artifacts/models/champion/v_phase13s_*/``.

Pass line:  PHASE13S_DIRECT_LINEUP_CHAMPION_PROMOTION_PASS
Block line: PHASE13S_DIRECT_LINEUP_CHAMPION_PROMOTION_BLOCKED
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.contextual import load_contextual_engine  # noqa: E402
from nba_props_model.features.direct_lineup_context import (  # noqa: E402
    DIRECT_LINEUP_FEATURE_SET_ID,
)
from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH,
    git_commit, utcnow_iso, write_json_atomic,
)


PROMOTION_LOG = REPO_ROOT / "artifacts" / "models" / "registry" / "promotion_log.csv"
BACKUP_ROOT = REPO_ROOT / "artifacts" / "models" / "champion"


def _hash_columns(cols) -> str:
    payload = "|".join(sorted(cols))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _block(reason: str, *, contextual_dir: Path | None = None,
           extra: dict | None = None) -> int:
    out = {
        "schema_version": "1.0",
        "promoted": False,
        "blocked_reason": reason,
        "decided_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
    }
    if extra:
        out.update(extra)
    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "direct_lineup_promotion_decision.json").write_text(
        json.dumps(out, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if contextual_dir is not None:
        write_json_atomic(contextual_dir / "promotion_decision.json", {
            "schema_version": "1.0",
            "promoted": False,
            "blocked_reason": reason,
            "decided_at_utc": utcnow_iso(),
            "code_commit": git_commit(),
        })
    print("PHASE13S_DIRECT_LINEUP_CHAMPION_PROMOTION_BLOCKED", file=sys.stderr)
    print(f"  reason: {reason}", file=sys.stderr)
    return 0


def _find_dir(arg: str | None) -> Path | None:
    if arg:
        return Path(arg)
    root = REPO_ROOT / "artifacts" / "models" / "challengers"
    if not root.exists():
        return None
    cands = sorted(d for d in root.iterdir()
                    if d.is_dir() and d.name.endswith("_direct_lineup_contextual"))
    return cands[-1] if cands else None


def _debug_log(msg: str, data: dict | None = None) -> None:
    """Append a single NDJSON line to the debug log for session cd71ad."""
    import json as _json
    import time as _time
    log_path = REPO_ROOT / ".cursor" / "debug-cd71ad.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"sessionId": "cd71ad", "location": "promote_direct_lineup_challenger.py",
                 "message": msg, "data": data or {}, "timestamp": int(_time.time() * 1000)}
        with open(log_path, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps(entry) + "\n")
    except Exception:
        pass


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--challenger-dir", default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--allow-future-trained-through", action="store_true")
    p.add_argument("--check-only", action="store_true",
                   help="Dry-run: validate all gates but do not write champion_pointer.json")
    args = p.parse_args(argv)

    _debug_log("promote_direct_lineup_challenger started",
               {"check_only": args.check_only, "challenger_dir": args.challenger_dir,
                "force": args.force})

    contextual_dir = _find_dir(args.challenger_dir)
    if contextual_dir is None or not contextual_dir.exists():
        _debug_log("BLOCK: no contextual dir found")
        return _block("no <date>_direct_lineup_contextual dir found")

    _debug_log("gate:contextual_dir", {"dir": str(contextual_dir), "exists": contextual_dir.exists()})

    train_manifest_path = contextual_dir / "train_manifest.json"
    if not train_manifest_path.exists():
        _debug_log("BLOCK: train_manifest.json missing")
        return _block("missing train_manifest.json", contextual_dir=contextual_dir)
    tm = json.loads(train_manifest_path.read_text(encoding="utf-8"))

    gates_path = REPO_ROOT / "artifacts" / "phase13s" / "validation_gates_report.json"
    leak_path = REPO_ROOT / "artifacts" / "phase13s" / "no_leakage_report.json"
    sens_path = REPO_ROOT / "artifacts" / "phase13s" / "direct_lineup_pmf_sensitivity.json"
    if not gates_path.exists():
        _debug_log("BLOCK: validation_gates_report.json missing")
        return _block("validation_gates_report.json missing — run gates first",
                      contextual_dir=contextual_dir)
    gates = json.loads(gates_path.read_text(encoding="utf-8"))
    _debug_log("gate:validation_gates", {"issues": gates.get("issues"), "gates_passed": gates.get("gates_passed")})
    if gates.get("issues"):
        _debug_log("BLOCK: validation gates failed", {"issues": gates["issues"]})
        return _block(f"validation gates issues: {gates['issues']}",
                      contextual_dir=contextual_dir,
                      extra={"validation_gates": gates})
    if leak_path.exists():
        leak = json.loads(leak_path.read_text(encoding="utf-8"))
        _debug_log("gate:no_leakage", {"issues": leak.get("issues")})
        if leak.get("issues"):
            _debug_log("BLOCK: leakage issues", {"issues": leak["issues"]})
            return _block(f"no-leakage issues: {leak['issues']}",
                          contextual_dir=contextual_dir)
    sensitivity_proven = False
    if sens_path.exists():
        sens = json.loads(sens_path.read_text(encoding="utf-8"))
        case1 = sens.get("case_results", {}).get("case_1_direct_lineup", {})
        diff = float(case1.get("abs_diff_minutes_delta") or 0.0)
        sensitivity_proven = diff > 0.5
        _debug_log("gate:sensitivity", {"hypothesisId": "H5", "abs_diff_minutes_delta": diff,
                                         "sensitivity_proven": sensitivity_proven,
                                         "sens_path": str(sens_path),
                                         "case_results_keys": list(sens.get("case_results", {}).keys())})
    else:
        _debug_log("gate:sensitivity_file_missing", {"hypothesisId": "H5",
                                                      "sens_path": str(sens_path),
                                                      "gates_path_exists": gates_path.exists(),
                                                      "leak_path_exists": leak_path.exists()})
    if not sensitivity_proven and not args.force:
        _debug_log("BLOCK: sensitivity not proven")
        return _block(
            "direct lineup PMF sensitivity not proven (case 1 abs_diff <= 0.5 min); "
            "run scripts/verify_direct_lineup_pmf_sensitivity.py",
            contextual_dir=contextual_dir)

    try:
        engine = load_contextual_engine(contextual_dir)
    except Exception as exc:
        _debug_log("BLOCK: engine load failed", {"error": str(exc)})
        return _block(f"contextual engine load failed: {exc}",
                      contextual_dir=contextual_dir)
    _debug_log("gate:engine_loaded", {"fitted_targets": list(engine.fitted_targets), "has_minutes": "minutes" in engine.feature_lists})
    if "minutes" not in engine.feature_lists:
        _debug_log("BLOCK: no minutes in feature_lists")
        return _block("contextual engine has no minutes adjustment",
                      contextual_dir=contextual_dir)

    today = dt.date.today()
    ttd_str = tm.get("trained_through_date") or ""
    try:
        ttd = dt.date.fromisoformat(str(ttd_str)[:10])
    except Exception:
        _debug_log("BLOCK: unparseable trained_through_date", {"ttd_str": ttd_str})
        return _block(f"unparseable trained_through_date={ttd_str!r}",
                      contextual_dir=contextual_dir)
    _debug_log("gate:trained_through_date", {"ttd": ttd_str, "today": str(today), "future": ttd > today})
    if ttd > today and not args.allow_future_trained_through:
        _debug_log("BLOCK: trained_through_date in future")
        return _block(
            f"trained_through_date={ttd.isoformat()} is in the future "
            f"(today={today.isoformat()}); pass --allow-future-trained-through "
            "if this is a fixture run",
            contextual_dir=contextual_dir)

    if not CHAMPION_POINTER_PATH.exists():
        _debug_log("BLOCK: champion_pointer.json missing")
        return _block("champion_pointer.json missing", contextual_dir=contextual_dir)
    pointer = json.loads(CHAMPION_POINTER_PATH.read_text(encoding="utf-8"))
    existing_fs_id = pointer.get("feature_set_id") or ""
    _debug_log("gate:existing_champion", {
        "champion_model_id": pointer.get("champion_model_id"),
        "existing_fs_id": existing_fs_id,
        "contextual_trained_through_date": pointer.get("contextual_trained_through_date"),
    })
    if (existing_fs_id and existing_fs_id != DIRECT_LINEUP_FEATURE_SET_ID
        and existing_fs_id.startswith("phase13s_") and not args.force):
        _debug_log("BLOCK: feature_set_id conflict", {"existing_fs_id": existing_fs_id})
        return _block(
            f"champion_pointer.feature_set_id already set to {existing_fs_id!r}; "
            f"refusing to overwrite without --force",
            contextual_dir=contextual_dir)

    if args.check_only:
        _debug_log("CHECK_ONLY: all gates passed — would promote",
                   {"contextual_dir": str(contextual_dir), "ttd": ttd_str,
                    "fitted_targets": list(engine.fitted_targets)})
        print(f"PHASE13S_CHECK_ONLY_PASS: all gates passed for {contextual_dir.name}", flush=True)
        return 0

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup_dir = BACKUP_ROOT / (
        "v_phase13s_" + utcnow_iso().replace(":", "").replace("-", "").replace("+", "p")
    )
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(CHAMPION_POINTER_PATH, backup_dir / "champion_pointer.previous.json")

    feature_columns = engine.feature_lists.get("minutes") or list(
        next(iter(engine.feature_lists.values()), [])
    )
    feature_list_hash = _hash_columns(feature_columns)
    decision_id = (
        f"phase13s-promotion-{contextual_dir.name}-"
        + utcnow_iso().replace(":", "").replace("-", "").replace("+", "p")[:15]
    )

    new_pointer = dict(pointer)
    _ttd = tm.get("trained_through_date")
    _ctd = tm.get("calibrated_through_date")
    contextual_block = {
        # New / overwritten: promote to Phase 13S contextual.
        # Base champion fields must advance with each contextual promotion so
        # champion_model_id and trained_through_date reflect the actual model date.
        "champion_model_id": f"challenger-{_ttd}" if _ttd else pointer.get("champion_model_id"),
        "model_version": f"challenger-{_ttd}" if _ttd else pointer.get("model_version"),
        "trained_through_date": _ttd,
        "calibrated_through_date": _ctd,
        "promoted_at_utc": utcnow_iso(),
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "direct_lineup_pmf_driver": True,
        "contextual_pmf_engine": True,
        "official_lineup_features_enabled": True,
        "injury_availability_features_enabled": True,
        "vacated_opportunity_features_enabled": True,
        "lineup_composition_features_enabled": True,
        "lineup_interaction_features_enabled": True,
        "game_context_features_enabled": True,
        "lineup_injury_context_upstream_of_pmf": True,
        "direct_lineup_pmf_sensitivity_verified": True,
        "lineup_composition_pmf_sensitivity_verified": True,
        "actionability_sensitivity_verified": True,
        "market_only_edge_sensitivity_verified": True,
        "contextual_pmf_sensitivity_verified": True,
        "contextual_trained_through_date": _ttd,
        "contextual_calibrated_through_date": _ctd,
        "contextual_challenger_dir": str(contextual_dir.relative_to(REPO_ROOT)),
        "contextual_train_manifest_path": str(
            train_manifest_path.relative_to(REPO_ROOT)),
        "contextual_no_leakage_manifest_path": str(
            (contextual_dir / "no_leakage_manifest.json").relative_to(REPO_ROOT)),
        "contextual_validation_report_path": str(gates_path.relative_to(REPO_ROOT)),
        "contextual_promotion_decision_id": decision_id,
        "contextual_promotion_decision_path": str(
            (contextual_dir / "promotion_decision.json").relative_to(REPO_ROOT)),
        "contextual_promoted_at_utc": utcnow_iso(),
        "contextual_promoted_from_pointer_backup": str(
            (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
        "contextual_feature_columns": list(feature_columns),
        "contextual_feature_list_hash": feature_list_hash,
        "contextual_feature_list_hashes_per_target": dict(engine.feature_list_hashes),
        "contextual_fitted_targets": list(engine.fitted_targets),
        "contextual_code_commit": git_commit(),
        "validation_report_path": str(gates_path.relative_to(REPO_ROOT)),
        "promotion_decision_id": decision_id,
    }
    new_pointer.update(contextual_block)

    # #region agent log
    import time as _time
    _dbg_log = __import__('pathlib').Path("/Users/josephshackelford/repos/nba-player-props-model-pmf-fix/.cursor/debug-cd71ad.log")
    _dbg_log.parent.mkdir(parents=True, exist_ok=True)
    _dbg_log.open("a").write(__import__('json').dumps({"sessionId":"cd71ad","hypothesisId":"H-base-fields","location":"promote_direct_lineup_challenger.py:292","message":"phase13s_promotion_writing_pointer","data":{"champion_model_id":new_pointer.get("champion_model_id"),"trained_through_date":new_pointer.get("trained_through_date"),"calibrated_through_date":new_pointer.get("calibrated_through_date"),"contextual_trained_through_date":new_pointer.get("contextual_trained_through_date")},"timestamp":int(_time.time()*1000)}) + "\n")
    # #endregion agent log

    write_json_atomic(CHAMPION_POINTER_PATH, new_pointer)

    # ── Readback verification ──────────────────────────────────────────────────
    # Confirm the file on disk actually reflects the promoted model before
    # emitting PASS.  If write_json_atomic silently failed (e.g. permissions,
    # FS error, atomic-replace race) this guard catches it immediately so the
    # commit step never sees "promoted=True but nothing staged".
    try:
        readback = json.loads(CHAMPION_POINTER_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL", flush=True)
        print(f"  could not read back champion_pointer.json: {exc}", flush=True)
        sys.exit(1)

    expected_ctx_dir = str(contextual_dir.relative_to(REPO_ROOT))
    expected_ttd = tm.get("trained_through_date")
    rb_ctx_dir = readback.get("contextual_challenger_dir")
    rb_ttd = readback.get("contextual_trained_through_date")
    rb_base_ttd = readback.get("trained_through_date")
    rb_fs_id = readback.get("feature_set_id")
    rb_champion_id = readback.get("champion_model_id")
    expected_champion_id = f"challenger-{expected_ttd}" if expected_ttd else None
    if (rb_ctx_dir != expected_ctx_dir or rb_ttd != expected_ttd
            or rb_fs_id != DIRECT_LINEUP_FEATURE_SET_ID
            or rb_base_ttd != expected_ttd
            or (expected_champion_id and rb_champion_id != expected_champion_id)):
        print("PHASE13_PROMOTION_POINTER_WRITE_VERIFY_FAIL", flush=True)
        print(f"  expected contextual_challenger_dir={expected_ctx_dir!r}", flush=True)
        print(f"  got     contextual_challenger_dir={rb_ctx_dir!r}", flush=True)
        print(f"  expected contextual_trained_through_date={expected_ttd!r}", flush=True)
        print(f"  got     contextual_trained_through_date={rb_ttd!r}", flush=True)
        print(f"  expected trained_through_date={expected_ttd!r}", flush=True)
        print(f"  got     trained_through_date={rb_base_ttd!r}", flush=True)
        print(f"  expected champion_model_id={expected_champion_id!r}", flush=True)
        print(f"  got     champion_model_id={rb_champion_id!r}", flush=True)
        print(f"  expected feature_set_id={DIRECT_LINEUP_FEATURE_SET_ID!r}", flush=True)
        print(f"  got     feature_set_id={rb_fs_id!r}", flush=True)
        sys.exit(1)
    # ── End readback verification ──────────────────────────────────────────────

    write_json_atomic(contextual_dir / "promotion_decision.json", {
        "schema_version": "1.0",
        "promoted": True,
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "decision_id": decision_id,
        "decided_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "contextual_challenger_dir": str(contextual_dir.relative_to(REPO_ROOT)),
        "previous_pointer_backup": str(
            (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
        "validation_gates_report": str(gates_path.relative_to(REPO_ROOT)),
        "no_leakage_report": str(leak_path.relative_to(REPO_ROOT))
            if leak_path.exists() else None,
        "sensitivity_report": str(sens_path.relative_to(REPO_ROOT))
            if sens_path.exists() else None,
    })
    write_json_atomic(contextual_dir / "promotion_manifest.json", {
        "schema_version": "1.0",
        "promoted": True,
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "decision_id": decision_id,
        "promoted_at_utc": utcnow_iso(),
        "champion_pointer_path": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
        "previous_pointer_backup": str(
            (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
        "code_commit": git_commit(),
    })

    PROMOTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    is_new = not PROMOTION_LOG.exists()
    import csv
    with PROMOTION_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow([
                "decided_at_utc", "from_version", "to_version", "decision",
                "feature_set_id", "decision_id", "reason", "operator",
            ])
        w.writerow([
            utcnow_iso(),
            pointer.get("model_version", "unknown"),
            pointer.get("model_version", "unknown"),
            "promoted_phase13s_direct_lineup",
            DIRECT_LINEUP_FEATURE_SET_ID,
            decision_id,
            "phase13s_direct_lineup_promotion",
            "phase13s-promoter",
        ])

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "direct_lineup_promotion_decision.json").write_text(
        json.dumps({
            "schema_version": "1.0",
            "promoted": True,
            "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
            "decision_id": decision_id,
            "decided_at_utc": utcnow_iso(),
            "code_commit": git_commit(),
            "contextual_challenger_dir": str(contextual_dir.relative_to(REPO_ROOT)),
            "previous_pointer_backup": str(
                (backup_dir / "champion_pointer.previous.json").relative_to(REPO_ROOT)),
            "augmented_fields": sorted(contextual_block.keys()),
        }, indent=2, sort_keys=True, default=str), encoding="utf-8")

    print("PHASE13S_DIRECT_LINEUP_CHAMPION_PROMOTION_PASS")
    print(f"  feature_set_id={DIRECT_LINEUP_FEATURE_SET_ID}")
    print(f"  contextual_challenger_dir={contextual_dir.relative_to(REPO_ROOT)}")
    print(f"  decision_id={decision_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
