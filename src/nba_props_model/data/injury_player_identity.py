"""Canonical injury-report name → player_id resolution with team/date context."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

from nba_props_model.schedule.game_start_times import NBA_TEAM_NAME_TO_ABBR

logger = logging.getLogger(__name__)

SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}


@dataclass
class InjuryMergeReport:
    total_nba_report_names: int = 0
    matched_exact: int = 0
    matched_initial_last_name: int = 0
    unmatched: int = 0
    ambiguous_dropped: int = 0
    alias_map_ambiguous_keys: list[str] = field(default_factory=list)
    unmatched_names: list[str] = field(default_factory=list)
    ambiguous_names: list[str] = field(default_factory=list)

    def to_compact_dict(self) -> dict[str, Any]:
        return {
            "total_nba_report_names": self.total_nba_report_names,
            "matched_exact": self.matched_exact,
            "matched_initial_last_name": self.matched_initial_last_name,
            "unmatched": self.unmatched,
            "ambiguous_dropped": self.ambiguous_dropped,
            "alias_map_ambiguous_keys": self.alias_map_ambiguous_keys,
            "unmatched_names": self.unmatched_names,
            "ambiguous_names": self.ambiguous_names,
        }


@dataclass(frozen=True)
class MatchResult:
    player_id: Optional[int]
    strategy: Optional[str]
    outcome: str  # resolved | unmatched | ambiguous


def parse_injury_name(name_lower: str) -> tuple[Optional[str], Optional[str], bool]:
    """Return (first_initial, last_name, had_suffix)."""
    tokens = [t for t in name_lower.split() if t]
    had_suffix = False
    if len(tokens) >= 2 and tokens[-1] in SUFFIXES:
        tokens = tokens[:-1]
        had_suffix = True
    if len(tokens) < 2:
        return None, None, had_suffix
    first_token = tokens[0]
    if not first_token:
        return None, None, had_suffix
    first_initial = first_token[0]
    last_name = " ".join(tokens[1:]).strip()
    if not first_initial or not last_name:
        return None, None, had_suffix
    return first_initial, last_name, had_suffix


def injury_report_team_to_abbr(team: str | None) -> tuple[str, bool]:
    """Map NBA official report team label to BDL-style abbreviation.

    Returns (abbr, mapped). ``mapped=False`` means the label could not be
    mapped to a canonical NBA team and must not be used to scope identity.
    """
    if not team:
        return "", False
    raw = str(team).strip()
    if not raw:
        return "", False
    if len(raw) <= 3 and raw.upper() == raw:
        return raw.upper(), True
    abbr = NBA_TEAM_NAME_TO_ABBR.get(raw)
    if abbr:
        return abbr, True
    lowered = raw.lower()
    for full, code in NBA_TEAM_NAME_TO_ABBR.items():
        if full.lower() == lowered:
            return code, True
    return raw.upper(), False


class InjuryPlayerIdentityIndex:
    """Roster-scoped player identity index for injury name matching."""

    def __init__(
        self,
        stats_df: pd.DataFrame,
        *,
        slate_date: str | None = None,
        name_column: str = "player_name",
    ) -> None:
        self._slate_date = slate_date
        self._name_column = name_column
        self._full_name_by_team: dict[tuple[str, str], set[int]] = {}
        self._full_name_global: dict[str, set[int]] = {}
        self._initial_by_team: dict[tuple[str, str], set[int]] = {}
        self._initial_global: dict[str, set[int]] = {}
        self._alias_ambiguous_initial: set[str] = set()
        self._build(stats_df)

    @property
    def alias_ambiguous_keys(self) -> list[str]:
        return sorted(self._alias_ambiguous_initial)

    def _build(self, stats_df: pd.DataFrame) -> None:
        if stats_df is None or stats_df.empty or self._name_column not in stats_df.columns:
            return

        df = stats_df.copy()
        if self._slate_date and "game_date" in df.columns:
            df["game_date"] = df["game_date"].astype(str).str[:10]
            df = df[df["game_date"] <= self._slate_date]
        if "game_date" in df.columns:
            df = df.sort_values("game_date", kind="mergesort")

        roster_cols = ["player_id", self._name_column]
        for col in ("team_abbr", "team", "team_id"):
            if col in df.columns:
                roster_cols.append(col)
        roster = df[roster_cols].drop_duplicates(subset=["player_id"], keep="last")

        for _, row in roster.iterrows():
            raw_name = str(row[self._name_column]).lower().strip()
            if not raw_name:
                continue
            try:
                pid = int(row["player_id"])
            except (TypeError, ValueError):
                continue

            team_abbr = ""
            team_mapped = False
            if "team_abbr" in row.index and pd.notna(row.get("team_abbr")):
                team_abbr = str(row["team_abbr"]).upper().strip()
                team_mapped = True
            elif "team" in row.index and pd.notna(row.get("team")):
                team_abbr, team_mapped = injury_report_team_to_abbr(str(row["team"]))

            self._full_name_global.setdefault(raw_name, set()).add(pid)
            if team_abbr and team_mapped:
                self._full_name_by_team.setdefault((raw_name, team_abbr), set()).add(pid)

            first_initial, last_name, _ = parse_injury_name(raw_name)
            if not (first_initial and last_name):
                continue
            for key in (f"{first_initial}. {last_name}", f"{first_initial} {last_name}"):
                if key in self._alias_ambiguous_initial:
                    continue
                bucket = self._initial_global.setdefault(key, set())
                bucket.add(pid)
                if len(bucket) > 1:
                    logger.warning(
                        "injury_merge_alias_ambiguous: key=%r candidate_pids=%s",
                        key,
                        sorted(bucket),
                    )
                    self._alias_ambiguous_initial.add(key)
                    self._initial_global.pop(key, None)
                if team_abbr and team_mapped:
                    self._initial_by_team.setdefault((key, team_abbr), set()).add(pid)

    def _resolve_exact(self, name_lower: str, team_abbr: str) -> MatchResult | None:
        if team_abbr:
            scoped = self._full_name_by_team.get((name_lower, team_abbr), set())
            if len(scoped) == 1:
                return MatchResult(next(iter(scoped)), "exact_full_name_team", "resolved")
            if len(scoped) > 1:
                return MatchResult(None, None, "ambiguous")

        global_cands = self._full_name_global.get(name_lower, set())
        if team_abbr:
            return None
        if len(global_cands) == 1:
            return MatchResult(next(iter(global_cands)), "exact_full_name", "resolved")
        if len(global_cands) > 1:
            return MatchResult(None, None, "ambiguous")
        return None

    def _initial_keys(self, name_lower: str) -> tuple[str, ...]:
        first_initial, last_name, _ = parse_injury_name(name_lower)
        if not (first_initial and last_name):
            return ()
        return (f"{first_initial}. {last_name}", f"{first_initial} {last_name}")

    def _resolve_initial(self, name_lower: str, team_abbr: str, *, had_suffix: bool) -> MatchResult:
        if had_suffix:
            return MatchResult(None, None, "unmatched")

        keys = self._initial_keys(name_lower)
        if not keys:
            return MatchResult(None, None, "unmatched")

        if team_abbr:
            for key in keys:
                scoped = self._initial_by_team.get((key, team_abbr), set())
                if len(scoped) == 1:
                    return MatchResult(next(iter(scoped)), "initial_last_name_team", "resolved")
                if len(scoped) > 1:
                    return MatchResult(None, None, "ambiguous")
            for key in keys:
                if key in self._alias_ambiguous_initial:
                    return MatchResult(None, None, "ambiguous")
            return MatchResult(None, None, "unmatched")

        for key in keys:
            if key in self._alias_ambiguous_initial:
                return MatchResult(None, None, "ambiguous")
            scoped = self._initial_global.get(key, set())
            if len(scoped) == 1:
                return MatchResult(next(iter(scoped)), "initial_last_name", "resolved")
            if len(scoped) > 1:
                return MatchResult(None, None, "ambiguous")
        return MatchResult(None, None, "unmatched")

    def resolve(
        self,
        name_lower: str,
        *,
        team: str | None = None,
        had_suffix: bool = False,
    ) -> MatchResult:
        team_abbr, team_mapped = injury_report_team_to_abbr(team)
        if not team_mapped:
            team_abbr = ""
        exact = self._resolve_exact(name_lower, team_abbr)
        if exact is not None:
            return exact
        return self._resolve_initial(name_lower, team_abbr, had_suffix=had_suffix)


def resolve_injury_report_name(
    index: InjuryPlayerIdentityIndex,
    name_lower: str,
    info: dict[str, Any],
) -> MatchResult:
    """Resolve one NBA injury-report entry using optional team metadata."""
    _, _, had_suffix = parse_injury_name(name_lower)
    if had_suffix and name_lower.split()[-1] in SUFFIXES:
        had_suffix = True
    team = info.get("team") if isinstance(info, dict) else None
    return index.resolve(name_lower, team=team, had_suffix=had_suffix)
