#!/usr/bin/env python3.10
"""
nba_injury_backfill.py — Official NBA Injury Report Backfill

Run from nbainjuries_env:
    source ~/nbainjuries_env/bin/activate
    python3.10 nba_injury_backfill.py

Produces: data/nba_injury_reports.parquet
Columns:
    report_date, game_date, matchup, team, player_name_raw,
    current_status, reason,
    dnp_injury, dnp_rest, dnp_coach_decision,
    is_injury_elevated_role (derived from teammate absences)
"""

import sys
import time
import logging
import pandas as pd
import pyarrow
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from nbainjuries import injury
except ImportError:
    print("ERROR: Run from nbainjuries_env: source ~/nbainjuries_env/bin/activate")
    sys.exit(1)


def classify_reason(status: str, reason: str) -> dict:
    """
    Classify a player entry into DNP reason flags.
    
    Rules derived from official NBA injury report Reason text:
    - dnp_rest:             Rest / Load Management / Injury Management
    - dnp_injury:           Injury/Illness prefix
    - dnp_coach_decision:   Not With Team / Coach Decision / G League / Personal Reasons
    """
    status = str(status).strip()
    reason = str(reason).strip()
    reason_lower = reason.lower()
    
    is_out = status in ("Out", "Doubtful")
    
    dnp_rest = 0
    dnp_injury = 0
    dnp_coach_decision = 0
    
    if is_out or status == "Questionable":
        if any(x in reason_lower for x in ["rest", "load management", "injury management",
                                             "maintenance", "workload"]):
            dnp_rest = 1
        elif reason_lower.startswith("injury/illness"):
            dnp_injury = 1
        elif any(x in reason_lower for x in ["not with team", "coach", "personal",
                                               "g league", "two-way", "trade",
                                               "suspension", "league"]):
            dnp_coach_decision = 1
        elif reason_lower in ("", "nan") and is_out:
            dnp_coach_decision = 1  # unknown Out = coach decision by default
    
    return {
        "dnp_injury":         dnp_injury,
        "dnp_rest":           dnp_rest,
        "dnp_coach_decision": dnp_coach_decision,
    }


