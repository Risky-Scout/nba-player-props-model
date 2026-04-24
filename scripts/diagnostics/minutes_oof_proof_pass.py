"""Minutes OOF proof pass — Phase A audit + Phase B minutes-side what-if.

Read-only experiment. Uses existing production helpers verbatim:
  - nba_props_model.models.minutes.minutes_distribution
  - nba_props_model.models.minutes.MinutesDistribution
  - nba_props_model.models.simulation.simulate_stat_pmf

Scope is strictly diagnostic — no production files are touched.

The script runs in this order:

  0. MATCH AUDIT (always prints first):
     Join the fold-1 universe to player_game_stats.parquet and
     training_table.parquet and report `n_fold_universe`,
     `n_matched_stats`, `n_matched_features`, `n_fully_auditable_rows`,
     `n_dropped_rows`, and a per-reason dropped-row breakdown. Rows that
     fail any prerequisite (no box score, no feature row, no strictly
     prior history) are excluded from the rest of the pass.

  1. PHASE A — minutes audit + per-stat decomposition on the audited
     universe only. For each (player_id, game_id, game_date) in the
     audited set, call minutes_distribution(), record predicted mean /
     quantiles / state probs + the realized `min` from the box score,
     then aggregate:
       - minutes audit (MAE, quantile coverage, P(min=0), P(<=12), etc.)
       - bucketed minutes bias
       - per-stat decomposition of the pred-vs-realized mean gap into a
         minutes component and a rate component, with a dominance label.
         PMF means for pts/reb/ast are computed ONLY on fold_1 rows whose
         (player_id, game_id) is in the auditable key set so the three
         quantities (pred_stat_mean, pred_minutes_mean, realized_mean)
         all live on the same universe.

  2. PHASE A stop condition:
     If all three ship-candidate stats (pts, reb, ast) classify as
     "rate_dominant", skip Phase B and recommend a rate-side pivot.

  3. PHASE B — minutes-side what-if (conditional):
     Fit an isotonic mapping predicted_mean_min -> realized_min on the
     fold. Recenter each MinutesDistribution by adding
     (mu_target - mu_current) to every conditional quantile value,
     clamping to [0, 48]. The constructor's band-clamp
     ([0, 24] limited, [24, 48] normal) will absorb some of the intended
     shift near the boundary — the actual achieved shift is reported.
     For pts/reb/ast, re-run simulate_stat_pmf on the recentered dist
     and compare BEFORE vs AFTER on an EXACT same-row keyed set. Rows
     whose AFTER PMF fails are excluded from BOTH BEFORE and AFTER.

  4. PHASE B coverage:
     `n_phase_b_rows`, `pct_phase_b_rows_of_fold_universe`, and a
     `coverage_limited` flag (true when < 90%) are reported and, when
     true, the final recommendation line includes a note stating that
     the Phase B result alone should not trigger productionization.

CLI:
    python scripts/diagnostics/minutes_oof_proof_pass.py \\
        --fold-oof artifacts/fold_1.parquet \\
        --stats-df data/player_game_stats.parquet \\
        --features-df data/training_table.parquet \\
        --minutes-models-dir artifacts/models \\
        --output-dir artifacts/diagnostics/fold_1_minutes_proof \\
        --n-draws 2000

If any required input cannot be reconstructed cleanly (after the MATCH
AUDIT is printed), the script fails loud with the exact missing
(player_id, game_id, game_date). No silent approximation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


LOGLOSS_EPS = 1e-6
SHIP_STATS = ("pts", "reb", "ast")


# ── small utilities ────────────────────────────────────────────────────────


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _require_path(p: Path, label: str) -> None:
    if not p.exists():
        _die(f"{label} not found: {p}")


# ── input loaders ──────────────────────────────────────────────────────────


def _load_fold_universe(fold_path: Path) -> pd.DataFrame:
    _require_path(fold_path, "--fold-oof")
    df = pd.read_parquet(fold_path)
    required = {"stat", "player_id", "game_id", "game_date", "outcome", "pmf"}
    missing = required - set(df.columns)
    if missing:
        _die(f"fold_oof missing columns: {sorted(missing)}")
    df = df.copy()
    df["stat"] = df["stat"].astype(str).str.lower()
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    df["outcome"] = df["outcome"].astype(int)
    return df


def _load_stats(stats_path: Path) -> pd.DataFrame:
    _require_path(stats_path, "--stats-df")
    cols = [
        "player_id", "game_id", "game_date", "team_id", "home_team_id",
        "min", "pts", "reb", "ast",
    ]
    df = pd.read_parquet(stats_path, columns=cols)
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    df["min"] = pd.to_numeric(df["min"], errors="coerce").fillna(0.0)
    for c in ("pts", "reb", "ast"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df


def _load_features(features_path: Path) -> pd.DataFrame:
    _require_path(features_path, "--features-df")
    df = pd.read_parquet(features_path)
    if "stat" not in df.columns:
        _die("training_table missing 'stat' column")
    # One row per (player_id, game_id); feature values identical across
    # stats at the same player-game, so pin to pts.
    df = df[df["stat"].astype(str).str.lower() == "pts"].copy()
    df["player_id"] = df["player_id"].astype(int)
    df["game_id"] = df["game_id"].astype(int)
    return df


def _load_availability_lookup() -> dict:
    """Load the as-of availability parquet via the standard path.
    Returns {(player_id, YYYY-MM-DD): availability dict}."""
    from nba_props_model.paths import DATA_DIR
    p = DATA_DIR / "player_availability_asof.parquet"
    if not p.exists():
        print(
            f"WARN: {p} missing; availability will be passed as None "
            f"(matches phase-8 behavior when artifact absent)."
        )
        return {}
    df = pd.read_parquet(p)
    df["game_date"] = df["game_date"].astype(str).str.slice(0, 10)
    cols = [c for c in df.columns if c not in ("player_id", "game_date", "team_id")]
    out: dict = {}
    for r in df.itertuples(index=False):
        out[(int(r.player_id), str(r.game_date))] = {
            c: getattr(r, c, None) for c in cols
        }
    return out


# ── match audit ────────────────────────────────────────────────────────────


def _match_audit(
    universe: pd.DataFrame,
    stats_df: pd.DataFrame,
    features_df: pd.DataFrame,
    stats_by_player: dict[int, pd.DataFrame],
) -> dict:
    """Aggregate join audit computed BEFORE any per-row work.

    Returns both the printable counts and the set of fully-auditable
    (player_id, game_id, game_date) triples. Does not touch
    minutes_distribution / simulate_stat_pmf.
    """
    n_universe = int(len(universe))
    stats_keys = set(
        (int(pid), int(gid))
        for pid, gid in zip(stats_df["player_id"], stats_df["game_id"])
    )
    feat_keys = set(
        (int(pid), int(gid))
        for pid, gid in zip(features_df["player_id"], features_df["game_id"])
    )
    rows_no_box: list[tuple] = []
    rows_no_features: list[tuple] = []
    rows_no_prior_history: list[tuple] = []
    rows_other: list[tuple] = []
    auditable: list[tuple] = []
    for u in universe.itertuples(index=False):
        pid = int(u.player_id); gid = int(u.game_id); gdate = str(u.game_date)
        key = (pid, gid)
        has_box = key in stats_keys
        has_feat = key in feat_keys
        # Strictly-prior history requires any stats row for this player
        # dated before game_date. Use the pre-grouped map for an O(log N)
        # check.
        hist = stats_by_player.get(pid)
        has_prior = bool(hist is not None and len(hist[hist["game_date"] < gdate]) >= 1)
        if has_box and has_feat and has_prior:
            auditable.append((pid, gid, gdate))
            continue
        # Classify the drop reason in priority order. A row may fail more
        # than one check; we report the first.
        if not has_box:
            rows_no_box.append((pid, gid, gdate))
        elif not has_feat:
            rows_no_features.append((pid, gid, gdate))
        elif not has_prior:
            rows_no_prior_history.append((pid, gid, gdate))
        else:
            rows_other.append((pid, gid, gdate))
    n_matched_stats = int(sum(
        1 for u in universe.itertuples(index=False)
        if (int(u.player_id), int(u.game_id)) in stats_keys
    ))
    n_matched_features = int(sum(
        1 for u in universe.itertuples(index=False)
        if (int(u.player_id), int(u.game_id)) in feat_keys
    ))
    audit = {
        "n_fold_universe": n_universe,
        "n_matched_stats": n_matched_stats,
        "n_matched_features": n_matched_features,
        "n_fully_auditable_rows": int(len(auditable)),
        "n_dropped_rows": int(n_universe - len(auditable)),
        "dropped_reasons": {
            "no_box_score_row": int(len(rows_no_box)),
            "no_feature_row": int(len(rows_no_features)),
            "no_strictly_prior_history": int(len(rows_no_prior_history)),
            "other": int(len(rows_other)),
        },
        "dropped_samples": {
            "no_box_score_row": rows_no_box[:5],
            "no_feature_row": rows_no_features[:5],
            "no_strictly_prior_history": rows_no_prior_history[:5],
            "other": rows_other[:5],
        },
    }
    return {"audit": audit, "auditable_keys": set((p, g) for p, g, _ in auditable)}


def _print_match_audit(audit: dict) -> None:
    print("\n=== MATCH AUDIT ===")
    print(f"  n_fold_universe           = {audit['n_fold_universe']:,}")
    print(f"  n_matched_stats           = {audit['n_matched_stats']:,}")
    print(f"  n_matched_features        = {audit['n_matched_features']:,}")
    print(f"  n_fully_auditable_rows    = {audit['n_fully_auditable_rows']:,}")
    print(f"  n_dropped_rows            = {audit['n_dropped_rows']:,}")
    print("  dropped_reasons:")
    for k, v in audit["dropped_reasons"].items():
        print(f"    {k:<28}  {v:,}")


# ── minutes-distribution reconstruction ───────────────────────────────────


def _rebuild_inputs(
    player_id: int,
    game_id: int,
    game_date: str,
    stats_df: pd.DataFrame,
    stats_by_player: dict[int, pd.DataFrame],
    avail_lookup: dict,
) -> dict:
    """Rebuild the exact argument bundle minutes_distribution() expects.

    Fail-loud on any missing input rather than approximate. The MATCH
    AUDIT has already filtered out missing rows, so these errors are
    defense-in-depth.
    """
    history = stats_by_player.get(player_id)
    if history is None:
        _die(f"no history rows in player_game_stats for player_id={player_id}")
    prior = history[history["game_date"] < game_date]
    if len(prior) < 1:
        _die(
            f"no strictly-prior game in player_game_stats for "
            f"(player_id={player_id}, game_date={game_date})"
        )

    row = history[history["game_date"] == game_date]
    row = row[row["game_id"] == game_id]
    if row.empty:
        _die(
            f"no box-score row for (player_id={player_id}, "
            f"game_id={game_id}, game_date={game_date})"
        )
    row = row.iloc[0]
    team_id = int(row["team_id"])
    home_team_id = int(row["home_team_id"])
    is_home = (team_id == home_team_id)
    realized_min = float(row["min"])
    realized_pts = int(row["pts"])
    realized_reb = int(row["reb"])
    realized_ast = int(row["ast"])

    prev = prior.tail(1)
    rest_days = 2
    if len(prev):
        prev_date = pd.to_datetime(prev.iloc[-1]["game_date"])
        rest_days = int((pd.to_datetime(game_date) - prev_date).days)
    b2b = 1 if rest_days == 1 else 0

    avail = avail_lookup.get((player_id, game_date))

    return {
        "prior_stats": prior,
        "game_context": {"rest_days": rest_days, "back_to_back": b2b},
        "is_home": bool(is_home),
        "target_date": game_date,
        "team_id": team_id,
        "all_stats_df": stats_df,
        "injury_map": {},
        "availability": avail,
        "realized_min": realized_min,
        "realized_pts": realized_pts,
        "realized_reb": realized_reb,
        "realized_ast": realized_ast,
    }


def _recentered_distribution(dist, shift: float):
    """Uniform-shift recentering.

    Adds `shift` to every conditional quantile value and clamps to
    [0, 48]. The constructor's band-clamp on limited_quantiles
    ([0, LIMITED_UPPER]) and normal_quantiles ([LIMITED_UPPER, 48]) will
    absorb part of the shift near the boundary; that is acceptable per
    the Phase B spec and the achieved shift is reported separately.
    state_probs are preserved so P(inactive) is unchanged.
    """
    from nba_props_model.models.minutes import MinutesDistribution
    if abs(shift) < 0.1:
        return dist
    lim_q = {k: float(np.clip(v + shift, 0.0, 48.0))
             for k, v in dist.limited_quantiles.items()}
    nor_q = {k: float(np.clip(v + shift, 0.0, 48.0))
             for k, v in dist.normal_quantiles.items()}
    return MinutesDistribution(
        state_probs=dist.state_probs,
        limited_quantiles=lim_q,
        normal_quantiles=nor_q,
    )


# ── PMF-level metrics (reused; inlined to avoid cross-module imports) ─────


def _pmf_mean_scalar(pmf: np.ndarray) -> float:
    return float(np.sum(pmf * np.arange(pmf.size)))


def _atom_metrics(P: np.ndarray, outcomes: np.ndarray) -> dict:
    n, max_k = P.shape
    realized = np.zeros_like(P)
    valid = (outcomes >= 0) & (outcomes < max_k)
    realized[np.arange(n)[valid], outcomes[valid]] = 1.0
    pred_mean_vec = P.mean(axis=0)
    emp_vec = realized.mean(axis=0)
    abs_dev = np.abs(pred_mean_vec - emp_vec)
    atom_ece_pred_mass = float(np.sum(pred_mean_vec * abs_dev))
    atom_brier = float(np.mean(np.sum((P - realized) ** 2, axis=1)))
    Pc = np.clip(P, LOGLOSS_EPS, 1 - LOGLOSS_EPS)
    rows_idx = np.arange(n)[valid]
    cols_idx = outcomes[valid]
    if len(rows_idx):
        atom_logloss = float(-np.mean(np.log(Pc[rows_idx, cols_idx])))
    else:
        atom_logloss = float("nan")
    pred_mean = float(np.sum(P * np.arange(max_k)[None, :], axis=1).mean())
    realized_mean = float(outcomes.mean())
    pred_p0 = float(P[:, 0].mean())
    realized_p0 = float((outcomes == 0).mean())
    pred_p_le1 = (
        float((P[:, 0] + P[:, 1]).mean()) if max_k >= 2 else float(P[:, 0].mean())
    )
    realized_p_le1 = float((outcomes <= 1).mean())
    return {
        "n_rows": int(n),
        "atom_ece_pred_mass": atom_ece_pred_mass,
        "atom_brier": atom_brier,
        "atom_logloss": atom_logloss,
        "pred_mean": pred_mean,
        "realized_mean": realized_mean,
        "pred_p0": pred_p0,
        "realized_p0": realized_p0,
        "pred_p_le1": pred_p_le1,
        "realized_p_le1": realized_p_le1,
    }


# ── phase A ───────────────────────────────────────────────────────────────


def _phase_a(
    universe: pd.DataFrame,
    stats_df: pd.DataFrame,
    stats_by_player: dict[int, pd.DataFrame],
    features_df: pd.DataFrame,
    avail_lookup: dict,
    fold_oof: pd.DataFrame,
) -> dict:
    from nba_props_model.models.minutes import minutes_distribution

    features_by_pg = features_df.set_index(["player_id", "game_id"], drop=False)

    rows_pred: list[dict] = []
    for u in universe.itertuples(index=False):
        pid = int(u.player_id); gid = int(u.game_id); gdate = str(u.game_date)
        inputs = _rebuild_inputs(pid, gid, gdate, stats_df, stats_by_player, avail_lookup)
        try:
            dist = minutes_distribution(
                prior_stats=inputs["prior_stats"],
                game_context=inputs["game_context"],
                is_home=inputs["is_home"],
                target_date=inputs["target_date"],
                team_id=inputs["team_id"],
                all_stats_df=inputs["all_stats_df"],
                injury_map=inputs["injury_map"],
                availability=inputs["availability"],
            )
        except Exception as e:
            _die(
                f"minutes_distribution raised for (pid={pid}, gid={gid}, "
                f"date={gdate}): {type(e).__name__}: {e}"
            )
        try:
            q10 = float(dist.quantile(0.10))
            q25 = float(dist.quantile(0.25))
            q50 = float(dist.quantile(0.50))
            q75 = float(dist.quantile(0.75))
            q90 = float(dist.quantile(0.90))
            pred_mean_min = float(dist.mean())
        except Exception as e:
            _die(
                f"dist method call raised for (pid={pid}, gid={gid}, "
                f"date={gdate}): {type(e).__name__}: {e}"
            )
        p_inactive, p_limited, p_normal = dist.state_probs
        rows_pred.append({
            "player_id": pid, "game_id": gid, "game_date": gdate,
            "pred_mean_min": pred_mean_min,
            "q10": q10, "q25": q25, "q50": q50, "q75": q75, "q90": q90,
            "p_inactive": float(p_inactive),
            "p_limited": float(p_limited),
            "p_normal": float(p_normal),
            "realized_min": float(inputs["realized_min"]),
            "realized_pts": int(inputs["realized_pts"]),
            "realized_reb": int(inputs["realized_reb"]),
            "realized_ast": int(inputs["realized_ast"]),
            # Keep dist for phase B (not serialized to JSON).
            "_dist": dist,
        })

    preds = pd.DataFrame(rows_pred)

    # Build the exact auditable key set that `preds` was constructed on.
    # Phase A per-stat decomposition must use only these keys so the
    # minutes-vs-rate split is computed on a single coherent universe.
    auditable_key_set: set[tuple[int, int]] = set(
        (int(pid), int(gid))
        for pid, gid in zip(preds["player_id"], preds["game_id"])
    )

    # ── minutes audit ──
    pred_min = preds["pred_mean_min"].to_numpy()
    real_min = preds["realized_min"].to_numpy()
    mae = float(np.mean(np.abs(pred_min - real_min)))
    medae = float(np.median(np.abs(pred_min - real_min)))
    pred_mean_minutes = float(pred_min.mean())
    realized_mean_minutes = float(real_min.mean())
    diff = realized_mean_minutes - pred_mean_minutes
    pct_diff = 100.0 * diff / max(realized_mean_minutes, 1e-9)
    cov = {
        f"q{q}_coverage": float(np.mean(real_min <= preds[f"q{q}"].to_numpy()))
        for q in (10, 25, 50, 75, 90)
    }
    pred_p_min0 = float(preds["p_inactive"].mean())
    realized_p_min0 = float((real_min == 0).mean())
    pred_p_min_le12 = float(np.mean([d.cdf(12.0) for d in preds["_dist"].tolist()]))
    pred_p_min_lt24 = float(np.mean([d.cdf(24.0 - 1e-9) for d in preds["_dist"].tolist()]))
    pred_p_min_ge32 = float(np.mean([1.0 - d.cdf(32.0) for d in preds["_dist"].tolist()]))
    realized_p_min_le12 = float(np.mean(real_min <= 12.0))
    realized_p_min_lt24 = float(np.mean(real_min < 24.0))
    realized_p_min_ge32 = float(np.mean(real_min >= 32.0))

    mae_passes = bool(mae < 4.5)
    q50_coverage_passes = bool(0.48 <= cov["q50_coverage"] <= 0.52)

    # ── bucketed minutes bias ──
    buckets: list[dict] = []
    edges = [(0, 6), (6, 12), (12, 18), (18, 24), (24, 30), (30, 36), (36, 49)]
    for lo, hi in edges:
        m = (pred_min >= lo) & (pred_min < hi)
        n = int(m.sum())
        if n == 0:
            continue
        mp = float(pred_min[m].mean())
        mr = float(real_min[m].mean())
        bias_pct = 100.0 * (mr - mp) / max(mr, 1e-9)
        buckets.append({
            "bucket": f"{lo}-{hi-1}", "n_rows": n,
            "mean_pred_min": mp, "mean_realized_min": mr, "bias_pct": bias_pct,
        })

    # ── per-stat decomposition on pts/reb/ast (audited universe only) ──
    def _stat_pred_mean_on_auditable(stat: str) -> tuple[float, int]:
        """Return (pred_stat_mean, n_rows_used) restricted to audited keys."""
        sub = fold_oof[fold_oof["stat"] == stat]
        keep_mask = [
            (int(pid), int(gid)) in auditable_key_set
            for pid, gid in zip(sub["player_id"], sub["game_id"])
        ]
        sub = sub.loc[keep_mask]
        if len(sub) == 0:
            return float("nan"), 0
        means = np.array([
            _pmf_mean_scalar(np.asarray(p, dtype=np.float64))
            for p in sub["pmf"].tolist()
        ])
        return float(means.mean()), int(len(sub))

    per_stat: dict = {}
    for stat in SHIP_STATS:
        pred_stat_mean, n_used = _stat_pred_mean_on_auditable(stat)
        realized_col = {"pts": "realized_pts", "reb": "realized_reb", "ast": "realized_ast"}[stat]
        realized_stat_mean = float(preds[realized_col].mean())
        implied_pred_rpm = pred_stat_mean / max(pred_mean_minutes, 1e-6)
        realized_rpm = realized_stat_mean / max(realized_mean_minutes, 1e-6)
        minutes_bias_pct = (realized_mean_minutes - pred_mean_minutes) / max(realized_mean_minutes, 1e-9)
        rate_bias_pct = (realized_rpm - implied_pred_rpm) / max(realized_rpm, 1e-9)
        ma = abs(minutes_bias_pct); ra = abs(rate_bias_pct)
        if ma > 2 * ra:
            cls = "minutes_dominant"
        elif ra > 2 * ma:
            cls = "rate_dominant"
        else:
            cls = "both"
        per_stat[stat] = {
            "n_audited_rows_used_for_stat_mean": n_used,
            "pred_stat_mean": pred_stat_mean,
            "realized_stat_mean": realized_stat_mean,
            "pred_minutes_mean": pred_mean_minutes,
            "realized_minutes_mean": realized_mean_minutes,
            "implied_pred_rate_per_minute": implied_pred_rpm,
            "realized_rate_per_minute": realized_rpm,
            "minutes_bias_pct": float(minutes_bias_pct),
            "rate_bias_pct": float(rate_bias_pct),
            "classification": cls,
        }

    phase_a = {
        "audit": {
            "n_rows": int(len(preds)),
            "pred_mean_minutes": pred_mean_minutes,
            "realized_mean_minutes": realized_mean_minutes,
            "diff": diff,
            "pct_diff": pct_diff,
            "mae": mae,
            "median_ae": medae,
            **cov,
            "pred_p_min0": pred_p_min0,
            "realized_p_min0": realized_p_min0,
            "pred_p_min_le12": pred_p_min_le12,
            "realized_p_min_le12": realized_p_min_le12,
            "pred_p_min_lt24": pred_p_min_lt24,
            "realized_p_min_lt24": realized_p_min_lt24,
            "pred_p_min_ge32": pred_p_min_ge32,
            "realized_p_min_ge32": realized_p_min_ge32,
            "mae_passes": mae_passes,
            "q50_coverage_passes": q50_coverage_passes,
        },
        "bucketed_bias": buckets,
        "per_stat": per_stat,
    }
    return {"phase_a": phase_a, "preds": preds, "features_by_pg": features_by_pg}


def _print_phase_a(phase_a: dict) -> None:
    a = phase_a["audit"]
    print("\n=== PHASE A — MINUTES AUDIT ===")
    print(
        f"  n={a['n_rows']}  pred_mean={a['pred_mean_minutes']:.2f}  "
        f"realized_mean={a['realized_mean_minutes']:.2f}  "
        f"diff={a['diff']:+.2f} ({a['pct_diff']:+.1f}%)"
    )
    print(
        f"  MAE={a['mae']:.2f} (target <4.5, pass={a['mae_passes']})  "
        f"medAE={a['median_ae']:.2f}"
    )
    print(
        f"  quantile coverage: q10={a['q10_coverage']:.3f}  q25={a['q25_coverage']:.3f}  "
        f"q50={a['q50_coverage']:.3f} (target [0.48, 0.52], pass={a['q50_coverage_passes']})  "
        f"q75={a['q75_coverage']:.3f}  q90={a['q90_coverage']:.3f}"
    )
    print(
        f"  P(min=0)  pred={a['pred_p_min0']:.3f}  realized={a['realized_p_min0']:.3f}"
    )
    print(
        f"  P(min<=12) pred={a['pred_p_min_le12']:.3f}  realized={a['realized_p_min_le12']:.3f}  "
        f"P(min<24) pred={a['pred_p_min_lt24']:.3f}  realized={a['realized_p_min_lt24']:.3f}  "
        f"P(min>=32) pred={a['pred_p_min_ge32']:.3f}  realized={a['realized_p_min_ge32']:.3f}"
    )
    print("  bucketed bias (pred_min bucket -> realized):")
    for b in phase_a["bucketed_bias"]:
        print(
            f"    {b['bucket']:>7}  n={b['n_rows']:>5}  pred={b['mean_pred_min']:.2f}  "
            f"real={b['mean_realized_min']:.2f}  bias={b['bias_pct']:+.1f}%"
        )
    print("  per-stat decomposition:")
    for stat, m in phase_a["per_stat"].items():
        print(
            f"    {stat:<4}  pred_mean={m['pred_stat_mean']:.2f}  "
            f"real={m['realized_stat_mean']:.2f}  "
            f"min_bias={100*m['minutes_bias_pct']:+.1f}%  "
            f"rate_bias={100*m['rate_bias_pct']:+.1f}%  "
            f"(n_audited_rows_used={m['n_audited_rows_used_for_stat_mean']})  "
            f"=> {m['classification']}"
        )


# ── phase B ───────────────────────────────────────────────────────────────


def _phase_b(
    preds: pd.DataFrame,
    features_by_pg: pd.DataFrame,
    fold_oof: pd.DataFrame,
    n_draws: int,
    n_fold_universe: int,
) -> dict:
    from sklearn.isotonic import IsotonicRegression
    from nba_props_model.models.simulation import simulate_stat_pmf

    pred_min = preds["pred_mean_min"].to_numpy()
    real_min = preds["realized_min"].to_numpy()
    iso = IsotonicRegression(y_min=0.0, y_max=48.0, out_of_bounds="clip").fit(
        pred_min, real_min,
    )
    preds = preds.copy()
    preds["mu_target"] = iso.predict(pred_min)
    preds["shift"] = preds["mu_target"] - pred_min

    achieved_shifts: list[float] = []
    new_dists: list = []
    for r in preds.itertuples(index=False):
        original = r._dist
        new = _recentered_distribution(original, float(r.shift))
        achieved_shifts.append(float(new.mean() - original.mean()))
        new_dists.append(new)
    preds["achieved_shift"] = achieved_shifts

    feature_row_by_pg = {}
    for pid, gid in zip(preds["player_id"], preds["game_id"]):
        row = features_by_pg.loc[(int(pid), int(gid))]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        feature_row_by_pg[(int(pid), int(gid))] = row.to_dict()

    per_stat_after: dict = {}
    for stat in SHIP_STATS:
        sub_before = fold_oof[fold_oof["stat"] == stat].copy()
        key_to_pmf_before = {
            (int(r.player_id), int(r.game_id)): np.asarray(r.pmf, dtype=np.float64)
            for r in sub_before.itertuples(index=False)
        }
        key_to_outcome = {
            (int(r.player_id), int(r.game_id)): int(r.outcome)
            for r in sub_before.itertuples(index=False)
        }
        rng = np.random.default_rng(0)
        after_pmfs: list[np.ndarray] = []
        outcomes: list[int] = []
        keys: list[tuple[int, int]] = []
        after_failures: list[dict] = []
        for (key, new_dist) in zip(
            zip(preds["player_id"], preds["game_id"]), new_dists
        ):
            key = (int(key[0]), int(key[1]))
            if key not in key_to_pmf_before:
                after_failures.append({"key": key, "reason": "no_before_pmf"})
                continue
            feature_row = feature_row_by_pg[key]
            try:
                pmf_obj = simulate_stat_pmf(
                    stat=stat, minutes_dist=new_dist,
                    feature_row=feature_row, n_draws=n_draws, rng=rng,
                )
            except Exception as e:
                after_failures.append({
                    "key": key, "reason": f"{type(e).__name__}: {e}",
                })
                continue
            if pmf_obj is None:
                after_failures.append({"key": key, "reason": "simulate_returned_none"})
                continue
            after_pmfs.append(np.asarray(pmf_obj.pmf, dtype=np.float64))
            outcomes.append(key_to_outcome[key])
            keys.append(key)
        if not after_pmfs:
            per_stat_after[stat] = {
                "error": "no after pmfs produced",
                "n_before_after_comparable_rows": 0,
                "n_after_failures": int(len(after_failures)),
                "after_failure_samples": after_failures[:5],
            }
            continue
        max_k = max(p.size for p in after_pmfs)
        P_after = np.zeros((len(after_pmfs), max_k), dtype=np.float64)
        for i, p in enumerate(after_pmfs):
            P_after[i, : p.size] = p
        outcomes_arr = np.array(outcomes, dtype=int)
        # Exact same-row BEFORE: only rows that produced an AFTER PMF
        # contribute to the BEFORE comparison block. `keys` is the
        # ordered intersection.
        before_pmfs = [key_to_pmf_before[k] for k in keys]
        max_k_b = max(p.size for p in before_pmfs)
        P_before = np.zeros((len(before_pmfs), max_k_b), dtype=np.float64)
        for i, p in enumerate(before_pmfs):
            P_before[i, : p.size] = p
        before = _atom_metrics(P_before, outcomes_arr)
        after = _atom_metrics(P_after, outcomes_arr)
        delta = {k: after[k] - before[k] for k in (
            "atom_ece_pred_mass", "atom_brier", "atom_logloss",
            "pred_mean", "pred_p0", "pred_p_le1",
        )}
        per_stat_after[stat] = {
            "n_before_after_comparable_rows": int(len(after_pmfs)),
            "n_after_failures": int(len(after_failures)),
            "after_failure_samples": after_failures[:5],
            "before": before,
            "after": after,
            "delta": delta,
        }

    n_phase_b_rows = int(len(preds))
    pct_phase_b_rows = (
        100.0 * n_phase_b_rows / max(n_fold_universe, 1)
    )
    coverage_limited = bool(pct_phase_b_rows < 90.0)

    return {
        "isotonic_fit_info": {
            "n_rows": int(len(pred_min)),
            "mean_shift": float(preds["shift"].mean()),
            "median_shift": float(preds["shift"].median()),
            "mean_achieved_shift": float(preds["achieved_shift"].mean()),
            "median_achieved_shift": float(preds["achieved_shift"].median()),
            "shift_absorbed_by_band_clamp_pct": float(
                100.0 * (1.0 - abs(preds["achieved_shift"].mean())
                          / max(abs(preds["shift"].mean()), 1e-9))
            ),
        },
        "coverage": {
            "n_phase_b_rows": n_phase_b_rows,
            "n_fold_universe": int(n_fold_universe),
            "pct_phase_b_rows_of_fold_universe": pct_phase_b_rows,
            "coverage_limited": coverage_limited,
        },
        "per_stat_after": per_stat_after,
    }


def _print_phase_b(phase_b: dict) -> None:
    fit = phase_b["isotonic_fit_info"]
    print("\n=== PHASE B — MINUTES-SIDE WHAT-IF ===")
    cov = phase_b["coverage"]
    print(
        f"  coverage: n_phase_b_rows={cov['n_phase_b_rows']:,}  "
        f"n_fold_universe={cov['n_fold_universe']:,}  "
        f"pct={cov['pct_phase_b_rows_of_fold_universe']:.1f}%  "
        f"coverage_limited={cov['coverage_limited']}"
    )
    print(
        f"  isotonic shift: mean={fit['mean_shift']:+.2f}  "
        f"median={fit['median_shift']:+.2f}  "
        f"achieved_mean={fit['mean_achieved_shift']:+.2f}  "
        f"absorbed_by_band_clamp={fit['shift_absorbed_by_band_clamp_pct']:.1f}%"
    )
    for stat, block in phase_b["per_stat_after"].items():
        if "error" in block:
            print(
                f"  [{stat}] ERROR: {block['error']}  "
                f"n_after_failures={block.get('n_after_failures', 0)}"
            )
            continue
        b = block["before"]; a = block["after"]; d = block["delta"]
        print(
            f"  [{stat}] n_before_after_comparable_rows="
            f"{block['n_before_after_comparable_rows']:,}  "
            f"n_after_failures={block['n_after_failures']}"
        )
        print(
            f"    BEFORE pred_mean={b['pred_mean']:.2f} realized={b['realized_mean']:.2f}  "
            f"p0 pred={b['pred_p0']:.3f} real={b['realized_p0']:.3f}  "
            f"p_le1 pred={b['pred_p_le1']:.3f} real={b['realized_p_le1']:.3f}"
        )
        print(
            f"    AFTER  pred_mean={a['pred_mean']:.2f} realized={a['realized_mean']:.2f}  "
            f"p0 pred={a['pred_p0']:.3f} real={a['realized_p0']:.3f}  "
            f"p_le1 pred={a['pred_p_le1']:.3f} real={a['realized_p_le1']:.3f}"
        )
        print(
            f"    DELTA  mean={d['pred_mean']:+.2f}  "
            f"atom_ece_pred_mass={d['atom_ece_pred_mass']:+.4f}  "
            f"atom_brier={d['atom_brier']:+.4f}  "
            f"atom_logloss={d['atom_logloss']:+.4f}"
        )


def _recommendation(phase_a: dict, phase_b: dict | None) -> str:
    per_stat = phase_a["per_stat"]
    all_rate = all(per_stat[s]["classification"] == "rate_dominant" for s in SHIP_STATS)
    if all_rate or phase_b is None:
        return "RECOMMEND: pivot to rate-side investigation."
    improved = 0
    regressed_ece = 0
    for stat, block in phase_b["per_stat_after"].items():
        if "delta" not in block:
            continue
        d = block["delta"]; b = block["before"]; a = block["after"]
        before_mean_err = abs(b["pred_mean"] - b["realized_mean"])
        after_mean_err = abs(a["pred_mean"] - a["realized_mean"])
        if after_mean_err < before_mean_err:
            improved += 1
        if d["atom_ece_pred_mass"] > 0.002:
            regressed_ece += 1
    coverage_limited = bool(phase_b.get("coverage", {}).get("coverage_limited", False))
    coverage_note = (
        "  NOTE: Phase B coverage is materially below the fold universe; "
        "this result alone should not trigger productionization."
        if coverage_limited else ""
    )
    if improved >= 2 and regressed_ece == 0:
        return (
            "RECOMMEND: productionize minutes-mean calibration layer. "
            "Validate with Phase 8 one-fold rerun."
        ) + coverage_note
    mae_passes = phase_a["audit"]["mae_passes"]
    if not mae_passes:
        return (
            "RECOMMEND: minutes fix will partially help; REB/AST low-count shape "
            "correction likely needed as a second pass. Consider productionizing "
            "minutes fix because mae_passes is False."
        ) + coverage_note
    return (
        "RECOMMEND: minutes fix will partially help; REB/AST low-count shape "
        "correction likely needed as a second pass. mae_passes is True — "
        "pivot to shape work first."
    ) + coverage_note


# ── main ──────────────────────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold-oof", required=True, type=Path)
    ap.add_argument("--stats-df", required=True, type=Path)
    ap.add_argument("--features-df", required=True, type=Path)
    ap.add_argument("--minutes-models-dir", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--n-draws", type=int, default=2000)
    args = ap.parse_args()

    _require_path(args.minutes_models_dir, "--minutes-models-dir")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fold_oof = _load_fold_universe(args.fold_oof)
    universe = (
        fold_oof[["player_id", "game_id", "game_date"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    print(f"Loaded fold universe: {len(universe):,} unique (player_id, game_id, game_date)")

    stats_df = _load_stats(args.stats_df)
    stats_by_player: dict[int, pd.DataFrame] = {
        int(pid): g.sort_values("game_date").reset_index(drop=True)
        for pid, g in stats_df.groupby("player_id")
    }
    print(f"Loaded stats_df: {len(stats_df):,} rows, {len(stats_by_player):,} players")

    features_df = _load_features(args.features_df)
    print(f"Loaded features_df (stat=pts slice): {len(features_df):,} rows")

    avail_lookup = _load_availability_lookup()
    print(f"Loaded availability lookup: {len(avail_lookup):,} keys")

    # Match audit runs BEFORE any per-row work and always prints.
    match_out = _match_audit(
        universe=universe, stats_df=stats_df,
        features_df=features_df, stats_by_player=stats_by_player,
    )
    _print_match_audit(match_out["audit"])
    if match_out["audit"]["n_fully_auditable_rows"] == 0:
        _die("n_fully_auditable_rows=0; cannot proceed.")
    auditable_keys: set[tuple[int, int]] = match_out["auditable_keys"]
    universe_auditable = universe[
        universe.apply(
            lambda r: (int(r["player_id"]), int(r["game_id"])) in auditable_keys,
            axis=1,
        )
    ].reset_index(drop=True)

    phase_a_out = _phase_a(
        universe=universe_auditable,
        stats_df=stats_df, stats_by_player=stats_by_player,
        features_df=features_df, avail_lookup=avail_lookup, fold_oof=fold_oof,
    )
    phase_a = phase_a_out["phase_a"]
    _print_phase_a(phase_a)

    phase_b = None
    all_rate = all(
        phase_a["per_stat"][s]["classification"] == "rate_dominant" for s in SHIP_STATS
    )
    if all_rate:
        print(
            "\nRECOMMEND: minutes is not the primary driver. Skipping Phase B. "
            "Pivot to rate-side investigation."
        )
    else:
        phase_b = _phase_b(
            preds=phase_a_out["preds"],
            features_by_pg=phase_a_out["features_by_pg"],
            fold_oof=fold_oof,
            n_draws=args.n_draws,
            n_fold_universe=int(match_out["audit"]["n_fold_universe"]),
        )
        _print_phase_b(phase_b)

    final_rec = _recommendation(phase_a, phase_b)
    print("\n" + final_rec)

    report = {
        "metadata": {
            "git_sha": _git_sha(),
            "run_timestamp": datetime.utcnow().isoformat() + "Z",
            "n_rows": int(len(universe_auditable)),
            "n_draws": int(args.n_draws),
            "fold_oof_path": str(args.fold_oof),
        },
        "match_audit": match_out["audit"],
        "phase_a": phase_a,
        "phase_b": phase_b,
        "recommendation": final_rec,
    }
    out_json = args.output_dir / "minutes_oof_proof_pass.json"
    out_json.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nWrote {out_json}")


if __name__ == "__main__":
    main()
