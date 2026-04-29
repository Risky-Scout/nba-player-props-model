"""Odds API capture for NBA player props (Phase 9).

CLI subcommands:
  live-events            — list current upcoming events
  live-event-odds        — fetch live odds for one event (all 10 markets by default)
  historical-events      — list events at a historical snapshot timestamp
  historical-event-odds  — fetch historical odds for one event at a snapshot
  live-snapshot          — capture every live event for a snapshot type
  historical-snapshot    — capture every historical event at a snapshot timestamp
  smoke-test             — exercise live + historical flows end-to-end on 1 event each

Reads ODDS_API_KEY from env. Never prints the key.

Outputs:
  data/odds_api/raw/YYYY-MM-DD/         — raw API responses (JSON)
  data/odds_api/processed/YYYY-MM-DD/   — flattened quotes + paired no-vig (parquet + csv)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
ODDS_RAW_DIR = REPO_ROOT / "data" / "odds_api" / "raw"
ODDS_PROCESSED_DIR = REPO_ROOT / "data" / "odds_api" / "processed"
SPORT_KEY = "basketball_nba"
BASE_URL = "https://api.the-odds-api.com/v4"

MAIN_MARKETS = [
    "player_points", "player_rebounds", "player_assists",
    "player_turnovers", "player_threes",
]
ALT_MARKETS = [
    "player_points_alternate", "player_rebounds_alternate",
    "player_assists_alternate", "player_turnovers_alternate",
    "player_threes_alternate",
]
DEFAULT_MARKETS = MAIN_MARKETS + ALT_MARKETS
MARKET_TO_STAT = {
    "player_points": "pts", "player_points_alternate": "pts",
    "player_rebounds": "reb", "player_rebounds_alternate": "reb",
    "player_assists": "ast", "player_assists_alternate": "ast",
    "player_turnovers": "tov", "player_turnovers_alternate": "tov",
    "player_threes": "fg3m", "player_threes_alternate": "fg3m",
}


# ── HTTP helpers ────────────────────────────────────────────────────────


def _get_api_key() -> str:
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        sys.exit("FATAL: ODDS_API_KEY not set in environment")
    return key


def _safe_url_for_log(url: str, params: dict) -> str:
    masked = {k: ("***" if k == "apiKey" else v) for k, v in params.items()}
    return f"{url}?{urlencode(masked)}"


def _http_get(url: str, params: dict, max_retries: int = 4,
              base_sleep_s: float = 1.5) -> tuple[int, Any, dict]:
    """GET with retry. Returns (status, body_json, response_headers).

    Never logs the api key.
    """
    full_url = f"{url}?{urlencode(params)}"
    log_url = _safe_url_for_log(url, params)
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                full_url, headers={"User-Agent": "phase9-odds-capture/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8")
                status = r.status
                hdrs = dict(r.headers)
            return status, (json.loads(body) if body else {}), hdrs
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="ignore") if e.fp else ""
            except Exception:
                pass
            if e.code == 429 or e.code >= 500:
                wait = base_sleep_s * attempt
                print(f"  [retry] HTTP {e.code} on {log_url} "
                      f"(attempt {attempt}/{max_retries}); sleep {wait:.1f}s")
                time.sleep(wait)
                last_err = (e.code, err_body[:300])
                continue
            print(f"  [error] HTTP {e.code} on {log_url}: {err_body[:300]}")
            return e.code, {}, {}
        except Exception as e:
            print(f"  [error] {type(e).__name__} on {log_url}: {e}")
            time.sleep(base_sleep_s * attempt)
            last_err = (None, str(e))
    print(f"  [error] giving up after {max_retries} retries: {last_err}")
    return 0, {}, {}


def _log_quota(headers: dict) -> None:
    used = headers.get("x-requests-used") or headers.get("X-Requests-Used")
    rem = headers.get("x-requests-remaining") or headers.get("X-Requests-Remaining")
    last = headers.get("x-requests-last") or headers.get("X-Requests-Last")
    if used or rem or last:
        print(f"  [quota] used={used} remaining={rem} last_cost={last}")


# ── Endpoints ───────────────────────────────────────────────────────────


def fetch_live_events(api_key: str) -> tuple[list[dict], dict]:
    url = f"{BASE_URL}/sports/{SPORT_KEY}/events"
    s, b, h = _http_get(url, {"apiKey": api_key})
    _log_quota(h)
    return (b if isinstance(b, list) else []), h


def fetch_live_event_odds(api_key: str, event_id: str, markets: list[str],
                          regions: str = "us") -> tuple[dict, dict]:
    url = f"{BASE_URL}/sports/{SPORT_KEY}/events/{event_id}/odds"
    params = {
        "apiKey": api_key, "regions": regions,
        "markets": ",".join(markets), "oddsFormat": "american",
    }
    s, b, h = _http_get(url, params)
    _log_quota(h)
    return (b if isinstance(b, dict) else {}), h


def fetch_historical_events(api_key: str, snapshot_iso: str) -> tuple[dict, dict]:
    url = f"{BASE_URL}/historical/sports/{SPORT_KEY}/events"
    params = {"apiKey": api_key, "date": snapshot_iso}
    s, b, h = _http_get(url, params)
    _log_quota(h)
    return (b if isinstance(b, dict) else {}), h


def fetch_historical_event_odds(api_key: str, event_id: str, snapshot_iso: str,
                                markets: list[str], regions: str = "us") -> tuple[dict, dict]:
    url = f"{BASE_URL}/historical/sports/{SPORT_KEY}/events/{event_id}/odds"
    params = {
        "apiKey": api_key, "date": snapshot_iso,
        "regions": regions, "markets": ",".join(markets),
        "oddsFormat": "american",
    }
    s, b, h = _http_get(url, params)
    _log_quota(h)
    return (b if isinstance(b, dict) else {}), h


# ── Flatten + pair ──────────────────────────────────────────────────────


def _unwrap_event(blob: Any) -> dict:
    """Historical event-odds responses are wrapped in {"data": {...event...}}."""
    if isinstance(blob, dict) and "data" in blob and "bookmakers" not in blob:
        d = blob.get("data") or {}
        return d if isinstance(d, dict) else {}
    return blob if isinstance(blob, dict) else {}


def flatten_event_odds(event_blob: Any, snapshot_meta: dict) -> list[dict]:
    """One row per outcome quote."""
    ev = _unwrap_event(event_blob)
    if not ev or "bookmakers" not in ev:
        return []
    rows = []
    event_id = ev.get("id", "")
    commence_time = ev.get("commence_time", "")
    home_team = ev.get("home_team", "")
    away_team = ev.get("away_team", "")
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for bk in ev.get("bookmakers", []) or []:
        bk_key = bk.get("key", "")
        bk_title = bk.get("title", "")
        bk_last = bk.get("last_update", "")
        for m in bk.get("markets", []) or []:
            mkey = m.get("key", "")
            stat = MARKET_TO_STAT.get(mkey)
            if not stat:
                continue
            mlast = m.get("last_update", "")
            is_alt = mkey.endswith("_alternate")
            for oc in m.get("outcomes", []) or []:
                player = oc.get("description") or oc.get("participant") or ""
                side = (oc.get("name") or "").strip()
                line = oc.get("point")
                price = oc.get("price")
                rows.append({
                    "snapshot_id": snapshot_meta["snapshot_id"],
                    "snapshot_time_utc": snapshot_meta["snapshot_time_utc"],
                    "snapshot_type": snapshot_meta["snapshot_type"],
                    "api_mode": snapshot_meta["api_mode"],
                    "sport_key": SPORT_KEY,
                    "event_id": event_id,
                    "commence_time_utc": commence_time,
                    "home_team": home_team,
                    "away_team": away_team,
                    "bookmaker_key": bk_key,
                    "bookmaker_title": bk_title,
                    "bookmaker_last_update": bk_last,
                    "market_key": mkey,
                    "market_stat": stat,
                    "is_alternate": bool(is_alt),
                    "market_last_update": mlast,
                    "player_name": str(player),
                    "side": side,
                    "line": (float(line) if line is not None else None),
                    "odds_american": (int(price) if isinstance(price, (int, float)) else None),
                    "outcome_sid": oc.get("sid", ""),
                    "raw_description": oc.get("description", ""),
                    "raw_name": oc.get("name", ""),
                    "source_file": snapshot_meta.get("source_file", ""),
                    "fetched_at_utc": fetched_at,
                })
    return rows


def american_to_decimal(american: float) -> float:
    return 1.0 + american / 100.0 if american > 0 else 1.0 + 100.0 / abs(american)


def american_to_implied(american: float) -> float:
    return 100.0 / (american + 100.0) if american > 0 else abs(american) / (abs(american) + 100.0)


def pair_quotes(quotes: list[dict]) -> list[dict]:
    """Pair Over/Under quotes by event/book/market/player/line/snapshot."""
    if not quotes:
        return []
    df = pd.DataFrame(quotes)
    if df.empty:
        return []
    pairs = []
    keys = ["event_id", "bookmaker_key", "market_key", "player_name",
            "line", "snapshot_time_utc"]
    for grp_keys, g in df.groupby(keys, dropna=False):
        over = g[g["side"].str.lower() == "over"]
        under = g[g["side"].str.lower() == "under"]
        if len(over) == 0 or len(under) == 0:
            continue
        if len(over) > 1:
            over = over.sort_values("market_last_update").tail(1)
        if len(under) > 1:
            under = under.sort_values("market_last_update").tail(1)
        o = over.iloc[0]; u = under.iloc[0]
        if o.get("odds_american") is None or u.get("odds_american") is None:
            continue
        try:
            oa = float(o["odds_american"]); ua = float(u["odds_american"])
        except Exception:
            continue
        od = american_to_decimal(oa); ud = american_to_decimal(ua)
        oi = american_to_implied(oa); ui = american_to_implied(ua)
        denom = oi + ui
        nv_o = oi / denom if denom > 0 else None
        nv_u = ui / denom if denom > 0 else None
        pair_str = (f'{o["event_id"]}|{o["bookmaker_key"]}|{o["market_key"]}|'
                    f'{o["player_name"]}|{o["line"]}|{o["snapshot_time_utc"]}')
        pair_key = hashlib.sha1(pair_str.encode("utf-8")).hexdigest()[:16]
        pairs.append({
            "snapshot_id": o["snapshot_id"],
            "snapshot_time_utc": o["snapshot_time_utc"],
            "snapshot_type": o["snapshot_type"],
            "api_mode": o["api_mode"],
            "event_id": o["event_id"],
            "commence_time_utc": o["commence_time_utc"],
            "home_team": o["home_team"],
            "away_team": o["away_team"],
            "bookmaker_key": o["bookmaker_key"],
            "bookmaker_title": o["bookmaker_title"],
            "market_key": o["market_key"],
            "market_stat": o["market_stat"],
            "is_alternate": bool(o["is_alternate"]),
            "player_name": o["player_name"],
            "line": (float(o["line"]) if o["line"] is not None else None),
            "over_odds_american": int(oa),
            "under_odds_american": int(ua),
            "over_odds_decimal": float(od),
            "under_odds_decimal": float(ud),
            "over_implied_prob": float(oi),
            "under_implied_prob": float(ui),
            "no_vig_over_prob": (float(nv_o) if nv_o is not None else None),
            "no_vig_under_prob": (float(nv_u) if nv_u is not None else None),
            "bookmaker_last_update": o["bookmaker_last_update"],
            "market_last_update": o["market_last_update"],
            "over_sid": o.get("outcome_sid", ""),
            "under_sid": u.get("outcome_sid", ""),
            "pair_key": pair_key,
            "fetched_at_utc": o["fetched_at_utc"],
        })
    return pairs


# ── I/O ─────────────────────────────────────────────────────────────────


def make_snapshot_meta(snapshot_type: str, snapshot_iso: str,
                       api_mode: str, source_file: str = "") -> dict:
    sid = hashlib.sha1(f"{api_mode}|{snapshot_type}|{snapshot_iso}".encode()).hexdigest()[:16]
    return {
        "snapshot_id": sid,
        "snapshot_time_utc": snapshot_iso,
        "snapshot_type": snapshot_type,
        "api_mode": api_mode,
        "source_file": source_file,
    }


def _safe_filename(s: str) -> str:
    return s.replace(":", "").replace("/", "_").replace(" ", "_")


def save_raw_json(blob, target_date: str, name: str, overwrite: bool = False) -> Path:
    out_dir = ODDS_RAW_DIR / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_safe_filename(name)}.json"
    if path.exists() and not overwrite:
        path = out_dir / f"{_safe_filename(name)}_{int(time.time())}.json"
    path.write_text(json.dumps(blob, indent=2))
    return path


def save_processed(quotes_df: pd.DataFrame, pairs_df: pd.DataFrame,
                   target_date: str, suffix: str) -> tuple[Path, Path]:
    out_dir = ODDS_PROCESSED_DIR / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = _safe_filename(suffix)
    q_pq = out_dir / f"odds_quotes_{suffix}.parquet"
    q_csv = out_dir / f"odds_quotes_{suffix}.csv"
    p_pq = out_dir / f"odds_pairs_{suffix}.parquet"
    p_csv = out_dir / f"odds_pairs_{suffix}.csv"
    if quotes_df is None or quotes_df.empty:
        quotes_df = pd.DataFrame()
    if pairs_df is None or pairs_df.empty:
        pairs_df = pd.DataFrame()
    quotes_df.to_parquet(q_pq, index=False)
    quotes_df.to_csv(q_csv, index=False)
    pairs_df.to_parquet(p_pq, index=False)
    pairs_df.to_csv(p_csv, index=False)
    return q_pq, p_pq


# ── Command implementations ─────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_live_events(args) -> int:
    api_key = _get_api_key()
    if args.dry_run:
        print("[dry-run] would fetch live events"); return 0
    events, _ = fetch_live_events(api_key)
    snap_iso = _now_iso()
    target = args.target_date or snap_iso[:10]
    p = save_raw_json(events, target, f"live_events_{snap_iso}")
    print(f"Live events: {len(events)}; saved → {p.relative_to(REPO_ROOT)}")
    return 0


def cmd_live_event_odds(args) -> int:
    api_key = _get_api_key()
    snap_iso = _now_iso()
    target = args.target_date or snap_iso[:10]
    if args.dry_run:
        print(f"[dry-run] would fetch live odds for {args.event_id}"); return 0
    markets = args.markets.split(",")
    odds, _ = fetch_live_event_odds(api_key, args.event_id, markets, args.regions)
    p_raw = save_raw_json(odds, target, f"live_event_{args.event_id}_{snap_iso}")
    meta = make_snapshot_meta(args.snapshot_type, snap_iso, "live",
                              str(p_raw.relative_to(REPO_ROOT)))
    quotes = flatten_event_odds(odds, meta)
    pairs = pair_quotes(quotes)
    save_processed(pd.DataFrame(quotes), pd.DataFrame(pairs), target,
                   f"live_event_{args.event_id}_{snap_iso}")
    print(f"event {args.event_id}: {len(quotes)} quotes, {len(pairs)} pairs")
    return 0


def cmd_historical_events(args) -> int:
    api_key = _get_api_key()
    target = args.target_date or args.snapshot_time_utc[:10]
    if args.dry_run:
        print(f"[dry-run] would fetch historical events at {args.snapshot_time_utc}"); return 0
    blob, _ = fetch_historical_events(api_key, args.snapshot_time_utc)
    p = save_raw_json(blob, target, f"hist_events_{args.snapshot_time_utc}")
    n = len(blob.get("data", []) or []) if isinstance(blob, dict) else 0
    print(f"Historical events at {args.snapshot_time_utc}: {n}; saved → {p.relative_to(REPO_ROOT)}")
    return 0


def cmd_historical_event_odds(args) -> int:
    api_key = _get_api_key()
    target = args.target_date or args.snapshot_time_utc[:10]
    if args.dry_run:
        print(f"[dry-run] would fetch historical odds for {args.event_id} at {args.snapshot_time_utc}")
        return 0
    markets = args.markets.split(",")
    blob, _ = fetch_historical_event_odds(api_key, args.event_id,
                                          args.snapshot_time_utc, markets, args.regions)
    p_raw = save_raw_json(blob, target,
                           f"hist_event_{args.event_id}_{args.snapshot_time_utc}")
    meta = make_snapshot_meta(args.snapshot_type, args.snapshot_time_utc,
                              "historical", str(p_raw.relative_to(REPO_ROOT)))
    quotes = flatten_event_odds(blob, meta)
    pairs = pair_quotes(quotes)
    save_processed(pd.DataFrame(quotes), pd.DataFrame(pairs), target,
                   f"hist_event_{args.event_id}_{args.snapshot_time_utc}")
    print(f"historical event {args.event_id}: {len(quotes)} quotes, {len(pairs)} pairs")
    return 0


def cmd_live_snapshot(args) -> int:
    api_key = _get_api_key()
    snap_iso = _now_iso()
    target = snap_iso[:10]
    if args.dry_run:
        print("[dry-run] would capture full live slate"); return 0
    events, _ = fetch_live_events(api_key)
    save_raw_json(events, target, f"live_events_{snap_iso}")
    print(f"Live events: {len(events)}")
    markets = args.markets.split(",")
    all_quotes, all_pairs = [], []
    for i, ev in enumerate(events[: args.max_events]):
        eid = ev.get("id");
        if not eid: continue
        odds, _ = fetch_live_event_odds(api_key, eid, markets, args.regions)
        save_raw_json(odds, target, f"live_event_{eid}_{snap_iso}")
        meta = make_snapshot_meta(args.snapshot_type, snap_iso, "live",
                                  f"data/odds_api/raw/{target}/live_event_{eid}_{_safe_filename(snap_iso)}.json")
        q = flatten_event_odds(odds, meta)
        all_quotes.extend(q); all_pairs.extend(pair_quotes(q))
        time.sleep(0.4)
    save_processed(pd.DataFrame(all_quotes), pd.DataFrame(all_pairs), target,
                   f"live_slate_{args.snapshot_type}_{snap_iso}")
    print(f"Live slate: {len(events[: args.max_events])} events captured; "
          f"{len(all_quotes)} quotes, {len(all_pairs)} pairs")
    return 0


def cmd_historical_snapshot(args) -> int:
    api_key = _get_api_key()
    target = args.target_date or args.snapshot_time_utc[:10]
    if args.dry_run:
        print("[dry-run] would capture full historical slate"); return 0
    blob, _ = fetch_historical_events(api_key, args.snapshot_time_utc)
    save_raw_json(blob, target, f"hist_events_{args.snapshot_time_utc}")
    events = blob.get("data", []) if isinstance(blob, dict) else []
    if args.commence_after:
        events = [e for e in events if e.get("commence_time", "") >= args.commence_after]
    if args.commence_before:
        events = [e for e in events if e.get("commence_time", "") <= args.commence_before]
    print(f"Historical events at {args.snapshot_time_utc}: {len(events)}")
    markets = args.markets.split(",")
    all_quotes, all_pairs = [], []
    for ev in events[: args.max_events]:
        eid = ev.get("id");
        if not eid: continue
        eb, _ = fetch_historical_event_odds(api_key, eid, args.snapshot_time_utc,
                                            markets, args.regions)
        save_raw_json(eb, target, f"hist_event_{eid}_{args.snapshot_time_utc}")
        meta = make_snapshot_meta(args.snapshot_type, args.snapshot_time_utc,
                                  "historical",
                                  f"data/odds_api/raw/{target}/hist_event_{eid}_{_safe_filename(args.snapshot_time_utc)}.json")
        q = flatten_event_odds(eb, meta)
        all_quotes.extend(q); all_pairs.extend(pair_quotes(q))
        time.sleep(0.4)
    save_processed(pd.DataFrame(all_quotes), pd.DataFrame(all_pairs), target,
                   f"hist_slate_{args.snapshot_type}_{args.snapshot_time_utc}")
    print(f"Historical slate: {len(events[: args.max_events])} events captured; "
          f"{len(all_quotes)} quotes, {len(all_pairs)} pairs")
    return 0


def _shift_iso(iso: str, delta_minutes: int) -> str:
    """Shift an ISO-8601 UTC ts (Zulu suffix) by `delta_minutes` minutes."""
    from datetime import datetime, timedelta, timezone
    dt = datetime.strptime(iso.replace("Z", "+00:00"), "%Y-%m-%dT%H:%M:%S%z")
    dt = dt.astimezone(timezone.utc) + timedelta(minutes=delta_minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_historical_lock_day(args) -> int:
    """Per-event historical lock capture for one calendar day.

    For each event scheduled on `--target-date` (filtered by an optional
    commence-window), fetch historical event-odds at
    `snapshot_time_utc = commence_time_utc - <lock_offset_minutes>` (default 5).
    Guarantees `snapshot_time_utc <= commence_time_utc` (no leakage).
    """
    api_key = _get_api_key()
    target = args.target_date
    # Initial events list snapshot: 11:00 UTC (≈07:00 ET) of the target date —
    # at that time every game is upcoming, so the event list is complete.
    list_snap = f"{target}T11:00:00Z"
    if args.dry_run:
        print(f"[dry-run] would fetch historical events at {list_snap}")
        return 0

    print(f"=" * 72)
    print(f"HISTORICAL LOCK DAY — target {target}")
    print(f"  events list snapshot: {list_snap}")
    print(f"  lock offset:          T-{args.lock_offset_minutes} min")
    print(f"=" * 72)
    blob, _ = fetch_historical_events(api_key, list_snap)
    save_raw_json(blob, target, f"hist_events_{list_snap}")
    events = blob.get("data", []) if isinstance(blob, dict) else []
    if args.commence_after:
        events = [e for e in events if e.get("commence_time", "") >= args.commence_after]
    if args.commence_before:
        events = [e for e in events if e.get("commence_time", "") <= args.commence_before]
    print(f"  events at list-snapshot: {len(events)} "
          f"(after commence window filter)")
    if not events:
        print(f"  WARN: no historical events for {target} in window")
        return 0
    events.sort(key=lambda e: e.get("commence_time", ""))
    selected = events[: args.max_events]
    print(f"  selecting first {len(selected)} of {len(events)} events")
    markets = args.markets.split(",") if args.markets else DEFAULT_MARKETS

    all_quotes: list[dict] = []
    all_pairs: list[dict] = []
    for ev in selected:
        eid = ev.get("id")
        commence = ev.get("commence_time", "")
        if not eid or not commence:
            print(f"  WARN: skipping event with missing id/commence_time: {ev}")
            continue
        snap_iso = _shift_iso(commence, -int(args.lock_offset_minutes))
        if snap_iso > commence:
            print(f"  ERROR: leakage check failed for {eid}: "
                  f"snap={snap_iso} > commence={commence}")
            continue
        print(f"  → event {eid} {ev.get('away_team')} @ {ev.get('home_team')}  "
              f"commence={commence}  lock_snap={snap_iso}")
        eb, _ = fetch_historical_event_odds(api_key, eid, snap_iso, markets, args.regions)
        save_raw_json(eb, target, f"hist_event_{eid}_lock_{snap_iso}")
        meta = make_snapshot_meta("historical_lock_minus_5m" if args.lock_offset_minutes == 5
                                  else f"historical_lock_minus_{args.lock_offset_minutes}m",
                                  snap_iso, "historical",
                                  f"data/odds_api/raw/{target}/hist_event_{eid}_lock_{_safe_filename(snap_iso)}.json")
        q = flatten_event_odds(eb, meta)
        p = pair_quotes(q)
        all_quotes.extend(q)
        all_pairs.extend(p)
        print(f"    quotes: {len(q)}  pairs: {len(p)}")
        time.sleep(0.4)

    save_processed(pd.DataFrame(all_quotes), pd.DataFrame(all_pairs), target,
                   f"hist_lockday_{target}")
    print(f"\nLOCK-DAY summary:")
    print(f"  events captured:       {len(selected)}")
    print(f"  total raw quote rows:  {len(all_quotes)}")
    print(f"  total paired rows:     {len(all_pairs)}")
    return 0


def cmd_smoke_test(args) -> int:
    api_key = _get_api_key()
    markets = args.markets.split(",") if args.markets else DEFAULT_MARKETS

    print("=" * 72)
    print("SMOKE TEST — LIVE")
    print("=" * 72)
    if args.dry_run:
        print("[dry-run] skipping live API calls")
    events, _ = fetch_live_events(api_key) if not args.dry_run else ([], {})
    print(f"Live events fetched: {len(events)}")
    if events:
        events_sorted = sorted(events, key=lambda e: e.get("commence_time", ""))
        ev = events_sorted[0]
        eid = ev.get("id")
        snap_iso = _now_iso()
        target = snap_iso[:10]
        save_raw_json(events_sorted, target, f"smoke_live_events_{snap_iso}")
        print(f"  selected: {eid} — {ev.get('away_team')} @ {ev.get('home_team')} "
              f"({ev.get('commence_time')})")
        print(f"  fetching {len(markets)} markets…")
        odds, _ = fetch_live_event_odds(api_key, eid, markets, args.regions)
        p_raw = save_raw_json(odds, target, f"smoke_live_event_{eid}_{snap_iso}")
        meta = make_snapshot_meta("smoke", snap_iso, "live",
                                  str(p_raw.relative_to(REPO_ROOT)))
        quotes = flatten_event_odds(odds, meta)
        pairs = pair_quotes(quotes)
        q_df = pd.DataFrame(quotes); p_df = pd.DataFrame(pairs)
        save_processed(q_df, p_df, target, f"smoke_live_{eid}_{snap_iso}")
        print(f"\nLIVE smoke metrics:")
        print(f"  event_id:           {eid}")
        print(f"  teams:              {ev.get('away_team')} @ {ev.get('home_team')}")
        print(f"  commence_time:      {ev.get('commence_time')}")
        print(f"  bookmakers:         {len(odds.get('bookmakers', []) or [])}")
        print(f"  raw quote rows:     {len(q_df)}")
        print(f"  paired rows:        {len(p_df)}")
        if not q_df.empty:
            print(f"  rows by market_key:")
            for k, v in q_df["market_key"].value_counts().items():
                print(f"    {k}: {v}")
            print(f"  rows by stat: {dict(q_df['market_stat'].value_counts())}")
            print(f"  rows by book: {dict(q_df['bookmaker_key'].value_counts())}")
            alt_count = int(q_df["is_alternate"].sum())
            main_count = int((~q_df["is_alternate"]).sum())
            print(f"  alternate rows:     {alt_count}")
            print(f"  main rows:          {main_count}")
        print(f"  unpaired (≈quotes - 2*pairs): {max(len(q_df) - 2 * len(p_df), 0)}")
        if not p_df.empty:
            print(f"  no-vig over min/max: {p_df['no_vig_over_prob'].min():.4f} / "
                  f"{p_df['no_vig_over_prob'].max():.4f}")
        seen = set(q_df["market_key"].unique()) if not q_df.empty else set()
        missing = [m for m in DEFAULT_MARKETS if m not in seen]
        if missing:
            print(f"  WARN: target markets NOT returned for this event: {missing}")
        else:
            print(f"  ALL 10 target markets returned ✓")
    else:
        print("  WARN: no live events available; LIVE smoke skipped.")

    print()
    print("=" * 72)
    print("SMOKE TEST — HISTORICAL")
    print("=" * 72)
    snap_h = "2026-04-27T11:00:00Z"
    target_h = "2026-04-27"
    print(f"Historical snapshot: {snap_h}")
    if args.dry_run:
        print("[dry-run] skipping historical API calls")
        return 0
    he_blob, _ = fetch_historical_events(api_key, snap_h)
    he_data = he_blob.get("data", []) if isinstance(he_blob, dict) else []
    save_raw_json(he_blob, target_h, f"smoke_hist_events_{snap_h}")
    print(f"  historical events at snapshot: {len(he_data)}")
    window_lo = "2026-04-27T00:00:00Z"
    window_hi = "2026-04-28T06:00:00Z"
    cands = [e for e in he_data if window_lo <= e.get("commence_time", "") <= window_hi]
    if not cands:
        print(f"  WARN: no historical events in window {window_lo}..{window_hi}; "
              f"falling back to first available event")
        cands = he_data
    if not cands:
        print("  ERROR: no historical events at all for this snapshot")
        return 0
    cands.sort(key=lambda e: e.get("commence_time", ""))
    h_ev = cands[0]; h_eid = h_ev.get("id")
    print(f"  selected historical event: {h_eid} — "
          f"{h_ev.get('away_team')} @ {h_ev.get('home_team')} "
          f"({h_ev.get('commence_time')})")
    h_blob, _ = fetch_historical_event_odds(api_key, h_eid, snap_h, markets, args.regions)
    p_raw_h = save_raw_json(h_blob, target_h, f"smoke_hist_event_{h_eid}_{snap_h}")
    meta_h = make_snapshot_meta("smoke", snap_h, "historical",
                                str(p_raw_h.relative_to(REPO_ROOT)))
    h_quotes = flatten_event_odds(h_blob, meta_h)
    h_pairs = pair_quotes(h_quotes)
    h_q_df = pd.DataFrame(h_quotes); h_p_df = pd.DataFrame(h_pairs)
    save_processed(h_q_df, h_p_df, target_h,
                   f"smoke_hist_{h_eid}_{snap_h}")
    print(f"\nHISTORICAL smoke metrics:")
    print(f"  event_id:           {h_eid}")
    print(f"  raw quote rows:     {len(h_q_df)}")
    print(f"  paired rows:        {len(h_p_df)}")
    if not h_q_df.empty:
        print(f"  rows by market_key:")
        for k, v in h_q_df["market_key"].value_counts().items():
            print(f"    {k}: {v}")
        print(f"  rows by stat: {dict(h_q_df['market_stat'].value_counts())}")
        print(f"  rows by book: {dict(h_q_df['bookmaker_key'].value_counts())}")
        alt_h = int(h_q_df["is_alternate"].sum())
        print(f"  alternate rows:     {alt_h}")
        if not h_p_df.empty:
            print(f"  no-vig over min/max: {h_p_df['no_vig_over_prob'].min():.4f} / "
                  f"{h_p_df['no_vig_over_prob'].max():.4f}")
        seen_h = set(h_q_df["market_key"].unique())
        missing_h = [m for m in DEFAULT_MARKETS if m not in seen_h]
        if missing_h:
            print(f"  WARN: target markets NOT returned at this historical snapshot: {missing_h}")
        else:
            print(f"  ALL 10 target markets returned ✓")
    else:
        print("  WARN: historical event-odds returned no props at this snapshot.")
    return 0


# ── Argparse ────────────────────────────────────────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke-test")
    s.add_argument("--max-events", type=int, default=1)
    s.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    s.add_argument("--regions", default="us")
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("live-events")
    s.add_argument("--target-date", default=None)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("live-event-odds")
    s.add_argument("--event-id", required=True)
    s.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    s.add_argument("--regions", default="us")
    s.add_argument("--snapshot-type", default="live")
    s.add_argument("--target-date", default=None)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("historical-events")
    s.add_argument("--snapshot-time-utc", required=True)
    s.add_argument("--target-date", default=None)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("historical-event-odds")
    s.add_argument("--event-id", required=True)
    s.add_argument("--snapshot-time-utc", required=True)
    s.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    s.add_argument("--regions", default="us")
    s.add_argument("--snapshot-type", default="historical")
    s.add_argument("--target-date", default=None)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("live-snapshot")
    s.add_argument("--snapshot-type", required=True,
                   choices=["morning_7am", "close_or_lock", "live", "smoke"])
    s.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    s.add_argument("--regions", default="us")
    s.add_argument("--max-events", type=int, default=20)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("historical-lock-day",
                       help="Per-event historical lock capture for one calendar day "
                            "(snapshot = commence_time - lock_offset_minutes, "
                            "guaranteed <= commence_time).")
    s.add_argument("--target-date", required=True)
    s.add_argument("--commence-after", default=None)
    s.add_argument("--commence-before", default=None)
    s.add_argument("--max-events", type=int, default=2)
    s.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    s.add_argument("--regions", default="us")
    s.add_argument("--lock-offset-minutes", type=int, default=5)
    s.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("historical-snapshot")
    s.add_argument("--snapshot-time-utc", required=True)
    s.add_argument("--snapshot-type", required=True,
                   choices=["historical_close", "historical_7am",
                            "historical_morning", "historical_lock", "historical"])
    s.add_argument("--target-date", default=None)
    s.add_argument("--markets", default=",".join(DEFAULT_MARKETS))
    s.add_argument("--regions", default="us")
    s.add_argument("--max-events", type=int, default=20)
    s.add_argument("--commence-after", default=None)
    s.add_argument("--commence-before", default=None)
    s.add_argument("--dry-run", action="store_true")

    args = p.parse_args()
    routes = {
        "smoke-test": cmd_smoke_test,
        "live-events": cmd_live_events,
        "live-event-odds": cmd_live_event_odds,
        "historical-events": cmd_historical_events,
        "historical-event-odds": cmd_historical_event_odds,
        "live-snapshot": cmd_live_snapshot,
        "historical-snapshot": cmd_historical_snapshot,
        "historical-lock-day": cmd_historical_lock_day,
    }
    return routes[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
