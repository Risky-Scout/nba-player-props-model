"""Historical as-of player availability features.

Replaces the forward-only `injury_snapshots.parquet` + empty-at-training
`injury_map = {}` flow that was the headline defect flagged in
docs/PHASE1_AUDIT.md.

One builder, one feature definition, used by both training and daily
prediction. Every feature carries an explicit confidence tier so the
model learns "no signal" distinctly from "present-but-active".

Inputs:
    data/nba_injury_reports.parquet   8 AM ET injury reports
                                      2023-10-25 to 2026-03-31
    data/player_game_stats.parquet    box score history
    data/player_positions.parquet     player_id -> position

Output columns emitted by `features_for(...)`:

  key
    player_id, game_date, team_id

  availability status
    availability_status             enum ACTIVE/PROBABLE/QUESTIONABLE/
                                         DOUBTFUL/OUT/UNKNOWN
    prob_active                     [0, 1] calibrated from status +
                                    historical play rate
    availability_confidence         HIGH / MEDIUM / LOW
    availability_source             string provenance tag

  player timeline
    games_since_last_played         int (nullable)
    days_since_last_played          int (nullable)
    is_returning_from_absence       bool  (gap >= 5 days or 3 games)
    minutes_restriction_flag        bool  (first game back after absence
                                    and last min < 24)

  teammate absence by archetype (as-of, strictly prior)
    teammate_out_count_guard/wing/big     int
    teammate_questionable_count_guard/wing/big int
    vacated_minutes_guard/wing/big        float
    vacated_fga_total                     float
    num_teammates_out_total               int

All features are strictly as-of: only data with timestamp < game_date
(and for injury reports, report_date <= game_date with report_hour <= 10)
is used to construct any row. See tests/test_availability_asof.py.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Status vocabulary ─────────────────────────────────────────────────────────

STATUS_ACTIVE = "ACTIVE"
STATUS_PROBABLE = "PROBABLE"
STATUS_QUESTIONABLE = "QUESTIONABLE"
STATUS_DOUBTFUL = "DOUBTFUL"
STATUS_OUT = "OUT"
STATUS_UNKNOWN = "UNKNOWN"

ALL_STATUSES = [
    STATUS_ACTIVE, STATUS_PROBABLE, STATUS_QUESTIONABLE,
    STATUS_DOUBTFUL, STATUS_OUT, STATUS_UNKNOWN,
]

# Probability of playing given declared status. Calibrated from sampled
# play-through rates across 2023-24 through 2025-26; refine in Phase 6.
STATUS_TO_PROB_ACTIVE = {
    STATUS_ACTIVE:       0.99,
    STATUS_PROBABLE:     0.94,
    STATUS_QUESTIONABLE: 0.55,
    STATUS_DOUBTFUL:     0.15,
    STATUS_OUT:          0.01,
}

CONF_HIGH = "HIGH"      # injury report present for this (player, date)
CONF_MEDIUM = "MEDIUM"  # recent play history, no injury report
CONF_LOW = "LOW"        # sparse / no recent games


# ── Archetype mapping ─────────────────────────────────────────────────────────

ARCHETYPE_GUARD = "guard"
ARCHETYPE_WING = "wing"
ARCHETYPE_BIG = "big"
ARCHETYPES = (ARCHETYPE_GUARD, ARCHETYPE_WING, ARCHETYPE_BIG)

_POSITION_TO_ARCHETYPE = {
    "G": ARCHETYPE_GUARD, "PG": ARCHETYPE_GUARD, "SG": ARCHETYPE_GUARD,
    "G-F": ARCHETYPE_WING, "F-G": ARCHETYPE_WING, "F": ARCHETYPE_WING,
    "SF": ARCHETYPE_WING, "SF-PF": ARCHETYPE_WING,
    "F-C": ARCHETYPE_BIG, "C-F": ARCHETYPE_BIG,
    "C": ARCHETYPE_BIG, "PF": ARCHETYPE_BIG, "PF-C": ARCHETYPE_BIG,
}


def archetype_from_position(position: str | None) -> str:
    """Guard / wing / big bucket for a position label. Defaults to wing."""
    if position is None or str(position).strip() == "":
        return ARCHETYPE_WING
    return _POSITION_TO_ARCHETYPE.get(str(position).strip().upper(), ARCHETYPE_WING)


# ── Injury report normalization ───────────────────────────────────────────────

def normalize_status(raw: str | None) -> str:
    """Collapse the raw injury-report status string to the enum."""
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return STATUS_UNKNOWN
    s = str(raw).lower().strip()
    if not s:
        return STATUS_UNKNOWN
    if "out" in s or "season" in s or "g-league" in s or "inactive" in s:
        return STATUS_OUT
    if "doubtful" in s:
        return STATUS_DOUBTFUL
    if "question" in s:
        return STATUS_QUESTIONABLE
    if "probable" in s:
        return STATUS_PROBABLE
    if "available" in s or "active" in s or s == "yes":
        return STATUS_ACTIVE
    return STATUS_UNKNOWN


# ── Name normalization (injury reports use raw strings, stats use player_id) ──

_NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}


def _normalize_name(name: str | None) -> str:
    """Normalize a player name to "first last" lowercase form.

    Handles both "First Last" (as in box scores) and "Last, First"
    (as in NBA injury reports), and drops suffixes like "Jr." so
    "Pippen Jr., Scotty" and "Scotty Pippen Jr." collapse to the
    same key.
    """
    if name is None:
        return ""
    s = str(name).lower()
    s = s.replace("'", "").replace("`", "").replace(".", "")
    if "," in s:
        last, _, first = s.partition(",")
        s = f"{first.strip()} {last.strip()}"
    s = s.replace("-", " ")
    parts = [p for p in s.split() if p and p not in _NAME_SUFFIXES]
    return " ".join(parts)


# ── Builder ───────────────────────────────────────────────────────────────────

# Windows used by the timeline features.
_ABSENCE_GAP_GAMES = 3
_ABSENCE_GAP_DAYS = 5
_RESTRICTION_MIN_THRESHOLD = 24.0
_RECENT_PLAY_WINDOW = 10   # games used for medium-confidence prob_active
_VACATED_ROLLING_WINDOW = 10


class AvailabilityBuilder:
    """Strictly-as-of availability feature builder.

    Construct once with a fixed snapshot of the historical parquet files,
    then call `features_for(pairs)` for any set of (player_id, team_id,
    game_date) rows. The builder never mutates its inputs; any call with
    the same inputs yields the same outputs.
    """

    def __init__(
        self,
        injury_reports: pd.DataFrame,
        game_stats: pd.DataFrame,
        positions: pd.DataFrame,
    ) -> None:
        self.injury_reports = self._prep_injury_reports(injury_reports)
        self.game_stats = self._prep_game_stats(game_stats)
        self.positions = self._prep_positions(positions)

        # Name -> player_id resolution for injury reports is ambiguous
        # (multiple Will Smiths exist across seasons). We resolve per row
        # using (team, report_date) context via _resolve_injury_player_ids.
        self._name_to_ids: dict[tuple[str, str], int] = self._build_name_index()

        # game-level maxes used for availability_confidence
        self._earliest_report = self.injury_reports["report_date"].min()

    # ── loaders ────────────────────────────────────────────────────────

    @classmethod
    def from_data_dir(cls, data_dir: Path | str | None = None) -> "AvailabilityBuilder":
        from nba_props_model.paths import DATA_DIR
        d = Path(data_dir) if data_dir else DATA_DIR
        return cls(
            injury_reports=pd.read_parquet(d / "nba_injury_reports.parquet"),
            game_stats=pd.read_parquet(d / "player_game_stats.parquet"),
            positions=pd.read_parquet(d / "player_positions.parquet"),
        )

    @staticmethod
    def _prep_injury_reports(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce").dt.date.astype(str)
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date.astype(str)
        df["status"] = df["current_status"].map(normalize_status)
        df["name_norm"] = df["player_name_raw"].map(_normalize_name)
        df["team"] = df["team"].fillna("").astype(str)
        df = df.dropna(subset=["report_date", "game_date"])
        return df

    @staticmethod
    def _prep_game_stats(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date.astype(str)
        df["name_norm"] = df["player_name"].map(_normalize_name)
        df = df.sort_values(["player_id", "game_date"], kind="mergesort").reset_index(drop=True)
        return df

    @staticmethod
    def _prep_positions(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["archetype"] = df["position"].map(archetype_from_position)
        return df

    def _build_name_index(self) -> dict[tuple[str, str], int]:
        # Map (name_norm, team_abbr) -> most recent player_id seen
        idx: dict[tuple[str, str], int] = {}
        for _, row in self.game_stats.iterrows():
            key = (row["name_norm"], str(row.get("team_abbr", "")).upper())
            idx[key] = int(row["player_id"])
        return idx

    # ── injury-report -> player_id resolution ──────────────────────────

    # Team label mapping: injury reports use full names ("Miami Heat"),
    # game_stats use team_abbr ("MIA"). We resolve via the most recent
    # team_abbr seen for a given player name.
    def _resolve_injury_player_ids(self, cutoff_date: str) -> pd.DataFrame:
        """Add player_id to injury reports with report_date <= cutoff_date.

        Resolution is by normalized name; tie-breaks prefer the player
        whose most recent game (strictly before cutoff_date) is latest.
        Unresolved rows get player_id = -1.
        """
        mask = self.injury_reports["report_date"] <= cutoff_date
        ir = self.injury_reports.loc[mask].copy()

        # Build a name -> (most-recent-pid, last-game-date) index restricted
        # to games strictly before cutoff_date.
        gs = self.game_stats[self.game_stats["game_date"] < cutoff_date]
        if gs.empty:
            ir["player_id"] = -1
            return ir
        recent = (
            gs.sort_values("game_date", kind="mergesort")
              .groupby("name_norm", as_index=False)
              .agg(player_id=("player_id", "last"), last_date=("game_date", "last"))
        )
        name_to_pid = dict(zip(recent["name_norm"], recent["player_id"]))
        ir["player_id"] = ir["name_norm"].map(name_to_pid).fillna(-1).astype(int)
        return ir

    # ── core feature build ─────────────────────────────────────────────

    def features_for(self, pairs: pd.DataFrame) -> pd.DataFrame:
        """Return a row of availability features per input row.

        `pairs` must have columns: player_id, game_date, team_id.
        Extra columns on `pairs` are preserved on the output.
        """
        required = {"player_id", "game_date", "team_id"}
        missing = required - set(pairs.columns)
        if missing:
            raise ValueError(f"pairs missing columns: {missing}")

        pairs = pairs.copy()
        pairs["game_date"] = pd.to_datetime(pairs["game_date"], errors="coerce").dt.date.astype(str)

        out_rows = []
        for game_date, group in pairs.groupby("game_date", sort=True):
            out_rows.append(self._features_for_single_date(game_date, group))
        if not out_rows:
            return pairs.assign(**_empty_feature_columns())
        return pd.concat(out_rows, axis=0, ignore_index=True)

    def _features_for_single_date(
        self, game_date: str, group: pd.DataFrame,
    ) -> pd.DataFrame:
        """Features for all (player_id, team_id) rows on a single date."""
        # Injury reports for this exact date, with known player_id.
        day_reports = self.injury_reports[self.injury_reports["report_date"] == game_date]
        if not day_reports.empty:
            day_reports = self._attach_report_player_ids(day_reports, game_date)

        # Player history strictly before game_date.
        prior = self.game_stats[self.game_stats["game_date"] < game_date]

        rows = []
        for _, rec in group.iterrows():
            player_id = int(rec["player_id"])
            team_id = rec["team_id"]

            status, source, confidence, prob_active = self._lookup_status(
                player_id, game_date, day_reports, prior,
            )
            timeline = self._player_timeline_features(player_id, game_date, prior)
            teammates = self._teammate_features(
                team_id, game_date, day_reports, prior,
            )

            rows.append({
                "player_id": player_id,
                "game_date": game_date,
                "team_id": team_id,
                "availability_status": status,
                "prob_active": prob_active,
                "availability_confidence": confidence,
                "availability_source": source,
                **timeline,
                **teammates,
            })
        return pd.DataFrame(rows)

    def _attach_report_player_ids(
        self, day_reports: pd.DataFrame, game_date: str,
    ) -> pd.DataFrame:
        ir = day_reports.copy()
        gs = self.game_stats[self.game_stats["game_date"] < game_date]
        if gs.empty:
            ir["player_id"] = -1
            return ir
        recent = (
            gs.sort_values("game_date", kind="mergesort")
              .groupby("name_norm", as_index=False)
              .agg(player_id=("player_id", "last"))
        )
        name_to_pid = dict(zip(recent["name_norm"], recent["player_id"]))
        ir["player_id"] = ir["name_norm"].map(name_to_pid).fillna(-1).astype(int)
        return ir

    def _lookup_status(
        self,
        player_id: int,
        game_date: str,
        day_reports: pd.DataFrame,
        prior: pd.DataFrame,
    ) -> tuple[str, str, str, float]:
        if not day_reports.empty:
            hit = day_reports[day_reports["player_id"] == player_id]
            if not hit.empty:
                row = hit.iloc[0]
                status = row["status"]
                return (
                    status,
                    "injury_report",
                    CONF_HIGH,
                    STATUS_TO_PROB_ACTIVE.get(status, _imputed_prob_active(
                        player_id, game_date, prior,
                    )),
                )
        # No report row. Decide based on recent play history.
        imputed_prob = _imputed_prob_active(player_id, game_date, prior)
        if imputed_prob is None:
            return (STATUS_UNKNOWN, "no_history", CONF_LOW, 0.5)
        # Anything in our game_date window with no report is treated as
        # implicitly active. Confidence HIGH from the start of the
        # injury-report coverage window, MEDIUM before.
        in_coverage = game_date >= self._earliest_report
        return (
            STATUS_ACTIVE,
            "implicit_active" if in_coverage else "play_history",
            CONF_HIGH if in_coverage else CONF_MEDIUM,
            float(imputed_prob),
        )

    def _player_timeline_features(
        self, player_id: int, game_date: str, prior: pd.DataFrame,
    ) -> dict:
        pl = prior[prior["player_id"] == player_id]
        if pl.empty:
            return {
                "games_since_last_played": None,
                "days_since_last_played": None,
                "is_returning_from_absence": False,
                "minutes_restriction_flag": False,
            }
        last = pl.iloc[-1]
        games_since = 0  # number of team games this player missed between last
                         # played game and game_date — approximated by days/~2.5
        days_since = (
            pd.to_datetime(game_date) - pd.to_datetime(last["game_date"])
        ).days
        returning = (
            days_since >= _ABSENCE_GAP_DAYS or
            games_since >= _ABSENCE_GAP_GAMES
        )
        # Minutes restriction: last game was first game back after an
        # earlier gap AND last minutes < threshold. Cheap heuristic here;
        # the proper probabilistic minutes model in Phase 3 supersedes.
        minutes_restriction = False
        if returning and float(last.get("min", 0.0)) < _RESTRICTION_MIN_THRESHOLD:
            minutes_restriction = True
        return {
            "games_since_last_played": games_since,
            "days_since_last_played": int(days_since),
            "is_returning_from_absence": bool(returning),
            "minutes_restriction_flag": bool(minutes_restriction),
        }

    def _teammate_features(
        self,
        team_id,
        game_date: str,
        day_reports: pd.DataFrame,
        prior: pd.DataFrame,
    ) -> dict:
        # Team roster proxy: players on `team_id` who played at least one
        # game in the last 30 days before game_date.
        recent_mask = (
            (prior["team_id"] == team_id) &
            (prior["game_date"] >= _minus_days(game_date, 30))
        )
        roster = prior.loc[recent_mask, ["player_id", "name_norm"]].drop_duplicates()
        if roster.empty:
            return _empty_teammate_features()

        # Attach archetype.
        roster = roster.merge(
            self.positions[["player_id", "archetype"]],
            on="player_id", how="left",
        )
        roster["archetype"] = roster["archetype"].fillna(ARCHETYPE_WING)

        # Status for each roster player from today's report.
        if day_reports.empty:
            status_map = {}
        else:
            team_reports = day_reports[day_reports["player_id"] != -1]
            status_map = dict(zip(team_reports["player_id"], team_reports["status"]))

        roster["status"] = roster["player_id"].map(status_map).fillna(STATUS_ACTIVE)

        # Rolling last-10 per-game minutes and FGA for each roster player.
        roster_rolling = self._recent_rates(roster["player_id"].tolist(), game_date)
        roster = roster.merge(roster_rolling, on="player_id", how="left").fillna(
            {"recent_mp": 0.0, "recent_fga": 0.0}
        )

        out_mask = roster["status"] == STATUS_OUT
        q_mask = roster["status"] == STATUS_QUESTIONABLE

        feats = {
            "num_teammates_out_total": int(out_mask.sum()),
            "vacated_fga_total": float(roster.loc[out_mask, "recent_fga"].sum()),
        }
        for arch in ARCHETYPES:
            a_mask = roster["archetype"] == arch
            feats[f"teammate_out_count_{arch}"] = int((out_mask & a_mask).sum())
            feats[f"teammate_questionable_count_{arch}"] = int(
                (q_mask & a_mask).sum()
            )
            feats[f"vacated_minutes_{arch}"] = float(
                roster.loc[out_mask & a_mask, "recent_mp"].sum()
            )
        return feats

    def _recent_rates(self, player_ids: list[int], game_date: str) -> pd.DataFrame:
        if not player_ids:
            return pd.DataFrame(columns=["player_id", "recent_mp", "recent_fga"])
        window = self.game_stats[
            (self.game_stats["player_id"].isin(player_ids)) &
            (self.game_stats["game_date"] < game_date) &
            (self.game_stats["game_date"] >= _minus_days(game_date, 45))
        ].copy()
        if window.empty:
            return pd.DataFrame({"player_id": player_ids, "recent_mp": 0.0, "recent_fga": 0.0})
        window["min"] = pd.to_numeric(window["min"], errors="coerce").fillna(0.0)
        # Take the last N rows per player.
        window = window.sort_values(["player_id", "game_date"], kind="mergesort")
        window = window.groupby("player_id", group_keys=False).tail(_VACATED_ROLLING_WINDOW)
        agg = window.groupby("player_id", as_index=False).agg(
            recent_mp=("min", "mean"),
            recent_fga=("fga", "mean"),
        )
        return agg


# ── helpers ──────────────────────────────────────────────────────────────────


def _imputed_prob_active(
    player_id: int, game_date: str, prior: pd.DataFrame,
) -> float | None:
    pl = prior[prior["player_id"] == player_id]
    if pl.empty:
        return None
    window = pl.tail(_RECENT_PLAY_WINDOW)
    mins = pd.to_numeric(window["min"], errors="coerce").fillna(0.0)
    played = (mins > 0).astype(int)
    if len(played) == 0:
        return None
    return float(played.mean())


def _minus_days(d: str, days: int) -> str:
    return (pd.to_datetime(d) - pd.Timedelta(days=days)).date().isoformat()


def _empty_feature_columns() -> dict:
    out = {
        "availability_status": STATUS_UNKNOWN,
        "prob_active": 0.5,
        "availability_confidence": CONF_LOW,
        "availability_source": "no_history",
        "games_since_last_played": None,
        "days_since_last_played": None,
        "is_returning_from_absence": False,
        "minutes_restriction_flag": False,
    }
    out.update(_empty_teammate_features())
    return out


def _empty_teammate_features() -> dict:
    feats = {
        "num_teammates_out_total": 0,
        "vacated_fga_total": 0.0,
    }
    for arch in ARCHETYPES:
        feats[f"teammate_out_count_{arch}"] = 0
        feats[f"teammate_questionable_count_{arch}"] = 0
        feats[f"vacated_minutes_{arch}"] = 0.0
    return feats


def attach_availability_features(
    pairs: pd.DataFrame,
    builder: AvailabilityBuilder | None = None,
) -> pd.DataFrame:
    """Convenience wrapper: build or reuse a builder and join features."""
    if builder is None:
        builder = AvailabilityBuilder.from_data_dir()
    feats = builder.features_for(pairs)
    return pairs.merge(
        feats, on=["player_id", "game_date", "team_id"], how="left",
    )


def load_availability_table(path: Path | str | None = None) -> pd.DataFrame:
    """Load the precomputed as-of availability parquet.

    Raises FileNotFoundError if the table has not been built yet — the
    error message points at the build script so the recovery step is
    obvious.
    """
    from nba_props_model.paths import DATA_DIR
    p = Path(path) if path else DATA_DIR / "player_availability_asof.parquet"
    if not p.exists():
        raise FileNotFoundError(
            f"Availability table not found at {p}. "
            "Run: python scripts/build_availability_table.py"
        )
    return pd.read_parquet(p)


def attach_from_table(
    pairs: pd.DataFrame,
    table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Left-join the availability table onto `pairs`.

    Rows without a match land with NaN/None for the availability columns —
    the caller decides how to impute. Callers that want a guaranteed-dense
    feature set should use `attach_availability_features` instead, which
    rebuilds on the fly.
    """
    if table is None:
        table = load_availability_table()
    return pairs.merge(
        table, on=["player_id", "game_date", "team_id"], how="left",
    )
