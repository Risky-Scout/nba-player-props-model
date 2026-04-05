"""
bdl_client.py — BallDontLie NBA API Client (v1 + v2)
=====================================================
Built from official OpenAPI spec: https://www.balldontlie.io/openapi.yml

Critical spec findings implemented here:
  - Cursor pagination:  meta.next_cursor used on MOST endpoints
  - Player props:       PlayerPropMeta has NO next_cursor — single-response, no loop
  - Prop type enum:     "points","rebounds","assists","threes","steals","blocks"
                        "threes" NOT "fg3m". This is a breaking difference.
  - Vendors (NBA):      draftkings, betway, betrivers, ballybet
  - v2/advanced_stats:  usage%, pace, possessions, touches, rebound_chances_*,
                        defended_at_rim_*, assist_percentage
  - v1/injuries:        status, return_date, description
  - v2/lineups:         starter=bool per player per game

Auth:  BDL_API_KEY env var ONLY. Hard fail if missing. Zero hardcoded defaults.
"""

import os
import time
import logging
import statistics
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE_V1 = "https://api.balldontlie.io/nba/v1"
BASE_V2 = "https://api.balldontlie.io/nba/v2"
MAX_PER_PAGE = 100
MAX_RETRIES = 6
BACKOFF_BASE = 2.0

# Official prop_type enum → internal stat key
NBA_PROP_TYPE_TO_STAT = {
    "points":   "pts",
    "rebounds": "reb",
    "assists":  "ast",
    "threes":   "fg3m",   # NOTE: BDL calls it "threes" NOT "fg3m"
    "steals":   "stl",
    "blocks":   "blk",
}
STAT_TO_PROP_TYPE = {v: k for k, v in NBA_PROP_TYPE_TO_STAT.items()}


def _get_api_key() -> str:
    key = os.environ.get("BDL_API_KEY", "").strip()
    if not key:
        raise EnvironmentError(
            "\n[DARKO] FATAL: BDL_API_KEY not set.\n"
            "  export BDL_API_KEY=your_key_here\n"
        )
    return key


def _headers() -> dict:
    return {"Authorization": _get_api_key()}


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def parse_minutes(min_str) -> float:
    if isinstance(min_str, (int, float)):
        return float(min_str)
    try:
        parts = str(min_str).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except:
        return 0.0


# ── Core request ──────────────────────────────────────────────────────────────

def bdl_get(url: str, params: Optional[dict] = None) -> dict:
    params = {k: v for k, v in (params or {}).items() if v is not None}
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        except requests.exceptions.RequestException as exc:
            wait = BACKOFF_BASE ** attempt
            logger.warning(f"Network error [{url}]: {exc}. Retry {attempt+1} in {wait:.0f}s")
            time.sleep(wait)
            continue

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = BACKOFF_BASE ** (attempt + 2)
            logger.warning(f"Rate limited. Waiting {wait:.0f}s (attempt {attempt+1})")
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            wait = BACKOFF_BASE ** attempt
            logger.warning(f"Server {resp.status_code}. Retry in {wait:.0f}s")
            time.sleep(wait)
            continue
        logger.error(f"API {resp.status_code} [{url}]: {resp.text[:300]}")
        resp.raise_for_status()
    raise RuntimeError(f"Max retries exceeded: {url}")


def bdl_get_all(url: str, params: Optional[dict] = None) -> list[dict]:
    """
    Cursor-based pagination. Iterates meta.next_cursor until null.
    DO NOT use for player props (they have no pagination).
    """
    params = dict(params or {})
    params["per_page"] = MAX_PER_PAGE
    all_records = []
    page = 0

    while True:
        page += 1
        result = bdl_get(url, params)
        data = result.get("data", [])
        if not isinstance(data, list):
            break
        all_records.extend(data)
        next_cursor = result.get("meta", {}).get("next_cursor")
        if not next_cursor:
            break
        params["cursor"] = next_cursor
        time.sleep(0.12)

    logger.debug(f"bdl_get_all: {len(all_records)} records in {page} pages from {url}")
    return all_records


# ── NBA v1 Endpoints ──────────────────────────────────────────────────────────

