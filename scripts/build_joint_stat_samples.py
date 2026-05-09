"""Generate predictions/joint_stat_samples_<date>.parquet (NBA Props Model M3).

Writes the canonical joint-sample artifact downstream M5 combo PMFs derive
from. Each output row corresponds to one (player_id, game_id, simulation_id)
tuple; each player-game contributes n_draws rows.

The slate, pipeline state, per-(player, game) feature/minutes construction,
AND role-bucket derivation MIRROR scripts/build_stat_grid_pmfs.py exactly
so the joint-sample player universe and role labeling match the production
PMF universe.

DIFFERENCE FROM build_stat_grid_pmfs.py:
  - emits raw integer samples per simulation_id (not PMFs)
  - uses simulate_joint_stat_samples (minutes-shared) instead of
    build_prop_pmfs (per-stat marginals)

USAGE:
    python scripts/build_joint_stat_samples.py --date 2026-05-09
    python scripts/build_joint_stat_samples.py --date 2026-05-09 \
        --n-draws 20000 --slate-source recent_rosters
    python scripts/build_joint_stat_samples.py --date 2026-05-09 \
        --n-draws 100 --max-keys 1 --out /tmp/smoke.parquet   # smoke

OUTPUTS (paired):
    predictions/joint_stat_samples_<date>.parquet         (samples)
    predictions/joint_stat_samples_<date>.manifest.json   (sidecar)

OUTPUT SCHEMA (registry-ordered):
    date, game_id, player_id, player_name, team, opponent,
    role_bucket, availability_state (nullable), simulation_id,
    minutes, inactive_flag, pts, reb, ast, fg3m, tov, stl, blk
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))  # for cross-script import

warnings.filterwarnings("ignore")

# Reuse the production prep helpers from build_stat_grid_pmfs.
# Underscore prefix is convention here, not enforcement; this is the
# explicit reuse strategy approved in the M3 design preview.
from build_stat_grid_pmfs import (  # noqa: E402
    _build_pipeline_state,
    _slate_keys_from_all_props,
    _slate_keys_from_recent_rosters,
    _fg3m_hurdle_model,
    _AVAILABILITY_COLS,
    PRED_DIR,
)

from nba_props_model.features.engineering import (  # noqa: E402
    build_player_game_features,
    add_interaction_features,
)
from nba_props_model.features.availability_asof import (  # noqa: E402
    AvailabilityBuilder as _AvailabilityBuilder,
)
from nba_props_model.models.minutes import minutes_distribution  # noqa: E402
# CORRECTED: use the SAME helper that build_stat_grid_pmfs.py uses.
from nba_props_model.calibration.role_buckets import (  # noqa: E402
    role_bucket_features_from_minutes_dist,
)
from nba_props_model.models.joint_simulation import (  # noqa: E402
    simulate_joint_stat_samples,
    ALL_BASE_STATS_JOINT,
    RATE_STATS_JOINT,
    HURDLE_STATS_JOINT,
    JOINT_SAMPLER_VERSION,
    RATE_STATS_SAMPLING_METHOD,
    HURDLE_STATS_SAMPLING_METHOD,
    COMBO_READINESS_NOTE,
)


DEFAULT_N_DRAWS = 20_000

# Per master prompt §5 schema, registry-ordered.
EXPECTED_COLUMNS = [
    "date", "game_id", "player_id", "player_name", "team", "opponent",
    "role_bucket", "availability_state", "simulation_id",
    "minutes", "inactive_flag",
    "pts", "reb", "ast", "fg3m", "tov", "stl", "blk",
]


def _now_utc_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _samples_for_player_game(
    player_id: int, gid: int, *,
    target_date: str, state: dict, fg3m_model, n_draws: int,
    rng: np.random.Generator,
) -> list[dict]:
    """Compute joint samples for one (player, game).

    Mirrors build_stat_grid_pmfs._row_for_player_game prep
    (feature_row, minutes_dist, role_bucket via
    role_bucket_features_from_minutes_dist) but emits raw integer
    samples via simulate_joint_stat_samples.

    Returns list of n_draws row dicts, or [] on any failure.
    """
    # ── Game lookup ────────────────────────────────────────────────────
    game = state["games_by_id"].get(int(gid))
    if game is None:
        return []
    home_id_raw = (game.get("home_team") or {}).get("id") or game.get("home_team_id")
    visitor_id_raw = (game.get("visitor_team") or {}).get("id") or game.get("visitor_team_id")
    try:
        home_id = int(home_id_raw) if home_id_raw is not None else None
        visitor_id = int(visitor_id_raw) if visitor_id_raw is not None else None
    except Exception:
        return []

    # ── Player history lookup ──────────────────────────────────────────
    stats_df = state["stats_df"]
    pdata = stats_df[stats_df["player_id"] == int(player_id)].copy()
    if pdata.empty:
        return []
    pdata = pdata.sort_values("game_date")
    last = pdata.iloc[-1]
    try:
        team_id = int(last.get("team_id"))
    except Exception:
        return []

    if team_id == home_id:
        opp_id = visitor_id
        is_home = True
    elif team_id == visitor_id:
        opp_id = home_id
        is_home = False
    else:
        return []

    player_name = str(last.get("player_name", f"Player {player_id}"))

    # ── Build feature row ──────────────────────────────────────────────
    try:
        base = build_player_game_features(
            player_id=int(player_id),
            game_date=target_date,
            stats_history=pdata,
            adv_history=state["adv_by_player"].get(int(player_id), []),
            game_context=state["ctx_map"].get(int(gid), {}),
            injury_map=state["injury_map"],
            opp_team_id=opp_id,
            is_home=is_home,
        )
        feature_row = add_interaction_features(base)
    except Exception:
        return []

    # ── Build minutes distribution ─────────────────────────────────────
    avail_lookup = state["availability_lookup"]
    avail_row = avail_lookup.get((int(player_id), str(target_date)))
    if avail_row is None and state.get("availability_builder") is not None:
        try:
            avail_row = state["availability_builder"].build_for(
                int(player_id), target_date,
            )
        except Exception:
            avail_row = None

    try:
        mp_dist = minutes_distribution(
            player_id=int(player_id),
            game_date=target_date,
            stats_history=pdata,
            adv_history=state["adv_by_player"].get(int(player_id), []),
            game_context=state["ctx_map"].get(int(gid), {}),
            injury_map=state["injury_map"],
            opp_team_id=opp_id,
            is_home=is_home,
            availability_row=avail_row,
        )
    except Exception:
        return []
    if mp_dist is None:
        return []

    # ── Role bucket (PARITY with build_stat_grid_pmfs.py) ──────────────
    try:
        role_features = role_bucket_features_from_minutes_dist(mp_dist)
        role_bucket = role_features.get("role_bucket", "rotation")
    except Exception:
        role_bucket = "rotation"

    # ── Joint sample ───────────────────────────────────────────────────
    samples = simulate_joint_stat_samples(
        minutes_dist=mp_dist,
        feature_row=feature_row,
        n_draws=int(n_draws),
        rng=rng,
        fg3m_hurdle_model=fg3m_model,
    )
    if samples is None:
        return []

    availability_state = "asof_table" if avail_row is not None else None

    rows: list[dict] = []
    for sim_id in range(int(n_draws)):
        rows.append({
            "date": target_date,
            "game_id": int(gid),
            "player_id": int(player_id),
            "player_name": player_name,
            "team": int(team_id),
            "opponent": int(opp_id) if opp_id is not None else None,
            "role_bucket": role_bucket,
            "availability_state": availability_state,
            "simulation_id": int(sim_id),
            "minutes": float(samples["minutes"][sim_id]),
            "inactive_flag": bool(samples["inactive_flag"][sim_id]),
            "pts": int(samples["pts"][sim_id]),
            "reb": int(samples["reb"][sim_id]),
            "ast": int(samples["ast"][sim_id]),
            "fg3m": int(samples["fg3m"][sim_id]),
            "tov": int(samples["tov"][sim_id]),
            "stl": int(samples["stl"][sim_id]),
            "blk": int(samples["blk"][sim_id]),
        })
    return rows


def _write_manifest(
    *, manifest_path: Path, target_date: str, n_draws: int,
    rows_written: int, player_game_count: int,
    rng_seed, slate_source: str, max_players_per_team: int,
    fg3m_loaded: bool,
) -> None:
    """Write the sidecar manifest declaring sampler version and method tags."""
    manifest = {
        "date": target_date,
        "n_draws": int(n_draws),
        "rows_written": int(rows_written),
        "player_game_count": int(player_game_count),
        "base_stats": list(ALL_BASE_STATS_JOINT),
        "rate_stats": list(RATE_STATS_JOINT),
        "hurdle_stats": list(HURDLE_STATS_JOINT),
        "joint_sampler_version": JOINT_SAMPLER_VERSION,
        "rate_stats_sampling_method": RATE_STATS_SAMPLING_METHOD,
        "hurdle_stats_sampling_method": HURDLE_STATS_SAMPLING_METHOD,
        "rng_seed": rng_seed if rng_seed is not None else None,
        "slate_source": slate_source,
        "max_players_per_team": int(max_players_per_team),
        "source_pipeline_helper": "scripts/build_stat_grid_pmfs.py",
        "fg3m_hurdle_model_loaded": bool(fg3m_loaded),
        "created_at_utc": _now_utc_iso(),
        "combo_readiness_note": COMBO_READINESS_NOTE,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=False))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                    help="YYYY-MM-DD slate date (US/Eastern)")
    ap.add_argument("--n-draws", type=int, default=DEFAULT_N_DRAWS,
                    help=f"joint samples per (player, game) "
                         f"(default: {DEFAULT_N_DRAWS})")
    ap.add_argument("--slate-source", choices=["recent_rosters", "all_props"],
                    default="recent_rosters",
                    help="player-game slate source")
    ap.add_argument("--max-players-per-team", type=int, default=18,
                    help="recent-roster candidates per team (default 18)")
    ap.add_argument("--all-props", default=None,
                    help="optional all_props_<date>.parquet path")
    ap.add_argument("--out", default=None,
                    help=("output parquet path; default "
                          "predictions/joint_stat_samples_<date>.parquet"))
    ap.add_argument("--seed", type=int, default=None,
                    help="optional RNG seed for reproducibility")
    ap.add_argument("--max-keys", type=int, default=None,
                    help="cap on (player, game) pairs (smoke testing)")
    args = ap.parse_args()

    target_date = args.date
    n_draws = int(args.n_draws)

    if not os.environ.get("BDL_API_KEY", "").strip():
        print("FATAL: BDL_API_KEY not set", file=sys.stderr)
        return 2

    out_path = Path(
        args.out or PRED_DIR / f"joint_stat_samples_{target_date}.parquet"
    )
    manifest_path = out_path.parent / (out_path.stem + ".manifest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    state = _build_pipeline_state(target_date)

    all_props_path = Path(
        args.all_props or PRED_DIR / f"all_props_{target_date}.parquet"
    )

    if args.slate_source == "all_props":
        if not all_props_path.exists():
            print(f"FATAL: {all_props_path} missing")
            return 1
        keys = _slate_keys_from_all_props(all_props_path)
        slate_label = str(all_props_path.relative_to(REPO_ROOT))
    else:
        keys = _slate_keys_from_recent_rosters(
            state, target_date,
            max_players_per_team=args.max_players_per_team,
        )
        slate_label = (
            f"recent_rosters(max_players_per_team="
            f"{args.max_players_per_team})"
        )

    if args.max_keys is not None:
        keys = keys[: int(args.max_keys)]

    print("=" * 72)
    print(f"build_joint_stat_samples — date={target_date} n_draws={n_draws}")
    print(f"  slate source : {slate_label}")
    print(f"  parquet out  : {out_path}")
    print(f"  manifest out : {manifest_path}")
    print("=" * 72)
    print(f"  slate (player_id, game_id) pairs: {len(keys)}")

    if not keys:
        print("  WARN: empty slate — nothing to compute.")
        return 1

    fg3m_model = _fg3m_hurdle_model(required=False)
    fg3m_loaded = fg3m_model is not None

    rng = np.random.default_rng(args.seed)

    rows: list[dict] = []
    skipped = 0
    produced_pairs = 0
    for i, (pid, gid) in enumerate(keys):
        produced = _samples_for_player_game(
            pid, gid, target_date=target_date, state=state,
            fg3m_model=fg3m_model, n_draws=n_draws, rng=rng,
        )
        if not produced:
            skipped += 1
            continue
        rows.extend(produced)
        produced_pairs += 1
        if (i + 1) % 25 == 0:
            print(f"    progress: {i + 1}/{len(keys)} pairs  "
                  f"(rows so far: {len(rows)})")

    print(f"\n  produced rows: {len(rows)}")
    print(f"  produced (player, game) pairs: {produced_pairs}")
    print(f"  skipped (player, game): {skipped}")
    if not rows:
        print("  WARN: no rows produced — leaving outputs untouched.")
        return 1

    df = pd.DataFrame(rows)
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        print(f"FATAL: output missing columns: {sorted(missing)}")
        return 1
    df = df[EXPECTED_COLUMNS]
    df.to_parquet(out_path, index=False)
    print(f"\n  wrote {out_path}")

    _write_manifest(
        manifest_path=manifest_path,
        target_date=target_date,
        n_draws=n_draws,
        rows_written=len(rows),
        player_game_count=produced_pairs,
        rng_seed=args.seed,
        slate_source=args.slate_source,
        max_players_per_team=args.max_players_per_team,
        fg3m_loaded=fg3m_loaded,
    )
    print(f"  wrote {manifest_path}")
    print(f"\nMILESTONE_3_DISPATCHER_RUN_OK ({_now_utc_iso()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
