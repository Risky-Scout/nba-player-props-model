"""Generate model-only PMFs for the player-stat grid for a given date.

Phase 12 Part G. Produces TOV (and on demand, every other supported stat)
PMFs for every player in tonight's slate, **independent of whether BDL
sells a market for that stat**. BDL does not sell turnovers, so the
production pipeline (`scripts/predict.py`) never emits TOV rows; this
script closes that gap.

The output is consumed by `scripts/build_daily_pmf_delivery.py`, which
merges the TOV rows into the canonical MODEL_ONLY parquet under
`deliveries/{date}/canonical_source/`.

Design
------
We reuse the production calibrators and feature builders. We never
fabricate. Specifically:

  - The slate's (player_id, game_id) universe comes from
    `predictions/all_props_{date}.parquet` (the same set the existing
    delivery is built on).
  - For each (player, game) we rebuild the same minutes distribution
    and feature row that `scripts/predict.py` would build (exact module
    calls — no shortcut).
  - We invoke `nba_props_model.pipelines.pmf_predict.build_prop_pmfs()`
    which returns a dict of `PropPMF` keyed by stat. That helper applies
    the role-aware Phase-8 calibrator (`pmf_cal_role_tov.pkl`) when
    present. The failed Phase 10D / 10D.2 overlays live in
    `artifacts/phase10d*` and are NOT loaded by this code path.

Hard rules (mirroring `docs/daily_pmf_delivery_spec.md`):
  - Model-only PMFs are canonical.
  - No market anchoring.
  - No fabrication: a player without a feature row is dropped.
  - TOV-status tag: `current_phase8`.

CLI:
    python scripts/build_stat_grid_pmfs.py --date 2026-04-29
    python scripts/build_stat_grid_pmfs.py --date 2026-04-29 \
        --stats tov pts reb ast fg3m
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

# Silence sklearn/numpy chatter that the prediction modules emit.
warnings.filterwarnings("ignore")

from nba_props_model.data.bdl_client import (  # noqa: E402
    get_games, get_game_odds,
    get_injuries, get_advanced_stats_v2,
    build_game_context_map, build_injury_map,
    get_nba_injury_report, merge_injury_sources,
    enrich_game_context_with_snapshots,
)
from nba_props_model.features.engineering import (  # noqa: E402
    build_player_game_features,
    add_interaction_features,
    ALL_TARGETS,
)
from nba_props_model.models.minutes import minutes_distribution  # noqa: E402
from nba_props_model.features.availability_asof import (  # noqa: E402
    load_availability_table as _load_availability_table,
    AvailabilityBuilder as _AvailabilityBuilder,
)
from nba_props_model.pipelines.pmf_predict import build_prop_pmfs  # noqa: E402
from nba_props_model.calibration.source_pmf_recalibration import (  # noqa: E402
    load_stat_grid_delivery_recalibrator,
)
from nba_props_model.calibration.role_buckets import role_bucket_features_from_minutes_dist  # noqa: E402
from nba_props_model.paths import MODEL_DIR  # noqa: E402
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402
from nba_props_model.pipelines.player_game_eligibility import (  # noqa: E402
    build_current_market_player_signal,
    build_player_game_eligibility,
    assert_no_ineligible_pmfs,
)
from nba_props_model.pipelines._stat_grid_eligibility_gate import (  # noqa: E402
    build_eligibility_map,
)


PRED_DIR = REPO_ROOT / "predictions"
DATA_DIR = REPO_ROOT / "data"

_AVAILABILITY_COLS = (
    "prob_active", "days_since_last_played", "is_returning_from_absence",
    "minutes_restriction_flag", "num_teammates_out_total",
    "vacated_minutes_guard", "vacated_minutes_wing", "vacated_minutes_big",
    "teammate_out_count_guard", "teammate_out_count_wing",
    "teammate_out_count_big", "vacated_fga_total",
)
_INACTIVE_STATUSES = {"out", "out for season", "injured", "inactive", "doubtful"}

# M8.6: full 12-stat mission canonical universe — 7 base + 5 combos
# (stocks/pa/pr/ra/pra). build_prop_pmfs must return joint-sample combo
# PMFs for mission combos (no legacy convolution / independence tags).
DEFAULT_STATS = MISSION_REQUIRED_TARGETS_CANONICAL
ALLOWED_STATS = MISSION_REQUIRED_TARGETS_CANONICAL

# M8.6: guard constants. Mission combos MUST come from joint-sample-derived
# PMFs and MUST NOT carry legacy convolution/independence model_version tags.
M8_5_MISSION_COMBOS = frozenset({"stocks", "pa", "pr", "ra", "pra"})
M8_5_LEGACY_COMBO_TAGS = ("stocks_conv_v1", "combo_independence_v1")


def _display_path(path: Path) -> str:
    """Return repo-relative path when possible, otherwise absolute path."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def _now_utc_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _fg3m_hurdle_model(*, required: bool = False):
    """Load the FG3M hurdle model artifact.

    If fg3m was requested, missing/unloadable artifacts are a hard failure.
    Silent FG3M drops make Derek/WoO PMF packages incomplete.
    """
    path = MODEL_DIR / "fg3m_hurdle.pkl"

    if not path.exists():
        if required:
            raise SystemExit(f"FATAL: missing FG3M hurdle artifact: {path}")
        return None

    try:
        from nba_props_model.models.fg3m_hurdle import FG3MHurdleModel
        return FG3MHurdleModel.load(str(path))
    except Exception as e:
        if required:
            raise SystemExit(
                f"FATAL: failed to load FG3M hurdle artifact {path}: "
                f"{type(e).__name__}: {e}"
            )
        return None