def get_player_game_stats(
    start_date: str,
    end_date: str,
    player_ids: Optional[list[int]] = None,
) -> list[dict]:
    """GET /nba/v1/stats — box score per player per game. GOAT tier for full history."""
    params: dict[str, Any] = {"start_date": start_date, "end_date": end_date}
    if player_ids:
        params["player_ids[]"] = player_ids
    raw = bdl_get_all(f"{BASE_V1}/stats", params)
    valid, skipped = [], 0
    for rec in raw:
        if not rec.get("player") or not rec.get("game", {}).get("id"):
            skipped += 1
            continue
        if parse_minutes(rec.get("min", "0")) < 1:
            continue
        valid.append(rec)
    if skipped:
        logger.warning(f"get_player_game_stats: dropped {skipped}/{len(raw)} incomplete records")
    return valid


def get_games(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    seasons: Optional[list[int]] = None,
    team_ids: Optional[list[int]] = None,
) -> list[dict]:
    """GET /nba/v1/games"""
    params: dict[str, Any] = {}
    if start_date: params["start_date"] = start_date
    if end_date:   params["end_date"]   = end_date
    if seasons:    params["seasons[]"]  = seasons
    if team_ids:   params["team_ids[]"] = team_ids
    return bdl_get_all(f"{BASE_V1}/games", params)


def get_game_odds(
    game_ids: Optional[list[int]] = None,
    dates: Optional[list[str]] = None,
) -> list[dict]:
    """
    GET /nba/v1/odds — spread/total/moneyline per vendor per game.
    GOAT tier. 2025-26 season onward only.
    Empty list = no odds available (expected for older seasons — not an error).
    """
    params: dict[str, Any] = {}
    if game_ids: params["game_ids[]"] = game_ids
    # API spec: 'date' (singular string) not 'dates[]'
    # Error response confirmed: {"param":"date / game_id","error":"..."}
    if dates:    params["date"] = dates[0] if len(dates) == 1 else dates[0]
    try:
        records = bdl_get_all(f"{BASE_V1}/odds", params)
        if not records:
            logger.debug("get_game_odds: empty (pre-2025-26 or games without odds data)")
        return records
    except Exception as exc:
        logger.warning(f"get_game_odds: {exc}")
        return []


def get_injuries() -> list[dict]:
    """
    GET /nba/v1/player_injuries — current injury report.
    Fields: player, status, return_date, description.
    No pagination needed — returns current snapshot. GOAT tier.
    NOTE: path is 'player_injuries' not 'injuries' (confirmed from API 404).
    """
    try:
        result = bdl_get("https://api.balldontlie.io/v1/player_injuries")
        return result.get("data", [])
    except Exception as exc:
        logger.warning(f"get_injuries: {exc}")
        return []


def get_players_active(season: int) -> list[dict]:
    """GET /nba/v1/players/active — active roster with position, height, weight."""
    try:
        result = bdl_get(f"{BASE_V1}/players/active", {"season": season})
        return result.get("data", [])
    except Exception as exc:
        logger.warning(f"get_players_active: {exc}")
        return []


def get_season_averages(
    player_ids: list[int],
    season: int,
) -> list[dict]:
    """GET /nba/v1/season_averages — season-long averages per player."""
    try:
        result = bdl_get(f"{BASE_V1}/season_averages", {
            "player_ids[]": player_ids,
            "season": season,
        })
        return result.get("data", [])
    except Exception as exc:
        logger.warning(f"get_season_averages: {exc}")
        return []


def get_team_season_stats(season: int, season_type: str = "regular") -> list[dict]:
    """
    GET /nba/v1/team_season_stats — team-level season stats.

    Returns per-team season aggregates. Used to build opponent defensive
    environment via build_opponent_env_map(). Available stat_type values:
        "general"   — pts, reb, ast, stl, blk, fga, fg3a, fta, tov, min
        "opponent"  — opponent pts/reb/ast/stl/blk allowed (most useful for env)
        "shooting"  — eFG%, TS%, FT_rate, 2P%, 3P%
        "tracking"  — touches, passes, drives, pull-up, C&S (if available)

    Call with multiple stat_types to build a full environment profile.
    """
    try:
        result = bdl_get(f"{BASE_V1}/team_season_stats", {
            "season": season,
            "season_type": season_type,
        })
        return result.get("data", [])
    except Exception as exc:
        logger.warning(f"get_team_season_stats(season={season}): {exc}")
        return []


