#!/usr/bin/env python3
"""Walk-forward OOF minutes distribution diagnostics (M8.6 Phase 3/4).

This script produces an OOF table suitable for *role- and availability-aware*
minutes diagnostics, including explicit DNP labels.

Key idea:
- `data/player_game_stats.parquet` contains only players who appeared in the box
  score (min >= 1), so it cannot represent DNP rows.
- `data/player_availability_asof.parquet` provides the per-(player, game_date)
  as-of availability snapshot; we treat its row-set as the evaluation universe
  and left-join box-score minutes to create `minutes_actual` with zeros for
  DNPs.

Outputs:
  - data/oof_minutes_predictions.parquet
  - artifacts/models/minutes_model_meta.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PARQUET = REPO_ROOT / "data" / "player_game_stats.parquet"
AVAIL = REPO_ROOT / "data" / "player_availability_asof.parquet"
OOF_OUT = REPO_ROOT / "data" / "oof_minutes_predictions.parquet"
MODEL_DIR = REPO_ROOT / "artifacts" / "models"
META = MODEL_DIR / "minutes_model_meta.json"


def _safe_logloss(y_true: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(y_true, dtype=float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _interp_quantile(q10: float, q50: float, q90: float, tau: float) -> float:
    """Piecewise-linear interpolation of an active-minutes quantile ladder."""
    t = float(np.clip(tau, 1e-6, 1 - 1e-6))
    if t <= 0.10:
        # Extend linearly from (0, 0) to (0.1, q10)
        return float(max(0.0, q10 * (t / 0.10)))
    if t <= 0.50:
        w = (t - 0.10) / 0.40
        return float(q10 + w * (q50 - q10))
    if t <= 0.90:
        w = (t - 0.50) / 0.40
        return float(q50 + w * (q90 - q50))
    # Extend linearly from (0.9, q90) to (1.0, 48)
    return float(q90 + (t - 0.90) / 0.10 * (48.0 - q90))


def _mix_quantile(p0: float, q10_a: float, q50_a: float, q90_a: float, tau: float) -> float:
    """Quantile of mixture: point-mass at 0 with prob p0 + continuous active ladder."""
    p0 = float(np.clip(p0, 0.0, 1.0))
    t = float(np.clip(tau, 1e-6, 1 - 1e-6))
    if t <= p0 + 1e-12:
        return 0.0
    if p0 >= 1.0 - 1e-12:
        return 0.0
    t_adj = (t - p0) / (1.0 - p0)
    return float(np.clip(_interp_quantile(q10_a, q50_a, q90_a, t_adj), 0.0, 48.0))


def _actual_role_bucket(minutes_actual: float) -> str:
    m = float(minutes_actual)
    if m <= 0.0:
        return "inactive_risk"
    if m < 12.0:
        return "fringe"
    if m < 18.0:
        return "bench"
    if m < 24.0:
        return "rotation"
    if m < 30.0:
        return "core"
    return "starter"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-train-rows", type=int, default=2000)
    ap.add_argument("--min-residuals", type=int, default=2000)
    args = ap.parse_args()

    if not PARQUET.exists():
        print("FATAL: missing data/player_game_stats.parquet", file=sys.stderr)
        return 2
    if not AVAIL.exists():
        print("FATAL: missing data/player_availability_asof.parquet", file=sys.stderr)
        return 2

    # Availability defines the evaluation universe (includes inactive rows).
    avail = pd.read_parquet(
        AVAIL,
        columns=[
            "player_id",
            "team_id",
            "game_date",
            "prob_active",
            "availability_status",
            "availability_confidence",
            "days_since_last_played",
            "games_since_last_played",
            "is_returning_from_absence",
            "minutes_restriction_flag",
            "num_teammates_out_total",
            "vacated_minutes_guard",
            "vacated_minutes_wing",
            "vacated_minutes_big",
            "teammate_out_count_guard",
            "teammate_out_count_wing",
            "teammate_out_count_big",
            "vacated_fga_total",
        ],
    )
    avail = avail.dropna(subset=["player_id", "game_date"]).copy()
    avail["game_date"] = pd.to_datetime(avail["game_date"])
    avail["player_id"] = avail["player_id"].astype(int)
    avail["prob_active"] = pd.to_numeric(avail["prob_active"], errors="coerce").fillna(0.95).clip(0.0, 1.0)

    # Box-score minutes for active players only.
    box = pd.read_parquet(PARQUET, columns=["player_id", "game_date", "min"])
    box = box.dropna(subset=["player_id", "game_date", "min"]).copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["player_id"] = box["player_id"].astype(int)
    box["minutes_actual"] = pd.to_numeric(box["min"], errors="coerce").fillna(0.0).clip(0.0, 60.0)
    box = box[["player_id", "game_date", "minutes_actual"]]

    # Join: missing minutes => DNP with minutes=0.
    base_df = avail.merge(box, on=["player_id", "game_date"], how="left")
    base_df["minutes_actual"] = base_df["minutes_actual"].fillna(0.0).astype(float)
    base_df["dnp_actual"] = (base_df["minutes_actual"] <= 0.0).astype(int)

    # Rolling features computed from realized minutes (including zeros), shifted by 1 game.
    base_df = base_df.sort_values(["player_id", "game_date"]).reset_index(drop=True)
    g = base_df.groupby("player_id", sort=False)["minutes_actual"]
    base_df["roll3"] = g.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    base_df["roll10"] = g.transform(lambda s: s.shift(1).rolling(10, min_periods=2).mean())
    base_df["p_active_roll20"] = g.transform(lambda s: (s.shift(1).rolling(20, min_periods=5).apply(lambda x: np.mean(np.asarray(x) > 0.0), raw=False)))
    base_df["minutes_baseline_roll10"] = base_df["roll10"]

    # Active-minutes training set excludes DNP rows.
    work = base_df.dropna(subset=["roll10"]).copy()
    feature_cols = [
        "roll3",
        "roll10",
        "p_active_roll20",
        "prob_active",
        "availability_confidence",
        "days_since_last_played",
        "games_since_last_played",
        "is_returning_from_absence",
        "minutes_restriction_flag",
        "num_teammates_out_total",
        "vacated_minutes_guard",
        "vacated_minutes_wing",
        "vacated_minutes_big",
        "teammate_out_count_guard",
        "teammate_out_count_wing",
        "teammate_out_count_big",
        "vacated_fga_total",
    ]
    for c in feature_cols:
        work[c] = pd.to_numeric(work[c], errors="coerce").fillna(0.0)

    dates = sorted(work["game_date"].unique())
    oof_rows: list[dict] = []

    try:
        from sklearn.linear_model import Ridge
    except Exception:
        Ridge = None  # type: ignore

    from nba_props_model.calibration.role_buckets import role_bucket_from_minutes_dist

    class _ProxyDist:
        __slots__ = ("_mu", "_q25", "state_probs")

        def __init__(self, mu: float, q25: float, p_inactive: float) -> None:
            self._mu = float(mu)
            self._q25 = float(q25)
            p0 = float(np.clip(p_inactive, 0.0, 1.0))
            # We don't model limited/normal split here; bucket logic only needs p0 + q25 + mean.
            self.state_probs = (p0, 0.0, 1.0 - p0)

        def mean(self) -> float:
            return self._mu

        def quantile(self, q: float) -> float:
            if abs(float(q) - 0.25) < 1e-9:
                return self._q25
            return self._mu

    for d in dates:
        train = work[work["game_date"] < d]
        test = work[work["game_date"] == d]
        if len(test) == 0:
            continue

        # DNP probability prediction comes from availability (as-of) signal.
        p_active_pred = test["prob_active"].to_numpy(dtype=float)
        p_dnp_pred = 1.0 - p_active_pred

        # Active-minutes regression (fit only on active rows in train).
        tr_active = train[train["dnp_actual"] == 0]
        te_X = test[feature_cols].to_numpy(dtype=float)
        base_active_mean = test["minutes_baseline_roll10"].fillna(0.0).to_numpy(dtype=float)
        if Ridge is not None and len(tr_active) >= args.min_train_rows:
            Xtr = tr_active[feature_cols].to_numpy(dtype=float)
            ytr = tr_active["minutes_actual"].to_numpy(dtype=float)
            m = Ridge(alpha=2.0, random_state=0)
            m.fit(Xtr, ytr)
            mean_active = m.predict(te_X)
            # Residual ladder from training active rows.
            resid = ytr - m.predict(Xtr)
        else:
            mean_active = base_active_mean.copy()
            resid = tr_active["minutes_actual"].to_numpy(dtype=float) - tr_active["minutes_baseline_roll10"].fillna(0.0).to_numpy(dtype=float)

        mean_active = np.clip(mean_active, 0.0, 48.0)
        if len(resid) >= args.min_residuals:
            qres10, qres50, qres90 = np.quantile(resid, [0.10, 0.50, 0.90]).tolist()
        elif len(resid) > 20:
            qres10, qres50, qres90 = np.quantile(resid, [0.10, 0.50, 0.90]).tolist()
        else:
            qres10, qres50, qres90 = (-6.0, 0.0, 6.0)

        q10_a = np.clip(mean_active + qres10, 0.0, 48.0)
        q50_a = np.clip(mean_active + qres50, 0.0, 48.0)
        q90_a = np.clip(mean_active + qres90, 0.0, 48.0)

        minutes_pred = (1.0 - p_dnp_pred) * mean_active
        q10 = np.array([_mix_quantile(p0, a10, a50, a90, 0.10) for p0, a10, a50, a90 in zip(p_dnp_pred, q10_a, q50_a, q90_a)], dtype=float)
        q50 = np.array([_mix_quantile(p0, a10, a50, a90, 0.50) for p0, a10, a50, a90 in zip(p_dnp_pred, q10_a, q50_a, q90_a)], dtype=float)
        q90 = np.array([_mix_quantile(p0, a10, a50, a90, 0.90) for p0, a10, a50, a90 in zip(p_dnp_pred, q10_a, q50_a, q90_a)], dtype=float)
        q25 = np.array([_mix_quantile(p0, a10, a50, a90, 0.25) for p0, a10, a50, a90 in zip(p_dnp_pred, q10_a, q50_a, q90_a)], dtype=float)

        for i, r in enumerate(test.itertuples(index=False)):
            mu = float(minutes_pred[i])
            role_pred = role_bucket_from_minutes_dist(_ProxyDist(mu=mu, q25=float(q25[i]), p_inactive=float(p_dnp_pred[i])))
            role_actual = _actual_role_bucket(float(getattr(r, "minutes_actual")))
            oof_rows.append(
                {
                    "game_date": str(pd.Timestamp(d).date()),
                    "player_id": int(getattr(r, "player_id")),
                    "team_id": int(getattr(r, "team_id")),
                    "minutes_actual": float(getattr(r, "minutes_actual")),
                    "dnp_actual": int(getattr(r, "dnp_actual")),
                    "active_prob_pred": float(p_active_pred[i]),
                    "dnp_prob_pred": float(p_dnp_pred[i]),
                    "minutes_pred_active_mean": float(mean_active[i]),
                    "minutes_pred": float(minutes_pred[i]),
                    "minutes_q10": float(q10[i]),
                    "minutes_q50": float(q50[i]),
                    "minutes_q90": float(q90[i]),
                    "minutes_baseline_roll10": float(getattr(r, "minutes_baseline_roll10")),
                    "availability_status": str(getattr(r, "availability_status")),
                    "availability_confidence": float(getattr(r, "availability_confidence")),
                    "role_bucket_pred": str(role_pred),
                    "role_bucket_actual": str(role_actual),
                }
            )

    if not oof_rows:
        print("FATAL: no OOF rows produced", file=sys.stderr)
        return 3

    oof = pd.DataFrame(oof_rows)
    OOF_OUT.parent.mkdir(parents=True, exist_ok=True)
    oof.to_parquet(OOF_OUT, index=False)

    mae_m = float(np.mean(np.abs(oof["minutes_actual"] - oof["minutes_pred"])))
    mae_b = float(np.mean(np.abs(oof["minutes_actual"] - oof["minutes_baseline_roll10"])))
    rmse_m = float(np.sqrt(np.mean((oof["minutes_actual"] - oof["minutes_pred"]) ** 2)))
    dnp_brier = float(np.mean((oof["dnp_actual"] - oof["dnp_prob_pred"]) ** 2))
    active_logloss = _safe_logloss(1 - oof["dnp_actual"].to_numpy(dtype=int), oof["active_prob_pred"].to_numpy(dtype=float))
    # Quantile coverage diagnostics.
    q10_cov = float(np.mean(oof["minutes_actual"].to_numpy(dtype=float) <= oof["minutes_q10"].to_numpy(dtype=float)))
    q50_cov = float(np.mean(oof["minutes_actual"].to_numpy(dtype=float) <= oof["minutes_q50"].to_numpy(dtype=float)))
    q90_cov = float(np.mean(oof["minutes_actual"].to_numpy(dtype=float) <= oof["minutes_q90"].to_numpy(dtype=float)))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "fitted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "oof_rows": int(len(oof)),
        "mae_model": mae_m,
        "mae_baseline_roll10": mae_b,
        "rmse_model": rmse_m,
        "dnp_brier": dnp_brier,
        "active_logloss": active_logloss,
        "q10_coverage": q10_cov,
        "q50_coverage": q50_cov,
        "q90_coverage": q90_cov,
        "sklearn_ridge": Ridge is not None,
        "oof_path": str(OOF_OUT.relative_to(REPO_ROOT)),
    }
    META.write_text(json.dumps(meta, indent=2) + "\n")

    print(
        "MINUTES_MODEL_TRAIN_PASS "
        f"oof_rows={len(oof)} mae_model={mae_m:.3f} mae_baseline={mae_b:.3f} "
        f"dnp_brier={dnp_brier:.4f} active_logloss={active_logloss:.4f} "
        f"q10_cov={q10_cov:.3f} q50_cov={q50_cov:.3f} q90_cov={q90_cov:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
