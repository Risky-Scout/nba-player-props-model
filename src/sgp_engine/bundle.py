from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .schema import read_table, write_table


BUNDLE_VERSION = "slate_state_bundle_v1"


@dataclass
class SlateStateBundle:
    root: Path
    manifest: dict[str, Any]
    games: pd.DataFrame
    players: pd.DataFrame
    player_stat_pmfs: pd.DataFrame
    market_lines: pd.DataFrame | None = None
    player_stat_components: pd.DataFrame | None = None
    game_team_context: pd.DataFrame | None = None
    lineup_scenarios: pd.DataFrame | None = None
    player_rotation_context: pd.DataFrame | None = None
    team_interaction_context: pd.DataFrame | None = None
    assist_network: pd.DataFrame | None = None
    rebound_context: pd.DataFrame | None = None
    defensive_event_context: pd.DataFrame | None = None
    calibration_context: pd.DataFrame | None = None

    @classmethod
    def load(cls, root: str | Path) -> "SlateStateBundle":
        root = Path(root)
        manifest_path = root / "bundle_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing bundle_manifest.json under {root}")
        manifest = json.loads(manifest_path.read_text())
        required = {
            "games": read_table(root / "games.parquet"),
            "players": read_table(root / "players.parquet"),
            "player_stat_pmfs": read_table(root / "player_stat_pmfs.parquet"),
        }
        optional_names = [
            "market_lines",
            "player_stat_components",
            "game_team_context",
            "lineup_scenarios",
            "player_rotation_context",
            "team_interaction_context",
            "assist_network",
            "rebound_context",
            "defensive_event_context",
            "calibration_context",
        ]
        optional = {}
        for name in optional_names:
            p = root / f"{name}.parquet"
            optional[name] = read_table(p) if p.exists() else None
        return cls(root=root, manifest=manifest, **required, **optional)

    def write(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "bundle_manifest.json").write_text(json.dumps(self.manifest, indent=2, sort_keys=True))
        write_table(self.games, self.root / "games.parquet")
        write_table(self.players, self.root / "players.parquet")
        write_table(self.player_stat_pmfs, self.root / "player_stat_pmfs.parquet")
        optional = {
            "market_lines": self.market_lines,
            "player_stat_components": self.player_stat_components,
            "game_team_context": self.game_team_context,
            "lineup_scenarios": self.lineup_scenarios,
            "player_rotation_context": self.player_rotation_context,
            "team_interaction_context": self.team_interaction_context,
            "assist_network": self.assist_network,
            "rebound_context": self.rebound_context,
            "defensive_event_context": self.defensive_event_context,
            "calibration_context": self.calibration_context,
        }
        for name, df in optional.items():
            if df is not None:
                write_table(df, self.root / f"{name}.parquet")

    @property
    def slate_date(self) -> str:
        return str(self.manifest.get("slate_date", ""))

    @property
    def status(self) -> str:
        return str(self.manifest.get("bundle_status", "UNKNOWN"))

    def assert_pass(self) -> None:
        if self.status != "PASS":
            raise RuntimeError(f"Slate bundle status is {self.status}; refusing to price.")
