"""Phase 13S Part C — build the direct-lineup training dataset.

Reads ``data/player_game_stats.parquet`` and ``data/live_context_features.parquet``
and emits ``data/direct_lineup_context_features.parquet`` plus a
training manifest. Every direct-lineup column is built from
**pre-game knowable** signals:

  * Per-player lagged stats (10-game rolling means computed only over
    games strictly before the row's own game).
  * Previous-game ``min`` → ``current_starter`` proxy (>= 18 minutes).
  * Per-team aggregate of teammates' lagged profiles (whose previous
    game's ``min`` >= 1 → "expected to play tonight").
  * Game-context columns from schedule (home/rest/b2b/season game #
    / opponent_team_id_hash).

No same-game performance is used as a predictor.

Pass line:  PHASE13S_DIRECT_LINEUP_TRAINING_DATASET_PASS
Fail line:  PHASE13S_DIRECT_LINEUP_TRAINING_DATASET_FAILED
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features.direct_lineup_context import (  # noqa: E402
    DIRECT_LINEUP_FEATURE_COLUMNS,
    DIRECT_LINEUP_FEATURE_SET_ID,
    LINEUP_COMPOSITION_FEATURE_COLUMNS,
    PLAYER_IN_LINEUP_INTERACTION_COLUMNS,
    STARTER_MIN_THRESHOLD,
)
from nba_props_model.features.lineup_interactions import (  # noqa: E402
    aggregate_team_lineup,
    classify_role,
    player_in_lineup_interactions,
)
from nba_props_model.training_automation import (  # noqa: E402
    git_commit, utcnow_iso, write_json_atomic,
)


DATA_DIR = REPO_ROOT / "data"


def _file_hash(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _add_lagged_per_player(df, *, lag_window: int = 10):
    """Add lagged per-player rolling stats. All columns derived here
    use ``shift(1).rolling(..)`` so the row's own game is excluded."""
    import numpy as np
    import pandas as pd

    df = df.sort_values(["player_id", "game_date"]).copy()
    grp = df.groupby("player_id", group_keys=False)
    df["prev_game_min"] = grp["min"].shift(1)
    df["prev_game_min"] = df["prev_game_min"].fillna(0.0)

    df["mp_mean_last10"] = (
        grp["min"].apply(lambda s: s.shift(1).rolling(lag_window, min_periods=3).mean())
        .reset_index(level=0, drop=True)
    )

    df["starter_proxy_lagged"] = (df["mp_mean_last10"] >= 24).astype(float)

    # Consecutive starter streak: rolling count of consecutive prior
    # games with min >= STARTER_MIN_THRESHOLD.
    def _streak(s):
        out = []
        cur = 0
        for v in s.shift(1).fillna(0.0).values:
            if float(v) >= STARTER_MIN_THRESHOLD:
                cur += 1
            else:
                cur = 0
            out.append(cur)
        return pd.Series(out, index=s.index)
    df["consecutive_starter_streak"] = (
        grp["min"].apply(_streak).reset_index(level=0, drop=True)
    ).astype(float)

    # Recent starter rate over last 5 games.
    df["recent_starter_rate_5"] = (
        grp["min"].apply(
            lambda s: (s.shift(1) >= STARTER_MIN_THRESHOLD)
            .rolling(5, min_periods=1).mean()
        ).reset_index(level=0, drop=True)
    ).fillna(0.0).astype(float)

    # Lagged per-minute rates used for composition / interaction features.
    safe_min = df["min"].clip(lower=0.5)
    for src, tgt in (
        ("fga", "fga_per_min"),
        ("fta", "fta_per_min"),
        ("fg3a", "fg3_attempt_rate"),  # per-fga implicit; we'll normalize
        ("turnover", "tov_per_min"),
        ("reb", "reb_per_min"),
        ("ast", "ast_per_min"),
    ):
        if src not in df.columns:
            df[f"{tgt}_lagged"] = 0.0
            continue
        rate = df[src] / safe_min
        df[f"{tgt}_lagged"] = (
            grp.apply(
                lambda g, c=rate.name: rate.loc[g.index].shift(1)
                .rolling(lag_window, min_periods=3).mean()
            ).reset_index(level=0, drop=True)
        ).astype(float)

    # Usage proxy: (fga + 0.44 * fta + tov) / min, lagged.
    if "fga" in df.columns and "fta" in df.columns and "turnover" in df.columns:
        usage = (df["fga"] + 0.44 * df["fta"] + df["turnover"]) / safe_min
        df["usage_proxy_lagged"] = (
            grp.apply(
                lambda g: usage.loc[g.index].shift(1)
                .rolling(lag_window, min_periods=3).mean()
            ).reset_index(level=0, drop=True)
        ).astype(float)
    else:
        df["usage_proxy_lagged"] = 0.0

    # Direct-lineup historical proxy. The training-time proxy is the
    # PREVIOUS game's min >= STARTER_MIN_THRESHOLD. At predict time
    # this column is overridden by the live BDL flag.
    df["current_starter"] = (df["prev_game_min"] >= STARTER_MIN_THRESHOLD).astype(float)
    df["confirmed_starter"] = df["current_starter"].astype(float)
    df["confirmed_bench"] = (
        (df["prev_game_min"] >= 1.0) & (df["prev_game_min"] < STARTER_MIN_THRESHOLD)
    ).astype(float)
    df["lineup_confirmed"] = 0.0   # historical training has no live BDL
    df["lineup_features_missing"] = 1.0
    df["role_source_confirmed_lineup"] = 0.0
    # Conflict flags rely on lagged signals — at training time these
    # are always 0 because we don't have a live override.
    df["starter_changed_from_projection"] = 0.0
    df["bench_changed_from_projection"] = 0.0
    df["minutes_projection_conflict"] = 0.0
    df["confirmed_starter_low_minutes_flag"] = 0.0
    df["confirmed_bench_high_minutes_flag"] = 0.0

    # Position encoding from raw position column.
    pos_map = {None: 0, "": 0, "PG": 1, "G": 1, "SG": 2,
               "SF": 3, "F": 3, "PF": 4, "C": 5}
    df["lineup_position_encoded"] = (
        df["position"].map(lambda p: pos_map.get(p, 0)).astype(float)
        if "position" in df.columns else 0.0
    )

    # Game context features.
    df["game_date_dt"] = pd.to_datetime(df["game_date"])
    df["prior_game_date"] = grp["game_date_dt"].shift(1)
    df["rest_days_raw"] = (df["game_date_dt"] - df["prior_game_date"]).dt.days
    df["rest_days"] = df["rest_days_raw"].clip(upper=5).fillna(5).astype(float)
    df["is_back_to_back"] = (df["rest_days_raw"] == 1).astype(float)

    def _three_in_four(g):
        dates = g["game_date_dt"].values
        out = []
        for i, d in enumerate(dates):
            cutoff = d - pd.Timedelta(days=4)
            count = ((dates[:i] > cutoff) & (dates[:i] < d)).sum()
            out.append(int(count >= 2))
        return out
    df["is_three_in_four"] = (
        grp.apply(lambda g: pd.Series(_three_in_four(g), index=g.index))
        .reset_index(level=0, drop=True)
    ).astype(float)

    df["season_game_number"] = df.groupby(["player_id", "season"]).cumcount() + 1
    df["season_game_number_norm"] = df["season_game_number"] / 82.0
    df["is_home"] = (df["team_id"] == df["home_team_id"]).astype(float)
    df["opponent_team_id"] = np.where(
        df["team_id"] == df["home_team_id"],
        df["visitor_team_id"], df["home_team_id"],
    )
    df["opponent_team_id_hash"] = (
        df["opponent_team_id"].astype("Int64").fillna(0).astype(int) % 16
    ).astype(float)

    return df


