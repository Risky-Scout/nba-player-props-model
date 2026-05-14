#!/usr/bin/env python3
"""Print the M8.9 player-prop feature contract summary."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.player_prop_feature_contract import (  # noqa: E402
    FEATURE_CONTRACT_VERSION,
    LeakageStatus,
    assert_feature_contract_coherent,
    feature_families,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    assert_feature_contract_coherent()
    families = feature_families()
    if args.json:
        payload = {
            "feature_contract_version": FEATURE_CONTRACT_VERSION,
            "n_families": len(families),
            "families": [
                {
                    "name": f.name,
                    "source": f.source,
                    "asof_column": f.asof_column,
                    "allowed_run_modes": [m.value for m in f.allowed_run_modes],
                    "leakage_status": f.leakage_status.value,
                    "stat_applicability": list(f.stat_applicability),
                    "n_features": len(f.features),
                    "features": [x.name for x in f.features],
                }
                for f in families
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"feature_contract_version={FEATURE_CONTRACT_VERSION}")
        print(f"n_families={len(families)}")
        for leak in LeakageStatus:
            n = sum(1 for fam in families if fam.leakage_status == leak)
            print(f"  leakage_status[{leak.value}]={n}")
    print("PLAYER_PROP_FEATURE_CONTRACT_DEFINED_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
