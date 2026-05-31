from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Literal

import pandas as pd


SUPPORTED_SIDES = {"over", "under", "o", "u", ">", "<", "gt", "lt", ">=", "<=", "ge", "le"}


@dataclass(frozen=True)
class SGPLeg:
    player_id: str
    stat: str
    line: float
    side: str
    game_id: str | None = None
    team_id: str | None = None
    label: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SGPLeg":
        side = str(d.get("side", d.get("direction", ""))).lower()
        if side not in SUPPORTED_SIDES:
            raise ValueError(f"Invalid SGP leg side {side!r}: {d}")
        return cls(
            player_id=str(d["player_id"] if "player_id" in d else d["playerId"]),
            stat=str(d["stat"]).lower(),
            line=float(d["line"]),
            side=side,
            game_id=str(d["game_id"]) if d.get("game_id") is not None else None,
            team_id=str(d["team_id"]) if d.get("team_id") is not None else None,
            label=d.get("label"),
        )


@dataclass(frozen=True)
class SGPTicket:
    legs: list[SGPLeg]
    ticket_id: str | None = None
    game_id: str | None = None
    offered_decimal_odds: float | None = None
    offered_american_odds: float | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SGPTicket":
        legs = [SGPLeg.from_dict(x) for x in d["legs"]]
        game_id = d.get("game_id") or d.get("gameId")
        if game_id is None:
            games = {leg.game_id for leg in legs if leg.game_id is not None}
            game_id = next(iter(games)) if len(games) == 1 else None
        return cls(
            legs=legs,
            ticket_id=d.get("ticket_id") or d.get("ticketId"),
            game_id=str(game_id) if game_id is not None else None,
            offered_decimal_odds=d.get("offered_decimal_odds"),
            offered_american_odds=d.get("offered_american_odds"),
        )

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


def american_to_decimal(american: float) -> float:
    american = float(american)
    if american > 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def decimal_to_american(decimal_odds: float) -> int:
    dec = float(decimal_odds)
    if dec <= 1:
        raise ValueError("Decimal odds must be > 1")
    if dec >= 2:
        return int(round((dec - 1) * 100))
    return int(round(-100 / (dec - 1)))


def prob_to_decimal(p: float) -> float:
    p = min(max(float(p), 1e-12), 1.0 - 1e-12)
    return 1.0 / p


def prob_to_american(p: float) -> int:
    return decimal_to_american(prob_to_decimal(p))


def calculate_ev(prob: float, decimal_odds: float) -> float:
    return float(prob) * float(decimal_odds) - 1.0


def read_table(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists() and path.suffix.lower() == ".parquet":
        csv_alt = path.with_suffix(".csv")
        if csv_alt.exists():
            path = csv_alt
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".json", ".jsonl"}:
        if suffix == ".jsonl":
            return pd.read_json(path, lines=True)
        return pd.read_json(path)
    raise ValueError(f"Unsupported table type: {path}")


def write_table(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        try:
            df.to_parquet(path, index=False)
        except ImportError:
            df.to_csv(path.with_suffix(".csv"), index=False)
    elif suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".jsonl":
        df.to_json(path, orient="records", lines=True)
    else:
        raise ValueError(f"Unsupported output table type: {path}")
