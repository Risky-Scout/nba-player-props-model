from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from ...bundle import SlateStateBundle
from ...pmf import parse_pmf, quantile_int_from_u, rank_to_uniform, event_probability
from ...simulation import SimulationTape


DIRECT_STATS = {"pts", "reb", "ast", "fg3m", "tov", "stl", "blk"}
COMBO_COMPONENTS = {
    "pa": ("pts", "ast"),
    "pr": ("pts", "reb"),
    "ra": ("reb", "ast"),
    "pra": ("pts", "reb", "ast"),
    "stocks": ("stl", "blk"),
}

# NBA regulation game = 5 periods × 48 min = 240 total team-player-minutes.
# OT adds one 5-min period per team (~25 player-minutes per OT period).
_REGULATION_TEAM_MINUTES: float = 240.0
_OT_EXTRA_MINUTES_PER_PERIOD: float = 25.0
_MEAN_OT_RATE: float = 0.06  # ~6 % of games go to OT (used for Dirichlet normalisation)

# Default factor weight table.  Each stat → list of (factor_name, weight) pairs.
# These can be overridden by artifacts/models/sgp/factor_weights/factor_weights_latest.json.
_DEFAULT_FACTOR_WEIGHTS: dict[str, list[tuple[str, float]]] = {
    "pts": [
        ("pace_z", 0.20), ("total_z", 0.20), ("team_offense_z", 0.18),
        ("team_shooting_z", 0.18), ("player_usage_z", 0.28),
        ("player_minutes_z", 0.24), ("player_shooting_z", 0.18),
        ("ot_flag", 0.08), ("blowout_z", -0.05),
    ],
    "fg3m": [
        ("pace_z", 0.17), ("total_z", 0.14), ("team_three_z", 0.30),
        ("team_shooting_z", 0.16), ("player_usage_z", 0.22),
        ("player_minutes_z", 0.22), ("player_shooting_z", 0.26),
        ("ot_flag", 0.06),
    ],
    "ast": [
        ("pace_z", 0.22), ("total_z", 0.18), ("team_assist_env_z", 0.30),
        ("team_shooting_z", 0.26), ("player_usage_z", 0.22),
        ("player_minutes_z", 0.25), ("ot_flag", 0.07),
    ],
    "reb": [
        ("pace_z", 0.20), ("opp_shooting_z", -0.15), ("team_rebound_pool_z", 0.20),
        ("opp_rebound_pool_z", 0.22), ("player_minutes_z", 0.28),
        ("player_energy_z", 0.22), ("ot_flag", 0.07), ("blowout_z", 0.03),
    ],
    "tov": [
        ("pace_z", 0.20), ("team_turnover_z", 0.26), ("opp_def_activity_z", 0.20),
        ("player_usage_z", 0.28), ("player_minutes_z", 0.22),
        ("foul_env_z", 0.08),
    ],
    "stl": [
        ("pace_z", 0.18), ("opp_turnover_z", 0.24), ("team_def_activity_z", 0.26),
        ("player_minutes_z", 0.22), ("player_defense_z", 0.24),
        ("player_energy_z", 0.14),
    ],
    "blk": [
        ("pace_z", 0.14), ("opp_offense_z", 0.14), ("team_def_activity_z", 0.20),
        ("player_minutes_z", 0.22), ("player_defense_z", 0.30),
        ("player_energy_z", 0.16), ("player_foul_z", -0.08),
    ],
}


def _stable_normal_key(seed: int, *parts: str) -> int:
    key = "|".join(map(str, (seed,) + parts))
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(h[:16], 16) % (2**32 - 1)


def _weighted_z(rng: np.random.Generator, factors: list[tuple[np.ndarray, float]], n: int) -> np.ndarray:
    used_var = sum(float(w) ** 2 for _, w in factors)
    if used_var >= 0.98:
        scale = max(0.05, np.sqrt(1.0 / used_var))
        z = sum(arr * (w * scale) for arr, w in factors)
        used_var = sum((w * scale) ** 2 for _, w in factors)
    else:
        z = sum(arr * w for arr, w in factors)
    idio_sd = float(np.sqrt(max(1.0 - used_var, 0.01)))
    return z + idio_sd * rng.normal(size=n)