def fetch_one_date(report_dt: datetime) -> pd.DataFrame:
    """Fetch injury report for one datetime. Returns empty df on failure."""
    try:
        df = injury.get_reportdata(report_dt, return_df=True)
        if df is None or len(df) == 0:
            return pd.DataFrame()
        df["report_date"] = report_dt.strftime("%Y-%m-%d")
        df["report_hour"] = report_dt.hour
        return df
    except Exception as e:
        logger.debug(f"  {report_dt.date()} fetch failed: {e}")
        return pd.DataFrame()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw report rows into clean feature rows."""
    if df.empty:
        return pd.DataFrame()
    
    rows = []
    for _, row in df.iterrows():
        status = str(row.get("Current Status", "")).strip()
        reason = str(row.get("Reason", "")).strip()
        flags = classify_reason(status, reason)
        
        rows.append({
            "report_date":      row.get("report_date", ""),
            "report_hour":      row.get("report_hour", 8),
            "game_date":        str(row.get("Game Date", "")).strip(),
            "matchup":          str(row.get("Matchup", "")).strip(),
            "team":             str(row.get("Team", "")).strip(),
            "player_name_raw":  str(row.get("Player Name", "")).strip(),
            "current_status":   status,
            "reason":           reason,
            **flags,
        })
    
    return pd.DataFrame(rows)


def backfill(start_date: str, end_date: str, out_path: str) -> pd.DataFrame:
    """
    Backfill injury reports from start_date to end_date.
    Fetches 8AM ET report for each date (aligns with scoring time).
    Incremental — skips already-fetched dates.
    """
    out = Path(out_path)
    
    # Load existing
    existing_dates = set()
    existing_df = pd.DataFrame()
    if out.exists():
        existing_df = pd.read_parquet(out)
        existing_dates = set(existing_df["report_date"].unique())
        logger.info(f"Existing: {len(existing_df)} rows across {len(existing_dates)} dates")
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end   = datetime.strptime(end_date,   "%Y-%m-%d")
    
    all_new = []
    current = start
    total = (end - start).days + 1
    fetched = 0
    skipped = 0
    empty = 0
    
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        
        if date_str in existing_dates:
            skipped += 1
            current += timedelta(days=1)
            continue
        
        # 8AM ET report
        report_dt = datetime(current.year, current.month, current.day, 8, 0)
        raw = fetch_one_date(report_dt)
        
        if raw.empty:
            empty += 1
        else:
            normalized = normalize(raw)
            if not normalized.empty:
                all_new.append(normalized)
                fetched += 1
                logger.info(f"  {date_str}: {len(normalized)} rows")
        
        time.sleep(0.3)  # be gentle with NBA servers
        current += timedelta(days=1)
    
    logger.info(f"Fetch complete: {fetched} new dates, {empty} empty, {skipped} skipped")
    
    if not all_new and existing_df.empty:
        logger.warning("No data fetched")
        return pd.DataFrame()
    
    parts = [existing_df] + all_new if not existing_df.empty else all_new
    combined = pd.concat([p for p in parts if not p.empty], ignore_index=True)
    combined = combined.drop_duplicates(subset=["report_date","player_name_raw","game_date"])
    
    out.parent.mkdir(exist_ok=True)
    combined.to_parquet(out, index=False)
    logger.info(f"Saved {len(combined)} rows to {out}")
    
    return combined


def build_training_features(injury_df: pd.DataFrame,
                              pgs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join injury reports to player_game_stats rows.
    
    For each player-game, find the latest 8AM ET report on that game_date
    and extract: dnp_injury, dnp_rest, dnp_coach_decision for prior game.
    Also derive is_injury_elevated_role from teammate absences.
    """
    if injury_df.empty:
        return pd.DataFrame()

    _abbr_to_full = {
        "ATL":"Atlanta Hawks","BOS":"Boston Celtics","BKN":"Brooklyn Nets",
        "CHA":"Charlotte Hornets","CHI":"Chicago Bulls","CLE":"Cleveland Cavaliers",
        "DAL":"Dallas Mavericks","DEN":"Denver Nuggets","DET":"Detroit Pistons",
        "GSW":"Golden State Warriors","HOU":"Houston Rockets","IND":"Indiana Pacers",
        "LAC":"Los Angeles Clippers","LAL":"Los Angeles Lakers","MEM":"Memphis Grizzlies",
        "MIA":"Miami Heat","MIL":"Milwaukee Bucks","MIN":"Minnesota Timberwolves",
        "NOP":"New Orleans Pelicans","NYK":"New York Knicks","OKC":"Oklahoma City Thunder",
        "ORL":"Orlando Magic","PHI":"Philadelphia 76ers","PHX":"Phoenix Suns",
        "POR":"Portland Trail Blazers","SAC":"Sacramento Kings","SAS":"San Antonio Spurs",
        "TOR":"Toronto Raptors","UTA":"Utah Jazz","WAS":"Washington Wizards",
    }

    # Normalize player names: "Last, First" -> "First Last"
    def normalize_name(name: str) -> str:
        if "," in name:
            parts = name.split(",", 1)
            return (parts[1].strip() + " " + parts[0].strip()).strip()
        return name.strip()
    
    injury_df = injury_df.copy()
    injury_df["player_name_norm"] = injury_df["player_name_raw"].apply(normalize_name)
    injury_df["report_date"] = pd.to_datetime(injury_df["report_date"])
    
    pgs = pgs_df.copy()
    pgs["game_date"] = pd.to_datetime(pgs["game_date"])
    
    rows = []
    for _, player_row in pgs.iterrows():
        pid    = player_row["player_id"]
        pname  = str(player_row["player_name"])
        gdate  = player_row["game_date"]
        tid    = player_row.get("team_id", 0)
        gid    = player_row["game_id"]
        
        # Get prior game injury report (same date, before tip)
        day_reports = injury_df[injury_df["report_date"] == gdate]
        
        # Find this player in the report
        player_report = day_reports[
            day_reports["player_name_norm"].str.lower() == pname.lower()
        ]
        
        dnp_injury = 0
        dnp_rest   = 0
        dnp_cd     = 0
        
        if len(player_report) > 0:
            r = player_report.iloc[0]
            dnp_injury = int(r.get("dnp_injury", 0))
            dnp_rest   = int(r.get("dnp_rest",   0))
            dnp_cd     = int(r.get("dnp_coach_decision", 0))
        
        # is_injury_elevated_role: injured teammate on SAME team
        player_team_name = _abbr_to_full.get(str(player_row.get("team_abbr","")), "")
        team_reports = day_reports[
            (day_reports["team"] == player_team_name) &
            (day_reports["current_status"].isin(["Out","Doubtful"])) &
            (day_reports["dnp_injury"] == 1) &
            (day_reports["player_name_norm"].str.lower() != pname.lower())
        ]
        is_elevated = int(len(team_reports) > 0)
        
        rows.append({
            "player_id":            pid,
            "game_id":              gid,
            "dnp_injury":           dnp_injury,
            "dnp_rest":             dnp_rest,
            "dnp_coach_decision":   dnp_cd,
            "is_injury_elevated_role": is_elevated,
        })
    
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2021-10-01")
    parser.add_argument("--end",   default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--out",   default="data/nba_injury_reports.parquet")
    parser.add_argument("--features-out", default="data/injury_training_features.parquet")
    args = parser.parse_args()
    
    logger.info(f"Backfilling {args.start} -> {args.end}")
    df = backfill(args.start, args.end, args.out)
    
    if not df.empty:
        print(f"\n=== Backfill Complete ===")
        print(f"Total rows: {len(df)}")
        print(f"Date range: {df['report_date'].min()} -> {df['report_date'].max()}")
        print(f"\nStatus breakdown:")
        print(df["current_status"].value_counts().to_dict())
        print(f"\nDNP classification:")
        print(f"  dnp_injury:         {df['dnp_injury'].sum()}")
        print(f"  dnp_rest:           {df['dnp_rest'].sum()}")
        print(f"  dnp_coach_decision: {df['dnp_coach_decision'].sum()}")
        
        # Build training features if pgs exists
        pgs_path = Path("data/player_game_stats.parquet")
        if pgs_path.exists():
            logger.info("Building training features...")
            pgs = pd.read_parquet(pgs_path)
            features = build_training_features(df, pgs)
            features.to_parquet(args.features_out, index=False)
            print(f"\nTraining features: {len(features)} rows -> {args.features_out}")
            print(f"  dnp_injury rows:         {features['dnp_injury'].sum()}")
            print(f"  dnp_rest rows:           {features['dnp_rest'].sum()}")
            print(f"  dnp_coach_decision rows: {features['dnp_coach_decision'].sum()}")
            print(f"  is_injury_elevated_role: {features['is_injury_elevated_role'].sum()}")
