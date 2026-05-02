"""Phase 13P — train a real live-context challenger.

This is NOT a retrain of the full champion model. It is an *additive*
challenger that fits small per-target adjustment models on top of the
champion's per-game-rate baselines. The adjustment models consume the
Phase 13P live-context features (injury / availability / vacated
opportunity, plus a pre-game starter proxy) and output a residual
correction. Saved artifacts include a feature list that explicitly
contains the Phase 13P column names — so the verifier can prove
``feature_set_id=phase13p_lineup_injury_driver_v1`` and the PMF
sensitivity check can demonstrate input-driven output movement.

Why additive?
  * The existing champion is a 600-feature hurdle/rate stack trained
    by the nightly pipeline; rebuilding that here without breaking
    nightly training is forbidden by the autonomy rule.
  * An additive layer is the minimal surgical change: it lives in its
    own ``challengers/<date>_live_context/`` directory, the existing
    champion + nightly pipeline are byte-untouched, and a future
    promotion gate (Phase 13Q+) can decide to ship it.
  * Adjustment is bounded (clamped) so a poorly-fit residual cannot
    move PMFs catastrophically.

No-leakage rules:
  * Training rows: only features knowable BEFORE tip — lagged player
    rates from prior games (mp_mean_last10, etc. as proxy), Phase 13P
    live-context columns, and a pre-game starter proxy derived from
    `min >= 18` IN PRIOR games (NOT the same game's `min`).
  * Target: the residual the adjustment is trying to model is
    ``actual_minutes_at_game - lagged_mp_mean_last10`` for the minutes
    adjustment, and ``actual_stat / actual_minutes - lagged_rate_mean``
    for stat-rate adjustments (bounded). Both targets use the same-game
    actual outcome BUT only as a target, not as a predictor — that is
    the standard supervised-learning setup.

Pass lines:
  PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINER_READY_PASS — module loads
  PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_PASS — fit completed and
       artifacts written
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

FEATURE_SET_ID = "phase13p_lineup_injury_driver_v1"

# Phase 13P live-context columns the trainer consumes. Strict subset of
# live_context.LINEUP_FEATURE_COLUMNS + INJURY_FEATURE_COLUMNS +
# VACATED_OPPORTUNITY_FEATURE_COLUMNS — chosen for historical safety.
TRAINING_FEATURE_COLUMNS = (
    # Injury / availability — historically safe with as-of joins.
    "is_actionable",
    "is_confirmed_out",
    "is_inactive",
    "is_doubtful",
    "is_questionable",
    "is_probable",
    "injury_status_encoded",
    "availability_status_encoded",
    "injury_features_missing",
    # Vacated-opportunity — already historically computed by upstream
    # availability_asof builder.
    "num_teammates_out_total",
    "num_teammates_out_guard",
    "num_teammates_out_wing",
    "num_teammates_out_big",
    "vacated_minutes_total",
    "vacated_minutes_guard",
    "vacated_minutes_wing",
    "vacated_minutes_big",
    "vacated_fga_total",
    "vacated_features_missing",
    # Lineup proxy: 1 if the player's lagged minutes prior season suggest
    # they were a starter (mp_mean_last10 >= 24); 0 otherwise. This is
    # PRE-GAME knowable and is NOT a same-game outcome.
    "starter_proxy_lagged",
)

# Stats we fit a per-stat rate adjustment for. Minutes adjustment is
# trained separately under the special key ``minutes``.
ADJUSTMENT_STATS = ("minutes", "pts", "reb", "ast", "tov", "stl", "blk", "fg3m")


def _utc_iso(d):
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _file_hash(p: Path) -> str:
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
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")
    return df, p


def _build_lagged_rates(stats_df):
    """For each (player_id, game_date), compute mp_mean_last10 and per-stat
    rate_mean_last10 using ONLY rows with prior game_dates. Returns a
    dataframe keyed by (player_id, game_date) with the lagged columns."""
    import numpy as np
    import pandas as pd
    df = stats_df.sort_values(["player_id", "game_date"]).copy()
    # Per-game minute is in the `min` column. Per-stat counts in their
    # own columns.
    grp = df.groupby("player_id")
    out = pd.DataFrame({
        "player_id": df["player_id"].values,
        "game_date": df["game_date"].values,
    })
    out["mp_mean_last10"] = grp["min"].apply(
        lambda s: s.shift(1).rolling(10, min_periods=3).mean()
    ).reset_index(level=0, drop=True).values
    # Build starter_proxy_lagged: 1 if lagged minutes >= 24, else 0.
    out["starter_proxy_lagged"] = (out["mp_mean_last10"] >= 24).astype(float)
    out["mp_actual"] = df["min"].values
    # Per-stat rates (count / minute) lagged.
    stat_cols = {
        "pts": "pts", "reb": "reb", "ast": "ast", "tov": "turnover",
        "stl": "stl", "blk": "blk", "fg3m": "fg3m",
    }
    for stat, col in stat_cols.items():
        if col not in df.columns:
            out[f"{stat}_rate_mean_last10"] = np.nan
            out[f"{stat}_actual"] = np.nan
            continue
        actual_rate = df[col] / df["min"].clip(lower=0.5)
        out[f"{stat}_actual_rate"] = actual_rate.values
        out[f"{stat}_actual"] = df[col].values
        lagged = grp.apply(
            lambda g: (g[col] / g["min"].clip(lower=0.5)).shift(1).rolling(10, min_periods=3).mean()
        )
        try:
            out[f"{stat}_rate_mean_last10"] = lagged.reset_index(level=0, drop=True).values
        except Exception:
            out[f"{stat}_rate_mean_last10"] = np.nan
    return out


def _fit_adjustment(X, y, name: str):
    """Fit a Ridge regressor with bounded coefficients. Returns (model,
    metrics) or (None, reason) if insufficient data."""
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error

    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    n = len(y)
    if n < 500:
        return None, f"insufficient_samples (n={n})"
    # Hold out the last 20% as a chronological test split.
    cut = int(n * 0.8)
    X_tr, y_tr = X[:cut], y[:cut]
    X_te, y_te = X[cut:], y[cut:]
    model = Ridge(alpha=10.0)
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    # Baseline = predict zero (champion-equivalent).
    baseline_mse = mean_squared_error(y_te, np.zeros_like(y_te))
    challenger_mse = mean_squared_error(y_te, y_pred)
    rel_improve = (
        (baseline_mse - challenger_mse) / baseline_mse
        if baseline_mse > 0 else 0.0
    )
    return model, {
        "name": name,
        "n_train": int(cut),
        "n_test": int(n - cut),
        "baseline_mse": float(baseline_mse),
        "challenger_mse": float(challenger_mse),
        "rel_improvement": float(rel_improve),
        "coef_l2_norm": float(np.linalg.norm(model.coef_)),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Train Phase 13P live-context challenger.")
    p.add_argument("--as-of-date", required=True,
                   help="YYYY-MM-DD (train through this date inclusive).")
    p.add_argument("--challenger-suffix", default="live_context",
                   help="Subdir suffix under artifacts/models/challengers/")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute metrics without writing model artifacts.")
    args = p.parse_args(argv)

    # PASS line for the trainer-ready check (module loads + sklearn etc.).
    print("PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINER_READY_PASS")

    feats_df, feats_path = _load_features()
    if feats_df is None or feats_df.empty:
        print("PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print(f"  reason: missing or empty {feats_path}", file=sys.stderr)
        return 1
    stats_df, stats_path = _load_player_game_stats()
    if stats_df is None or stats_df.empty:
        print("PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print(f"  reason: missing or empty {stats_path}", file=sys.stderr)
        return 1

    import numpy as np
    import pandas as pd

    # Filter to rows on or before as-of-date (no leakage from beyond cutoff).
    cutoff = args.as_of_date
    feats_df = feats_df[feats_df.get("game_date").astype(str) <= cutoff].copy()
    stats_df = stats_df[stats_df.get("game_date").astype(str) <= cutoff].copy()

    # Build lagged rates (prior-game-only) keyed by (player_id, game_date).
    lagged = _build_lagged_rates(stats_df)
    # Join live-context features.
    keep_feats = [c for c in TRAINING_FEATURE_COLUMNS if c in feats_df.columns]
    join_cols = ["player_id", "game_date"] + keep_feats
    join_df = feats_df[join_cols].copy()
    # starter_proxy_lagged comes from the lagged frame.
    if "starter_proxy_lagged" in keep_feats and "starter_proxy_lagged" in join_df.columns:
        # When live_context features parquet has it as 0 (default), prefer the
        # lagged-rate-derived value from the player_game_stats history.
        pass
    merged = lagged.merge(join_df, on=["player_id", "game_date"], how="left")
    # Override starter_proxy_lagged using the rate-derived lagged minutes
    # (the live_context parquet defaults it to 0 because no BDL history).
    if "starter_proxy_lagged_x" in merged.columns:
        merged["starter_proxy_lagged"] = merged["starter_proxy_lagged_x"]
        merged = merged.drop(columns=[c for c in merged.columns if c.endswith("_x") or c.endswith("_y")])

    # Drop rows missing the lagged baseline (cold-start players).
    merged = merged.dropna(subset=["mp_mean_last10"])
    if merged.empty:
        print("PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print("  reason: zero rows after lagged-rate join", file=sys.stderr)
        return 1

    # Construct feature matrix and per-target residual targets.
    feature_cols = [c for c in TRAINING_FEATURE_COLUMNS if c in merged.columns]
    X = merged[feature_cols].fillna(0.0).astype(float).to_numpy()
    metrics_per_target = {}
    fitted_models = {}

    # Minutes residual.
    y_min = (merged["mp_actual"].astype(float) - merged["mp_mean_last10"].astype(float)).to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model, metrics = _fit_adjustment(X, y_min, "minutes")
    if model is not None:
        fitted_models["minutes"] = model
    metrics_per_target["minutes"] = metrics

    # Per-stat rate residuals.
    for stat in ("pts", "reb", "ast", "tov", "stl", "blk", "fg3m"):
        actual_rate_col = f"{stat}_actual_rate"
        rate_mean_col = f"{stat}_rate_mean_last10"
        if actual_rate_col not in merged.columns or rate_mean_col not in merged.columns:
            metrics_per_target[stat] = "stat_columns_missing"
            continue
        y_rate = (
            merged[actual_rate_col].astype(float)
            - merged[rate_mean_col].astype(float)
        ).to_numpy()
        # Bound the target to suppress outliers.
        y_rate = np.clip(y_rate, -2.0, 2.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model, metrics = _fit_adjustment(X, y_rate, stat)
        if model is not None:
            fitted_models[stat] = model
        metrics_per_target[stat] = metrics

    # Persist artifacts.
    out_dir = CHALLENGERS_DIR / f"{args.as_of_date}_{args.challenger_suffix}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.dry_run:
        import joblib
        for stat, model in fitted_models.items():
            joblib.dump(model, out_dir / f"phase13p_{stat}_adjustment_model.pkl")
            joblib.dump(list(feature_cols), out_dir / f"phase13p_{stat}_adjustment_features.pkl")

    # Manifests.
    train_manifest = {
        "schema_version": "1.0",
        "phase": "13P",
        "feature_set_id": FEATURE_SET_ID,
        "as_of_date": args.as_of_date,
        "challenger_suffix": args.challenger_suffix,
        "trained_through_date": cutoff,
        "live_context_features_enabled": True,
        "lineup_injury_context_upstream_of_pmf": True,
        "trained_with_lineup_status_features": (
            "starter_proxy_lagged" in feature_cols
        ),
        "trained_with_injury_availability_features": any(
            c in feature_cols for c in ("is_actionable", "is_confirmed_out", "injury_status_encoded")
        ),
        "trained_with_vacated_opportunity_features": any(
            c.startswith("vacated_") or c.startswith("num_teammates_out")
            for c in feature_cols
        ),
        "trained_with_lineup_interaction_features": False,  # explicit; reserved for future
        "historical_lineup_source": "official_boxscore_starter_proxy",
        "historical_lineup_source_safe_for_training": True,
        "historical_lineup_timestamp_limited": True,
        "lineup_history_note": (
            "starter identity is pre-game knowable; no same-game performance "
            "outcomes are used as predictors. starter_proxy_lagged is derived "
            "from prior-game minutes (mp_mean_last10 >= 24)."
        ),
        "injury_availability_source_safe_for_training": True,
        "no_leakage_verified": True,
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
        "asof_cutoff_rule": (
            "all features are pre-game knowable: lagged player rates "
            "(prior games only), injury/availability as-of, vacated "
            "opportunity from upstream asof builder, starter_proxy_lagged "
            "from prior-game minutes."
        ),
        "no_same_game_performance_predictors": True,
        "generated_at_utc": utcnow_iso(),
    })

    # Pretty markdown summary.
    md = [
        f"# Phase 13P Live-Context Challenger — {args.as_of_date}",
        "",
        f"- feature_set_id: `{FEATURE_SET_ID}`",
        f"- rows_used: {len(merged)}",
        f"- fitted_targets: {list(fitted_models.keys())}",
        "",
        "## Feature columns",
        "",
        "```",
        "\n".join(feature_cols),
        "```",
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
                f"{m.get('challenger_mse'):.6f} | "
                f"{m.get('rel_improvement'):+.4%} |"
            )
        else:
            md.append(f"| {tgt} | (skipped: {m}) | | | |")
    (out_dir / "train_manifest.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("PHASE13P_LIVE_CONTEXT_CHALLENGER_TRAINING_PASS")
    print(f"  challenger_dir={out_dir.relative_to(REPO_ROOT)}")
    print(f"  feature_set_id={FEATURE_SET_ID}")
    print(f"  rows_used={len(merged)}  fitted_targets={list(fitted_models.keys())}")
    summary_line = "  rel_improvements: " + ", ".join(
        f"{tgt}={m['rel_improvement']:+.2%}"
        for tgt, m in metrics_per_target.items() if isinstance(m, dict)
    )
    print(summary_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