def _pmf_to_dict(pmf: np.ndarray) -> dict:
    """Serialize a PMF as `{int_value: prob}` so it round-trips through
    parquet/jsonl/csv without numpy quirks."""
    arr = np.asarray(pmf, dtype=float).ravel()
    s = arr.sum()
    if s > 0 and np.isfinite(s):
        arr = arr / s
    return {int(k): float(v) for k, v in enumerate(arr) if v > 0.0}


def _pmf_summary(pmf: np.ndarray) -> dict:
    arr = np.asarray(pmf, dtype=float).ravel()
    s = float(arr.sum())
    if s > 0 and np.isfinite(s):
        norm = arr / s
    else:
        norm = arr
    K = len(norm)
    ks = np.arange(K)
    mean = float((norm * ks).sum())
    cdf = np.cumsum(norm)
    median = int(np.searchsorted(cdf, 0.5)) if K > 0 else 0
    mode = int(np.argmax(norm)) if K > 0 else 0
    return {"mean": mean, "median": median, "mode": mode,
            "support_max": int(K - 1) if K > 0 else 0,
            "pmf_sum": s}


def _slate_keys_from_all_props(all_props_path: Path) -> list[tuple[int, int]]:
    """Read the existing all_props parquet and return the unique
    `(player_id, game_id)` slate. Drops rows with NaN keys."""
    df = pd.read_parquet(all_props_path, columns=["player_id", "game_id"])
    df = df.dropna(subset=["player_id", "game_id"]).copy()
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    pairs = set(zip(df["player_id"].tolist(), df["game_id"].tolist()))
    return sorted(pairs)


