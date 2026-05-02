"""Phase 13O — verify no_leakage by reading
artifacts/phase13o/live_context_feature_manifest.json and inspecting
``leakage_notes``. Emit PHASE13O_NO_LEAKAGE_PASS / _FAILED."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = REPO_ROOT / "artifacts" / "phase13o" / "live_context_feature_manifest.json"
    if not p.exists():
        print("PHASE13O_NO_LEAKAGE_FAILED", file=sys.stderr)
        print(f"  reason: missing {p.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print("PHASE13O_NO_LEAKAGE_FAILED", file=sys.stderr)
        print(f"  reason: cannot parse manifest: {exc}", file=sys.stderr)
        return 1
    leak = m.get("leakage_notes") or []
    if leak:
        print("PHASE13O_NO_LEAKAGE_FAILED", file=sys.stderr)
        for n in leak:
            print(f"  - {n}", file=sys.stderr)
        return 1
    print("PHASE13O_NO_LEAKAGE_PASS")
    print(f"  asof_cutoff_rule={m.get('asof_cutoff_rule')!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
