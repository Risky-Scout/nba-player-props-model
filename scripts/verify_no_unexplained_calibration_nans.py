#!/usr/bin/env python3
"""Reject diagnostics meta that still carries unexplained NaNs or silent constant-prob holes."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def _walk_nonfinite(obj, path: str = "$") -> list[str]:
    bad: list[str] = []
    if isinstance(obj, float) and not math.isfinite(obj):
        bad.append(path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            bad.extend(_walk_nonfinite(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad.extend(_walk_nonfinite(v, f"{path}[{i}]"))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", type=Path, default=None, help="diagnostics_*.meta.json")
    args = ap.parse_args()

    meta_path = args.meta
    if meta_path is None:
        docs = Path("artifacts/docs")
        if not docs.is_dir():
            print("ABORT: no artifacts/docs", file=sys.stderr)
            return 2
        cands = sorted(docs.glob("diagnostics_*.meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            print("ABORT: no diagnostics_*.meta.json", file=sys.stderr)
            return 2
        meta_path = cands[0]
        print(f"Using newest meta: {meta_path}")

    raw = meta_path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}", file=sys.stderr)
        return 1

    bad = _walk_nonfinite(data)
    if bad:
        print("FAIL: non-finite floats in meta (expected null + status fields):", file=sys.stderr)
        for b in bad[:80]:
            print(f"  {b}", file=sys.stderr)
        return 1

    cps = data.get("calibration_constant_prob_summary") or {}
    n_grp = int(cps.get("n_constant_prob_groups") or 0)
    by_stat = cps.get("constant_prob_groups_by_stat") or {}
    keys = cps.get("constant_prob_fold_keys")
    if n_grp > 0:
        stat_sum = 0
        if isinstance(by_stat, dict):
            for _k, v in by_stat.items():
                try:
                    stat_sum += int(v)
                except (TypeError, ValueError):
                    pass
        if stat_sum == 0 and not (isinstance(keys, list) and len(keys) > 0):
            print(
                "FAIL: n_constant_prob_groups>0 but no constant_prob_groups_by_stat counts "
                "and no constant_prob_fold_keys",
                file=sys.stderr,
            )
            return 1

    print("CALIBRATION_JSON_HYGIENE_VERIFIER_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