def get_team_season_averages(
    season: int,
    stat_type: str = "general",
    season_type: str = "regular",
    team_id: Optional[int] = None,
) -> list[dict]:
    """
    GET /nba/v1/season_averages — team-level season averages, broken out by
    category (general, opponent, defense, shooting, tracking, etc.).

    This is the primary source for pre-built opponent defensive environment
    features, eliminating the need to recompute from raw box scores.

    Key stat_types for opponent environment modeling:
        "general"  — raw per-game averages (pts, reb, ast, stl, blk, fga, fg3a)
        "opponent" — what the team ALLOWS per game (opp_pts, opp_reb, opp_ast,
                     opp_fg3a, opp_fga, opp_stl, opp_blk)
        "shooting" — eFG%, TS%, FGA/FTA split, 3P% breakdown
        "defense"  — defensive rating, opp eFG%, opp 3P%
        "tracking" — opponent drives/touches (if BDL GOAT tier exposes this)

    Returns: list of team records, each containing team.id and relevant stats.
    Returns [] on any failure (safe degradation).

    Usage example (predict/train scripts):
        records = get_team_season_averages(season=2026, stat_type="opponent")
        opp_env = build_opponent_env_map(records, stat_type="opponent")
        ctx["opp_env"] = opp_env.get(opp_team_id, {})
    """
    params: dict[str, Any] = {
        "season": season,
        "season_type": season_type,
    }
    if stat_type:
        params["type"] = stat_type
    if team_id:
        params["team_id"] = team_id

    try:
        result = bdl_get(f"{BASE_V1}/season_averages", params)
        records = result.get("data", [])
        if not records:
            logger.info(
                f"get_team_season_averages: empty (season={season}, type={stat_type})"
            )
        return records
    except Exception as exc:
        logger.warning(
            f"get_team_season_averages(season={season}, type={stat_type}): {exc}"
        )
        return []


def build_opponent_env_map(
    team_avg_records: list[dict],
    stat_type: str = "opponent",
) -> dict[int, dict]:
    """
    Build {team_id: opponent_env_dict} from get_team_season_averages() records.

    When stat_type="opponent", each record contains what the team ALLOWS per game.
    These become the opponent environment features in game_context and replace
    the from-scratch computation in opponent_defensive_features() for teams where
    season-level averages are available (more stable than 10-game rolling).

    The rolling box-score computation in opponent_defensive_features() remains
    the fallback when this map is absent or the team_id is missing.

    Keys produced (mirroring feature_engineering.py opponent env names):
        opp_pts_allowed      — opponent points allowed per game
        opp_reb_allowed      — opponent total rebounds allowed per game
        opp_oreb_allowed     — opponent offensive rebounds allowed per game
        opp_ast_allowed      — opponent assists allowed per game
        opp_3pa_allowed      — opponent 3-point attempts allowed per game
        opp_3pm_allowed      — opponent 3-pointers made against per game
        opp_fga_allowed      — opponent field goal attempts allowed per game
        opp_stl_allowed      — opponent steals allowed (i.e. live-ball TOs forced)
        opp_blk_allowed      — opponent blocks per game (rim protection proxy)
        opp_3p_rate_allowed  — opp 3PA / opp FGA allowed (shot profile)
        opp_pace_proxy       — possession proxy from allowed volume

    These are SEASON averages, not rolling-10 — deliberately more stable.
    feature_engineering.py gates them as "opp_*_allowed_last10" for naming
    consistency; at retrain time, use the rolling version from box scores
    for historical rows and season averages for current-season predictions.
    """
    result: dict[int, dict] = {}

    FIELD_MAP_OPPONENT = {
        # BDL "opponent" stat_type field → internal key
        "pts":      "opp_pts_allowed",
        "reb":      "opp_reb_allowed",
        "oreb":     "opp_oreb_allowed",
        "ast":      "opp_ast_allowed",
        "fg3a":     "opp_3pa_allowed",
        "fg3m":     "opp_3pm_allowed",
        "fga":      "opp_fga_allowed",
        "stl":      "opp_stl_allowed",
        "blk":      "opp_blk_allowed",
        "turnover": "opp_tov_forced",
        "fta":      "opp_fta_allowed",
    }

    for rec in team_avg_records:
        team_obj = rec.get("team") or {}
        tid = team_obj.get("id")
        if not tid:
            continue
        tid = int(tid)
        env: dict[str, Any] = {}

        for bdl_key, internal_key in FIELD_MAP_OPPONENT.items():
            val = _safe_float(rec.get(bdl_key))
            if val is not None:
                env[internal_key] = val

        # Derived: 3P rate allowed
        fga = env.get("opp_fga_allowed")
        fg3a = env.get("opp_3pa_allowed")
        if fga and fg3a and fga > 0:
            env["opp_3p_rate_allowed"] = round(fg3a / fga, 4)

        # Derived: pace proxy (FGA + 0.44*FTA + TOV - OREB)
        fta  = _safe_float(rec.get("fta"))
        tov  = _safe_float(rec.get("turnover"))
        oreb = env.get("opp_oreb_allowed")
        if all(v is not None for v in [fga, fta, tov, oreb]):
            env["opp_pace_proxy"] = round(fga + 0.44 * fta + tov - oreb, 2)

        if env:
            result[tid] = env

    logger.info(f"build_opponent_env_map: built env for {len(result)} teams")
    return result


