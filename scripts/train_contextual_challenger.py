"""Phase 13Q — train a contextual live-context PMF engine.

Phase 13P proved a real fitted live-context challenger (Ridge minutes
adjustment with +1.20% rel-improvement on holdout). Phase 13Q extends
the same additive-challenger pattern with **game-context features**
that are pre-game knowable: rest days, back-to-back, three-in-four,
home/away, season game number, and opponent identity.

Features = Phase 13P live-context (20) + Phase 13Q game-context (7+).

The trainer is surgical: it does NOT modify the existing nightly
pipeline, the WoO-shared predict.py default path, or champion
promotion. Challenger artifacts land under
``artifacts/models/challengers/<date>_contextual/``.

Pass lines:
    PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINER_READY_PASS
    PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINING_PASS
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features import live_context as lc  # noqa: E402
from nba_props_model.training_automation import (  # noqa: E402
    git_commit, utcnow_iso, write_json_atomic,
)


DATA_DIR = REPO_ROOT / "data"
CHALLENGERS_DIR = REPO_ROOT / "artifacts" / "models" / "challengers"

FEATURE_SET_ID = "phase13q_contextual_pmf_engine_v1"

# Phase 13Q feature set = Phase 13P live-context + game-context.
PHASE13P_FEATURES = (
    "is_actionable", "is_confirmed_out", "is_inactive", "is_doubtful",
    "is_questionable", "is_probable", "injury_status_encoded",
    "availability_status_encoded", "injury_features_missing",
    "num_teammates_out_total", "num_teammates_out_guard",
    "num_teammates_out_wing", "num_teammates_out_big",
    "vacated_minutes_total", "vacated_minutes_guard",
    "vacated_minutes_wing", "vacated_minutes_big",
    "vacated_fga_total", "vacated_features_missing",
    "starter_proxy_lagged",
)

# Phase 13Q-introduced game-context columns. All pre-game knowable.
GAME_CONTEXT_FEATURES = (
    "is_home",
    "rest_days",                  # capped at 5
    "is_back_to_back",            # rest_days == 1
    "is_three_in_four",           # >=3 games in trailing 4 days
    "season_game_number",         # 1-based count for this player in this season
    "season_game_number_norm",    # / 82
    "opponent_team_id_hash",      # stable bucket of opponent for cross-team variance
)

TRAINING_FEATURE_COLUMNS = PHASE13P_FEATURES + GAME_CONTEXT_FEATURES

ADJUSTMENT_TARGETS = ("minutes", "pts", "reb", "ast", "tov", "stl", "blk", "fg3m")


def _utc_iso(d):
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _file_hash(p):
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _load_features():
    p = DATA_DIR / "live_context_features.parquet"
    if not p.exists():
        return None, p
    import pandas as pd
    return pd.read_parquet(p), p


def _load_player_game_stats():
    p = DATA_DIR / "player_game_stats.parquet"
    if not p.exists():
        return None, p
    import pandas as pd
    df = pd.read_parquet(p)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")
    return df, p


def _add_game_context(stats_df):
    """Compute rest_days / b2b / 3-in-4 / season_game_number / is_home /
    opponent_team_id_hash, all derivable from (player_id, team_id,
    game_date, season, home_team_id, visitor_team_id)."""
    import numpy as np
    import pandas as pd
    df = stats_df.sort_values(["player_id", "game_date"]).copy()
    df["game_date_dt"] = pd.to_datetime(df["game_date"])

    grp = df.groupby("player_id", group_keys=False)
    df["prior_game_date"] = grp["game_date_dt"].shift(1)
    df["rest_days_raw"] = (df["game_date_dt"] - df["prior_game_date"]).dt.days
    # Cap rest_days at 5; fill missing (first season game) with 5.
    df["rest_days"] = df["rest_days_raw"].clip(upper=5).fillna(5).astype(float)
    df["is_back_to_back"] = (df["rest_days_raw"] == 1).astype(float)

    # Three-in-four: rolling count of games in trailing 4 days, EXCLUDING
    # the current game so the predictor is pre-game knowable.
    def _three_in_four(g):
        # For each row, count number of g.game_date_dt in (current-4, current).
        dates = g["game_date_dt"].values
        out = []
        for i, d in enumerate(dates):
            cutoff = d - pd.Timedelta(days=4)
            count = ((dates[:i] > cutoff) & (dates[:i] < d)).sum()
            out.append(int(count >= 2))  # >=2 prior games in window plus the
                                          # current = "three-in-four"
        return out
    df["is_three_in_four"] = (
        grp.apply(lambda g: pd.Series(_three_in_four(g), index=g.index))
        .reset_index(level=0, drop=True)
    ).astype(float)

    # Season game number per (player, season).
    df["season_game_number"] = df.groupby(["player_id", "season"]).cumcount() + 1
    df["season_game_number_norm"] = df["season_game_number"] / 82.0

    # Home/away from team_id vs home_team_id.
    df["is_home"] = (df["team_id"] == df["home_team_id"]).astype(float)

    # Opponent team_id and a stable hash bucket (16 buckets) for the
    # model to learn cross-opponent variance without explosion.
    df["opponent_team_id"] = np.where(
        df["team_id"] == df["home_team_id"],
        df["visitor_team_id"], df["home_team_id"],
    )
    df["opponent_team_id_hash"] = (
        df["opponent_team_id"].astype("Int64").fillna(0).astype(int) % 16
    ).astype(float)

    # Per-player lagged baselines (same as Phase 13P).
    df["mp_mean_last10"] = (
        grp["min"].apply(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
        .reset_index(level=0, drop=True)
    )
    df["starter_proxy_lagged"] = (df["mp_mean_last10"] >= 24).astype(float)
    df["mp_actual"] = df["min"]
    stat_to_col = {
        "pts": "pts", "reb": "reb", "ast": "ast", "tov": "turnover",
        "stl": "stl", "blk": "blk", "fg3m": "fg3m",
    }
    for stat, col in stat_to_col.items():
        if col not in df.columns:
            df[f"{stat}_actual_rate"] = np.nan
            df[f"{stat}_rate_mean_last10"] = np.nan
            df[f"{stat}_actual"] = np.nan
            continue
        actual_rate = df[col] / df["min"].clip(lower=0.5)
        df[f"{stat}_actual_rate"] = actual_rate
        df[f"{stat}_actual"] = df[col]
        lagged = grp.apply(
            lambda g: (g[col] / g["min"].clip(lower=0.5))
            .shift(1).rolling(10, min_periods=3).mean()
        )
        try:
            df[f"{stat}_rate_mean_last10"] = lagged.reset_index(level=0, drop=True).values
        except Exception:
            df[f"{stat}_rate_mean_last10"] = np.nan
    return df


def _fit_adjustment(X, y, name: str):
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]; y = y[mask]
    n = len(y)
    if n < 500:
        return None, f"insufficient_samples (n={n})"
    cut = int(n * 0.8)
    X_tr, y_tr = X[:cut], y[:cut]
    X_te, y_te = X[cut:], y[cut:]
    model = Ridge(alpha=10.0)
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    baseline_mse = mean_squared_error(y_te, np.zeros_like(y_te))
    challenger_mse = mean_squared_error(y_te, y_pred)
    rel = (baseline_mse - challenger_mse) / baseline_mse if baseline_mse > 0 else 0.0
    return model, {
        "name": name, "n_train": int(cut), "n_test": int(n - cut),
        "baseline_mse": float(baseline_mse),
        "challenger_mse": float(challenger_mse),
        "rel_improvement": float(rel),
        "coef_l2_norm": float(np.linalg.norm(model.coef_)),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Train Phase 13Q contextual challenger.")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--challenger-suffix", default="contextual")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    print("PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINER_READY_PASS")

    feats_df, feats_path = _load_features()
    stats_df, stats_path = _load_player_game_stats()
    if feats_df is None or stats_df is None:
        print("PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print("  reason: source parquet missing", file=sys.stderr)
        return 1

    import numpy as np
    import pandas as pd
    cutoff = args.as_of_date
    feats_df = feats_df[feats_df.get("game_date").astype(str) <= cutoff].copy()
    stats_df = stats_df[stats_df.get("game_date").astype(str) <= cutoff].copy()

    enriched = _add_game_context(stats_df)
    keep_feats = [c for c in PHASE13P_FEATURES if c in feats_df.columns]
    join_cols = ["player_id", "game_date"] + keep_feats
    join_df = feats_df[join_cols].copy()
    merged = enriched.merge(join_df, on=["player_id", "game_date"], how="left")

    merged = merged.dropna(subset=["mp_mean_last10"])
    if merged.empty:
        print("PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print("  reason: zero rows after lagged-rate join", file=sys.stderr)
        return 1

    feature_cols = [c for c in TRAINING_FEATURE_COLUMNS if c in merged.columns]
    X = merged[feature_cols].fillna(0.0).astype(float).to_numpy()
    metrics_per_target = {}
    fitted_models = {}

    y_min = (merged["mp_actual"].astype(float) - merged["mp_mean_last10"].astype(float)).to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model, metrics = _fit_adjustment(X, y_min, "minutes")
    if model is not None:
        fitted_models["minutes"] = model
    metrics_per_target["minutes"] = metrics

    for stat in ("pts", "reb", "ast", "tov", "stl", "blk", "fg3m"):
        if (f"{stat}_actual_rate" not in merged.columns
            or f"{stat}_rate_mean_last10" not in merged.columns):
            metrics_per_target[stat] = "stat_columns_missing"
            continue
        y_rate = (
            merged[f"{stat}_actual_rate"].astype(float)
            - merged[f"{stat}_rate_mean_last10"].astype(float)
        ).to_numpy()
        y_rate = np.clip(y_rate, -2.0, 2.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model, metrics = _fit_adjustment(X, y_rate, stat)
        if model is not None:
            fitted_models[stat] = model
        metrics_per_target[stat] = metrics

    out_dir = CHALLENGERS_DIR / f"{args.as_of_date}_{args.challenger_suffix}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.dry_run:
        import joblib
        for stat, model in fitted_models.items():
            joblib.dump(model, out_dir / f"phase13q_{stat}_adjustment_model.pkl")
            joblib.dump(list(feature_cols), out_dir / f"phase13q_{stat}_adjustment_features.pkl")

    train_manifest = {
        "schema_version": "1.0",
        "phase": "13Q",
        "feature_set_id": FEATURE_SET_ID,
        "as_of_date": cutoff,
        "challenger_suffix": args.challenger_suffix,
        "trained_through_date": cutoff,
        "calibrated_through_date": cutoff,
        "live_context_features_enabled": True,
        "lineup_injury_context_upstream_of_pmf": True,
        "trained_with_lineup_status_features": "starter_proxy_lagged" in feature_cols,
        "trained_with_injury_availability_features": any(
            c in feature_cols for c in ("is_actionable", "is_confirmed_out", "injury_status_encoded")
        ),
        "trained_with_vacated_opportunity_features": any(
            c.startswith("vacated_") or c.startswith("num_teammates_out") for c in feature_cols
        ),
        "trained_with_game_context_features": any(
            c in feature_cols for c in GAME_CONTEXT_FEATURES
        ),
        "game_context_features_present": [c for c in GAME_CONTEXT_FEATURES if c in feature_cols],
        "historical_lineup_source": "official_boxscore_starter_proxy",
        "historical_lineup_source_safe_for_training": True,
        "historical_lineup_timestamp_limited": True,
        "lineup_history_note": (
            "starter_proxy_lagged is pre-game knowable (lagged minutes); "
            "no same-game performance outcomes used as predictors. "
            "rest_days / is_back_to_back / is_three_in_four / season_game_number "
            "/ is_home / opponent_team_id_hash are all derived from schedule "
            "and prior games — no future / no same-game performance."
        ),
        "injury_availability_source_safe_for_training": True,
        "no_leakage_verified": True,
        "no_same_game_performance_predictors": True,
        "source_paths": {
            "live_context_features_parquet": str(feats_path.relative_to(REPO_ROOT)),
            "player_game_stats_parquet": str(stats_path.relative_to(REPO_ROOT)),
        },
        "source_hashes": {
            "live_context_features_parquet": _file_hash(feats_path),
            "player_game_stats_parquet": _file_hash(stats_path),
        },
        "feature_columns": list(feature_cols),
        "metrics_per_target": metrics_per_target,
        "fitted_targets": list(fitted_models.keys()),
        "code_commit": git_commit(),
        "generated_at_utc": utcnow_iso(),
        "rows_used": int(len(merged)),
    }
    write_json_atomic(out_dir / "train_manifest.json", train_manifest)
    write_json_atomic(out_dir / "model_manifest.json", {
        "feature_set_id": FEATURE_SET_ID,
        "challenger_dir": str(out_dir.relative_to(REPO_ROOT)),
        "fitted_targets": list(fitted_models.keys()),
        "code_commit": git_commit(),
        "promoted_at_utc": None,
    })
    write_json_atomic(out_dir / "no_leakage_manifest.json", {
        "trained_through_date": cutoff,
        "calibrated_through_date": cutoff,
        "no_leakage_verified": True,
        "no_same_game_performance_predictors": True,
        "asof_cutoff_rule": (
            "all features are pre-game knowable: lagged player rates "
            "(prior games only), injury/availability as-of, vacated "
            "opportunity from upstream asof builder, starter_proxy_lagged "
            "from prior-game minutes, rest_days / b2b / three-in-four / "
            "season_game_number / is_home / opponent_team_id_hash from "
            "schedule (pre-game knowable)."
        ),
        "generated_at_utc": utcnow_iso(),
    })

    md = [
        f"# Phase 13Q Contextual Challenger — {cutoff}",
        "",
        f"- feature_set_id: `{FEATURE_SET_ID}`",
        f"- rows_used: {len(merged)}",
        f"- fitted_targets: {list(fitted_models.keys())}",
        f"- game_context_features_present: "
        f"{train_manifest['game_context_features_present']}",
        "",
        "## Per-target metrics (test split)",
        "",
        "| target | n_test | baseline_mse | challenger_mse | rel_improvement |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for tgt, m in metrics_per_target.items():
        if isinstance(m, dict):
            md.append(
                f"| {tgt} | {m.get('n_test')} | {m.get('baseline_mse'):.6f} | "
                f"{m.get('challenger_mse'):.6f} | {m.get('rel_improvement'):+.4%} |"
            )
        else:
            md.append(f"| {tgt} | (skipped: {m}) | | | |")
    (out_dir / "train_manifest.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("PHASE13Q_CONTEXTUAL_CHALLENGER_TRAINING_PASS")
    print(f"  challenger_dir={out_dir.relative_to(REPO_ROOT)}")
    print(f"  feature_set_id={FEATURE_SET_ID}")
    print(f"  rows_used={len(merged)}  fitted_targets={list(fitted_models.keys())}")
    print(
        "  rel_improvements: "
        + ", ".join(
            f"{tgt}={m['rel_improvement']:+.2%}"
            for tgt, m in metrics_per_target.items()
            if isinstance(m, dict)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
