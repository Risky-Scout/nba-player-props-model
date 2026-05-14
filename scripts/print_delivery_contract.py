#!/usr/bin/env python3
"""Print the frozen M8.8 delivery contract summary."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.delivery.delivery_contract import (  # noqa: E402
    DELIVERY_CONTRACT_VERSION,
    PIPELINE_MODE_BY_RUN_MODE,
    RunMode,
    delivery_file_specs,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()
    specs = delivery_file_specs()
    if args.json:
        rows = []
        for s in specs:
            rows.append(
                {
                    "relative_path": s.relative_path,
                    "presence": {k.value: v.value for k, v in s.presence.items()},
                    "required_columns": list(s.required_columns),
                }
            )
        print(json.dumps({"version": DELIVERY_CONTRACT_VERSION, "files": rows}, indent=2))
    else:
        print(f"delivery_contract_version={DELIVERY_CONTRACT_VERSION}")
        print(f"n_files={len(specs)}")
        for m in RunMode:
            print(f"  run_mode {m.value} -> pipeline_mode={PIPELINE_MODE_BY_RUN_MODE[m]}")
    print("DELIVERY_CONTRACT_DEFINED_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