# ── NBA v2 Endpoints ──────────────────────────────────────────────────────────

def get_player_prop_odds(game_id: int) -> list[dict]:
    """
    GET https://api.balldontlie.io/v2/odds/player_props?game_id=<id>
    Confirmed from official docs: base is /v2/odds/ not /nba/v1/ or /nba/v2/

    SPEC: meta has NO next_cursor — all results in ONE response.
    Do NOT call bdl_get_all() — single bdl_get() only.

    Prop types: points, rebounds, assists, threes, steals, blocks
                + quarter variants: points_1q, rebounds_1q, assists_1q
                + first3min variants (ignore these for main props)
    Market: over_under {over_odds, under_odds} | milestone {odds}
    Vendors: draftkings, betway, betrivers, ballybet
    """
    BASE_PROPS = "https://api.balldontlie.io/v2/odds"
    try:
        result = bdl_get(f"{BASE_PROPS}/player_props", {"game_id": game_id})
        records = result.get("data", [])
        if not records:
            logger.info(f"get_player_prop_odds: no props for game_id={game_id}")
        return records
    except Exception as exc:
        logger.warning(f"get_player_prop_odds(game_id={game_id}): {exc}")
        return []


def get_advanced_stats_v2(
    start_date: str,
    end_date: str,
    player_ids: Optional[list[int]] = None,
) -> list[dict]:
    """
    GET /nba/v2/advanced_stats
    Per-game advanced stats. Key fields for DARKO:
      usage_percentage     — primary usage signal for PTS/AST projection
      pace, possessions    — game script / tempo
      pace_per_40          — pace normalized
      touches, passes      — creation role proxy (AST model)
      rebound_chances_def/off/total — REB opportunity (REB model)
      defended_at_rim_fga/fgm/fg_pct — rim protection (BLK model)
      effective_field_goal_percentage, true_shooting_percentage — efficiency
      assist_percentage, assist_ratio, assist_to_turnover — playmaking
      net_rating, offensive_rating, defensive_rating — overall impact
      contested_shots, deflections — defensive activity (STL model)
    """
    params: dict[str, Any] = {"start_date": start_date, "end_date": end_date}
    if player_ids:
        params["player_ids[]"] = player_ids
    try:
        return bdl_get_all(f"{BASE_V2}/stats/advanced", params)
    except Exception as exc:
        logger.warning(f"get_advanced_stats_v2: {exc}")
        return []


def get_lineups(game_id: int) -> list[dict]:
    """
    GET /nba/v2/lineups?game_id=<id>
    Returns NBALineup: starter=bool, position, player, team.
    Use to detect missing starters (star-out flags).
    """
    try:
        result = bdl_get(f"{BASE_V2}/lineups", {"game_id": game_id})
        return result.get("data", [])
    except Exception as exc:
        logger.warning(f"get_lineups(game_id={game_id}): {exc}")
        return []


# ── Prop parsing ──────────────────────────────────────────────────────────────

def parse_prop_market(prop: dict) -> tuple[Optional[int], Optional[int]]:
    """Return (over_odds, under_odds). Milestone markets return (odds, None)."""
    market = prop.get("market", {})
    if market.get("type") == "over_under":
        return market.get("over_odds"), market.get("under_odds")
    elif market.get("type") == "milestone":
        return market.get("odds"), None
    return None, None