def _slate_keys_from_recent_rosters(
    state: dict,
    target_date: str,
    *,
    max_players_per_team: int = 18,
    recent_days: int = 120,
) -> list[tuple[int, int]]:
    """Build a model-only slate without depending on market/all_props rows.

    Uses today's BDL game slate plus recent team roster history. Inactive
    players are filtered by the same injury map used later by the PMF row
    builder. Feature/minutes construction still decides whether a player is
    actually computable; this function only supplies candidate player-game
    pairs.
    """
    stats_df = state.get("stats_df")
    games_by_id = state.get("games_by_id", {})
    inactive_ids = set(state.get("inactive_player_ids", set()))

    if stats_df is None or stats_df.empty or not games_by_id:
        return []

    required = {"player_id", "team_id", "game_date"}
    if not required.issubset(set(stats_df.columns)):
        return []

    df = stats_df.copy()
    df["game_date_dt"] = pd.to_datetime(df["game_date"], errors="coerce")
    df["player_id_num"] = pd.to_numeric(df["player_id"], errors="coerce")
    df["team_id_num"] = pd.to_numeric(df["team_id"], errors="coerce")
    df = df.dropna(subset=["game_date_dt", "player_id_num", "team_id_num"])

    target_ts = pd.Timestamp(target_date)
    df = df[df["game_date_dt"] < target_ts]
    if df.empty:
        return []

    recent_cutoff = target_ts - pd.Timedelta(days=int(recent_days))
    minutes_col = next(
        (c for c in ("minutes", "min", "mp", "minutes_played") if c in df.columns),
        None,
    )

    keys: set[tuple[int, int]] = set()

    for gid, game in sorted(games_by_id.items()):
        home_id = (
            (game.get("home_team") or {}).get("id")
            or game.get("home_team_id")
        )
        visitor_id = (
            (game.get("visitor_team") or {}).get("id")
            or game.get("visitor_team_id")
        )

        for team_id in (home_id, visitor_id):
            if team_id is None:
                continue

            try:
                team_id_int = int(team_id)
            except Exception:
                continue

            team_df = df[df["team_id_num"] == team_id_int].copy()
            if team_df.empty:
                continue

            recent = team_df[team_df["game_date_dt"] >= recent_cutoff].copy()
            if recent.empty:
                recent = team_df.copy()

            grouped = recent.groupby("player_id_num").agg(
                last_game=("game_date_dt", "max"),
                recent_games=("game_date_dt", "count"),
            )

            if minutes_col is not None:
                recent[minutes_col] = pd.to_numeric(recent[minutes_col], errors="coerce")
                grouped["recent_minutes"] = (
                    recent.groupby("player_id_num")[minutes_col]
                    .mean()
                    .fillna(0.0)
                )
            else:
                grouped["recent_minutes"] = 0.0

            grouped = grouped.sort_values(
                ["recent_minutes", "recent_games", "last_game"],
                ascending=[False, False, False],
            )

            for pid_float in grouped.head(int(max_players_per_team)).index:
                pid = int(pid_float)
                if pid in inactive_ids:
                    continue
                keys.add((pid, int(gid)))

    return sorted(keys)



