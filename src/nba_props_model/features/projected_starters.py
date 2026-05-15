"""Projected-starter prior for the MORNING run path.

Why this module exists
======================

In the MORNING_EXPECTED run mode (5–8 hours pre-tip) we do not yet have an
official lineup. The legacy code path filled every player's
``expected_starter_prob`` with the placeholder ``0.5``, which is not a feature
- the PMF model gets no per-player signal about who is actually expected to
start.

This module derives a real per-player projected-starter prior from the
historical box-score table ``data/player_game_stats.parquet`` plus the
availability snapshot. The prior is then plugged into the morning expected
lineup features in :mod:`asof_feature_store` and :mod:`injury_lineup_features`.

Strict leakage contract
=======================

Per ``.cursor/rules/nba-pmf-market-superiority.mdc`` (Section: leakage rules):

* Rows whose ``game_date >= slate_date`` MUST NOT be read. We use a strict
  less-than filter so the slate-day box score, mid-game updates, or any later
  game can never contaminate the morning prior.
* No closing-line market data is used here. No post-outcome feature touches
  this code path.

Definitions
===========

``data/player_game_stats.parquet`` does not carry a starter flag. We derive
the per-game starter flag using the standard NBA proxy:

* For each (game_id, team_id) the five players with the most minutes are the
  starters. Ties are broken first by ``plus_minus`` (better → more likely a
  starter who played the start of the game), then by ``player_id`` to keep
  the derivation deterministic.

This proxy agrees with the actual box-score starters in the high 90% range
for full-NBA games and is the most accurate signal available from the
current BDL ingest without adding a paid play-by-play feed.

Outputs (per player_id, team_id)
================================

``expected_starter`` (bool)
    ``True`` iff ``expected_starter_prob >= 0.5``.

``expected_starter_prob`` (float in (1e-3, 1 - 1e-3))
    Beta-Binomial smoothed starter rate over the last N games, then
    renormalized so that the team has exactly five active players with
    ``expected_starter_prob >= 0.5``.

``expected_lineup_confidence`` (float in [0, 1])
    A weighted average of three components:
        a) sample size :math:`n / N`
        b) posterior sharpness :math:`1 - 4 \\cdot \\mathrm{Var}(\\mathrm{Beta}(\\alpha+k, \\beta+n-k))`
           (1.0 when the Beta posterior is degenerate, 0.0 when it is uniform)
        c) availability confidence ``prob_active``
    Equal weights (1/3 each) by default.

``expected_rotation_rank`` (int 1..15)
    Rank within team by ``p_start * max(prob_active, 0.1)``; 1 = most likely
    starter. Tie-break by recent mean minutes.

``expected_bench_role`` (bool)
    ``not expected_starter``.

``projected_rotation_slot`` (str)
    ``"starter"`` for rank<=5, ``"rotation"`` for rank<=9, ``"deep_bench"`` for
    rank>=10.

``projected_closing_lineup_flag`` (bool)
    ``rank<=5 and prob_active>=0.85``.

``projected_blowout_rotation_risk`` (float in [0, 1])
    Heuristic risk that a player loses minutes when the game is a blowout.
    Closing-lineup players have near-zero risk; deep-bench players with no
    recent garbage-time minutes have low risk; mid-rotation players have the
    highest risk.

``feature_freshness`` (str)
    ``"projected_starter_rolling_N{N}"`` for every row produced by this module,
    so downstream verifiers can distinguish it from the legacy
    ``projected_lineup`` placeholder.

Renormalization
===============

After computing the raw Beta-Binomial estimates we sort the team's active
players by ``p_start * max(prob_active, 0.1)`` (tie-broken by recent mean
minutes). The top 5 are bumped to ``expected_starter_prob = max(p, 0.5 + ε)``
and the rest are clamped to ``min(p, 0.5 - ε)``. ε is a small positive
floor so the boolean ``expected_starter`` flag is strictly determined by
the renormalized prob. This guarantees:

    sum(expected_starter for player in team) == 5

provided the team has at least 5 active rows. If the team has fewer than 5
active players in the slate, every available player is treated as a starter
(the renormalization simply takes whoever is left).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


DEFAULT_WINDOW_N = 10
DEFAULT_ALPHA = 1.0
DEFAULT_BETA = 1.0
PROB_FLOOR = 1e-3
PROB_CEIL = 1.0 - 1e-3
RENORM_EPS = 1e-3

LOW_PROB_ACTIVE_FLOOR = 0.1


@dataclass(frozen=True)
class ProjectedStarterConfig:
    window_n: int = DEFAULT_WINDOW_N
    alpha: float = DEFAULT_ALPHA
    beta: float = DEFAULT_BETA
    prob_floor: float = PROB_FLOOR
    prob_ceil: float = PROB_CEIL


def _normalize_date_series(values: pd.Series) -> pd.Series:
    """Return a string series in 'YYYY-MM-DD' form (no tz)."""
    if values.empty:
        return values
    if pd.api.types.is_datetime64_any_dtype(values):
        return values.dt.strftime("%Y-%m-%d")
    return values.astype(str).str.slice(0, 10)


def _derive_starter_flag(games: pd.DataFrame) -> pd.DataFrame:
    """Derive per-row starter flag for box-score rows.

    Standard NBA proxy: the five players with the most minutes per
    (game_id, team_id) are starters. Tie-break by ``plus_minus`` desc,
    then by ``player_id`` for determinism.
    """
    if games.empty:
        out = games.copy()
        out["__started"] = False
        return out

    out = games.copy()
    if "plus_minus" not in out.columns:
        out["plus_minus"] = 0.0
    out["plus_minus"] = pd.to_numeric(out["plus_minus"], errors="coerce").fillna(0.0)
    out["min"] = pd.to_numeric(out["min"], errors="coerce").fillna(0.0)

    out["__rank_in_game"] = (
        out
        .sort_values(["game_id", "team_id", "min", "plus_minus", "player_id"], ascending=[True, True, False, False, True])
        .groupby(["game_id", "team_id"], sort=False)
        .cumcount()
        + 1
    )
    out["__started"] = out["__rank_in_game"] <= 5
    return out


def _last_n_per_player(
    games: pd.DataFrame,
    window_n: int,
) -> pd.DataFrame:
    """For each player, return the last ``window_n`` games (by game_date desc)."""
    if games.empty:
        return games

    g = games.sort_values(["player_id", "game_date", "game_id"], ascending=[True, False, False]).copy()
    g["__per_player_idx"] = g.groupby("player_id").cumcount()
    return g[g["__per_player_idx"] < window_n].drop(columns=["__per_player_idx"])


def _beta_posterior_variance(k: np.ndarray, n: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """Variance of Beta(alpha+k, beta+(n-k))."""
    a = alpha + k
    b = beta + (n - k)
    denom = (a + b) ** 2 * (a + b + 1.0)
    return (a * b) / np.where(denom > 0, denom, 1.0)


def _confidence(
    n_games: np.ndarray,
    window_n: int,
    posterior_var: np.ndarray,
    prob_active: np.ndarray,
) -> np.ndarray:
    """Lineup confidence in [0, 1], an equal-weighted average of:

    a) sample size :math:`n / N` (capped at 1)
    b) posterior sharpness :math:`1 - 4 \\cdot \\mathrm{Var}` (Beta variance maxes
       at 1/4 for the uniform; this maps it to 0).
    c) availability confidence ``prob_active``.
    """
    sample_size = np.clip(n_games / max(window_n, 1), 0.0, 1.0)
    sharpness = np.clip(1.0 - 4.0 * posterior_var, 0.0, 1.0)
    availability = np.clip(np.nan_to_num(prob_active, nan=0.5), 0.0, 1.0)
    return (sample_size + sharpness + availability) / 3.0


def _blowout_risk(rank: np.ndarray, recent_mean_minutes: np.ndarray) -> np.ndarray:
    """Heuristic risk that a player loses minutes in a blowout.

    * starter (rank<=5) → 0.05 (closing 5 normally stays in if blowout-with)
    * rotation (6..9) → 0.35 (most vulnerable to early pulls or extended garbage time)
    * deep_bench (>=10) with low recent minutes → 0.05 (unlikely to be affected
      because they don't normally play; in blowouts they may even gain minutes)
    * deep_bench with non-trivial recent minutes → 0.20 (their minutes were
      already garbage time)
    """
    rank = np.asarray(rank, dtype=float)
    mins = np.asarray(recent_mean_minutes, dtype=float)
    risk = np.where(rank <= 5, 0.05, np.where(rank <= 9, 0.35, np.where(mins >= 6.0, 0.20, 0.05)))
    return risk.astype(float)


def _renormalize_to_five(
    df: pd.DataFrame,
    prob_floor: float,
    prob_ceil: float,
) -> pd.DataFrame:
    """Force exactly five team starters by clamping ``expected_starter_prob``.

    Sort active players (treated as ``prob_active >= 0.5`` OR top-5 by
    ``p_start * prob_active`` regardless of availability — a returning star
    with low data may still legitimately start). Tie-break by recent mean
    minutes.

    Top 5 → ``max(p, 0.5 + ε)`` (still capped at ``prob_ceil``).
    Rest  → ``min(p, 0.5 - ε)`` (still floored at ``prob_floor``).
    """
    if df.empty:
        return df

    out_chunks: list[pd.DataFrame] = []
    for team_id, sub in df.groupby("team_id", sort=False, dropna=False):
        sub = sub.copy()
        prob_active_eff = sub["prob_active"].fillna(0.5).astype(float).clip(lower=LOW_PROB_ACTIVE_FLOOR)
        sub["__rank_score"] = sub["expected_starter_prob"].astype(float) * prob_active_eff
        sub = sub.sort_values(
            ["__rank_score", "recent_mean_minutes", "player_id"],
            ascending=[False, False, True],
        ).reset_index(drop=True)
        sub["expected_rotation_rank"] = sub.index.astype(int) + 1

        floor = 0.5 + RENORM_EPS
        ceiling = 0.5 - RENORM_EPS

        top5 = sub["expected_rotation_rank"] <= 5
        sub.loc[top5, "expected_starter_prob"] = np.maximum(
            sub.loc[top5, "expected_starter_prob"].astype(float).to_numpy(),
            floor,
        )
        sub.loc[~top5, "expected_starter_prob"] = np.minimum(
            sub.loc[~top5, "expected_starter_prob"].astype(float).to_numpy(),
            ceiling,
        )
        sub["expected_starter_prob"] = sub["expected_starter_prob"].clip(lower=prob_floor, upper=prob_ceil)
        sub = sub.drop(columns=["__rank_score"])
        out_chunks.append(sub)

    return pd.concat(out_chunks, ignore_index=True)


def compute_projected_starter_prior(
    eligible_players: pd.DataFrame,
    slate_date: str,
    player_game_stats: pd.DataFrame,
    config: ProjectedStarterConfig | None = None,
) -> pd.DataFrame:
    """Compute the per-player projected-starter prior for the morning run.

    Parameters
    ----------
    eligible_players
        Must contain ``player_id`` and ``team_id``. May contain
        ``prob_active`` (float, NaN ok); if missing we assume 0.95 (the
        player is on the slate so the slate already filtered out inactive
        players).
    slate_date
        ``YYYY-MM-DD`` string. Rows in ``player_game_stats`` with
        ``game_date >= slate_date`` are dropped before the prior is built.
        This is the LEAKAGE GUARD; do not relax it.
    player_game_stats
        DataFrame loaded from ``data/player_game_stats.parquet``. Must
        contain at least: ``player_id``, ``game_id``, ``game_date``,
        ``team_id``, ``min``. ``plus_minus`` is used for tie-breaking the
        starter derivation; missing values are treated as 0.

    Returns
    -------
    DataFrame keyed by (player_id, team_id) with the columns listed in this
    module's docstring.
    """
    cfg = config or ProjectedStarterConfig()
    base_cols = ["player_id", "team_id"]
    out = eligible_players[base_cols + [c for c in eligible_players.columns if c not in base_cols]].copy()
    if "prob_active" not in out.columns:
        out["prob_active"] = np.nan
    out["prob_active"] = pd.to_numeric(out["prob_active"], errors="coerce")

    if player_game_stats is None or player_game_stats.empty:
        out["k_starts"] = 0
        out["n_games"] = 0
        out["recent_mean_minutes"] = 0.0
        out["posterior_var"] = (cfg.alpha * cfg.beta) / ((cfg.alpha + cfg.beta) ** 2 * (cfg.alpha + cfg.beta + 1.0))
        out["expected_starter_prob"] = cfg.alpha / (cfg.alpha + cfg.beta)
    else:
        history = player_game_stats.copy()
        history["game_date"] = _normalize_date_series(history["game_date"])
        history = history[history["game_date"] < slate_date].copy()

        if "team_id" not in history.columns:
            history["team_id"] = pd.NA

        history["min"] = pd.to_numeric(history["min"], errors="coerce").fillna(0.0)

        starter_rows = _derive_starter_flag(history)
        per_player_keep_cols = ["player_id", "team_id", "game_id", "game_date", "min", "__started"]
        starter_rows = starter_rows[per_player_keep_cols]

        windowed = _last_n_per_player(starter_rows, cfg.window_n)
        if windowed.empty:
            agg = pd.DataFrame(columns=["player_id", "k_starts", "n_games", "recent_mean_minutes"])
        else:
            agg = (
                windowed.groupby("player_id", sort=False)
                .agg(
                    k_starts=("__started", "sum"),
                    n_games=("__started", "size"),
                    recent_mean_minutes=("min", "mean"),
                )
                .reset_index()
            )
            agg["k_starts"] = agg["k_starts"].astype(int)
            agg["n_games"] = agg["n_games"].astype(int)
        out = out.merge(agg, on="player_id", how="left")
        out["k_starts"] = out["k_starts"].fillna(0).astype(int)
        out["n_games"] = out["n_games"].fillna(0).astype(int)
        out["recent_mean_minutes"] = out["recent_mean_minutes"].fillna(0.0).astype(float)
        k = out["k_starts"].to_numpy()
        n = out["n_games"].to_numpy()
        out["expected_starter_prob"] = (k + cfg.alpha) / (n + cfg.alpha + cfg.beta)
        out["posterior_var"] = _beta_posterior_variance(k, n, cfg.alpha, cfg.beta)

    out["expected_starter_prob"] = np.clip(
        out["expected_starter_prob"].astype(float), cfg.prob_floor, cfg.prob_ceil
    )

    prob_active_for_conf = out["prob_active"].fillna(0.95)
    out["expected_lineup_confidence"] = _confidence(
        n_games=out["n_games"].to_numpy(),
        window_n=cfg.window_n,
        posterior_var=out["posterior_var"].to_numpy(),
        prob_active=prob_active_for_conf.to_numpy(),
    )

    out = _renormalize_to_five(out, cfg.prob_floor, cfg.prob_ceil)

    out["expected_starter"] = out["expected_starter_prob"] >= 0.5
    out["expected_bench_role"] = ~out["expected_starter"]

    rank = out["expected_rotation_rank"].to_numpy()
    out["projected_rotation_slot"] = np.where(
        rank <= 5,
        "starter",
        np.where(rank <= 9, "rotation", "deep_bench"),
    )

    prob_active_filled = out["prob_active"].fillna(0.95).astype(float)
    out["projected_closing_lineup_flag"] = (rank <= 5) & (prob_active_filled >= 0.85)
    out["projected_blowout_rotation_risk"] = _blowout_risk(rank, out["recent_mean_minutes"].to_numpy())

    out["feature_freshness"] = f"projected_starter_rolling_N{cfg.window_n}"
    out["expected_lineup_source_internal"] = f"projected_starter_rolling_N{cfg.window_n}"

    keep = [
        "player_id",
        "team_id",
        "k_starts",
        "n_games",
        "recent_mean_minutes",
        "posterior_var",
        "expected_starter",
        "expected_starter_prob",
        "expected_lineup_confidence",
        "expected_rotation_rank",
        "expected_bench_role",
        "projected_rotation_slot",
        "projected_closing_lineup_flag",
        "projected_blowout_rotation_risk",
        "feature_freshness",
        "expected_lineup_source_internal",
    ]
    keep_present = [c for c in keep if c in out.columns]
    return out[keep_present].copy()


def load_player_game_stats(repo_root: Path) -> pd.DataFrame:
    """Load ``data/player_game_stats.parquet`` if present, else empty frame."""
    p = repo_root / "data" / "player_game_stats.parquet"
    if not p.is_file():
        return pd.DataFrame(columns=["player_id", "team_id", "game_id", "game_date", "min", "plus_minus"])
    return pd.read_parquet(p)


def build_projected_starter_frame(
    repo_root: Path,
    slate_date: str,
    eligible_players: pd.DataFrame,
    config: ProjectedStarterConfig | None = None,
) -> pd.DataFrame:
    """Convenience: load ``player_game_stats.parquet`` and run the prior."""
    history = load_player_game_stats(repo_root)
    return compute_projected_starter_prior(
        eligible_players=eligible_players,
        slate_date=slate_date,
        player_game_stats=history,
        config=config,
    )