def parse_props_for_game(
    game_id: int,
    raw_props: Optional[list[dict]] = None,
    price_shop: bool = True,
) -> dict[tuple, dict]:
    """
    Parse all props for a game into {(player_id, stat_key): best_prop_dict}.

    With price_shop=True (default):
      - Collects all vendor snapshots per (player, stat)
      - For each snapshot, selects: best OVER odds, best UNDER odds
      - Adds disagreement features: line_std across vendors, best vs worst odds gap
      - Returns a single record with the best available pricing for each side

    Without price_shop:
      - Selects latest updated_at per (player, stat) from any vendor

    Translates BDL prop_type ("threes") → internal stat key ("fg3m").
    Only over_under markets processed (milestone markets skipped).
    Devigged implied probs computed from best available odds.
    """
    if raw_props is None:
        raw_props = get_player_prop_odds(game_id)

    # Stage all vendor records
    staging: dict[tuple, list] = {}
    for p in raw_props:
        pid = p.get("player_id")
        raw_type = p.get("prop_type", "")
        stat_key = NBA_PROP_TYPE_TO_STAT.get(raw_type)
        if not all([pid, stat_key]):
            continue
        over_odds, under_odds = parse_prop_market(p)
        if over_odds is None or under_odds is None:
            continue
        try:
            line = float(p["line_value"])
        except (KeyError, TypeError, ValueError):
            continue

        op, up = devig_two_way(over_odds, under_odds)
        key = (int(pid), stat_key)
        staging.setdefault(key, []).append({
            "player_id":          int(pid),
            "game_id":            game_id,
            "stat":               stat_key,
            "prop_type_raw":      raw_type,
            "line":               line,
            "over_odds":          over_odds,
            "under_odds":         under_odds,
            "implied_prob_over":  op,
            "implied_prob_under": up,
            "vendor":             p.get("vendor", "unknown"),
            "updated_at":         p.get("updated_at", ""),
            "line_is_real":       True,
        })

    if not price_shop:
        # Legacy: keep latest snapshot per key
        return {k: sorted(v, key=lambda x: x["updated_at"])[-1] for k, v in staging.items()}

    # Price shop: pick best odds per side, add disagreement features
    result = {}
    for key, records in staging.items():
        lines = [r["line"] for r in records]
        consensus_line = float(statistics.median(lines))

        # Filter to records on/near the consensus line (±0.5) for fair comparison
        on_line = [r for r in records if abs(r["line"] - consensus_line) <= 0.5]
        if not on_line:
            on_line = records  # fallback

        # Best OVER: highest over_odds (least negative = cheapest price)
        best_over_rec  = max(on_line, key=lambda r: r["over_odds"])
        # Best UNDER: highest under_odds
        best_under_rec = max(on_line, key=lambda r: r["under_odds"])

        # Recompute devigged probs from best available odds
        # (use best_over_odds + best_under_odds for the most accurate no-vig price)
        best_over_odds  = best_over_rec["over_odds"]
        best_under_odds = best_under_rec["under_odds"]
        imp_over, imp_under = devig_two_way(best_over_odds, best_under_odds)

        # All-vendor consensus implied prob (more stable)
        all_ops = [r["implied_prob_over"] for r in on_line]
        consensus_imp_over = float(statistics.mean(all_ops))

        # Disagreement features
        line_std  = float(statistics.stdev(lines)) if len(lines) > 1 else 0.0
        odds_vals = [r["over_odds"] for r in on_line]
        odds_range = max(odds_vals) - min(odds_vals) if len(odds_vals) > 1 else 0
        n_vendors = len(set(r["vendor"] for r in records))

        # Latest snapshot (for timestamp reference)
        latest = sorted(records, key=lambda x: x["updated_at"])[-1]

        result[key] = {
            "player_id":              int(key[0]),
            "game_id":                game_id,
            "stat":                   key[1],
            "prop_type_raw":          latest["prop_type_raw"],
            "line":                   consensus_line,          # consensus line
            "over_odds":              best_over_odds,          # best available OVER
            "under_odds":             best_under_odds,         # best available UNDER
            "best_over_vendor":       best_over_rec["vendor"],
            "best_under_vendor":      best_under_rec["vendor"],
            "implied_prob_over":      imp_over,
            "implied_prob_under":     imp_under,
            "consensus_imp_over":     consensus_imp_over,
            # Disagreement signals: high disagreement = model edge more reliable
            "line_std":               line_std,
            "odds_range":             int(odds_range),
            "n_vendors":              n_vendors,
            "updated_at":             latest["updated_at"],
            "line_is_real":           True,
            # Snapshot archive (for CLV true tracking)
            "_all_vendor_records":    records,
        }

    return result


