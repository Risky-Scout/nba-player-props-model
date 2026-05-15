#!/usr/bin/env python3
"""Daily projected minutes + rotation artifact builder.

Writes:
    artifacts/minutes_predictions/{slate_date}/minutes_predictions.parquet
        FULL player-game universe (every active roster slot the minutes
        model can produce a prediction for — INCLUDING deep-bench rows).
        This artifact powers the upstream eligibility gate but must NEVER
        be treated as a publication-ready universe.
    artifacts/minutes_predictions/{slate_date}/minutes_predictions_eligible.parquet
        Filtered universe restricted to rows that satisfy the
        ``player_game_eligibility`` rule (current market line OR
        starter_probability >= 0.50 OR rotation_probability >= 0.50 OR
        minutes_mean >= 12). Adds two columns to the base schema:
        ``has_current_market_line`` (bool) and ``eligibility_reason``
        (one of ``current_market_line``, ``starter_probability``,
        ``rotation_probability``, ``minutes_floor``). This is the artifact
        downstream publication code (canonical, review, Derek) must
        derive its player universe from.
    artifacts/minutes_predictions/{slate_date}/manifest.json
        Both artifact paths + universe / eligible row counts.

This is the upstream signal used by the player-game eligibility gate
(see ``src/nba_props_model/pipelines/player_game_eligibility.py``). It is
the canonical answer to "who plays tonight, in what role, and for how
many minutes" — derived from the state-aware minutes model in
``src/nba_props_model/models/minutes.py`` plus injury / availability /
lineup features, with current market quotes as a soft signal at the
eligibility-gate layer (NOT here).

Run mode ``morning_expected`` is what the morning publish pipeline calls
this script with. ``close_lock`` is the late evening counterpart that
incorporates confirmed lineups.

Required feature-row source (searched in order):
    data/features/player_game_features_{slate_date}_{run_mode}.parquet
    data/features/injury_lineup_features_{slate_date}_{run_mode}.parquet
    data/features/player_game_features_{slate_date}_close_lock.parquet

Fails with a clear message if none of them exists. We do NOT fall back
to silently fetching BDL from inside this script — feature regeneration
is its own pipeline stage and a missing feature parquet is a data-
readiness blocker.

Output columns (exactly this contract — the eligibility gate and
validator read it):
    slate_date, game_id, player_id, player_name, team, opponent,
    is_home, rotation_probability, starter_probability, projected_role,
    minutes_mean, minutes_p10, minutes_p50, minutes_p90, minutes_std,
    p_inactive_used, minutes_source, minutes_model_version,
    feature_snapshot_id, lineup_snapshot_id, injury_freshness_status,
    lineup_freshness_status, inferred_at_utc

Internal validation hard-fails on:
    duplicate slate_date/game_id/player_id rows; null minutes_mean;
    null minutes_p10/p50/p90; null rotation_probability /
    starter_probability; non-finite minutes; minutes outside [0, 60];
    probabilities outside [0, 1].
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

warnings.filterwarnings("ignore")

from nba_props_model.models.minutes import (  # noqa: E402
    MinutesDistribution,
    minutes_distribution,
    projected_role_from_minutes_summary,
    role_probabilities_from_minutes_summary,
    summarize_minutes_distribution,
)
from nba_props_model.pipelines.player_game_eligibility import (  # noqa: E402
    ROTATION_MINUTES_FLOOR,
    ROTATION_PROB_FLOOR,
    STARTER_PROB_FLOOR,
    build_current_market_player_signal,
)


REQUIRED_OUTPUT_COLUMNS = [
    "slate_date",
    "game_id",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "is_home",
    "rotation_probability",
    "starter_probability",
    "projected_role",
    "minutes_mean",
    "minutes_p10",
    "minutes_p50",
    "minutes_p90",
    "minutes_std",
    "p_inactive_used",
    "minutes_source",
    "minutes_model_version",
    "feature_snapshot_id",
    "lineup_snapshot_id",
    "injury_freshness_status",
    "lineup_freshness_status",
    "inferred_at_utc",
]


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _file_sha256(p: Path) -> Optional[str]:
    if not p or not p.exists():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_feature_source(slate_date: str, run_mode: str) -> Path:
    # Prefer the player_prop_features snapshot produced by the daily
    # delivery orchestrator (scripts/run_daily_delivery_pipeline.py)
    # via build_player_prop_feature_snapshot.py during the morning
    # publish flow. It carries the same (player_id, game_id) universe
    # and team / is_home identity columns build_minutes_predictions
    # needs, so it is the canonical feature source for the upstream
    # minutes / rotation artifact required by the stat-grid eligibility gate.
    candidates = [
        REPO_ROOT / "data" / "features" / f"player_prop_features_{slate_date}_{run_mode}.parquet",
        REPO_ROOT / "data" / "features" / f"player_game_features_{slate_date}_{run_mode}.parquet",
        REPO_ROOT / "data" / "features" / f"injury_lineup_features_{slate_date}_{run_mode}.parquet",
        REPO_ROOT / "data" / "features" / f"player_game_features_{slate_date}_close_lock.parquet",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise SystemExit(
        "FATAL: no feature-row source found for slate_date={d}, run_mode={m}. "
        "Searched:\n  - {a}\n  - {b}\n  - {c}\n  - {e}\n"
        "Build features first via scripts/build_player_feature_store.py, "
        "scripts/build_injury_lineup_features.py, or "
        "scripts/build_player_prop_feature_snapshot.py.".format(
            d=slate_date, m=run_mode,
            a=candidates[0].relative_to(REPO_ROOT),
            b=candidates[1].relative_to(REPO_ROOT),
            c=candidates[2].relative_to(REPO_ROOT),
            e=candidates[3].relative_to(REPO_ROOT),
        )
    )


def _team_abbr_lookup() -> dict:
    """Best-effort team_id -> abbreviation map. Reads
    ``data/bdl_team_abbreviations.json`` if present, otherwise falls
    back to an empty dict (team/opponent columns will be None)."""
    p = REPO_ROOT / "data" / "bdl_team_abbreviations.json"
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text())
    except Exception:
        return {}
    out: dict[int, str] = {}
    for k, v in (raw or {}).items():
        try:
            out[int(k)] = str(v)
        except Exception:
            continue
    return out


def _player_history(stats_df: pd.DataFrame, player_id: int, target_date: str) -> pd.DataFrame:
    df = stats_df[stats_df["player_id"] == player_id]
    if df.empty:
        return df
    df = df.copy()
    df["game_date_str"] = pd.to_datetime(df["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df[df["game_date_str"] < str(target_date)]
    df["game_date"] = df["game_date_str"]
    return df.drop(columns=["game_date_str"]).sort_values("game_date").reset_index(drop=True)


def _try_minutes_distribution(
    *,
    stats_df: pd.DataFrame,
    player_id: int,
    target_date: str,
    team_id: int,
    is_home: bool,
    availability: Optional[dict],
) -> Optional[MinutesDistribution]:
    """Best-effort live-mode minutes distribution. Returns None if no
    prior history is available for this player."""
    prior = _player_history(stats_df, player_id, target_date)
    if prior.empty:
        return None
    try:
        return minutes_distribution(
            prior_stats=prior,
            game_context={"rest_days": 2, "back_to_back": 0},
            is_home=bool(is_home),
            target_date=target_date,
            team_id=int(team_id) if team_id is not None else -1,
            all_stats_df=stats_df,
            injury_map=None,
            availability=availability,
        )
    except Exception:
        return None


def _synthetic_distribution_from_summary(
    *,
    minutes_mean: float,
    minutes_q50: Optional[float],
    p_inactive: Optional[float],
) -> MinutesDistribution:
    """Build a coherent MinutesDistribution from a minutes-summary fallback.

    Used when no prior-game history is available for the player (rookie /
    very-recent acquisition). The shape is the same legacy quantile
    ladder used inside ``_legacy_distribution``; it preserves the mean
    and gives a sensible spread so the eligibility-gate path produces
    stable role probabilities.
    """
    mean = float(minutes_mean if minutes_mean is not None else 0.0)
    p_in = float(np.clip(float(p_inactive if p_inactive is not None else 0.0), 0.0, 1.0))
    q50 = float(minutes_q50 if minutes_q50 is not None else mean)
    sigma = max(2.0, 0.30 * mean)
    limited_q = {
        10: max(0.0, min(24.0, mean - 1.5 * sigma)),
        25: max(0.0, min(24.0, mean - 0.8 * sigma)),
        50: max(0.0, min(24.0, q50)),
        75: max(0.0, min(24.0, mean + 0.8 * sigma)),
        90: max(0.0, min(24.0, mean + 1.5 * sigma)),
    }
    normal_q = {
        10: max(24.0, min(48.0, mean - 1.5 * sigma)),
        25: max(24.0, min(48.0, mean - 0.8 * sigma)),
        50: max(24.0, min(48.0, q50 if q50 >= 24.0 else mean)),
        75: max(24.0, min(48.0, mean + 0.8 * sigma)),
        90: max(24.0, min(48.0, mean + 1.5 * sigma)),
    }
    p_normal = 0.7 if mean >= 24.0 else 0.4
    p_limited = max(0.0, 1.0 - p_in - p_normal)
    total = max(p_in + p_limited + p_normal, 1e-9)
    return MinutesDistribution(
        state_probs=(p_in / total, p_limited / total, p_normal / total),
        limited_quantiles=limited_q,
        normal_quantiles=normal_q,
    )


def _seeded_std_from_distribution(
    dist: MinutesDistribution,
    *,
    slate_date: str,
    game_id: int,
    player_id: int,
) -> float:
    """Per-spec deterministic per-row std fallback when dist.std() is
    not finite. Re-seeds RNG from (slate_date, game_id, player_id)."""
    seed = int(hashlib.md5(
        f"{slate_date}:{game_id}:{player_id}".encode("utf-8")
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    samples = dist.sample(20000, rng=rng)
    return float(np.std(samples))


def _resolve_team(features_row: pd.Series, team_abbr_map: dict) -> tuple[Optional[str], Optional[str], Optional[bool]]:
    """Best-effort team/opponent/is_home resolution from a feature row.

    Prefers team_id -> abbr lookup when team_id is present (player_game /
    injury_lineup feature sources). Falls back to existing `team` /
    `opponent` string columns when the feature source carries them
    directly (canonical-derived player_prop_features snapshot).
    """
    team_id = features_row.get("team_id")
    opp_id = features_row.get("opp_team_id")
    is_home_v = features_row.get("is_home")
    try:
        team_abbr = team_abbr_map.get(int(team_id)) if team_id is not None and not (isinstance(team_id, float) and math.isnan(team_id)) else None
    except Exception:
        team_abbr = None
    try:
        opp_abbr = team_abbr_map.get(int(opp_id)) if opp_id is not None and not (isinstance(opp_id, float) and math.isnan(opp_id)) else None
    except Exception:
        opp_abbr = None
    if team_abbr is None:
        existing = features_row.get("team")
        if isinstance(existing, str) and existing:
            team_abbr = existing
    if opp_abbr is None:
        existing_opp = features_row.get("opponent")
        if isinstance(existing_opp, str) and existing_opp:
            opp_abbr = existing_opp
    if isinstance(is_home_v, float) and math.isnan(is_home_v):
        is_home = None
    else:
        is_home = bool(is_home_v) if is_home_v is not None else None
    return team_abbr, opp_abbr, is_home


def _hash_path(p: Optional[Path]) -> Optional[str]:
    if p is None or not p.exists():
        return None
    return _file_sha256(p)[:16] if _file_sha256(p) else None


def build_minutes_predictions(
    *,
    slate_date: str,
    train_through_date: str,
    run_mode: str,
    stats_df: pd.DataFrame,
    features_df: pd.DataFrame,
    feature_source: Path,
    team_abbr_map: dict,
) -> pd.DataFrame:
    if features_df is None or features_df.empty:
        raise SystemExit(
            "FATAL: feature parquet is empty; no players to predict for slate_date="
            f"{slate_date}"
        )

    keys = ["player_id", "game_id"]
    missing = [c for c in keys if c not in features_df.columns]
    if missing:
        raise SystemExit(
            f"FATAL: feature parquet missing required keys {missing}"
        )

    # One inference row per (player_id, game_id). Feature parquet often has
    # one row per (player, game, stat); dedupe is safe because the minutes /
    # role columns are identical across stats for a player-game.
    fdf = features_df.copy()
    fdf["player_id"] = pd.to_numeric(fdf["player_id"], errors="coerce").astype("Int64")
    fdf["game_id"] = pd.to_numeric(fdf["game_id"], errors="coerce").astype("Int64")
    fdf = fdf.dropna(subset=keys).drop_duplicates(keys, keep="first")

    feature_snapshot_id = _hash_path(feature_source)
    inferred_at = _now_utc_iso()
    rows: list[dict] = []
    minutes_model_version = "state_aware_v1"

    for _, r in fdf.iterrows():
        pid = int(r["player_id"])
        gid = int(r["game_id"])

        team_abbr, opp_abbr, is_home = _resolve_team(r, team_abbr_map)
        team_id_raw = r.get("team_id")
        try:
            team_id = int(team_id_raw) if team_id_raw is not None and not (isinstance(team_id_raw, float) and math.isnan(team_id_raw)) else -1
        except Exception:
            team_id = -1

        dist = _try_minutes_distribution(
            stats_df=stats_df,
            player_id=pid,
            target_date=slate_date,
            team_id=team_id,
            is_home=bool(is_home) if is_home is not None else False,
            availability=None,
        )
        minutes_source = "state_aware_minutes_model"
        if dist is None:
            dist = _synthetic_distribution_from_summary(
                minutes_mean=float(r.get("minutes_mean") or 0.0),
                minutes_q50=(float(r.get("minutes_q50")) if r.get("minutes_q50") is not None and not (isinstance(r.get("minutes_q50"), float) and math.isnan(r.get("minutes_q50"))) else None),
                p_inactive=(float(r.get("p_inactive_used")) if r.get("p_inactive_used") is not None and not (isinstance(r.get("p_inactive_used"), float) and math.isnan(r.get("p_inactive_used"))) else None),
            )
            minutes_source = "feature_row_summary_fallback"

        try:
            summary = summarize_minutes_distribution(dist)
        except RuntimeError as exc:
            raise SystemExit(
                f"FATAL: minutes summary failed for player_id={pid} game_id={gid}: {exc}"
            )

        if not np.isfinite(summary["minutes_std"]):
            summary["minutes_std"] = _seeded_std_from_distribution(
                dist, slate_date=slate_date, game_id=gid, player_id=pid,
            )

        role_probs = role_probabilities_from_minutes_summary(summary)
        projected_role = projected_role_from_minutes_summary(summary)

        rows.append({
            "slate_date": str(slate_date),
            "game_id": gid,
            "player_id": pid,
            "player_name": r.get("player_name"),
            "team": team_abbr,
            "opponent": opp_abbr,
            "is_home": is_home,
            "rotation_probability": float(role_probs["rotation_probability"]),
            "starter_probability": float(role_probs["starter_probability"]),
            "projected_role": projected_role,
            "minutes_mean": float(summary["minutes_mean"]),
            "minutes_p10": float(summary["minutes_p10"]),
            "minutes_p50": float(summary["minutes_p50"]),
            "minutes_p90": float(summary["minutes_p90"]),
            "minutes_std": float(summary["minutes_std"]),
            "p_inactive_used": float(summary["p_inactive_used"]),
            "minutes_source": minutes_source,
            "minutes_model_version": minutes_model_version,
            "feature_snapshot_id": feature_snapshot_id,
            "lineup_snapshot_id": None,
            "injury_freshness_status": r.get("injury_freshness_status"),
            "lineup_freshness_status": r.get("availability_table_freshness") or r.get("lineup_freshness_status"),
            "inferred_at_utc": inferred_at,
        })

    out = pd.DataFrame(rows, columns=REQUIRED_OUTPUT_COLUMNS)
    return out


def validate_minutes_artifact(df: pd.DataFrame, *, slate_date: str) -> None:
    missing = [c for c in REQUIRED_OUTPUT_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(
            f"FATAL: minutes_predictions missing required columns: {missing}"
        )

    if df.empty:
        # Empty slate is itself a blocker; the caller decides whether
        # to fail hard or write the empty manifest.
        return

    dupes = df.duplicated(["slate_date", "game_id", "player_id"]).sum()
    if dupes:
        raise SystemExit(
            f"FATAL: minutes_predictions has duplicate slate_date/game_id/player_id rows: {dupes}"
        )

    for col in [
        "minutes_mean",
        "minutes_p10",
        "minutes_p50",
        "minutes_p90",
        "minutes_std",
        "rotation_probability",
        "starter_probability",
        "p_inactive_used",
    ]:
        bad = df[col].isna().sum() + (~np.isfinite(df[col].astype(float))).sum()
        if int(bad) > 0:
            raise SystemExit(
                f"FATAL: minutes_predictions has {int(bad)} null/non-finite {col} rows"
            )

    out_of_range_minutes = (
        (df["minutes_mean"] < 0.0)
        | (df["minutes_mean"] > 60.0)
        | (df["minutes_p10"] < 0.0)
        | (df["minutes_p10"] > 60.0)
        | (df["minutes_p50"] < 0.0)
        | (df["minutes_p50"] > 60.0)
        | (df["minutes_p90"] < 0.0)
        | (df["minutes_p90"] > 60.0)
    ).sum()
    if int(out_of_range_minutes) > 0:
        raise SystemExit(
            f"FATAL: minutes_predictions has {int(out_of_range_minutes)} rows "
            "with minutes outside [0, 60]"
        )

    bad_probs = (
        (df["rotation_probability"] < 0.0)
        | (df["rotation_probability"] > 1.0)
        | (df["starter_probability"] < 0.0)
        | (df["starter_probability"] > 1.0)
        | (df["p_inactive_used"] < 0.0)
        | (df["p_inactive_used"] > 1.0)
    ).sum()
    if int(bad_probs) > 0:
        raise SystemExit(
            f"FATAL: minutes_predictions has {int(bad_probs)} probability values "
            "outside [0, 1]"
        )


_VALID_ELIGIBILITY_REASONS = (
    "current_market_line",
    "starter_probability",
    "rotation_probability",
    "minutes_floor",
)


def _load_current_market_df(slate_date: str) -> tuple[pd.DataFrame, Optional[Path]]:
    """Locate today's odds snapshot (or fall back to market_comparison) so the
    eligible-view builder can compute ``has_current_market_line``.

    Returns ``(market_df, source_path)``. ``market_df`` is empty if no
    source is available — the eligibility builder then relies on the
    three model-derived floors (starter / rotation / minutes).
    """
    odds_dir = REPO_ROOT / "data" / "odds_api" / "processed" / slate_date
    if odds_dir.exists():
        cands = sorted(odds_dir.glob("odds_pairs_*.parquet"))
        if cands:
            try:
                return pd.read_parquet(cands[-1]), cands[-1]
            except Exception:
                pass
    market_cmp = (
        REPO_ROOT
        / "deliveries"
        / slate_date
        / "wizard_of_odds"
        / "market_comparison.parquet"
    )
    if market_cmp.exists():
        try:
            return pd.read_parquet(market_cmp), market_cmp
        except Exception:
            pass
    return pd.DataFrame(columns=["slate_date", "game_id", "player_id", "line"]), None


def build_eligible_view(
    universe_df: pd.DataFrame,
    *,
    slate_date: str,
    market_df: pd.DataFrame,
) -> pd.DataFrame:
    """Filter the universe down to eligibility-positive rows and append
    ``has_current_market_line`` + ``eligibility_reason``.

    Eligibility rule mirrors
    ``player_game_eligibility.build_player_game_eligibility``:
        has_current_market_line OR
        starter_probability >= 0.50 OR
        rotation_probability >= 0.50 OR
        minutes_mean >= 12.0
    """
    base = universe_df.copy()
    base["slate_date"] = base["slate_date"].astype(str).str[:10]

    sig = build_current_market_player_signal(market_df, slate_date=slate_date)
    if sig is None or sig.empty:
        sig = pd.DataFrame(
            columns=[
                "slate_date",
                "game_id",
                "player_id",
                "has_current_market_line",
                "quoted_stats",
            ]
        )
    else:
        sig = sig.copy()
        sig["slate_date"] = sig["slate_date"].astype(str).str[:10]

    keys = ["slate_date", "game_id", "player_id"]
    sig_int = sig[keys + ["has_current_market_line"]].copy() if not sig.empty else sig.copy()
    if not sig_int.empty:
        sig_int["game_id"] = pd.to_numeric(sig_int["game_id"], errors="coerce").astype("Int64")
        sig_int["player_id"] = pd.to_numeric(sig_int["player_id"], errors="coerce").astype("Int64")
        sig_int = sig_int.dropna(subset=["game_id", "player_id"])

    base["game_id"] = pd.to_numeric(base["game_id"], errors="coerce").astype("Int64")
    base["player_id"] = pd.to_numeric(base["player_id"], errors="coerce").astype("Int64")

    merged = base.merge(sig_int, on=keys, how="left")
    merged["has_current_market_line"] = (
        merged["has_current_market_line"].fillna(False).astype(bool)
    )

    for col in ("minutes_mean", "rotation_probability", "starter_probability"):
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    mask_market = merged["has_current_market_line"]
    mask_starter = merged["starter_probability"].ge(STARTER_PROB_FLOOR).fillna(False)
    mask_rotation = merged["rotation_probability"].ge(ROTATION_PROB_FLOOR).fillna(False)
    mask_minutes = merged["minutes_mean"].ge(ROTATION_MINUTES_FLOOR).fillna(False)

    eligible_mask = mask_market | mask_starter | mask_rotation | mask_minutes
    merged["eligibility_reason"] = np.select(
        [mask_market, mask_starter, mask_rotation, mask_minutes],
        list(_VALID_ELIGIBILITY_REASONS),
        default="not_eligible",
    )

    out = merged.loc[eligible_mask].copy()
    out["game_id"] = out["game_id"].astype("int64")
    out["player_id"] = out["player_id"].astype("int64")
    return out.reset_index(drop=True)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slate-date", required=True, help="YYYY-MM-DD")
    ap.add_argument(
        "--train-through-date",
        required=False,
        default=None,
        help=(
            "YYYY-MM-DD. Metadata stamp for the manifest. "
            "Defaults to --slate-date when omitted (live morning runs do "
            "not retrain the minutes model, so a separate train-through "
            "date is not strictly required)."
        ),
    )
    ap.add_argument("--run-mode", default="morning_expected",
                    help="morning_expected / close_lock / custom label")
    args = ap.parse_args(argv)

    slate_date = args.slate_date
    train_through = args.train_through_date or slate_date
    run_mode = args.run_mode

    feature_source = _find_feature_source(slate_date, run_mode)
    print(f"  feature_source: {feature_source.relative_to(REPO_ROOT)}")

    stats_path = REPO_ROOT / "data" / "player_game_stats.parquet"
    if not stats_path.exists():
        raise SystemExit(f"FATAL: missing {stats_path}")

    stats_df = pd.read_parquet(stats_path)
    features_df = pd.read_parquet(feature_source)

    team_abbr_map = _team_abbr_lookup()

    df = build_minutes_predictions(
        slate_date=slate_date,
        train_through_date=train_through,
        run_mode=run_mode,
        stats_df=stats_df,
        features_df=features_df,
        feature_source=feature_source,
        team_abbr_map=team_abbr_map,
    )

    validate_minutes_artifact(df, slate_date=slate_date)

    out_dir = REPO_ROOT / "artifacts" / "minutes_predictions" / slate_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pq = out_dir / "minutes_predictions.parquet"
    df.to_parquet(out_pq, index=False)
    print(f"  wrote {out_pq.relative_to(REPO_ROOT)} rows={len(df)}")

    market_df, market_source = _load_current_market_df(slate_date)
    eligible_df = build_eligible_view(
        df, slate_date=slate_date, market_df=market_df
    )
    out_eligible_pq = out_dir / "minutes_predictions_eligible.parquet"
    eligible_df.to_parquet(out_eligible_pq, index=False)
    print(
        f"  wrote {out_eligible_pq.relative_to(REPO_ROOT)} "
        f"rows={len(eligible_df)} "
        f"(universe={len(df)} dropped={len(df) - len(eligible_df)})"
    )

    manifest = {
        "slate_date": slate_date,
        "train_through_date": train_through,
        "run_mode": run_mode,
        "status": "passed" if len(df) > 0 else "empty_slate",
        "row_count": int(len(df)),
        "filtered_eligible_row_count": int(len(eligible_df)),
        "universe_artifact_path": str(out_pq.relative_to(REPO_ROOT)),
        "eligible_artifact_path": str(out_eligible_pq.relative_to(REPO_ROOT)),
        "source_features_path": str(feature_source.relative_to(REPO_ROOT)),
        "feature_snapshot_id": _hash_path(feature_source),
        "current_market_source_path": (
            str(market_source.relative_to(REPO_ROOT)) if market_source is not None else None
        ),
        "minutes_model_version": "state_aware_v1",
        "required_columns_present": [c for c in REQUIRED_OUTPUT_COLUMNS if c in df.columns],
        "eligibility_floors": {
            "starter_probability": STARTER_PROB_FLOOR,
            "rotation_probability": ROTATION_PROB_FLOOR,
            "minutes_mean": ROTATION_MINUTES_FLOOR,
        },
        "created_at_utc": _now_utc_iso(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"  wrote {(out_dir / 'manifest.json').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