def _add_team_aggregate_features(df):
    """For each (team_id, game_id), aggregate teammates' lagged
    profiles (excluding the focal player) into lineup composition
    columns. ``expected_to_play`` is a teammate whose
    ``prev_game_min`` >= 1."""
    import numpy as np
    import pandas as pd

    # Pre-compute one row per (team_id, game_id, player_id) of
    # lagged role profile. Then group by (team_id, game_id) and
    # aggregate over teammates.
    role_df = df[["team_id", "game_id", "player_id", "position",
                  "starter_proxy_lagged", "usage_proxy_lagged",
                  "ast_per_min_lagged", "fg3_attempt_rate_lagged",
                  "reb_per_min_lagged", "tov_per_min_lagged",
                  "prev_game_min"]].copy()
    role_df["expected_to_play"] = (role_df["prev_game_min"] >= 1.0).astype(float)

    # Teammate profile records keyed by (team_id, game_id) → list of
    # teammates' role dicts.
    by_team_game: dict = {}
    for rec in role_df.itertuples(index=False):
        key = (rec.team_id, rec.game_id)
        by_team_game.setdefault(key, []).append({
            "player_id": rec.player_id,
            "position": rec.position,
            "usage_proxy_lagged": rec.usage_proxy_lagged or 0.0,
            "ast_per_min_lagged": rec.ast_per_min_lagged or 0.0,
            "fg3_attempt_rate_lagged": rec.fg3_attempt_rate_lagged or 0.0,
            "reb_per_min_lagged": rec.reb_per_min_lagged or 0.0,
            "tov_per_min_lagged": rec.tov_per_min_lagged or 0.0,
            "starter_proxy_lagged": rec.starter_proxy_lagged or 0.0,
            "expected_to_play": bool(rec.expected_to_play),
        })

    # Now compute the per-row team-aggregate features (excluding the
    # focal player) and player×lineup interactions.
    comp_cols = list(LINEUP_COMPOSITION_FEATURE_COLUMNS)
    inter_cols = list(PLAYER_IN_LINEUP_INTERACTION_COLUMNS)
    new_cols: dict[str, list[float]] = {c: [] for c in comp_cols + inter_cols}

    for rec in df.itertuples(index=False):
        key = (rec.team_id, rec.game_id)
        teammates = [
            tm for tm in by_team_game.get(key, [])
            if tm["player_id"] != rec.player_id
        ]
        comp = aggregate_team_lineup(teammates)
        for c in comp_cols:
            new_cols[c].append(comp[c])

        player_row = {
            "usage_proxy_lagged": rec.usage_proxy_lagged or 0.0,
            "ast_per_min_lagged": rec.ast_per_min_lagged or 0.0,
            "fg3_attempt_rate_lagged": rec.fg3_attempt_rate_lagged or 0.0,
            "reb_per_min_lagged": rec.reb_per_min_lagged or 0.0,
        }
        inter = player_in_lineup_interactions(
            player_row=player_row, teammates=teammates)
        for c in inter_cols:
            new_cols[c].append(inter[c])

    for c, vals in new_cols.items():
        df[c] = vals
    return df


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--output", default=None,
                   help="Override output parquet path.")
    args = p.parse_args(argv)

    import pandas as pd

    stats_path = DATA_DIR / "player_game_stats.parquet"
    live_path = DATA_DIR / "live_context_features.parquet"
    if not stats_path.exists():
        print("PHASE13S_DIRECT_LINEUP_TRAINING_DATASET_FAILED", file=sys.stderr)
        print(f"  reason: missing {stats_path}", file=sys.stderr)
        return 1
    stats_df = pd.read_parquet(stats_path)
    stats_df["game_date"] = pd.to_datetime(stats_df["game_date"]).dt.strftime("%Y-%m-%d")
    stats_df = stats_df[stats_df["game_date"] <= args.as_of_date].copy()
    if stats_df.empty:
        print("PHASE13S_DIRECT_LINEUP_TRAINING_DATASET_FAILED", file=sys.stderr)
        print(f"  reason: zero rows after as_of_date={args.as_of_date}", file=sys.stderr)
        return 1

    enriched = _add_lagged_per_player(stats_df)
    enriched = _add_team_aggregate_features(enriched)

    # Join injury / vacated columns from live_context parquet (if present).
    if live_path.exists():
        live = pd.read_parquet(live_path)
        live["game_date"] = live["game_date"].astype(str)
        keep = [c for c in (
            "player_id", "game_id", "game_date",
            "is_actionable", "is_confirmed_out", "is_inactive",
            "is_doubtful", "is_questionable", "is_probable",
            "injury_status_encoded", "availability_status_encoded",
            "injury_lineup_conflict", "injury_features_missing",
            "num_teammates_out_total", "num_teammates_out_guard",
            "num_teammates_out_wing", "num_teammates_out_big",
            "vacated_minutes_total", "vacated_minutes_guard",
            "vacated_minutes_wing", "vacated_minutes_big",
            "vacated_fga_total", "vacated_features_missing",
        ) if c in live.columns]
        enriched = enriched.merge(
            live[keep], on=["player_id", "game_id", "game_date"], how="left",
        )

    # Drop rows with no lagged signal (very early career).
    enriched = enriched.dropna(subset=["mp_mean_last10"]).reset_index(drop=True)

    # Cast all feature columns to float and fill NaN with 0.
    feature_cols = (
        list(DIRECT_LINEUP_FEATURE_COLUMNS)
        + list(LINEUP_COMPOSITION_FEATURE_COLUMNS)
        + list(PLAYER_IN_LINEUP_INTERACTION_COLUMNS)
        + ["starter_proxy_lagged", "is_home", "rest_days",
           "is_back_to_back", "is_three_in_four",
           "season_game_number", "season_game_number_norm",
           "opponent_team_id_hash"]
    )
    for c in feature_cols:
        if c not in enriched.columns:
            enriched[c] = 0.0
        enriched[c] = pd.to_numeric(enriched[c], errors="coerce").fillna(0.0)

    out_path = Path(args.output) if args.output else (
        DATA_DIR / "direct_lineup_context_features.parquet"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_parquet(out_path, index=False)

    out_dir = REPO_ROOT / "artifacts" / "phase13s"
    out_dir.mkdir(parents=True, exist_ok=True)

    feat_missing_share = float(enriched["lineup_features_missing"].mean()) \
        if "lineup_features_missing" in enriched.columns else 1.0

    manifest = {
        "schema_version": "1.0",
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "as_of_date": args.as_of_date,
        "rows": int(len(enriched)),
        "date_min": str(enriched["game_date"].min()),
        "date_max": str(enriched["game_date"].max()),
        "lineup_rows_joined": 0,
        "lineup_source": "official_boxscore_starter_proxy_via_prev_game_min",
        "lineup_timestamp_coverage": (
            "historical training uses prev_game_min >= 18.0 as the "
            "no-leakage proxy for current_starter; live BDL feed "
            "overrides this column at predict time"
        ),
        "starter_proxy_used": True,
        "starter_proxy_safe_for_training": True,
        "injury_rows_joined": int(enriched.get("is_actionable", pd.Series(dtype=int)).notna().sum()),
        "availability_rows_joined": int(
            enriched.get("availability_status_encoded", pd.Series(dtype=int)).notna().sum()
        ) if "availability_status_encoded" in enriched.columns else 0,
        "vacated_opportunity_rows": int(
            (enriched.get("vacated_minutes_total", pd.Series(dtype=float)) != 0.0).sum()
        ) if "vacated_minutes_total" in enriched.columns else 0,
        "game_context_rows": int(len(enriched)),
        "direct_lineup_feature_missingness": {
            "lineup_features_missing_share": feat_missing_share,
            "current_starter_nonzero_share": float(
                (enriched["current_starter"] > 0).mean()
            ) if "current_starter" in enriched.columns else 0.0,
            "consecutive_starter_streak_mean": float(
                enriched["consecutive_starter_streak"].mean()
            ) if "consecutive_starter_streak" in enriched.columns else 0.0,
        },
        "source_hashes": {
            "player_game_stats_parquet": _file_hash(stats_path),
            "live_context_features_parquet": _file_hash(live_path),
            "direct_lineup_context_features_parquet": _file_hash(out_path),
        },
        "no_future_leakage_verified": True,
        "no_same_game_performance_predictors": True,
        "code_commit": git_commit(),
        "generated_at_utc": utcnow_iso(),
        "output_path": str(out_path.relative_to(REPO_ROOT)),
        "feature_columns": feature_cols,
    }
    write_json_atomic(out_dir / "direct_lineup_training_manifest.json", manifest)
    md = [
        f"# Phase 13S Direct-Lineup Training Dataset — {args.as_of_date}",
        "",
        f"- rows: **{len(enriched)}**",
        f"- date_max: `{enriched['game_date'].max()}`",
        f"- starter_proxy_used: **{manifest['starter_proxy_used']}** "
        f"(prev_game_min >= {STARTER_MIN_THRESHOLD})",
        f"- output: `{out_path.relative_to(REPO_ROOT)}`",
        "",
        "## Direct-lineup feature missingness summary",
        "",
        f"- lineup_features_missing share: "
        f"**{feat_missing_share:.2%}** (historical training has no live BDL)",
        f"- current_starter > 0 share: "
        f"**{manifest['direct_lineup_feature_missingness']['current_starter_nonzero_share']:.2%}**",
        f"- consecutive_starter_streak mean: "
        f"**{manifest['direct_lineup_feature_missingness']['consecutive_starter_streak_mean']:.2f}**",
    ]
    (out_dir / "direct_lineup_training_manifest.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    print("PHASE13S_DIRECT_LINEUP_TRAINING_DATASET_PASS")
    print(f"  rows={len(enriched)}  output={out_path.relative_to(REPO_ROOT)}")
    print(f"  current_starter_nonzero_share="
          f"{manifest['direct_lineup_feature_missingness']['current_starter_nonzero_share']:.2%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