def get_best_bet_odds(prop: dict, side: str) -> tuple[int, str]:
    """
    Given a price-shopped prop dict and the bet side,
    return (best_american_odds, best_vendor_name).
    """
    if side == "OVER":
        return prop.get("over_odds", -110), prop.get("best_over_vendor", "unknown")
    else:
        return prop.get("under_odds", -110), prop.get("best_under_vendor", "unknown")


# ── Odds math ────────────────────────────────────────────────────────────────

def devig_two_way(over_odds: int, under_odds: int) -> tuple[float, float]:
    """Multiplicative devig. Returns (over_prob, under_prob) summing to 1.0."""
    def raw(american: int) -> float:
        return (100.0 / (american + 100)) if american > 0 else (abs(american) / (abs(american) + 100))
    ro, ru = raw(over_odds), raw(under_odds)
    total = ro + ru
    if total <= 0:
        return 0.5, 0.5
    return ro / total, ru / total


def build_game_context_map(odds_records: list[dict]) -> dict[int, dict]:
    """
    {game_id: context_dict} from raw game odds.
    context_dict keys:
        consensus_total, consensus_spread_home
        open_close_total_delta, open_close_spread_delta   ← line movement signals
        implied_home_total, implied_away_total
        blowout_risk, market_pace_proxy
        vendor_count, odds_available
    """
    from collections import defaultdict
    by_game: dict[int, list] = defaultdict(list)
    for rec in odds_records:
        gid = rec.get("game_id")
        if gid:
            by_game[int(gid)].append(rec)

    result = {}
    for gid, records in by_game.items():
        sorted_r = sorted(records, key=lambda x: x.get("updated_at", "") or "")
        opening, closing = sorted_r[0], sorted_r[-1]

        totals  = [float(r["total_value"])       for r in records if r.get("total_value")]
        spreads = [float(r["spread_home_value"])  for r in records if r.get("spread_home_value")]

        total  = statistics.median(totals)  if totals  else 220.0
        spread = statistics.median(spreads) if spreads else 0.0

        open_t = _safe_float(opening.get("total_value"))
        close_t = _safe_float(closing.get("total_value"))
        open_s  = _safe_float(opening.get("spread_home_value"))
        close_s = _safe_float(closing.get("spread_home_value"))

        result[gid] = {
            "consensus_total":          total,
            "consensus_spread_home":    spread,
            "open_close_total_delta":   (close_t - open_t) if (close_t and open_t) else 0.0,
            "open_close_spread_delta":  (close_s - open_s) if (close_s and open_s) else 0.0,
            "implied_home_total":       (total / 2) - (spread / 2),
            "implied_away_total":       (total / 2) + (spread / 2),
            "blowout_risk":             abs(spread),
            "market_pace_proxy":        total / 220.0,
            "vendor_count":             len(set(r.get("vendor") for r in records if r.get("vendor"))),
            "odds_available":           True,
        }
    return result


