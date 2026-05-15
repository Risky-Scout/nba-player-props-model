"""Player-game eligibility gate.

Single source of truth for whether a (slate_date, game_id, player_id) is
eligible to receive a model PMF in tonight's delivery.

Eligibility rule:

    player_game_eligible = (
        has_current_market_line
        OR starter_probability    >= 0.50
        OR rotation_probability   >= 0.50
        OR minutes_mean           >= 12
    )

Non-goals:
    * Does NOT compute PMFs.
    * Does NOT fetch BDL/Odds. Inputs are caller-supplied DataFrames.
    * Does NOT mutate inputs (returns a new frame).
    * Does NOT use market lines as the SOLE rotation signal — projected
      minutes/role from the internal minutes model are first-class.

Stale-date market lines are filtered out by ``build_current_market_player_signal``
which restricts the joined signal to rows whose ``slate_date`` exactly
matches the slate. Empty BDL ``/v2/lineups`` therefore cannot leak into
this module because nothing here consults BDL — eligibility decisions
come from the upstream minutes_predictions artifact plus today's odds
snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


EMPTY_LINE_VALUES = {"", " ", "NA", "N/A", "nan", "None", None}
ROTATION_MINUTES_FLOOR = 12.0
STARTER_PROB_FLOOR = 0.50
ROTATION_PROB_FLOOR = 0.50


REQUIRED_MINUTES_COLUMNS = [
    "slate_date",
    "game_id",
    "player_id",
    "minutes_mean",
    "minutes_p10",
    "minutes_p50",
    "minutes_p90",
    "minutes_std",
    "rotation_probability",
    "starter_probability",
    "projected_role",
    "p_inactive_used",
]


def normalize_line_column(df: pd.DataFrame, line_col: str = "line") -> pd.DataFrame:
    df = df.copy()
    if line_col not in df.columns:
        df[line_col] = np.nan

    df[line_col] = df[line_col].replace(list(EMPTY_LINE_VALUES), np.nan)
    df[line_col] = pd.to_numeric(df[line_col], errors="coerce")
    return df


def require_minutes_contract(minutes: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_MINUTES_COLUMNS if c not in minutes.columns]
    if missing:
        raise RuntimeError(
            f"minutes_predictions missing required columns: {missing}"
        )

    dupes = minutes.duplicated(["slate_date", "game_id", "player_id"]).sum()
    if dupes:
        raise RuntimeError(
            f"minutes_predictions has duplicate slate_date/game_id/player_id rows: {dupes}"
        )


def build_current_market_player_signal(
    market_df: pd.DataFrame,
    *,
    slate_date: str,
) -> pd.DataFrame:
    if market_df is None or market_df.empty:
        return pd.DataFrame(
            columns=[
                "slate_date",
                "game_id",
                "player_id",
                "has_current_market_line",
                "quoted_stats",
            ]
        )

    df = market_df.copy()

    if "slate_date" not in df.columns:
        if "game_date" in df.columns:
            df["slate_date"] = df["game_date"].astype(str).str[:10]
        else:
            df["slate_date"] = str(slate_date)

    df["slate_date"] = df["slate_date"].astype(str).str[:10]
    df = df[df["slate_date"] == str(slate_date)]

    df = normalize_line_column(df, "line")
    df = df.dropna(subset=["line"])

    if df.empty:
        return pd.DataFrame(
            columns=[
                "slate_date",
                "game_id",
                "player_id",
                "has_current_market_line",
                "quoted_stats",
            ]
        )

    if "stat" not in df.columns:
        df["stat"] = None

    out = (
        df.groupby(["slate_date", "game_id", "player_id"], as_index=False)
        .agg(
            has_current_market_line=("line", "size"),
            quoted_stats=("stat", lambda s: sorted(set(s.dropna().astype(str)))),
        )
    )
    out["has_current_market_line"] = out["has_current_market_line"] > 0
    return out


def build_player_game_eligibility(
    player_games: pd.DataFrame,
    minutes_predictions: pd.DataFrame,
    current_market_signal: pd.DataFrame,
    *,
    slate_date: str,
) -> pd.DataFrame:
    require_minutes_contract(minutes_predictions)

    base = player_games.copy()
    if "slate_date" not in base.columns:
        base["slate_date"] = str(slate_date)
    base["slate_date"] = base["slate_date"].astype(str).str[:10]

    required_base = ["slate_date", "game_id", "player_id"]
    missing_base = [c for c in required_base if c not in base.columns]
    if missing_base:
        raise RuntimeError(f"player_games missing required keys: {missing_base}")

    m = minutes_predictions.copy()
    m["slate_date"] = m["slate_date"].astype(str).str[:10]

    sig = current_market_signal.copy()
    if sig.empty:
        sig = pd.DataFrame(
            columns=[
                "slate_date",
                "game_id",
                "player_id",
                "has_current_market_line",
                "quoted_stats",
            ]
        )
    if "slate_date" not in sig.columns:
        sig["slate_date"] = str(slate_date)
    sig["slate_date"] = sig["slate_date"].astype(str).str[:10]

    keep_cols = [
        "slate_date",
        "game_id",
        "player_id",
        "minutes_mean",
        "minutes_p10",
        "minutes_p50",
        "minutes_p90",
        "minutes_std",
        "rotation_probability",
        "starter_probability",
        "projected_role",
        "p_inactive_used",
        "minutes_source",
        "minutes_model_version",
    ]
    keep_cols = [c for c in keep_cols if c in m.columns]

    out = (
        base.drop_duplicates(["slate_date", "game_id", "player_id"])
        .merge(
            m[keep_cols],
            on=["slate_date", "game_id", "player_id"],
            how="left",
            validate="one_to_one",
        )
        .merge(
            sig[
                [
                    "slate_date",
                    "game_id",
                    "player_id",
                    "has_current_market_line",
                    "quoted_stats",
                ]
            ],
            on=["slate_date", "game_id", "player_id"],
            how="left",
        )
    )

    out["has_current_market_line"] = out["has_current_market_line"].fillna(False)

    for c in ["minutes_mean", "rotation_probability", "starter_probability"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["player_game_eligible"] = (
        out["has_current_market_line"]
        | out["starter_probability"].ge(STARTER_PROB_FLOOR).fillna(False)
        | out["rotation_probability"].ge(ROTATION_PROB_FLOOR).fillna(False)
        | out["minutes_mean"].ge(ROTATION_MINUTES_FLOOR).fillna(False)
    )

    out["eligibility_reason"] = np.select(
        [
            out["has_current_market_line"],
            out["starter_probability"].ge(STARTER_PROB_FLOOR).fillna(False),
            out["rotation_probability"].ge(ROTATION_PROB_FLOOR).fillna(False),
            out["minutes_mean"].ge(ROTATION_MINUTES_FLOOR).fillna(False),
        ],
        [
            "current_market_line",
            "starter_probability",
            "rotation_probability",
            "minutes_floor",
        ],
        default="not_eligible",
    )

    return out


def assert_no_ineligible_pmfs(df: pd.DataFrame, *, label: str) -> None:
    if "player_game_eligible" not in df.columns:
        raise RuntimeError(f"{label} missing player_game_eligible")
    bad = df["player_game_eligible"].astype(bool) == False
    if bad.any():
        sample = df.loc[
            bad,
            [
                c
                for c in [
                    "slate_date",
                    "game_id",
                    "player_id",
                    "player_name",
                    "stat",
                    "minutes_mean",
                    "rotation_probability",
                    "starter_probability",
                    "eligibility_reason",
                ]
                if c in df.columns
            ],
        ].head(25).to_dict("records")
        raise RuntimeError(
            f"{label} contains ineligible PMF rows: {int(bad.sum())}; sample={sample}"
        )