def _build_pipeline_state(target_date: str) -> dict:
    """Mirror predict.py's setup just enough to compute one
    minutes_distribution + feature_row per (player, game). Returns a
    dict of state objects used by the per-player loop."""
    print("  loading historical inputs…")
    stats_path = DATA_DIR / "player_game_stats.parquet"
    adv_path = DATA_DIR / "advanced_stats.parquet"
    if not stats_path.exists():
        raise SystemExit(f"missing: {stats_path}")
    stats_df = pd.read_parquet(stats_path)
    adv_df = pd.read_parquet(adv_path) if adv_path.exists() else pd.DataFrame()

    adv_by_player: dict[int, list] = {}
    if not adv_df.empty:
        for pid, grp in adv_df.groupby("player_id"):
            adv_by_player[int(pid)] = grp.sort_values("game_date").to_dict("records")

    print(f"  fetching BDL games for {target_date}…")
    games = get_games(start_date=target_date, end_date=target_date)
    print(f"    {len(games)} games")

    today_odds_raw = get_game_odds(dates=[target_date])
    ctx_map = build_game_context_map(today_odds_raw) if today_odds_raw else {}
    ctx_map = enrich_game_context_with_snapshots(ctx_map, games, target_date)

    print("  fetching injuries (BDL + NBA official)…")
    injury_raw = get_injuries()
    injury_map = build_injury_map(injury_raw) if injury_raw else {}
    nba_report = get_nba_injury_report()
    injury_report_fetched_at_utc = _now_utc_iso()
    injury_freshness_status = "fresh" if nba_report else ("fresh" if injury_raw else "unknown")
    injury_context_source = (
        "bdl_plus_nba_official" if nba_report
        else ("bdl_injuries_only" if injury_raw else "none")
    )
    injury_map = merge_injury_sources(injury_map, nba_report, stats_df)
    inactive_ids = {
        int(pid) for pid, info in injury_map.items()
        if str(info.get("status", "")).lower().strip() in _INACTIVE_STATUSES
    }
    print(f"    injury_map={len(injury_map)} inactive={len(inactive_ids)}")

    # Availability lookup (for the state-aware minutes model).
    availability_lookup: dict[tuple[int, str], dict] = {}
    availability_builder = None
    try:
        av_df = _load_availability_table()
        today_mask = av_df["game_date"].astype(str).str[:10] == target_date
        av_today = av_df[today_mask]
        if av_today.empty:
            availability_builder = _AvailabilityBuilder.from_data_dir()
        else:
            for r in av_today.itertuples(index=False):
                availability_lookup[(int(r.player_id), str(r.game_date))] = {
                    c: getattr(r, c, None) for c in _AVAILABILITY_COLS
                }
    except FileNotFoundError:
        availability_builder = None

    av_path = DATA_DIR / "player_availability_asof.parquet"
    suppress_inactive_risk = False
    availability_table_freshness = "unknown"
    availability_age_hours: float | None = None
    if av_path.exists():
        availability_age_hours = (time.time() - av_path.stat().st_mtime) / 3600.0
        if availability_age_hours > 6.0:
            availability_table_freshness = "stale"
            suppress_inactive_risk = True
        else:
            availability_table_freshness = "fresh"
    else:
        availability_table_freshness = "missing"
        suppress_inactive_risk = True
    if os.environ.get("NBA_FORCE_AVAILABILITY_FRESH", "").strip() == "1":
        suppress_inactive_risk = False
        availability_table_freshness = "forced_fresh"

    if suppress_inactive_risk:
        print(
            "  availability guard: suppress_inactive_risk=True "
            f"freshness={availability_table_freshness!r} "
            f"age_hours={availability_age_hours}"
        )

    games_by_id = {int(g["id"]): g for g in games if g.get("id")}

    return {
        "stats_df": stats_df,
        "adv_by_player": adv_by_player,
        "games_by_id": games_by_id,
        "ctx_map": ctx_map,
        "injury_map": injury_map,
        "inactive_player_ids": inactive_ids,
        "availability_lookup": availability_lookup,
        "availability_builder": availability_builder,
        "injury_freshness_status": injury_freshness_status,
        "injury_context_source": injury_context_source,
        "injury_report_fetched_at_utc": injury_report_fetched_at_utc,
        "suppress_inactive_risk": suppress_inactive_risk,
        "availability_table_freshness": availability_table_freshness,
        "availability_table_age_hours": availability_age_hours,
    }