def enrich_game_context_with_team_ids(
    ctx_map: dict,
    games: list,
    opp_env_map: Optional[dict] = None,
) -> dict:
    """
    Enrich a game_context_map with team IDs from the BDL games list,
    and optionally stamp pre-built opponent defensive environment data.

    Adds to each context entry:
        home_team_id  : int — BDL team_id of the home team
        away_team_id  : int — BDL team_id of the away team

    If opp_env_map is provided (built via build_opponent_env_map()):
        home_opp_env  : dict — season-level defensive env of the HOME team
                              (used when the player is on the AWAY team)
        away_opp_env  : dict — season-level defensive env of the AWAY team
                              (used when the player is on the HOME team)

    These allow build_player_game_features() to derive opp_team_id and
    optionally pass pre-built season averages to opponent_defensive_features(),
    which falls back to rolling box-score computation if absent.

        opp_team_id = ctx['away_team_id'] if is_home else ctx['home_team_id']

    Called from:
        predict_darko_v4.py  — after build_game_context_map()
        train_v12.py         — after build_game_context_map()

    Safe degradation: missing game IDs or missing opp_env entries are silently
    skipped — no KeyErrors, no partial failures.
    """
    gid_to_teams: dict[int, tuple[int, int]] = {}
    for game in games:
        gid      = game.get("id")
        home_obj = game.get("home_team") or {}
        away_obj = game.get("visitor_team") or {}
        htid     = home_obj.get("id")
        atid     = away_obj.get("id")
        if gid and htid and atid:
            gid_to_teams[int(gid)] = (int(htid), int(atid))

    enriched = 0
    for gid, ctx in ctx_map.items():
        teams = gid_to_teams.get(int(gid))
        if not teams:
            continue
        htid, atid = teams
        ctx["home_team_id"] = htid
        ctx["away_team_id"] = atid

        # Stamp season-level opponent env if provided
        if opp_env_map:
            ctx["home_opp_env"] = opp_env_map.get(htid, {})
            ctx["away_opp_env"] = opp_env_map.get(atid, {})

        enriched += 1

    logger.info(
        f"enrich_game_context_with_team_ids: {enriched}/{len(ctx_map)} games enriched"
        + (f" (opp_env_map: {len(opp_env_map)} teams)" if opp_env_map else "")
    )
    return ctx_map


def build_injury_map(injury_records: list[dict]) -> dict[int, dict]:
    """{player_id: {status, return_date, description}}"""
    result = {}
    for rec in injury_records:
        pid = (rec.get("player") or {}).get("id")
        if pid:
            result[int(pid)] = {
                "status":      rec.get("status", "unknown"),
                "return_date": rec.get("return_date"),
                "description": rec.get("description", ""),
            }
    return result


def build_starter_map(lineup_records: list[dict]) -> dict[int, set]:
    """{team_id: set_of_starter_player_ids}"""
    from collections import defaultdict
    result: dict[int, set] = defaultdict(set)
    for rec in lineup_records:
        if rec.get("starter"):
            tid = (rec.get("team") or {}).get("id")
            pid = (rec.get("player") or {}).get("id")
            if tid and pid:
                result[int(tid)].add(int(pid))
    return dict(result)


# ── Snapshot-based line movement enrichment ───────────────────────────────────

def load_line_movement_snapshot(target_date: str) -> dict:
    """
    Load opening_lines_{date}.json and closing_lines_{date}.json,
    join on home_team+away_team label, and return a dict mapping
    game label → {total_move, spread_move, opening_total, closing_total, ...}

    Called by predict_darko_v4.py and train_v12.py to enrich game_context_map
    with high-quality sharp money signals.

    Key     : "{away_team} @ {home_team}"  (matches build_game_context_map label)
    Returns : {} if either snapshot file is missing or unreadable (safe degradation)

    Data flow:
      snapshot_opening_lines.py (9 AM ET) → data/opening_lines_{date}.json
      snapshot_closing_lines.py (6 PM ET) → graded/closing_lines_{date}.json
      [next day 8 AM] predict_darko_v4.py loads yesterday's both snapshots
                      as "prior day sharp action" signal AND today's opening

    Note on naming:
      The Odds API uses its own event_id, not BDL game_id.
      We join on normalized team label (away @ home) which is consistent
      across both snapshot files and the BDL game context map.
    """
    import json, re
    from pathlib import Path

    DATA_DIR   = Path("data")
    GRADED_DIR = Path("graded")

    opening_path = DATA_DIR   / f"opening_lines_{target_date}.json"
    closing_path = GRADED_DIR / f"closing_lines_{target_date}.json"

    if not opening_path.exists() or not closing_path.exists():
        return {}

    try:
        with open(opening_path) as f:
            opening = json.load(f)
        with open(closing_path) as f:
            closing = json.load(f)
    except Exception as e:
        logger.warning(f"load_line_movement_snapshot: failed to load files: {e}")
        return {}

    # Build game-level closing snapshot from The Odds API event keys
    # Closing lines file is keyed by "{player_norm}|{stat}|{line}" (player props)
    # We need game-level totals — stored per event in opening_lines_{date}.json

    # Opening is keyed by event_id with home_team, away_team, consensus_total,
    # consensus_spread. We also need closing game totals.
    # The closing_lines_{date}.json has player props only (no game totals).
    # Closing GAME totals come from The Odds API snapshot_closing_lines.py
    # which was not yet fetching game totals. We use BDL open_close_total_delta
    # as fallback. True cross-source delta is:
    #   total_move = bdl_consensus_total - opening_total  (8AM vs 9AM)
    # For now: return opening context enriched with implied team totals for
    # the game_context_map so training has correct implied totals at 9 AM open.

    result = {}
    for eid, rec in opening.items():
        if not isinstance(rec, dict):
            continue
        home = rec.get("home_team", "")
        away = rec.get("away_team", "")
        game_label = f"{away} @ {home}"

        result[game_label] = {
            "opening_total":   rec.get("consensus_total"),
            "opening_spread":  rec.get("consensus_spread"),
            "implied_home_total_open": rec.get("implied_home_total"),
            "implied_away_total_open": rec.get("implied_away_total"),
            "books_total_open": rec.get("books_total", {}),
            "snapshot_type":   "opening",
        }

    logger.info(
        f"load_line_movement_snapshot: {len(result)} games "
        f"from {opening_path.name}"
    )
    return result


