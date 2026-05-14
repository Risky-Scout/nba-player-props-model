#!/usr/bin/env python3
"""Run a subprocess and tee stdout/stderr into artifacts/run_logs/<run_id>/<step>.*.log

Usage:
  python3 scripts/run_with_warning_capture.py --run-id myrun --step diagnostics -- \\
    python3 scripts/run_diagnostics.py --allow-baseline-only
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if "--" not in sys.argv:
        print("Need -- before command", file=sys.stderr)
        return 2
    i = sys.argv.index("--")
    pre = sys.argv[1:i]
    post = sys.argv[i + 1 :]
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--step", default="step")
    a = ap.parse_args(pre)
    log_dir = REPO_ROOT / "artifacts" / "run_logs" / a.run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"{a.step}.stdout.log").write_text("", encoding="utf-8")
    p = subprocess.run(post, cwd=str(REPO_ROOT), capture_output=True, text=True)
    (log_dir / f"{a.step}.stdout.log").write_text(p.stdout or "", encoding="utf-8")
    (log_dir / f"{a.step}.stderr.log").write_text(p.stderr or "", encoding="utf-8")
    print(p.stdout or "", end="")
    print(p.stderr or "", end="", file=sys.stderr)
    return int(p.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
