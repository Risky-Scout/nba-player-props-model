#!/usr/bin/env python3
"""Fail CI if Phase 8 diagnostics misrepresent market evaluation or superiority."""
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
    ap.add_argument(
        "--meta",
        type=Path,
        default=None,
        help="Path to diagnostics_*.meta.json (default: newest under artifacts/docs/).",
    )
    ap.add_argument(
        "--expect-workflow-market-eval",
        action="store_true",
        help="CI: workflow is titled for market eval — require require_market_eval and event_market_scored.",
    )
    args = ap.parse_args()

    meta_path = args.meta
    if meta_path is None:
        docs = Path("artifacts/docs")
        if not docs.is_dir():
            print("ABORT: no artifacts/docs and no --meta", file=sys.stderr)
            return 2
        cands = sorted(docs.glob("diagnostics_*.meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            print("ABORT: no diagnostics_*.meta.json under artifacts/docs", file=sys.stderr)
            return 2
        meta_path = cands[0]
        print(f"Using newest meta: {meta_path}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    bad = _walk_nonfinite(data)
    if bad:
        print("FAIL: non-finite JSON values (use null, not NaN):", file=sys.stderr)
        for b in bad[:50]:
            print(f"  {b}", file=sys.stderr)
        return 1

    req = bool(data.get("require_market_eval"))
    allow_bl = bool(data.get("allow_baseline_only"))
    status = str(data.get("market_eval_status") or "")
    strict_res = str(data.get("strict_contract_result") or "")
    msup = bool(data.get("market_superiority_claim_allowed"))
    gsup = bool(data.get("global_market_superiority_claim_allowed"))

    if allow_bl and msup:
        print("FAIL: allow_baseline_only with market_superiority_claim_allowed=true", file=sys.stderr)
        return 1

    if msup and strict_res != "pass":
        print(
            f"FAIL: market_superiority_claim_allowed=true but strict_contract_result={strict_res!r}",
            file=sys.stderr,
        )
        return 1

    if gsup and strict_res != "pass":
        print(
            f"FAIL: global_market_superiority_claim_allowed=true but strict_contract_result={strict_res!r}",
            file=sys.stderr,
        )
        return 1

    if args.expect_workflow_market_eval:
        if not req:
            print("FAIL: workflow expects market eval but require_market_eval is false in meta", file=sys.stderr)
            return 1
        if status != "event_market_scored":
            print(
                f"FAIL: workflow expects market eval but market_eval_status={status!r}",
                file=sys.stderr,
            )
            return 1

    if req and status not in ("event_market_scored",):
        print(
            f"FAIL: require_market_eval but market_eval_status={status!r} (expected event_market_scored)",
            file=sys.stderr,
        )
        return 1

    print("PHASE8_MARKET_EVAL_CONTRACT_VERIFIER_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