def _load_factor_weights(repo_root: Path) -> tuple[dict[str, list[tuple[str, float]]], bool]:
    """Load learned factor weights if available; return (weights_dict, learned_flag)."""
    fw_path = repo_root / "artifacts" / "models" / "sgp" / "factor_weights" / "factor_weights_latest.json"
    if not fw_path.exists():
        return _DEFAULT_FACTOR_WEIGHTS, False
    try:
        raw = json.loads(fw_path.read_text())
        weights: dict[str, list[tuple[str, float]]] = {}
        for stat, pairs in raw.items():
            if stat.startswith("_"):
                # Skip metadata keys like "_meta".
                continue
            if isinstance(pairs, list):
                weights[stat] = [(str(p[0]), float(p[1])) for p in pairs if len(p) == 2]
            elif isinstance(pairs, dict):
                weights[stat] = [(str(k), float(v)) for k, v in pairs.items()]
        # Fill missing stats from defaults.
        for k, v in _DEFAULT_FACTOR_WEIGHTS.items():
            weights.setdefault(k, v)
        return weights, True
    except Exception:
        return _DEFAULT_FACTOR_WEIGHTS, False


def _build_latent_from_weights(
    stat: str,
    factor_weights: dict[str, list[tuple[str, float]]],
    *,
    rng: np.random.Generator,
    n: int,
    pace_z: np.ndarray,
    total_z: np.ndarray,
    ot_flag: np.ndarray,
    blowout_z: np.ndarray,
    foul_env_z: np.ndarray,
    player_factors: dict[str, np.ndarray],
    team_factors: dict[str, np.ndarray],
    opp_factors: dict[str, np.ndarray],
) -> np.ndarray:
    """Build a latent normal variable from the factor weight table."""
    named: dict[str, np.ndarray] = {
        "pace_z": pace_z, "total_z": total_z, "ot_flag": ot_flag,
        "blowout_z": blowout_z, "foul_env_z": foul_env_z,
        "team_offense_z": team_factors.get("offense_z", rng.normal(size=n)),
        "team_shooting_z": team_factors.get("shooting_z", rng.normal(size=n)),
        "team_three_z": team_factors.get("three_z", rng.normal(size=n)),
        "team_assist_env_z": team_factors.get("assist_env_z", rng.normal(size=n)),
        "team_rebound_pool_z": team_factors.get("rebound_pool_z", rng.normal(size=n)),
        "team_turnover_z": team_factors.get("turnover_z", rng.normal(size=n)),
        "team_def_activity_z": team_factors.get("def_activity_z", rng.normal(size=n)),
        "opp_offense_z": opp_factors.get("offense_z", rng.normal(size=n)),
        "opp_shooting_z": opp_factors.get("shooting_z", rng.normal(size=n)),
        "opp_rebound_pool_z": opp_factors.get("rebound_pool_z", rng.normal(size=n)),
        "opp_def_activity_z": opp_factors.get("def_activity_z", rng.normal(size=n)),
        "opp_turnover_z": opp_factors.get("turnover_z", rng.normal(size=n)),
        "player_minutes_z": player_factors.get("minutes_z", rng.normal(size=n)),
        "player_usage_z": player_factors.get("usage_z", rng.normal(size=n)),
        "player_shooting_z": player_factors.get("shooting_z", rng.normal(size=n)),
        "player_energy_z": player_factors.get("energy_z", rng.normal(size=n)),
        "player_defense_z": player_factors.get("defense_z", rng.normal(size=n)),
        "player_foul_z": player_factors.get("foul_z", rng.normal(size=n)),
    }
    pairs = factor_weights.get(stat, [])
    if not pairs:
        return rng.normal(size=n)
    factor_list = [(named[name], w) for name, w in pairs if name in named]
    if not factor_list:
        return rng.normal(size=n)
    return _weighted_z(rng, factor_list, n)


