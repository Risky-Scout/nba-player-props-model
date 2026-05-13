#!/usr/bin/env python3
"""Walk-forward OOF minutes model vs rolling-10 baseline (M8.6 Phase 3).

Uses only past games for each player (shifted rolling means). No target-game
leakage. Writes:
  - data/oof_minutes_predictions.parquet
  - artifacts/models/minutes_model.pkl (sklearn Ridge if available)
  - artifacts/models/minutes_model_meta.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PARQUET = REPO_ROOT / "data" / "player_game_stats.parquet"
OOF_OUT = REPO_ROOT / "data" / "oof_minutes_predictions.parquet"
MODEL_DIR = REPO_ROOT / "artifacts" / "models"
PKL = MODEL_DIR / "minutes_model.pkl"
META = MODEL_DIR / "minutes_model_meta.json"


def _add_lags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["player_id", "game_date"]).copy()
    g = df.groupby("player_id", sort=False)["min"]
    df["roll3"] = g.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    df["roll10"] = g.transform(lambda s: s.shift(1).rolling(10, min_periods=2).mean())
    df["baseline_roll10"] = df["roll10"]
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--walk-forward", action="store_true", default=True)
    ap.add_argument("--min-train-rows", type=int, default=200,
                    help="Minimum training rows per OOF fold to use Ridge (else baseline).")
    args = ap.parse_args()

    if not PARQUET.exists():
        print("FATAL: missing data/player_game_stats.parquet", file=sys.stderr)
        return 2

    raw = pd.read_parquet(PARQUET, columns=["player_id", "game_date", "min"])
    raw = raw.dropna(subset=["player_id", "game_date", "min"])
    raw["game_date"] = pd.to_datetime(raw["game_date"])
    df = _add_lags(raw)
    df = df.dropna(subset=["roll10"])

    unique_dates = sorted(df["game_date"].unique())
    oof_rows: list[dict] = []

    try:
        from sklearn.linear_model import Ridge
    except ImportError:
        Ridge = None  # type: ignore

    for d in unique_dates:
        train = df[df["game_date"] < d]
        test = df[df["game_date"] == d]
        if len(train) < 50 or len(test) == 0:
            continue
        Xtr = train[["roll3", "roll10"]].fillna(0).values
        ytr = train["min"].values
        Xte = test[["roll3", "roll10"]].fillna(0).values
        yte = test["min"].values
        base = test["baseline_roll10"].fillna(test["min"]).values

        if Ridge is not None and len(train) >= args.min_train_rows:
            m = Ridge(alpha=2.0, random_state=0)
            m.fit(Xtr, ytr)
            pred = m.predict(Xte)
        else:
            pred = base.copy()

        for i, r in test.reset_index(drop=True).iterrows():
            oof_rows.append({
                "game_date": str(d.date()),
                "player_id": int(r["player_id"]),
                "minutes_actual": float(yte[i]),
                "minutes_pred": float(pred[i]),
                "minutes_baseline_roll10": float(base[i]),
            })

    if not oof_rows:
        print("FATAL: no OOF rows produced", file=sys.stderr)
        return 3

    oof = pd.DataFrame(oof_rows)
    OOF_OUT.parent.mkdir(parents=True, exist_ok=True)
    oof.to_parquet(OOF_OUT, index=False)

    mae_m = float(np.mean(np.abs(oof["minutes_actual"] - oof["minutes_pred"])))
    mae_b = float(np.mean(np.abs(oof["minutes_actual"] - oof["minutes_baseline_roll10"])))
    rmse_m = float(np.sqrt(np.mean((oof["minutes_actual"] - oof["minutes_pred"]) ** 2)))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "fitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "oof_rows": int(len(oof)),
        "mae_model": mae_m,
        "mae_baseline_roll10": mae_b,
        "rmse_model": rmse_m,
        "walk_forward": bool(args.walk_forward),
        "sklearn_ridge": Ridge is not None,
        "oof_path": str(OOF_OUT.relative_to(REPO_ROOT)),
    }
    META.write_text(json.dumps(meta, indent=2) + "\n")

    if Ridge is not None:
        # Final fit on all data for deployment artifact
        X = df[["roll3", "roll10"]].fillna(0).values
        y = df["min"].values
        final = Ridge(alpha=2.0, random_state=0)
        final.fit(X, y)
        import joblib

        joblib.dump({"model": final, "feature_names": ["roll3", "roll10"]}, PKL)
        meta["model_path"] = str(PKL.relative_to(REPO_ROOT))
        META.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"MINUTES_MODEL_TRAIN_PASS oof_rows={len(oof)} mae_model={mae_m:.3f} mae_baseline={mae_b:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
