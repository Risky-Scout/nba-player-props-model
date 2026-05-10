"""Build combo PMFs from joint stat samples (NBA Props Model M5A).

Reads predictions/joint_stat_samples_<date>.parquet (M3 dispatcher
output) and derives empirical combo PMFs by grouping samples by
(player_id, game_id) and summing component columns within the SAME
simulation_id. This is the joint-sample alternative to
combo_independence_v1 / sparse_hurdle.stocks_pmf -- it preserves the
within-game correlation structure that np.convolve loses.

This is M5A: foundation only. Combo PMFs produced here are NOT
wired into production delivery. They are also marked
calibrated=False / calibration_status=pending_m6_stat_role_calibration
because role-aware calibrators for combo stats do not exist yet
(M6 handles that).

Outputs (default):
    predictions/combo_pmfs_from_joint_samples_<date>.parquet
    predictions/combo_pmfs_from_joint_samples_<date>.manifest.json

Examples:
    python scripts/build_combo_pmfs_from_joint_samples.py --date 2026-05-09
    python scripts/build_combo_pmfs_from_joint_samples.py --date 2026-05-09 \
        --combos stl_blk pts_reb_ast
    python scripts/build_combo_pmfs_from_joint_samples.py --date 2026-05-09 \
        --in /tmp/synth.parquet --out /tmp/combos.parquet
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.models.joint_combo_pmfs import (  # noqa: E402
    JOINT_COMBO_PMF_VERSION,
    MODEL_VERSION_TAG,
    CALIBRATION_STATUS_PENDING_M6,
    DEFAULT_MISSION_COMBOS,
    ALL_KNOWN_COMBOS,
    COMPONENT_DOMAIN_MAX,
    combo_domain_max,
    empirical_combo_pmf_from_samples,
    normalize_combo_name,
    mission_alias_for,
)
from nba_props_model.models.joint_simulation import (  # noqa: E402
    JOINT_SAMPLER_VERSION,
)

logger = logging.getLogger(__name__)
PRED_DIR = REPO_ROOT / "predictions"


REQUIRED_INPUT_COLS = {
    "date", "game_id", "player_id", "simulation_id",
    "pts", "reb", "ast", "stl", "blk",
}


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate combo PMFs from joint stat samples (NBA Props Model M5A).",
    )
    p.add_argument(
        "--date", required=True,
        help="YYYY-MM-DD slate date (US/Eastern); used to locate input parquet by default.",
    )
    p.add_argument(
        "--in", dest="in_path", default=None,
        help="Joint sample parquet input; default predictions/joint_stat_samples_<date>.parquet",
    )
    p.add_argument(
        "--out", default=None,
        help="Output parquet path; default predictions/combo_pmfs_from_joint_samples_<date>.parquet",
    )
    p.add_argument(
        "--combos", nargs="+", default=None,
        help=("Combos to derive (canonical or mission names). "
              "Default: " + " ".join(DEFAULT_MISSION_COMBOS)),
    )
    p.add_argument(
        "--include-ra", action="store_true",
        help="Also include ra/reb_ast (NOT mission-required).",
    )
    return p


def _format_pmf_json(pmf: np.ndarray) -> str:
    """Serialize PMF to compact JSON {str(int): float} for non-zero entries."""
    return json.dumps({str(i): float(p) for i, p in enumerate(pmf) if p > 0.0})


def _row_for_group(
    group: pd.DataFrame,
    canonical_combo: str,
    *,
    sample_source: str,
) -> dict:
    pmf = empirical_combo_pmf_from_samples(group, canonical_combo)
    pmf = np.asarray(pmf, dtype=np.float64)
    pmf_sum = float(pmf.sum())
    pmf_sum_error = float(abs(pmf_sum - 1.0))
    pmf_valid = bool(
        pmf_sum_error < 1e-6
        and bool(np.isfinite(pmf).all())
        and bool((pmf >= 0.0).all())
    )

    representative = group.iloc[0]
    return {
        "date": str(representative.get("date", "")),
        "game_id": int(representative["game_id"]),
        "player_id": int(representative["player_id"]),
        "player_name": str(representative.get("player_name", "")),
        "team": str(representative.get("team", "")),
        "opponent": str(representative.get("opponent", "")),
        "role_bucket": str(representative.get("role_bucket", "unknown")),
        "stat": canonical_combo,
        "mission_stat": mission_alias_for(canonical_combo),
        "pmf_json": _format_pmf_json(pmf),
        "support_min": int(0),
        "support_max": int(combo_domain_max(canonical_combo)),
        "pmf_sum_error": pmf_sum_error,
        "pmf_valid": pmf_valid,
        "n_draws": int(len(group)),
        "sample_source": str(sample_source),
        "joint_sampler_version": str(JOINT_SAMPLER_VERSION),
        "combo_pmf_version": JOINT_COMBO_PMF_VERSION,
        "model_version": f"{JOINT_SAMPLER_VERSION}+{MODEL_VERSION_TAG}",
        "calibrated": False,
        "calibration_status": CALIBRATION_STATUS_PENDING_M6,
    }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = _build_argparser().parse_args()

    in_path = (
        Path(args.in_path) if args.in_path
        else PRED_DIR / f"joint_stat_samples_{args.date}.parquet"
    )
    out_path = (
        Path(args.out) if args.out
        else PRED_DIR / f"combo_pmfs_from_joint_samples_{args.date}.parquet"
    )
    manifest_path = out_path.parent / (out_path.stem + ".manifest.json")

    if not in_path.exists():
        print(f"ABORT: joint sample input not found: {in_path}", file=sys.stderr)
        return 2

    if args.combos:
        canonical: list = []
        for c in args.combos:
            try:
                canonical.append(normalize_combo_name(c))
            except ValueError as e:
                print(f"ABORT: {e}", file=sys.stderr)
                return 4
    else:
        canonical = list(DEFAULT_MISSION_COMBOS)
    if args.include_ra and "ra" not in canonical:
        canonical.append("ra")
    seen: set = set()
    canonical = [c for c in canonical if not (c in seen or seen.add(c))]

    print(f"  input: {in_path}")
    print(f"  output: {out_path}")
    print(f"  combos (canonical): {canonical}")
    print(f"  combos (mission):  {[mission_alias_for(c) for c in canonical]}")

    df = pd.read_parquet(in_path)
    print(f"  input rows: {len(df):,}")

    missing_cols = REQUIRED_INPUT_COLS - set(df.columns)
    if missing_cols:
        print(f"ABORT: input missing required columns: {missing_cols}", file=sys.stderr)
        return 3

    rows: list = []
    n_groups = 0
    for (player_id, game_id), group in df.groupby(["player_id", "game_id"], sort=False):
        n_groups += 1
        for c in canonical:
            rows.append(_row_for_group(group, c, sample_source=str(in_path)))

    print(f"  groups (player x game): {n_groups}")
    print(f"  output rows: {len(rows)}")

    if not rows:
        print("ABORT: no output rows produced", file=sys.stderr)
        return 5

    out_df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(out_path, index=False)
    print(f"  wrote: {out_path}")

    pmf_validity_rate = (
        float(out_df["pmf_valid"].mean()) if len(out_df) else 1.0
    )
    pmf_sum_error_max = (
        float(out_df["pmf_sum_error"].max()) if len(out_df) else 0.0
    )
    manifest = {
        "schema_version": "1.0",
        "date": args.date,
        "input": str(in_path),
        "output": str(out_path),
        "rows": len(rows),
        "groups": n_groups,
        "combos_canonical": canonical,
        "combos_mission": [mission_alias_for(c) for c in canonical],
        "combo_pmf_version": JOINT_COMBO_PMF_VERSION,
        "joint_sampler_version": JOINT_SAMPLER_VERSION,
        "model_version_tag": MODEL_VERSION_TAG,
        "calibrated": False,
        "calibration_status": CALIBRATION_STATUS_PENDING_M6,
        "pmf_validity_rate": pmf_validity_rate,
        "pmf_sum_error_max": pmf_sum_error_max,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": (
            "M5A foundation. Combo PMFs are NOT yet wired into production delivery. "
            "Combo calibrators do not exist (combos are calibrated=False / "
            "calibration_status=pending_m6_stat_role_calibration). M6 handles "
            "stat x role calibration for combos."
        ),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  wrote manifest: {manifest_path}")

    print("BUILD_COMBO_PMFS_FROM_JOINT_SAMPLES_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