def _row_for_player_game(player_id: int, gid: int, *, target_date: str,
                            state: dict, fg3m_model, stats: list[str], recalibrator=None,
                            eligibility_row=None) -> list[dict]:
    """Compute PMFs for one (player, game). Returns list of canonical
    delivery rows — one per stat in `stats` — or an empty list if the
    feature build / minutes model fails.

    ``eligibility_row`` (dict | None): when provided, the canonical
    eligibility / minutes columns are stamped onto every emitted PMF
    row so downstream (canonical_source, review, derek) can rely on
    them without re-deriving. The upstream eligibility gate guarantees
    that ``eligibility_row['player_game_eligible']`` is True for every
    (player_id, game_id) reaching this function.
    """
    if player_id in state["inactive_player_ids"]:
        return []
    game = state["games_by_id"].get(gid)
    if not game:
        return []
    home_id = (game.get("home_team") or {}).get("id") or game.get("home_team_id")
    vis_id = (game.get("visitor_team") or {}).get("id") or game.get("visitor_team_id")
    home_nm = (game.get("home_team") or {}).get("full_name", "")
    vis_nm = (game.get("visitor_team") or {}).get("full_name", "")
    glabel = f"{vis_nm} @ {home_nm}"
    ctx = state["ctx_map"].get(gid, {})

    pdata = state["stats_df"][state["stats_df"]["player_id"] == player_id].copy()
    if pdata.empty:
        return []
    pdata["game_date"] = pd.to_datetime(pdata["game_date"]).dt.strftime("%Y-%m-%d")
    if len(pdata[pdata["season"] == 2025]) < 5:
        # Mirror predict.py's MIN_GAMES_SEASON gate (5).
        return []

    team_id = int(pdata.iloc[-1]["team_id"] or 0)
    is_home = int(team_id == home_id)
    opp_id = vis_id if is_home else home_id

    padv = sorted(
        state["adv_by_player"].get(player_id, []),
        key=lambda x: x.get("game_date", pd.Timestamp("2000")),
    )
    padv_prior = [
        r for r in padv
        if pd.Timestamp(r.get("game_date", pd.Timestamp("2000")))
        < pd.Timestamp(target_date)
    ]

    try:
        base = build_player_game_features(
            player_id=player_id, prior_stats=pdata, prior_adv=padv_prior,
            game_context=ctx, is_home=bool(is_home),
            target_date=target_date, team_id=team_id,
            all_stats_df=state["stats_df"], injury_map=state["injury_map"],
            opp_team_id=opp_id,
        )
    except Exception:
        return []

    avail = None
    if state["availability_lookup"]:
        avail = state["availability_lookup"].get((player_id, target_date))
    elif state["availability_builder"] is not None:
        try:
            pairs = pd.DataFrame([{
                "player_id": player_id, "team_id": team_id,
                "game_date": target_date,
            }])
            fts = state["availability_builder"].features_for(pairs)
            if len(fts):
                avail = {c: fts.iloc[0].get(c) for c in _AVAILABILITY_COLS}
        except Exception:
            avail = None

    try:
        mp_dist = minutes_distribution(
            prior_stats=pdata, game_context=ctx,
            is_home=bool(is_home), target_date=target_date, team_id=team_id,
            all_stats_df=state["stats_df"], injury_map=state["injury_map"],
            availability=avail,
        )
    except Exception:
        return []
    if mp_dist is None:
        return []

    try:
        role_features = role_bucket_features_from_minutes_dist(
            mp_dist,
            suppress_inactive_risk=bool(state.get("suppress_inactive_risk")),
        )
    except Exception:
        role_features = {}

    role_bucket = role_features.get("role_bucket")
    role_source = "derived_from_projected_minutes" if role_bucket else "missing"
    mp_bucket_val = role_features.get("mp_bucket")
    usage_bucket_val = base.get("usage_bucket") if isinstance(base, dict) else None
    minutes_mean = role_features.get("minutes_mean")
    minutes_q50 = role_features.get("minutes_q50")
    p_inactive_used = role_features.get("p_inactive_used", role_features.get("p_inactive"))
    if p_inactive_used is None:
        p_inactive_used = getattr(mp_dist, "p_inactive", None)

    # Build the PMF dict for this player. The interaction features added
    # in predict.py are per-stat; build_prop_pmfs only needs the base
    # feature row (it pulls per-stat sub-features internally).
    rng = np.random.default_rng(hash(("stat_grid", player_id, gid)) & 0xFFFFFFFF)
    try:
        pmf_pack = build_prop_pmfs(
            minutes_dist=mp_dist, feature_row=base,
            fg3m_hurdle_model=fg3m_model, rng=rng,
        )
    except Exception:
        return []

    player_name = str(pdata.iloc[-1].get("player_name", f"Player {player_id}"))
    out_rows: list[dict] = []
    for stat in stats:
        prop = pmf_pack.get(stat)
        if prop is None or prop.pmf is None:
            # M8.5: per-player missing for mission combos is a
            # structural error, not a data-sparsity skip. The joint-
            # sample combo path in pmf_predict.build_prop_pmfs
            # produces all the mission combos or raises; an absent
            # combo here means the function was reverted or has a bug.
            if stat in M8_5_MISSION_COMBOS:
                raise SystemExit(
                    f"FATAL: STAT_GRID_MISSION_COMBO_MISSING "
                    f"player_id={player_id} game_id={gid} stat={stat}: "
                    f"mission combo absent from build_prop_pmfs output. "
                    f"See M8.5."
                )
            continue
        # M8.5: defense-in-depth — mission combos must NOT carry the
        # legacy convolution/independence model_version tags. If the
        # joint-sample patch in pmf_predict is reverted or bypassed,
        # this guard catches it before any delivery is written.
        if stat in M8_5_MISSION_COMBOS:
            mv = str(prop.model_version)
            for legacy in M8_5_LEGACY_COMBO_TAGS:
                if legacy in mv:
                    raise SystemExit(
                        f"FATAL: STAT_GRID_LEGACY_COMBO_PATH "
                        f"player_id={player_id} game_id={gid} "
                        f"stat={stat} model_version={mv!r}: mission "
                        f"combo emitted via legacy convolution/"
                        f"independence path. Must use "
                        f"joint_sampler_v1+joint_combo_pmf_v1. See M8.5."
                    )
        pmf_out = np.asarray(prop.pmf, dtype=float).ravel()
        recal_meta = {}
        if recalibrator is not None:
            try:
                pmf_out, recal_meta = recalibrator.apply(
                    pmf_out, stat=stat, role_bucket=role_bucket
                )
            except Exception as e:
                raise SystemExit(
                    f"FATAL: STAT_GRID_SOURCE_RECALIBRATION_FAILED "
                    f"player_id={player_id} game_id={gid} stat={stat} "
                    f"role_bucket={role_bucket}: {type(e).__name__}: {e}"
                )

        s = _pmf_summary(pmf_out)
        recal_applied = bool(recal_meta.get("source_recalibration_applied", False))
        # Eligibility row carries the canonical-shape minutes/role/
        # market columns the upstream eligibility gate computed. Stamp
        # them onto every emitted PMF row so canonical_source can be
        # validated by a simple column-presence + truthiness check.
        elig = eligibility_row or {}
        out_rows.append({
            "player_id": int(player_id),
            "player_name": player_name,
            "team_id": int(team_id) if team_id else None,
            "game_id": int(gid),
            "game": glabel,
            "is_home": bool(is_home),
            "opp_team_id": int(opp_id) if opp_id else None,
            "role_bucket": role_bucket,
            "role_source": role_source,
            "mp_bucket": mp_bucket_val,
            "usage_bucket": usage_bucket_val,
            "slate_date": str(target_date),
            "minutes_mean": elig.get("minutes_mean", minutes_mean),
            "minutes_q50": elig.get("minutes_p50", minutes_q50),
            "minutes_p10": elig.get("minutes_p10"),
            "minutes_p50": elig.get("minutes_p50", minutes_q50),
            "minutes_p90": elig.get("minutes_p90"),
            "minutes_std": elig.get("minutes_std"),
            "p_inactive_used": elig.get("p_inactive_used", p_inactive_used),
            "rotation_probability": elig.get("rotation_probability"),
            "starter_probability": elig.get("starter_probability"),
            "projected_role": elig.get("projected_role"),
            "player_game_eligible": bool(elig.get("player_game_eligible", True)),
            "eligibility_reason": elig.get("eligibility_reason"),
            "has_current_market_line": bool(elig.get("has_current_market_line", False)),
            "minutes_source": elig.get("minutes_source"),
            "minutes_model_version": elig.get("minutes_model_version"),
            "injury_freshness_status": state.get("injury_freshness_status"),
            "injury_context_source": state.get("injury_context_source"),
            "injury_report_fetched_at_utc": state.get("injury_report_fetched_at_utc"),
            "availability_table_freshness": state.get("availability_table_freshness"),
            "availability_table_age_hours": state.get("availability_table_age_hours"),
            "suppress_inactive_risk": bool(state.get("suppress_inactive_risk")),
            "availability_blocks_market_superiority": bool(
                state.get("suppress_inactive_risk")
            ),
            "stat": stat,
            "side": "MODEL_ONLY",
            "line": None,
            "odds": None,
            "model_version": prop.model_version,
            "calibrated": bool(prop.calibrated or recal_applied),
            "source_recalibration_applied": recal_applied,
            "source_recalibration_version": recal_meta.get("source_recalibration_version"),
            "source_recalibration_stage": recal_meta.get("source_recalibration_stage"),
            "source_recalibration_role_bucket": role_bucket,
            "pmf": json.dumps(_pmf_to_dict(pmf_out)),
            "pmf_summary_mean": s["mean"],
            "pmf_summary_median": s["median"],
            "pmf_summary_mode": s["mode"],
            "support_max": s["support_max"],
            "pmf_sum_error": float(abs(s["pmf_sum"] - 1.0)),
            "tov_status": (
                "current_phase8" if stat == "tov" else None
            ),
            "tov_status_reason": (
                "Phase 10D/10D.2 overlay failed independent validation; "
                "see docs/phase11_tov_structural_refit_plan.md"
                if stat == "tov" else None
            ),
            "line_is_real": False,
            "scored_at_utc": _now_utc_iso(),
        })
    return out_rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                     help="YYYY-MM-DD slate date (US/Eastern)")
    ap.add_argument("--stats", nargs="+", default=list(DEFAULT_STATS),
                     choices=list(ALLOWED_STATS),
                     help=("stats to emit (default: 12-stat mission "
                           "canonical [pts reb ast fg3m tov stl blk "
                           "stocks pa pr ra pra])"))
    ap.add_argument("--slate-source", choices=["recent_rosters", "all_props"],
                    default="recent_rosters",
                    help=("player-game slate source; default recent_rosters "
                          "keeps PMF-only delivery independent of market rows"))
    ap.add_argument("--max-players-per-team", type=int, default=18,
                    help="recent-roster candidates per team for PMF-only slate")
    ap.add_argument("--all-props",
                     default=None,
                     help=("optional path to predictions/all_props_{date}.parquet; "
                           "used only with --slate-source all_props"))
    ap.add_argument("--out",
                     default=None,
                     help=("output parquet path; "
                            "default predictions/stat_grid_{date}.parquet"))
    ap.add_argument(
        "--feature-snapshot",
        default=None,
        help="Optional player-prop feature snapshot parquet to merge on player_id/stat.",
    )
    args = ap.parse_args()

    target_date = args.date
    if not os.environ.get("BDL_API_KEY", "").strip():
        print("FATAL: BDL_API_KEY not set", file=sys.stderr)
        return 2

    out_path = Path(args.out or PRED_DIR / f"stat_grid_{target_date}.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    state = _build_pipeline_state(target_date)

    all_props_path = Path(
        args.all_props or PRED_DIR / f"all_props_{target_date}.parquet"
    )

    if args.slate_source == "all_props":
        if not all_props_path.exists():
            print(f"FATAL: {all_props_path} missing and --slate-source all_props was requested")
            return 1
        keys = _slate_keys_from_all_props(all_props_path)
        slate_source_label = str(all_props_path.relative_to(REPO_ROOT))
    else:
        keys = _slate_keys_from_recent_rosters(
            state,
            target_date,
            max_players_per_team=args.max_players_per_team,
        )
        slate_source_label = (
            f"recent_rosters(max_players_per_team={args.max_players_per_team})"
        )

    print("=" * 72)
    print(f"build_stat_grid_pmfs — date={target_date} stats={args.stats}")
    print(f" slate source: {slate_source_label}")
    print(f" output : {_display_path(out_path)}")
    print("=" * 72)

    print(" slate (player_id, game_id) pairs: " + str(len(keys)))
    # Upstream player-game eligibility gate. Filter the slate to player-games
    # passing the rule (market line OR projected starter/rotation OR
    # minutes_mean >= 12) BEFORE any PMF is built. See
    # src/nba_props_model/pipelines/player_game_eligibility.py for the rule.
    eligibility_by_key = build_eligibility_map(REPO_ROOT, target_date, keys)
    eligible_keys = [k for k in keys if k in eligibility_by_key]
    print("  eligibility-filtered slate kept " + str(len(eligible_keys))
          + " of " + str(len(keys)) + " candidates")
    if not eligible_keys:
        print(" WARN: zero player-games passed eligibility; nothing to compute.")
        return 1
    if not keys:
        print(" WARN: empty slate — nothing to compute.")
        return 1

    fg3m_model = _fg3m_hurdle_model(required=("fg3m" in args.stats)) if "fg3m" in args.stats else None

    recalibrator = load_stat_grid_delivery_recalibrator()
    print(
        "  source recalibrator: "
        f"enabled={getattr(recalibrator, 'enabled', None)} "
        f"version={getattr(recalibrator, 'version', None)}"
    )

    rows: list[dict] = []
    skipped = 0
    for pid, gid in eligible_keys:
        produced = _row_for_player_game(
            pid, gid, target_date=target_date, state=state,
            fg3m_model=fg3m_model, stats=args.stats,
            recalibrator=recalibrator,
            eligibility_row=eligibility_by_key.get((pid, gid)),
        )
        if not produced:
            skipped += 1
            continue
        rows.extend(produced)

    print(f"\n  produced rows: {len(rows)}")
    print(f"  skipped (player, game): {skipped}")
    if not rows:
        print("  WARN: no rows produced — leaving output untouched.")
        return 1

    df = pd.DataFrame(rows)
    assert_no_ineligible_pmfs(df, label="stat_grid_pmfs")
    if args.feature_snapshot:
        snap_path = Path(args.feature_snapshot)
        if not snap_path.is_absolute():
            snap_path = REPO_ROOT / snap_path
        if not snap_path.is_file():
            raise SystemExit(f"FATAL: feature snapshot missing: {snap_path}")
        snap_df = pd.read_parquet(snap_path)
        join_cols = [c for c in ("player_id", "stat") if c in snap_df.columns and c in df.columns]
        if len(join_cols) < 2:
            raise SystemExit(
                "FATAL: feature snapshot missing join keys player_id/stat for parity merge"
            )
        keep_cols = [c for c in snap_df.columns if c not in set(df.columns) or c in ("player_id", "stat")]
        snap_df = snap_df[keep_cols].drop_duplicates(subset=join_cols)
        df = df.merge(snap_df, on=join_cols, how="left")
        df["feature_snapshot_attached"] = True
        df["feature_snapshot_path"] = str(snap_path)
    per_stat_counts = df.groupby('stat').size().to_dict()
    print(f"  per-stat counts:\n{df.groupby('stat').size().to_string()}")

    # M8.6: hard gate — every requested stat must have at least one
    # emitted row. Zero coverage across the entire slate for any
    # requested stat is a structural failure (do not silently ship
    # sub-12 coverage when 12 are requested).
    requested = set(args.stats)
    emitted = set(per_stat_counts.keys())
    missing_at_run_level = sorted(requested - emitted)
    if missing_at_run_level:
        raise SystemExit(
            f"FATAL: STAT_GRID_EMISSION_INCOMPLETE no rows emitted "
            f"for requested stats={missing_at_run_level}; "
            f"requested={sorted(requested)} emitted={sorted(emitted)} "
            f"per_stat_counts={per_stat_counts}. See M8.4 patch "
            "requirement."
        )

    df.to_parquet(out_path, index=False)
    print(f"\nwrote {_display_path(out_path)}  ({_now_utc_iso()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
