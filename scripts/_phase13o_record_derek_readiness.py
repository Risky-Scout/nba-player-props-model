"""Phase 13O — record current champion + feature_set_id into
artifacts/phase13o/derek_output_readiness.json. Emit
PHASE13O_DEREK_OUTPUT_READINESS_PASS."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features import live_context as lc  # noqa: E402
from nba_props_model.training_automation import (  # noqa: E402
    CHAMPION_POINTER_PATH, read_json,
)


def main() -> int:
    pointer = read_json(CHAMPION_POINTER_PATH) if CHAMPION_POINTER_PATH.exists() else {}
    out = {
        "feature_set_id": lc.feature_set_id(),
        "feature_set_hash": lc.feature_set_hash(),
        "champion_model_id": pointer.get("champion_model_id"),
        "trained_through_date": pointer.get("trained_through_date"),
        "calibrated_through_date": pointer.get("calibrated_through_date"),
        # The current promoted champion does NOT consume Phase 13O
        # features. These flags become true when a Phase 13O challenger
        # is promoted via the existing promotion gates.
        "live_context_features_enabled": False,
        "trained_with_bdl_lineup_features": False,
        "trained_with_injury_availability_features": False,
        "trained_with_vacated_opportunity_features": False,
        "champion_pointer_path": str(CHAMPION_POINTER_PATH.relative_to(REPO_ROOT)),
    }
    out_dir = REPO_ROOT / "artifacts" / "phase13o"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "derek_output_readiness.json").write_text(
        json.dumps(out, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("PHASE13O_DEREK_OUTPUT_READINESS_PASS")
    print(f"  feature_set_id={out['feature_set_id']!r}")
    print(f"  champion_model_id={out['champion_model_id']!r}")
    print(f"  live_context_features_enabled={out['live_context_features_enabled']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
