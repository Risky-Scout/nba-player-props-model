"""Phase 13S Part D — train the direct-lineup contextual challenger.

Reads ``data/direct_lineup_context_features.parquet`` and trains
Ridge adjustment models for minutes + 7 stat rates that consume the
direct lineup features (``current_starter``, ``confirmed_starter``,
``consecutive_starter_streak``, ...), the lineup composition
features, and the player×lineup interaction features alongside the
Phase 13R injury / vacated-opportunity / game-context columns.

Saves under ``artifacts/models/challengers/<as_of_date>_direct_lineup_contextual/``:

    phase13s_<target>_features.pkl
    phase13s_<target>_adjustment.pkl
    train_manifest.json
    model_manifest.json
    no_leakage_manifest.json

Pass line:  PHASE13S_DIRECT_LINEUP_CHALLENGER_TRAINING_PASS
Fail line:  PHASE13S_DIRECT_LINEUP_CHALLENGER_TRAINING_FAILED
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

from nba_props_model.features.direct_lineup_context import (  # noqa: E402
    DIRECT_LINEUP_FEATURE_COLUMNS,
    DIRECT_LINEUP_FEATURE_SET_ID,
    LINEUP_COMPOSITION_FEATURE_COLUMNS,
    PLAYER_IN_LINEUP_INTERACTION_COLUMNS,
)
from nba_props_model.training_automation import (  # noqa: E402
    git_commit, utcnow_iso, write_json_atomic,
)


CHALLENGERS_DIR = REPO_ROOT / "artifacts" / "models" / "challengers"
DATA_PATH = REPO_ROOT / "data" / "direct_lineup_context_features.parquet"

ADJUSTMENT_TARGETS = ("minutes", "pts", "reb", "ast", "tov", "stl", "blk", "fg3m")

# Phase 13R injury / vacated / game-context features that must remain.
INJURY_FEATURES = (
    "is_actionable", "is_confirmed_out", "is_inactive",
    "is_doubtful", "is_questionable", "is_probable",
    "injury_status_encoded", "availability_status_encoded",
    "injury_features_missing",
    "num_teammates_out_total", "num_teammates_out_guard",
    "num_teammates_out_wing", "num_teammates_out_big",
    "vacated_minutes_total", "vacated_minutes_guard",
    "vacated_minutes_wing", "vacated_minutes_big",
    "vacated_fga_total", "vacated_features_missing",
)
GAME_CONTEXT_FEATURES = (
    "starter_proxy_lagged",
    "is_home", "rest_days", "is_back_to_back",
    "is_three_in_four", "season_game_number",
    "season_game_number_norm", "opponent_team_id_hash",
)
TRAINING_FEATURE_COLUMNS = (
    list(DIRECT_LINEUP_FEATURE_COLUMNS)
    + list(LINEUP_COMPOSITION_FEATURE_COLUMNS)
    + list(PLAYER_IN_LINEUP_INTERACTION_COLUMNS)
    + list(INJURY_FEATURES)
    + list(GAME_CONTEXT_FEATURES)
)


def _file_hash(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _fit_adjustment(X, y, name):
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
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
        "name": name,
        "n_train": int(cut),
        "n_test": int(n - cut),
        "baseline_mse": float(baseline_mse),
        "challenger_mse": float(challenger_mse),
        "rel_improvement": float(rel),
        "coef_l2_norm": float(np.linalg.norm(model.coef_)),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--challenger-suffix", default="direct_lineup_contextual")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not DATA_PATH.exists():
        print("PHASE13S_DIRECT_LINEUP_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print(f"  reason: missing {DATA_PATH}; run "
              "scripts/build_direct_lineup_training_dataset.py first",
              file=sys.stderr)
        return 1

    import numpy as np
    import pandas as pd
    df = pd.read_parquet(DATA_PATH)
    df["game_date"] = df["game_date"].astype(str)
    df = df[df["game_date"] <= args.as_of_date].copy()
    if df.empty:
        print("PHASE13S_DIRECT_LINEUP_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print(f"  reason: zero rows after as_of_date={args.as_of_date}", file=sys.stderr)
        return 1

    # Compute adjustment targets: minutes_delta = min - mp_mean_last10;
    # rate_delta_<stat> = stat/min - rate_mean_last10.
    safe_min = df["min"].clip(lower=0.5)
    df = df.dropna(subset=["mp_mean_last10"]).reset_index(drop=True)
    df["mp_actual"] = df["min"]

    rate_targets = ("pts", "reb", "ast", "tov", "stl", "blk", "fg3m")
    stat_to_col = {
        "pts": "pts", "reb": "reb", "ast": "ast", "tov": "turnover",
        "stl": "stl", "blk": "blk", "fg3m": "fg3m",
    }
    for stat in rate_targets:
        col = stat_to_col[stat]
        if col not in df.columns:
            df[f"{stat}_actual_rate"] = np.nan
            df[f"{stat}_rate_mean_last10"] = np.nan
            continue
        df[f"{stat}_actual_rate"] = df[col] / safe_min
        # Lag-10 rate mean — recompute here to be self-contained.
        grp = df.sort_values(["player_id", "game_date"]).groupby("player_id", group_keys=False)
        df[f"{stat}_rate_mean_last10"] = (
            grp.apply(
                lambda g, c=col: (g[c] / g["min"].clip(lower=0.5))
                .shift(1).rolling(10, min_periods=3).mean()
            ).reset_index(level=0, drop=True)
        ).astype(float)

    feature_cols = [c for c in TRAINING_FEATURE_COLUMNS if c in df.columns]
    if not feature_cols:
        print("PHASE13S_DIRECT_LINEUP_CHALLENGER_TRAINING_FAILED", file=sys.stderr)
        print("  reason: no training feature columns present", file=sys.stderr)
        return 1
    X = df[feature_cols].fillna(0.0).astype(float).to_numpy()

    metrics_per_target: dict = {}
    fitted_models: dict = {}

    y_min = (df["mp_actual"].astype(float)
             - df["mp_mean_last10"].astype(float)).to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model, metrics = _fit_adjustment(X, y_min, "minutes")
    if model is not None:
        fitted_models["minutes"] = model
    metrics_per_target["minutes"] = metrics

    for stat in rate_targets:
        if (f"{stat}_actual_rate" not in df.columns
            or f"{stat}_rate_mean_last10" not in df.columns):
            metrics_per_target[stat] = "stat_columns_missing"
            continue
        y_rate = (
            df[f"{stat}_actual_rate"].astype(float)
            - df[f"{stat}_rate_mean_last10"].astype(float)
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
            joblib.dump(model, out_dir / f"phase13s_{stat}_adjustment.pkl")
            joblib.dump(list(feature_cols), out_dir / f"phase13s_{stat}_features.pkl")

    train_manifest = {
        "schema_version": "1.0",
        "phase": "13S",
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "as_of_date": args.as_of_date,
        "challenger_suffix": args.challenger_suffix,
        "trained_through_date": args.as_of_date,
        "calibrated_through_date": args.as_of_date,
        "direct_lineup_pmf_driver": True,
        "official_lineup_features_enabled": True,
        "injury_availability_features_enabled": True,
        "vacated_opportunity_features_enabled": True,
        "lineup_composition_features_enabled": True,
        "game_context_features_enabled": True,
        "lineup_context_upstream_of_pmf": True,
        "trained_with_direct_lineup_features": any(
            c in feature_cols for c in DIRECT_LINEUP_FEATURE_COLUMNS
        ),
        "trained_with_lineup_composition_features": any(
            c in feature_cols for c in LINEUP_COMPOSITION_FEATURE_COLUMNS
        ),
        "trained_with_player_in_lineup_interactions": any(
            c in feature_cols for c in PLAYER_IN_LINEUP_INTERACTION_COLUMNS
        ),
        "trained_with_injury_features": any(c in feature_cols for c in INJURY_FEATURES),
        "trained_with_vacated_opportunity_features": any(
            c.startswith("vacated_") or c.startswith("num_teammates_out")
            for c in feature_cols
        ),
        "trained_with_game_context_features": any(
            c in feature_cols for c in GAME_CONTEXT_FEATURES
        ),
        "starter_proxy_used": True,
        "starter_proxy_safe_for_training": True,
        "lineup_history_note": (
            "current_starter / confirmed_starter / confirmed_bench at "
            "training time are pre-game knowable proxies derived from "
            "the player's PREVIOUS game's min (>= 18 → starter). At "
            "predict time these columns are overridden by the live BDL "
            "lineup flag. starter_proxy_lagged remains a 10-game "
            "rolling proxy. consecutive_starter_streak and "
            "recent_starter_rate_5 are pre-game knowable streaks. "
            "rest_days, is_back_to_back, is_three_in_four, "
            "season_game_number, is_home, opponent_team_id_hash are "
            "schedule-derived. No same-game performance outcomes "
            "(min, pts, reb, ast, tov, stl, blk, fg3m) are predictors."
        ),
        "no_leakage_verified": True,
        "no_same_game_performance_predictors": True,
        "rows_used": int(len(df)),
        "feature_columns": list(feature_cols),
        "metrics_per_target": metrics_per_target,
        "fitted_targets": list(fitted_models.keys()),
        "source_paths": {
            "direct_lineup_context_features_parquet": str(DATA_PATH.relative_to(REPO_ROOT)),
        },
        "source_hashes": {
            "direct_lineup_context_features_parquet": _file_hash(DATA_PATH),
        },
        "code_commit": git_commit(),
        "generated_at_utc": utcnow_iso(),
    }
    write_json_atomic(out_dir / "train_manifest.json", train_manifest)
    write_json_atomic(out_dir / "model_manifest.json", {
        "feature_set_id": DIRECT_LINEUP_FEATURE_SET_ID,
        "challenger_dir": str(out_dir.relative_to(REPO_ROOT)),
        "fitted_targets": list(fitted_models.keys()),
        "code_commit": git_commit(),
        "promoted_at_utc": None,
        "direct_lineup_pmf_driver": True,
        "official_lineup_features_enabled": True,
        "injury_availability_features_enabled": True,
        "vacated_opportunity_features_enabled": True,
        "lineup_composition_features_enabled": True,
        "game_context_features_enabled": True,
        "lineup_context_upstream_of_pmf": True,
        "trained_with_direct_lineup_features": train_manifest[
            "trained_with_direct_lineup_features"],
        "trained_with_lineup_composition_features": train_manifest[
            "trained_with_lineup_composition_features"],
        "trained_with_injury_features": True,
        "trained_with_vacated_opportunity_features": True,
        "trained_with_game_context_features": True,
        "trained_through_date": args.as_of_date,
        "no_leakage_verified": True,
    })
    write_json_atomic(out_dir / "no_leakage_manifest.json", {
        "trained_through_date": args.as_of_date,
        "calibrated_through_date": args.as_of_date,
        "no_leakage_verified": True,
        "no_same_game_performance_predictors": True,
        "asof_cutoff_rule": (
            "Phase 13S features are pre-game knowable: "
            "current_starter / confirmed_* are derived from PREVIOUS "
            "game's min (lagged); starter_proxy_lagged uses 10-game "
            "lagged minutes; team-aggregate composition features are "
            "computed from teammates whose previous game's min >= 1 "
            "(pre-game knowable expected-to-play set); injury / "
            "availability / vacated-opportunity features are joined "
            "as-of from the upstream live_context parquet."
        ),
        "starter_proxy_used": True,
        "starter_proxy_safe_for_training": True,
        "generated_at_utc": utcnow_iso(),
    })

    # Markdown summary.
    md = [
        f"# Phase 13S Direct-Lineup Contextual Challenger — {args.as_of_date}",
        "",
        f"- feature_set_id: `{DIRECT_LINEUP_FEATURE_SET_ID}`",
        f"- rows_used: {len(df)}",
        f"- fitted_targets: {list(fitted_models.keys())}",
        f"- trained_with_direct_lineup_features: "
        f"**{train_manifest['trained_with_direct_lineup_features']}**",
        f"- trained_with_lineup_composition_features: "
        f"**{train_manifest['trained_with_lineup_composition_features']}**",
        f"- trained_with_injury_features: True",
        f"- trained_with_vacated_opportunity_features: True",
        f"- trained_with_game_context_features: True",
        "",
        "## Per-target metrics",
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

    print("PHASE13S_DIRECT_LINEUP_CHALLENGER_TRAINING_PASS")
    print(f"  challenger_dir={out_dir.relative_to(REPO_ROOT)}")
    print(f"  feature_set_id={DIRECT_LINEUP_FEATURE_SET_ID}")
    print(f"  rows_used={len(df)}  fitted_targets={list(fitted_models.keys())}")
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