@dataclass
class NBASimulator:
    """Lineup-conditional NBA same-game simulator.

    v1 implements a marginal-anchored mechanism-factor simulation:
      - shared game factors generate pace, score script, blowout, overtime
      - shared team factors generate shooting, usage, rebounding, turnovers
      - Phase D: competitive minutes pool with Dirichlet allocation and negative
        teammate correlation (if star plays more, backup plays less)
      - shared player factors generate minutes/usage/energy
      - delivered calibrated PMFs anchor each player-stat marginal
      - inverse-CDF mapping converts latent simulation worlds to integer outcomes
      - factor weights loaded from artifacts/models/sgp/factor_weights/factor_weights_latest.json
        if available; otherwise hardcoded defaults are used
      - marginal preservation report generated and stored in tape metadata
    """
    bundle: SlateStateBundle
    n_sims: int = 200000
    seed: int = 20260530

    def run(self) -> SimulationTape:
        repo_root = Path(self.bundle.root).parents[2]  # deliveries/{date}/sgp_engine/v1 → repo root
        factor_weights, learned_weights = _load_factor_weights(repo_root)

        rng = np.random.default_rng(self.seed)
        stats: dict[tuple[str, str, str], np.ndarray] = {}
        factors_out: dict[str, np.ndarray] = {}

        pmfs = self.bundle.player_stat_pmfs.copy()
        pmfs["stat"] = pmfs["stat"].astype(str).str.lower()

        # Marginal preservation tracking.
        marginal_records: list[dict[str, Any]] = []

        # Minutes allocation diagnostics.
        minutes_diag: dict[str, Any] = {}

        for game_id, game_pmfs in pmfs.groupby("game_id", dropna=False):
            game_id = str(game_id)
            # Global game script factors.
            pace_z = rng.normal(size=self.n_sims)
            total_z = rng.normal(size=self.n_sims)
            close_z = rng.normal(size=self.n_sims)
            foul_env_z = rng.normal(size=self.n_sims)
            ot_flag = rng.binomial(1, _MEAN_OT_RATE, size=self.n_sims).astype(float)
            blowout_z = rng.normal(size=self.n_sims)

            factors_out[f"{game_id}__pace_z"] = pace_z.astype(np.float32)
            factors_out[f"{game_id}__total_z"] = total_z.astype(np.float32)
            factors_out[f"{game_id}__overtime_flag"] = ot_flag.astype(np.float32)

            # Full team total minutes per simulation (varies with OT draws).
            full_team_total = (
                _REGULATION_TEAM_MINUTES + _OT_EXTRA_MINUTES_PER_PERIOD * ot_flag
            )  # shape (n_sims,)

            # Expected (mean) full team total – used as Dirichlet normaliser so that
            # each tracked player's *expected* simulated minutes equals their PMF mean.
            full_team_expected = (
                _REGULATION_TEAM_MINUTES + _OT_EXTRA_MINUTES_PER_PERIOD * _MEAN_OT_RATE
            )  # scalar ≈ 241.5

            teams = sorted(set(map(str, game_pmfs["team_id"].dropna())))
            team_factors: dict[str, dict[str, np.ndarray]] = {}
            for team in teams:
                team_factors[team] = {
                    "offense_z": rng.normal(size=self.n_sims),
                    "shooting_z": rng.normal(size=self.n_sims),
                    "three_z": rng.normal(size=self.n_sims),
                    "assist_env_z": rng.normal(size=self.n_sims),
                    "rebound_pool_z": rng.normal(size=self.n_sims),
                    "turnover_z": rng.normal(size=self.n_sims),
                    "def_activity_z": rng.normal(size=self.n_sims),
                }

            # Phase D: competitive minutes pool per team.
            # Draw Dirichlet shares and allocate *full_team_total* minutes.
            # A ghost/remainder bucket absorbs the gap between full_team_expected and
            # sum(tracked_expected_minutes), so that each tracked player's simulated
            # minutes are centred on their PMF-expected value (minutes_z mean ≈ 0).
            team_minutes_sim: dict[str, dict[str, np.ndarray]] = {}
            team_concentration = 20.0

            for team in teams:
                team_pmf_rows = game_pmfs[game_pmfs["team_id"].astype(str) == team].copy()
                if team_pmf_rows.empty:
                    continue

                # Get unique players on this team with their expected minutes.
                # Some columns are only present in real deliveries, not minimal test bundles.
                avail_cols = ["player_id"]
                for opt in ["minutes_mean", "minutes_std", "p_inactive_used", "lineup_status"]:
                    if opt in team_pmf_rows.columns:
                        avail_cols.append(opt)
                player_rows = (
                    team_pmf_rows[avail_cols]
                    .drop_duplicates(subset=["player_id"])
                    .copy()
                )
                # Ensure optional columns exist with safe defaults.
                for missing_col, default_val in [
                    ("minutes_mean", np.nan), ("minutes_std", np.nan),
                    ("p_inactive_used", np.nan), ("lineup_status", None),
                ]:
                    if missing_col not in player_rows.columns:
                        player_rows[missing_col] = default_val

                # Determine which players are active (not inactive/out).
                active_mask = []
                for _, pr in player_rows.iterrows():
                    p_inact = pr.get("p_inactive_used")
                    lineup = str(pr.get("lineup_status", "") or "")
                    is_inactive = (
                        (p_inact is not None and not (isinstance(p_inact, float) and np.isnan(p_inact)) and float(p_inact) > 0.3)
                        or "out" in lineup.lower()
                    )
                    active_mask.append(not is_inactive)

                active_player_ids = [
                    str(getattr(pr, "player_id", None))
                    for pr, is_active in zip(player_rows.itertuples(index=False), active_mask)
                    if is_active
                ]

                if not active_player_ids:
                    continue

                # Phase D competitive minutes pool only applies when multiple players
                # compete for minutes.  With a single player there is no competition
                # and the Dirichlet would unconditionally allocate the full team total
                # to that one player, producing extreme minutes_z values.
                if len(active_player_ids) < 2:
                    continue

                # Build expected minutes for active players.
                exp_mins: dict[str, float] = {}
                exp_stds: dict[str, float] = {}
                for _, pr in player_rows.iterrows():
                    pid = str(pr["player_id"])
                    if pid not in active_player_ids:
                        continue
                    m = pr.get("minutes_mean")
                    s = pr.get("minutes_std")
                    exp_mins[pid] = float(m) if m is not None and not (isinstance(m, float) and np.isnan(m)) else 20.0
                    exp_stds[pid] = float(s) if s is not None and not (isinstance(s, float) and np.isnan(s)) else 5.0

                tracked_exp_total = sum(exp_mins.values())
                if tracked_exp_total <= 0:
                    tracked_exp_total = len(active_player_ids) * 20.0

                # ── Ghost/remainder bucket (P0 Dirichlet inflation fix) ────────
                # The PMF delivery only covers 8–9 tracked players per team, whose
                # expected minutes sum to 184–197.  The full game has 240+ minutes
                # split across the entire 15-man roster.  Without a ghost bucket the
                # Dirichlet would inflate every tracked player's minutes by 22–30%,
                # creating a systematic +5–7% upward bias in all stat outcomes.
                #
                # Fix: add a synthetic "untracked_bench" bucket to absorb the gap.
                # The Dirichlet normaliser is full_team_expected (≈241.5), so each
                # tracked player's E[simulated_minutes] = exp_mins[pid].  The ghost's
                # allocation is discarded; it never enters the simulation.
                ghost_expected = max(full_team_expected - tracked_exp_total, 0.0)
                use_ghost = ghost_expected > 0.5  # only when gap is meaningful

                if use_ghost:
                    total_all = tracked_exp_total + ghost_expected  # ≈ full_team_expected
                    all_exp = [exp_mins[pid] for pid in active_player_ids] + [ghost_expected]
                    concentrations = np.array([
                        max(m / total_all, 1e-3) * team_concentration for m in all_exp
                    ])
                    shares = rng.dirichlet(concentrations, size=self.n_sims)  # (n_sims, n_tracked+1)
                    # Drop ghost bucket (last column); scale by full team total.
                    actual_minutes = shares[:, :-1] * full_team_total[:, np.newaxis]
                    method = "ghost_remainder_dirichlet"
                else:
                    # Tracked players already consume close to the full team total;
                    # allocate tracked_exp_total proportionally and scale with OT.
                    concentrations = np.array([
                        max(exp_mins[pid] / tracked_exp_total, 1e-3) * team_concentration
                        for pid in active_player_ids
                    ])
                    shares = rng.dirichlet(concentrations, size=self.n_sims)  # (n_sims, n_tracked)
                    actual_minutes = shares * full_team_total[:, np.newaxis]
                    method = "tracked_total_dirichlet"

                # Record per-team diagnostics.
                realized_mins_mean = float(actual_minutes.mean(axis=0).sum())
                minutes_diag[f"{game_id}__{team}"] = {
                    "method": method,
                    "tracked_expected_total": round(tracked_exp_total, 2),
                    "full_team_expected": round(full_team_expected, 2),
                    "ghost_expected_minutes": round(ghost_expected, 2),
                    "realized_tracked_minutes_mean": round(realized_mins_mean, 2),
                    "inflation_factor_raw": round(float(_REGULATION_TEAM_MINUTES) / max(tracked_exp_total, 1), 4),
                }

                for i, pid in enumerate(active_player_ids):
                    am = actual_minutes[:, i]
                    em = exp_mins[pid]
                    es = max(exp_stds[pid], 1.0)
                    minutes_z = np.clip((am - em) / es, -4.0, 4.0)
                    team_minutes_sim.setdefault(team, {})[pid] = minutes_z
                    stats[(game_id, pid, "minutes")] = am.astype(np.float32)

                factors_out[f"{game_id}__{team}__team_total_minutes"] = full_team_total.astype(np.float32)

            # Build player factors, pulling minutes_z from Phase D where available.
            player_factors: dict[str, dict[str, np.ndarray]] = {}
            for player_id in sorted(set(map(str, game_pmfs["player_id"].dropna()))):
                team_id = str(game_pmfs[game_pmfs["player_id"].astype(str) == player_id]["team_id"].iloc[0]) if len(game_pmfs) > 0 else "UNK"
                phase_d_minutes_z = team_minutes_sim.get(team_id, {}).get(player_id)
                player_factors[player_id] = {
                    "minutes_z": phase_d_minutes_z if phase_d_minutes_z is not None else rng.normal(size=self.n_sims),
                    "usage_z": rng.normal(size=self.n_sims),
                    "shooting_z": rng.normal(size=self.n_sims),
                    "energy_z": rng.normal(size=self.n_sims),
                    "defense_z": rng.normal(size=self.n_sims),
                    "foul_z": rng.normal(size=self.n_sims),
                }

            # Simulate direct stats from anchored PMFs.
            for _, r in game_pmfs[game_pmfs["stat"].isin(DIRECT_STATS)].iterrows():
                player_id = str(r["player_id"])
                team_id = str(r.get("team_id", "UNK"))
                opp_id = str(r.get("opponent_id", "UNK"))
                stat = str(r["stat"]).lower()
                pmf = parse_pmf(r["pmf_json"], domain_max=r.get("domain_max"))

                pf = player_factors[player_id]
                tf = team_factors.get(team_id, {k: rng.normal(size=self.n_sims) for k in ["offense_z", "shooting_z", "three_z", "assist_env_z", "rebound_pool_z", "turnover_z", "def_activity_z"]})
                of = team_factors.get(opp_id, {k: rng.normal(size=self.n_sims) for k in ["offense_z", "shooting_z", "three_z", "assist_env_z", "rebound_pool_z", "turnover_z", "def_activity_z"]})

                latent = _build_latent_from_weights(
                    stat,
                    factor_weights,
                    rng=rng,
                    n=self.n_sims,
                    pace_z=pace_z,
                    total_z=total_z,
                    ot_flag=ot_flag,
                    blowout_z=blowout_z,
                    foul_env_z=foul_env_z,
                    player_factors=pf,
                    team_factors=tf,
                    opp_factors=of,
                )

                u = norm.cdf(latent)
                outcomes = quantile_int_from_u(pmf, u)
                stats[(game_id, player_id, stat)] = outcomes

                # Marginal preservation: compare simulated mean and P(over line) to PMF.
                ks = np.arange(len(pmf), dtype=float)
                pmf_mean = float((ks * pmf).sum())
                pmf_var = float(((ks - pmf_mean) ** 2 * pmf).sum())
                sim_mean = float(outcomes.mean())
                sim_var = float(outcomes.var()) if len(outcomes) > 1 else np.nan
                line = r.get("line")
                if line is not None and not (isinstance(line, float) and np.isnan(line)):
                    try:
                        pmf_p_over = event_probability(pmf, float(line), "over")
                        sim_p_over = float((outcomes.astype(float) > float(line)).mean())
                    except Exception:
                        pmf_p_over = sim_p_over = np.nan
                else:
                    # Use PMF mean as evaluation line when no market line available.
                    try:
                        pmf_p_over = event_probability(pmf, pmf_mean, "over")
                        sim_p_over = float((outcomes.astype(float) > pmf_mean).mean())
                    except Exception:
                        pmf_p_over = sim_p_over = np.nan
                marginal_records.append({
                    "game_id": game_id,
                    "player_id": player_id,
                    "stat": stat,
                    "pmf_mean": pmf_mean,
                    "sim_mean": sim_mean,
                    "mean_delta": sim_mean - pmf_mean,
                    "pmf_variance": pmf_var,
                    "sim_variance": sim_var,
                    "variance_delta": sim_var - pmf_var if np.isfinite(sim_var) else np.nan,
                    "pmf_p_over_line": pmf_p_over,
                    "sim_p_over_line": sim_p_over,
                    "p_over_signed_diff": (sim_p_over - pmf_p_over) if np.isfinite(pmf_p_over) and np.isfinite(sim_p_over) else np.nan,
                    "line": line if line is not None and not (isinstance(line, float) and np.isnan(line)) else pmf_mean,
                })

            # Build combo stats from components, then optionally marginal-anchor ranks.
            for _, r in game_pmfs[game_pmfs["stat"].isin(COMBO_COMPONENTS)].iterrows():
                player_id = str(r["player_id"])
                stat = str(r["stat"]).lower()
                comps = COMBO_COMPONENTS[stat]
                component_arrays = []
                missing = False
                for c in comps:
                    key = (game_id, player_id, c)
                    if key not in stats:
                        missing = True
                        break
                    component_arrays.append(stats[key].astype(np.int16))
                if missing:
                    pf = player_factors.get(player_id)
                    latent = (
                        pf["minutes_z"] * 0.35 + pf["usage_z"] * 0.25 + rng.normal(size=self.n_sims) * 0.90
                        if pf else rng.normal(size=self.n_sims)
                    )
                    stats[(game_id, player_id, stat)] = quantile_int_from_u(
                        parse_pmf(r["pmf_json"], domain_max=r.get("domain_max")), norm.cdf(latent)
                    )
                    continue

                raw_combo = np.sum(component_arrays, axis=0).astype(np.int16)
                # Algebraic sum preserves joint consistency for mixed combo+component tickets.
                stats[(game_id, player_id, stat)] = raw_combo
                # Rank-anchored variant matches the delivered combo PMF marginal exactly.
                # Used for standalone combo legs where no component overlap exists in the ticket.
                try:
                    _combo_pmf = parse_pmf(r["pmf_json"], domain_max=r.get("domain_max"))
                    _u = rank_to_uniform(raw_combo.astype(float))
                    stats[(game_id, player_id, stat + "_anchored")] = (
                        quantile_int_from_u(_combo_pmf, _u).astype(np.int16)
                    )
                except Exception:
                    pass

        return SimulationTape(
            n_sims=self.n_sims,
            stats=stats,
            factors=factors_out,
            metadata={
                "sport": "nba",
                "seed": self.seed,
                "bundle_root": str(self.bundle.root),
                "simulator": "nba_mechanism_factor_marginal_anchored_v1",
                "learned_factor_weights": learned_weights,
                "marginal_preservation_report": marginal_records,
                "minutes_allocation_diagnostics": minutes_diag,
                "minutes_allocation_method": "ghost_remainder_dirichlet",
            },
        )
