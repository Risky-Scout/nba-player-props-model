#!/usr/bin/env python3
"""Smoke tests for run_diagnostics preflight (missing training table, meta shape)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    fails: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        fake_oof = REPO_ROOT / "data" / "oof_pmfs.parquet"
        if not fake_oof.exists():
            print("SKIP: data/oof_pmfs.parquet missing", file=sys.stderr)
            return 0
        run_date = f"preflight_{uuid.uuid4().hex[:10]}"
        tt_missing = td_path / "no_training_table.parquet"
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "run_diagnostics.py"),
            "--run-date",
            run_date,
            "--oof-path",
            str(fake_oof),
            "--training-table",
            str(tt_missing),
            "--allow-baseline-only",
        ]
        r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if r.returncode != 3:
            fails.append(f"expected_exit_3_got_{r.returncode}")
        if "Traceback" in (r.stderr or ""):
            fails.append("raw_traceback_on_missing_training_table")
        sidecar = REPO_ROOT / "artifacts" / "docs" / f"diagnostics_{run_date}.meta.json"
        if not sidecar.exists():
            fails.append("meta_not_written")
        else:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            if data.get("failure_code") != "MISSING_TRAINING_TABLE":
                fails.append("wrong_failure_code")
            if data.get("diagnostics_status") != "failed_preflight":
                fails.append("wrong_diagnostics_status")
            sidecar.unlink(missing_ok=True)

    miss_meta = REPO_ROOT / "artifacts" / "docs" / "diagnostics_NONEXISTENT_RUN.meta.json"
    vcmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "verify_phase8_market_eval_contract.py"),
        "--meta",
        str(miss_meta),
    ]
    r2 = subprocess.run(vcmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if r2.returncode == 0:
        fails.append("verifier_should_fail_on_missing_meta")

    if fails:
        print("VERIFY_RUN_DIAGNOSTICS_PREFLIGHT_CONTRACT_FAIL")
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1

    print("VERIFY_RUN_DIAGNOSTICS_PREFLIGHT_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
