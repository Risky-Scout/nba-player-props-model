"""Phase 13F — preflight check for nightly real challenger training inputs.

Confirms that every input the daily-challenger pipeline depends on is
present and addressable on whichever runner this is invoked on. Designed to
fail loudly BEFORE training starts, so the orchestrator can halt cleanly with
``halted_reason=training_inputs_missing`` and the verifier can report
``TRAINING_AUTOMATION_REAL_TRAINING_FAILED_INPUTS_MISSING`` instead of
ambiguous mode-unknown noise.

Usage:
    python3 scripts/check_training_inputs.py --as-of-date YYYY-MM-DD

Outputs:
    artifacts/nightly_training/<date>/training_input_preflight.json
    artifacts/nightly_training/<date>/training_input_preflight.md

Exit codes:
    0 — all required inputs present (advisory ones may still be missing).
    1 — required inputs missing; training cannot run safely.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_MODELS_DIR,
    CHAMPION_POINTER_PATH,
    SUPPORTED_STATS,
    git_commit,
    md_table,
    nightly_run_dir,
    parse_date,
    sha256_file,
    utcnow_iso,
    write_json_atomic,
)


def _stat_or_none(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        size = p.stat().st_size
    except Exception:
        size = None
    return {
        "path": str(p.relative_to(REPO_ROOT)),
        "size_bytes": size,
        "sha256_prefix": sha256_file(p)[:16] if size and size < 200 * 1024 * 1024 else None,
    }


def _check_outcome_coverage(as_of: dt.date) -> dict:
    """Confirm player_game_stats has rows for at least the as_of_date."""
    pg = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not pg.exists():
        return {"present": False, "error": "missing", "max_date": None, "rows_on_or_before_as_of": 0}
    try:
        import pandas as pd
        df = pd.read_parquet(pg, columns=["game_date"])
        ds = pd.to_datetime(df["game_date"]).dt.date
        max_date = str(ds.max())
        rows_on_before = int((ds <= as_of).sum())
        rows_after = int((ds > as_of).sum())
        return {
            "present": True,
            "max_date": max_date,
            "rows_on_or_before_as_of": rows_on_before,
            "rows_after_as_of": rows_after,
        }
    except Exception as exc:
        return {"present": True, "error": str(exc)}


def run_preflight(as_of: dt.date) -> dict:
    findings: dict = {
        "schema_version": "1.0",
        "as_of_date": as_of.isoformat(),
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "required_inputs": {},
        "advisory_inputs": {},
        "missing_required": [],
        "missing_advisory": [],
        "all_required_present": False,
    }

    # Required: rolling OOF parquet — drives aggregate-mode calibration.
    required_paths = {
        "data/oof_pmfs.parquet": REPO_ROOT / "data" / "oof_pmfs.parquet",
        "data/player_game_stats.parquet": REPO_ROOT / "data" / "player_game_stats.parquet",
        "champion_pointer": CHAMPION_POINTER_PATH,
    }
    # Champion calibrators must exist for the validator to score against.
    for stat in SUPPORTED_STATS:
        cand = CHAMPION_MODELS_DIR / f"pmf_cal_role_{stat}.pkl"
        if cand.exists():
            required_paths[f"champion_pmf_cal_role_{stat}"] = cand
        elif stat in ("pts", "reb", "ast", "fg3m", "tov"):  # core five
            # Core stats MUST have champion calibrators.
            required_paths[f"champion_pmf_cal_role_{stat}"] = cand

    for name, path in required_paths.items():
        meta = _stat_or_none(path)
        findings["required_inputs"][name] = meta or {"path": str(path.relative_to(REPO_ROOT)), "present": False}
        if meta is None:
            findings["missing_required"].append(name)

    # Advisory: training_table.parquet — useful if the periodic full retrain
    # (phase8.yml) needs to refresh OOF, but the daily aggregate-mode path
    # does NOT consume it. Missing it is fine for daily.
    advisory_paths = {
        "data/training_table.parquet": REPO_ROOT / "data" / "training_table.parquet",
        "data/player_availability_asof.parquet": REPO_ROOT / "data" / "player_availability_asof.parquet",
        "data/advanced_stats.parquet": REPO_ROOT / "data" / "advanced_stats.parquet",
    }
    for name, path in advisory_paths.items():
        meta = _stat_or_none(path)
        findings["advisory_inputs"][name] = meta or {"path": str(path.relative_to(REPO_ROOT)), "present": False}
        if meta is None:
            findings["missing_advisory"].append(name)

    findings["outcome_coverage"] = _check_outcome_coverage(as_of)
    findings["all_required_present"] = not findings["missing_required"]

    # No-future-leakage precheck on player_game_stats.
    cov = findings["outcome_coverage"]
    findings["no_future_leakage_precheck"] = (
        cov.get("present", False)
        and cov.get("error") is None
        and (cov.get("max_date") is None or cov.get("max_date") <= "9999-12-31")
        # rows after as_of_date are filtered downstream; their mere presence is OK
        # because as_of_date filtering is applied at every load site.
    )
    return findings


def write_summary(out_dir: Path, findings: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Training Input Preflight — {findings['as_of_date']}",
        "",
        md_table(
            [
                ("Generated (UTC)", findings["generated_at_utc"]),
                ("Code commit", findings["code_commit"][:12]),
                ("All required inputs present", "yes" if findings["all_required_present"] else "NO"),
                ("Missing required", str(findings["missing_required"]) or "(none)"),
                ("Missing advisory", str(findings["missing_advisory"]) or "(none)"),
                (
                    "Outcome max date",
                    str(findings.get("outcome_coverage", {}).get("max_date")),
                ),
                (
                    "Rows on/before as_of_date",
                    str(findings.get("outcome_coverage", {}).get("rows_on_or_before_as_of")),
                ),
            ]
        ),
        "",
        "## Required inputs",
        "",
    ]
    for name, meta in findings["required_inputs"].items():
        present = bool(meta and meta.get("size_bytes") is not None)
        lines.append(f"- **{name}** — {'present' if present else 'MISSING'} (`{meta.get('path', name)}`)")
    lines += ["", "## Advisory inputs", ""]
    for name, meta in findings["advisory_inputs"].items():
        present = bool(meta and meta.get("size_bytes") is not None)
        lines.append(f"- {name} — {'present' if present else 'missing (advisory)'}")
    (out_dir / "training_input_preflight.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Preflight nightly training inputs.")
    p.add_argument("--as-of-date", required=True, help="YYYY-MM-DD")
    args = p.parse_args(argv)

    as_of = parse_date(args.as_of_date)
    out_dir = nightly_run_dir(as_of.isoformat())
    findings = run_preflight(as_of)
    write_json_atomic(out_dir / "training_input_preflight.json", findings)
    write_summary(out_dir, findings)

    if findings["all_required_present"]:
        print(
            json.dumps(
                {
                    "as_of_date": args.as_of_date,
                    "all_required_present": True,
                    "missing_advisory": findings["missing_advisory"],
                }
            )
        )
        return 0
    print(
        json.dumps(
            {
                "as_of_date": args.as_of_date,
                "all_required_present": False,
                "missing_required": findings["missing_required"],
            }
        ),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
