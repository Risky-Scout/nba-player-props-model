"""Phase 13U — cascading game-start-time resolver.

Resolves a per-game UTC start time using only real sources, in priority
order:

    1. existing ``predictions/all_props_<date>.parquet`` ``game_start_time``
       column (when populated for the row's game_id).
    2. ``predictions/pmf_display_<date>.json`` top-level / row-level
       time keys when present.
    3. cached Odds API processed parquet
       ``data/odds_api/processed/<date>/odds_pairs_*.parquet`` —
       ``commence_time_utc`` keyed by (home_team, away_team).
    4. cached Odds API raw events ``data/odds_api/raw/<date>/event_*.json``.
    5. live Odds API events endpoint
       ``GET /v4/sports/basketball_nba/events?apiKey=…`` (when
       ``ODDS_API_KEY`` is in the environment).
    6. live BDL ``/v1/games?start_date=&end_date=`` (when
       ``BDL_API_KEY`` is in the environment).

The resolver returns one ``GameStartTimeRecord`` per
``(game_id, team_id_for_team, team_id_for_opponent)`` tuple, carrying:

    * resolved_game_start_time_utc (str or None)
    * source_used (str)
    * source_confidence ('high'/'medium'/'low'/'unresolved')
    * source_payload_hash (str, used to audit subsequent resolutions)
    * resolution_blocker (str when resolution failed)

No fabricated timestamps are ever produced; if every source returns
nothing the record's ``resolution_blocker`` is set explicitly and
``resolved_game_start_time_utc`` is ``None``.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional


REPO_ROOT = Path(__file__).resolve().parents[3]


# Canonical NBA team-name → abbreviation mapping (mirrors
# scripts/build_daily_pmf_delivery.py).
NBA_TEAM_NAME_TO_ABBR: dict[str, str] = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU",
    "Indiana Pacers": "IND", "LA Clippers": "LAC",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM", "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}
NBA_TEAM_ABBR_TO_NAME: dict[str, str] = {
    v: k for k, v in NBA_TEAM_NAME_TO_ABBR.items()
}


@dataclass
class GameStartTimeRecord:
    game_id: str
    team_abbr: str
    opponent_abbr: str
    resolved_game_start_time_utc: Optional[str] = None
    source_used: str = "unresolved"
    source_confidence: str = "unresolved"
    source_payload_hash: str = ""
    resolution_blocker: str = ""

    def as_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "team_abbr": self.team_abbr,
            "opponent_abbr": self.opponent_abbr,
            "resolved_game_start_time_utc": self.resolved_game_start_time_utc,
            "source_used": self.source_used,
            "source_confidence": self.source_confidence,
            "source_payload_hash": self.source_payload_hash,
            "resolution_blocker": self.resolution_blocker,
        }


def _hash_payload(payload) -> str:
    if isinstance(payload, (dict, list)):
        s = json.dumps(payload, sort_keys=True, default=str)
    else:
        s = str(payload)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _load_team_id_to_abbr(repo_root: Path) -> dict[int, str]:
    p = repo_root / "data" / "player_game_stats.parquet"
    if not p.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_parquet(p, columns=["team_id", "team_abbr"]).drop_duplicates()
        return dict(zip(df["team_id"].astype(int), df["team_abbr"].astype(str)))
    except Exception:
        return {}


def _load_predictions(repo_root: Path, delivery_date: str):
    """Load predictions DataFrame for game-id resolution.

    Cascade:
    1. ``predictions/all_props_<date>.parquet`` — written by the daily
       predict step (present on normal game days).
    2. ``deliveries/<date>/canonical_source/all_props_model_only.parquet``
       — written by the delivery build; available even when the predict
       step failed or ran in a mode that skips the predictions/ commit
       (e.g. woo_morning_monetization manual rebuild). Carries game_id
       which is all the resolver needs to anchor tip-time lookups.
    """
    p = repo_root / "predictions" / f"all_props_{delivery_date}.parquet"
    if p.exists():
        try:
            import pandas as pd
            return pd.read_parquet(p), p
        except Exception:
            return None, p
    # Fallback: canonical delivery artifact — has game_id even when the
    # predictions/ file was never committed (manual rebuild modes).
    p2 = (repo_root / "deliveries" / delivery_date
          / "canonical_source" / "all_props_model_only.parquet")
    if p2.exists():
        try:
            import pandas as pd
            return pd.read_parquet(p2), p2
        except Exception:
            return None, p2
    return None, p


def _load_pmf_display(repo_root: Path, delivery_date: str) -> Optional[dict]:
    p = repo_root / "predictions" / f"pmf_display_{delivery_date}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_pmf_display_matchups(pmf_disp: Optional[dict]) -> dict[tuple[str, str], str]:
    """Return ``{(away_abbr, home_abbr): "Away @ Home"}`` plus reverse,
    parsed from ``pmf_display['props'][i]['game']`` strings."""
    out: dict[tuple[str, str], str] = {}
    if not pmf_disp:
        return out
    for prop in (pmf_disp.get("props") or []):
        s = prop.get("game") or ""
        if " @ " not in s:
            continue
        away, home = s.split(" @ ", 1)
        away_a = NBA_TEAM_NAME_TO_ABBR.get(away.strip())
        home_a = NBA_TEAM_NAME_TO_ABBR.get(home.strip())
        if away_a and home_a:
            out[(away_a, home_a)] = s
            out[(home_a, away_a)] = s
    return out


def _from_predictions(predictions_df, repo_root: Path
                       ) -> dict[str, GameStartTimeRecord]:
    """Source 1: existing predictions parquet ``game_start_time`` column."""
    out: dict[str, GameStartTimeRecord] = {}
    if predictions_df is None or "game_id" not in predictions_df.columns:
        return out
    if "game_start_time" not in predictions_df.columns:
        return out
    team_map = _load_team_id_to_abbr(repo_root)
    for gid, sub in predictions_df.groupby(predictions_df["game_id"].astype(str)):
        non_null = sub["game_start_time"].dropna()
        if non_null.empty:
            continue
        gt = str(non_null.iloc[0])
        team_ids = sorted({int(t) for t in sub["team_id"].dropna().unique()
                            if "team_id" in sub.columns})[:2]
        if len(team_ids) >= 2:
            a = team_map.get(team_ids[0], "")
            b = team_map.get(team_ids[1], "")
        else:
            a = b = ""
        out[gid] = GameStartTimeRecord(
            game_id=gid, team_abbr=a, opponent_abbr=b,
            resolved_game_start_time_utc=gt,
            source_used="predictions_parquet_game_start_time",
            source_confidence="high",
            source_payload_hash=_hash_payload(gt),
        )
    return out


def _from_odds_api_cached(repo_root: Path, delivery_date: str,
                            ) -> list[dict]:
    """Source 3 + 4: cached Odds API for that delivery_date. Returns a
    list of ``{"home": abbr, "away": abbr, "commence_time_utc": str,
    "event_id": str, "source_payload_hash": str}`` records."""
    rows: list[dict] = []
    proc = repo_root / "data" / "odds_api" / "processed" / delivery_date
    if proc.exists():
        try:
            import pandas as pd
            files = sorted(proc.glob("odds_pairs_*.parquet"))
            if files:
                # Latest snapshot for the date.
                df = pd.read_parquet(files[-1])
                if "commence_time_utc" in df.columns:
                    sub = df[["event_id", "home_team", "away_team",
                              "commence_time_utc"]].drop_duplicates()
                    for _, r in sub.iterrows():
                        home = NBA_TEAM_NAME_TO_ABBR.get(str(r.get("home_team")))
                        away = NBA_TEAM_NAME_TO_ABBR.get(str(r.get("away_team")))
                        if not (home and away):
                            continue
                        rows.append({
                            "home": home, "away": away,
                            "commence_time_utc": str(r["commence_time_utc"]),
                            "event_id": str(r["event_id"]),
                            "source": "odds_api_processed_cached",
                            "source_file": files[-1].name,
                        })
        except Exception:
            pass
    raw = repo_root / "data" / "odds_api" / "raw" / delivery_date
    if not rows and raw.exists():
        for fn in sorted(raw.glob("event_*.json")):
            try:
                rec = json.loads(fn.read_text(encoding="utf-8"))
                home = NBA_TEAM_NAME_TO_ABBR.get(str(rec.get("home_team")))
                away = NBA_TEAM_NAME_TO_ABBR.get(str(rec.get("away_team")))
                ct = rec.get("commence_time")
                if home and away and ct:
                    rows.append({
                        "home": home, "away": away,
                        "commence_time_utc": str(ct),
                        "event_id": str(rec.get("id", "")),
                        "source": "odds_api_raw_cached",
                        "source_file": fn.name,
                    })
            except Exception:
                continue
    return rows


def _odds_api_live_events(api_key: str, *, timeout: float = 10.0
                          ) -> list[dict]:
    """Source 5: live Odds API events. Returns the raw events list."""
    if not api_key:
        return []
    base = "https://api.the-odds-api.com/v4/sports/basketball_nba/events"
    qs = urllib.parse.urlencode({"apiKey": api_key, "dateFormat": "iso"})
    url = f"{base}?{qs}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "phase13u-game-start-time-resolver",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []


def _bdl_live_games(api_key: str, delivery_date: str, *, timeout: float = 10.0
                    ) -> list[dict]:
    """Source 6: live BDL ``/v1/games`` for the delivery date."""
    if not api_key:
        return []
    qs = urllib.parse.urlencode([
        ("start_date", delivery_date),
        ("end_date", delivery_date),
        ("per_page", 100),
    ])
    url = f"https://api.balldontlie.io/nba/v1/games?{qs}"
    try:
        req = urllib.request.Request(url, headers={
            "Authorization": api_key,
            "User-Agent": "phase13u-game-start-time-resolver",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return list(payload.get("data") or [])
    except Exception:
        return []


def _games_to_lookup(events: Iterable[dict]) -> dict[tuple[str, str], dict]:
    """Index ``{(away_abbr, home_abbr): {commence_time_utc, event_id, source}}``
    from a list of cached/live event records."""
    out: dict[tuple[str, str], dict] = {}
    for ev in events:
        away_a = ev.get("away") or NBA_TEAM_NAME_TO_ABBR.get(
            str(ev.get("away_team", "")))
        home_a = ev.get("home") or NBA_TEAM_NAME_TO_ABBR.get(
            str(ev.get("home_team", "")))
        ct = ev.get("commence_time_utc") or ev.get("commence_time")
        if not (away_a and home_a and ct):
            continue
        key = (away_a, home_a)
        out[key] = {
            "commence_time_utc": str(ct),
            "event_id": ev.get("event_id") or ev.get("id") or "",
            "source": ev.get("source") or "odds_api_live",
            "source_file": ev.get("source_file"),
        }
        out[(home_a, away_a)] = out[key]
    return out


def _bdl_games_to_lookup(games: Iterable[dict]) -> dict[str, dict]:
    """Index BDL ``/v1/games`` payloads by ``id``-as-string and team
    abbreviations."""
    by_gid: dict[str, dict] = {}
    by_pair: dict[tuple[str, str], dict] = {}
    for g in games:
        gid = str(g.get("id") or "")
        if not gid:
            continue
        # BDL game.status is "Final" / "<scheduled-time-string>" / etc.
        # game.date is YYYY-MM-DD (date-only, ET typically). game.time
        # is the tip clock when the game has started; for scheduled games
        # use status which is the human-readable scheduled tip in ET.
        # The most reliable timestamp is `time` only when game has tipped.
        # For scheduled games we rely on `status` plus the ``date`` UTC
        # midpoint approximation — but to avoid fabricating, we treat
        # BDL as providing only the date (no precise tip), and only
        # honor the cached/live Odds API result for tip timing.
        record = {
            "commence_time_utc": g.get("datetime"),
            "event_id": gid,
            "source": "bdl_games",
            "bdl_status": g.get("status"),
            "bdl_date": g.get("date"),
            "bdl_time": g.get("time"),
            "home_team_abbr": (g.get("home_team") or {}).get("abbreviation"),
            "visitor_team_abbr": (g.get("visitor_team") or {}).get("abbreviation"),
        }
        by_gid[gid] = record
        h = record["home_team_abbr"]
        a = record["visitor_team_abbr"]
        if h and a:
            by_pair[(a, h)] = record
            by_pair[(h, a)] = record
    return {"by_gid": by_gid, "by_pair": by_pair}


@dataclass
class GameStartTimeResolver:
    repo_root: Path = REPO_ROOT
    odds_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("ODDS_API_KEY")
    )
    bdl_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("BDL_API_KEY")
    )

    def resolve(self, delivery_date: str
                ) -> tuple[list[GameStartTimeRecord], dict]:
        """Return ``(records, telemetry)``."""
        team_id_to_abbr = _load_team_id_to_abbr(self.repo_root)
        predictions_df, _pred_path = _load_predictions(
            self.repo_root, delivery_date)
        pmf_disp = _load_pmf_display(self.repo_root, delivery_date)
        matchups_from_pmf = _parse_pmf_display_matchups(pmf_disp)

        # Source 1 — existing parquet column.
        from_pred = _from_predictions(predictions_df, self.repo_root)

        # Source 3+4 — cached Odds API.
        cached_events = _from_odds_api_cached(self.repo_root, delivery_date)
        cached_lookup = _games_to_lookup(cached_events)

        # Source 5 — live Odds API.
        live_events = (
            _odds_api_live_events(self.odds_api_key) if self.odds_api_key else []
        )
        live_lookup = _games_to_lookup([
            {"home": NBA_TEAM_NAME_TO_ABBR.get(str(e.get("home_team", ""))),
             "away": NBA_TEAM_NAME_TO_ABBR.get(str(e.get("away_team", ""))),
             "commence_time_utc": e.get("commence_time"),
             "event_id": e.get("id"),
             "source": "odds_api_live"}
            for e in live_events
            if e.get("commence_time")
        ])

        # Source 6 — live BDL games.
        bdl_games = (
            _bdl_live_games(self.bdl_api_key, delivery_date)
            if self.bdl_api_key else []
        )
        bdl_lookup = _bdl_games_to_lookup(bdl_games)

        records: list[GameStartTimeRecord] = []
        telemetry: dict = {
            "delivery_date": delivery_date,
            "predictions_present": predictions_df is not None,
            "predictions_rows": int(len(predictions_df)) if predictions_df is not None else 0,
            "predictions_unique_games": (
                int(predictions_df["game_id"].astype(str).nunique())
                if predictions_df is not None and "game_id" in predictions_df.columns
                else 0
            ),
            "from_predictions_count": len(from_pred),
            "odds_api_cached_events": len(cached_events),
            "odds_api_live_events": len(live_events),
            "bdl_live_games": len(bdl_games),
            "odds_api_key_present": bool(self.odds_api_key),
            "bdl_api_key_present": bool(self.bdl_api_key),
            "pmf_display_matchups_parsed": len(matchups_from_pmf) // 2,
        }

        if predictions_df is None or "game_id" not in predictions_df.columns:
            telemetry["resolution_blocker"] = (
                "predictions/all_props_<date>.parquet missing or has no game_id"
            )
            return records, telemetry

        # Iterate over unique games in the predictions parquet.
        for gid, sub in predictions_df.groupby(
            predictions_df["game_id"].astype(str)
        ):
            team_ids = sorted({
                int(t) for t in sub["team_id"].dropna().unique()
                if "team_id" in sub.columns
            })
            abbrs = [team_id_to_abbr.get(t, "") for t in team_ids]
            team_abbr = abbrs[0] if abbrs else ""
            opponent_abbr = abbrs[1] if len(abbrs) > 1 else ""

            # Source 1.
            rec = from_pred.get(gid)
            if rec is not None:
                rec.team_abbr = team_abbr
                rec.opponent_abbr = opponent_abbr
                records.append(rec)
                continue

            # Build matchup keys for the lookup tables.
            key1 = (team_abbr, opponent_abbr) if (team_abbr and opponent_abbr) else None

            # Source 3+4: cached Odds API.
            cand = cached_lookup.get(key1) if key1 else None
            if cand:
                records.append(GameStartTimeRecord(
                    game_id=gid, team_abbr=team_abbr,
                    opponent_abbr=opponent_abbr,
                    resolved_game_start_time_utc=cand["commence_time_utc"],
                    source_used=cand.get("source", "odds_api_cached"),
                    source_confidence="high",
                    source_payload_hash=_hash_payload(cand),
                ))
                continue

            # Source 5: live Odds API.
            cand = live_lookup.get(key1) if key1 else None
            if cand:
                records.append(GameStartTimeRecord(
                    game_id=gid, team_abbr=team_abbr,
                    opponent_abbr=opponent_abbr,
                    resolved_game_start_time_utc=cand["commence_time_utc"],
                    source_used="odds_api_live_events",
                    source_confidence="high",
                    source_payload_hash=_hash_payload(cand),
                ))
                continue

            # Source 6: live BDL by game_id (preferred when both
            # systems use BDL ids), else by team-pair.
            bdl_rec = bdl_lookup["by_gid"].get(gid) or (
                bdl_lookup["by_pair"].get(key1) if key1 else None
            )
            if bdl_rec and bdl_rec.get("commence_time_utc"):
                records.append(GameStartTimeRecord(
                    game_id=gid, team_abbr=team_abbr,
                    opponent_abbr=opponent_abbr,
                    resolved_game_start_time_utc=bdl_rec["commence_time_utc"],
                    source_used="bdl_games_endpoint",
                    source_confidence="medium",
                    source_payload_hash=_hash_payload(bdl_rec),
                ))
                continue

            # Unresolved.
            blocker_parts = []
            if not team_abbr or not opponent_abbr:
                blocker_parts.append(
                    f"team_id_to_abbr lookup incomplete (team_ids={team_ids})"
                )
            if not cached_events and not live_events and not bdl_games:
                blocker_parts.append(
                    "no Odds API cache, no live ODDS_API_KEY response, "
                    "and no BDL_API_KEY response"
                )
            elif not cached_events:
                blocker_parts.append(
                    f"no cached Odds API for {delivery_date}; live "
                    "endpoint may have only future-day games"
                )
            records.append(GameStartTimeRecord(
                game_id=gid, team_abbr=team_abbr,
                opponent_abbr=opponent_abbr,
                resolved_game_start_time_utc=None,
                source_used="unresolved",
                source_confidence="unresolved",
                resolution_blocker=("; ".join(blocker_parts)
                                     or "no real source returned a tip time"),
            ))

        telemetry["resolved_count"] = sum(
            1 for r in records if r.resolved_game_start_time_utc
        )
        telemetry["unresolved_count"] = sum(
            1 for r in records if not r.resolved_game_start_time_utc
        )
        return records, telemetry


def resolve_game_start_times(delivery_date: str, *,
                              repo_root: Optional[Path] = None,
                              ) -> tuple[list[GameStartTimeRecord], dict]:
    resolver = GameStartTimeResolver(repo_root=repo_root or REPO_ROOT)
    return resolver.resolve(delivery_date)