def enrich_game_context_with_snapshots(
    ctx_map: dict,
    games: list,
    target_date: str,
    opp_env_map: Optional[dict] = None,
) -> dict:
    """
    Enrich a game_context_map (keyed by BDL game_id) with:

    1. Team IDs (home_team_id, away_team_id) — always, from games list.
    2. Season-level opponent defensive env (home_opp_env, away_opp_env)
       — when opp_env_map is provided via build_opponent_env_map().
    3. Line movement signals (total_move, spread_move, opening_total, etc.)
       — when opening_lines_{date}.json snapshot exists.

    Callers pass opp_env_map built from get_team_season_averages("opponent"):

        records   = get_team_season_averages(season=2026, stat_type="opponent")
        opp_env   = build_opponent_env_map(records)
        ctx_map   = enrich_game_context_with_snapshots(
                        ctx_map, games, target_date, opp_env_map=opp_env
                    )

    Safe degradation: all three enrichments are independent; failure in one
    leaves the others intact.
    """
    # Step 1 + 2: team IDs and optional season-level opp env
    ctx_map = enrich_game_context_with_team_ids(ctx_map, games, opp_env_map=opp_env_map)

    # Step 3: line movement from snapshot files
    snapshot_data = load_line_movement_snapshot(target_date)
    if not snapshot_data:
        logger.info("  No snapshot data — ctx_map team IDs set, line movement skipped")
        return ctx_map

    # Build BDL game_id → label map
    gid_to_label = {}
    for game in games:
        gid    = game.get("id")
        home   = (game.get("home_team") or {}).get("full_name", "")
        away   = (game.get("visitor_team") or {}).get("full_name", "")
        if gid and home and away:
            gid_to_label[gid] = f"{away} @ {home}"

    enriched = 0
    for gid, ctx in ctx_map.items():
        label = gid_to_label.get(gid, "")
        snap  = snapshot_data.get(label)
        if not snap:
            continue

        open_total  = snap.get("opening_total")
        open_spread = snap.get("opening_spread")

        # Cross-source total_move: BDL consensus (~8 AM) vs Odds API open (9 AM)
        bdl_total = ctx.get("consensus_total")
        if open_total and bdl_total:
            ctx["total_move"]  = round(float(bdl_total) - float(open_total), 2)
        elif ctx.get("open_close_total_delta"):
            ctx["total_move"]  = ctx["open_close_total_delta"]
        else:
            ctx["total_move"]  = None

        bdl_spread = ctx.get("consensus_spread_home")
        if open_spread is not None and bdl_spread is not None:
            ctx["spread_move"] = round(float(bdl_spread) - float(open_spread), 2)
        elif ctx.get("open_close_spread_delta"):
            ctx["spread_move"] = ctx["open_close_spread_delta"]
        else:
            ctx["spread_move"] = None

        ctx["opening_total"]           = open_total
        ctx["opening_spread"]          = open_spread
        ctx["implied_home_total_open"] = snap.get("implied_home_total_open")
        ctx["implied_away_total_open"] = snap.get("implied_away_total_open")
        enriched += 1

    logger.info(f"  Game context enriched with snapshot data: {enriched}/{len(ctx_map)} games")
    return ctx_map
