from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


@dataclass
class SimulationTape:
    """In-memory same-game simulation tape.

    stats maps (game_id, player_id, stat) -> integer outcome vector length n_sims.
    factors stores optional diagnostic latent state arrays.
    """
    n_sims: int
    stats: dict[tuple[str, str, str], np.ndarray]
    factors: dict[str, np.ndarray]
    metadata: dict[str, Any]

    def get(self, game_id: str, player_id: str, stat: str) -> np.ndarray:
        key = (str(game_id), str(player_id), str(stat).lower())
        if key not in self.stats:
            raise KeyError(f"Simulation tape missing stat {key}")
        return self.stats[key]

    def has(self, game_id: str, player_id: str, stat: str) -> bool:
        return (str(game_id), str(player_id), str(stat).lower()) in self.stats

    def save_npz(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays: dict[str, np.ndarray] = {
            "__keys__": np.array(["|".join(k) for k in self.stats.keys()], dtype=object),
            "__n_sims__": np.array([self.n_sims], dtype=np.int64),
        }
        for i, (key, arr) in enumerate(self.stats.items()):
            if np.issubdtype(arr.dtype, np.floating):
                arrays[f"stat_{i}"] = arr.astype(np.float32, copy=False)
            else:
                arrays[f"stat_{i}"] = arr.astype(np.int16, copy=False)
        # Factors can be large; only save 1D numeric diagnostic arrays.
        for name, arr in self.factors.items():
            if isinstance(arr, np.ndarray) and arr.ndim == 1 and len(arr) == self.n_sims:
                arrays[f"factor__{name}"] = arr.astype(np.float32, copy=False)
        np.savez_compressed(path, **arrays)

    def to_frame(self) -> pd.DataFrame:
        """Return a long DataFrame with one row per (game_id, player_id, stat, sim_index).

        Columns: game_id, player_id, stat, outcome (int16), sim_index (int32).
        """
        if not self.stats:
            return pd.DataFrame(columns=["game_id", "player_id", "stat", "outcome", "sim_index"])

        sim_index = np.arange(self.n_sims, dtype=np.int32)
        parts = []
        for (game_id, player_id, stat), arr in self.stats.items():
            parts.append(pd.DataFrame({
                "game_id": game_id,
                "player_id": player_id,
                "stat": stat,
                "outcome": arr.astype(np.int16),
                "sim_index": sim_index,
            }))

        return pd.concat(parts, ignore_index=True)

    def to_wide_frame(self) -> pd.DataFrame:
        """Return a wide DataFrame with columns: simulation_id, game_id, player_id, and one column per stat.

        Stat columns: pts, reb, ast, fg3m, tov, stl, blk, pa, pr, ra, pra, stocks.
        Missing stats for a player are left as NaN.  Uses vectorised construction for
        performance at high sim counts.
        """
        WIDE_STATS = ["pts", "reb", "ast", "fg3m", "tov", "stl", "blk", "pa", "pr", "ra", "pra", "stocks"]
        player_stats: dict[tuple[str, str], dict[str, np.ndarray]] = {}
        for (game_id, player_id, stat), arr in self.stats.items():
            if stat in WIDE_STATS:
                player_stats.setdefault((game_id, player_id), {})[stat] = arr

        if not player_stats:
            return pd.DataFrame(columns=["simulation_id", "game_id", "player_id"] + WIDE_STATS)

        sim_ids = np.arange(self.n_sims, dtype=np.int32)
        parts = []
        for (game_id, player_id), stat_arrays in player_stats.items():
            chunk: dict[str, Any] = {
                "simulation_id": sim_ids,
                "game_id": game_id,
                "player_id": player_id,
            }
            for stat in WIDE_STATS:
                if stat in stat_arrays:
                    chunk[stat] = stat_arrays[stat].astype(np.int16)
                else:
                    chunk[stat] = np.full(self.n_sims, np.nan, dtype=np.float32)
            parts.append(pd.DataFrame(chunk))

        return pd.concat(parts, ignore_index=True)

    @classmethod
    def load_npz(cls, path: str | Path) -> "SimulationTape":
        z = np.load(path, allow_pickle=True)
        keys = [tuple(str(x).split("|", 2)) for x in z["__keys__"]]
        n_sims = int(z["__n_sims__"][0])
        stats = {}
        for i, key in enumerate(keys):
            stats[key] = z[f"stat_{i}"]
        factors = {k.replace("factor__", "", 1): z[k] for k in z.files if k.startswith("factor__")}
        return cls(n_sims=n_sims, stats=stats, factors=factors, metadata={"loaded_from": str(path)})
