"""Build the canonical OOF player×game crosswalk.

Joins Phase 8 OOF rows (which carry only player_id + game_id + stat +
outcome) to player_name + team + opponent + team_abbr via the local
`data/player_game_stats.parquet`. Also normalizes player_name for
fuzzy-match against the Odds API.

Output:
  artifacts/market_manifest/oof_player_game_crosswalk.parquet
  artifacts/market_manifest/oof_player_game_crosswalk.csv

Schema (one row per (game_id, player_id) — UNIQUE; stats are NOT
multiplied here, since name + team are stat-invariant):

  game_id
  game_date
  player_id
  player_name
  normalized_player_name
  team
  opponent
  team_abbr
  opponent_abbr
  source_file
  source_confidence  (1.0 = direct join from player_game_stats)
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OOF_ROOT = Path("/tmp/phase8_full_vectorized_success/artifacts_downloaded")
PGS_PATH = REPO_ROOT / "data" / "player_game_stats.parquet"
OUT_DIR = REPO_ROOT / "artifacts" / "market_manifest"

NBA_ABBR_TO_NAME = {
    "ATL":"Atlanta Hawks","BOS":"Boston Celtics","BKN":"Brooklyn Nets",
    "CHA":"Charlotte Hornets","CHI":"Chicago Bulls","CLE":"Cleveland Cavaliers",
    "DAL":"Dallas Mavericks","DEN":"Denver Nuggets","DET":"Detroit Pistons",
    "GSW":"Golden State Warriors","HOU":"Houston Rockets","IND":"Indiana Pacers",
    "LAC":"LA Clippers","LAL":"Los Angeles Lakers","MEM":"Memphis Grizzlies",
    "MIA":"Miami Heat","MIL":"Milwaukee Bucks","MIN":"Minnesota Timberwolves",
    "NOP":"New Orleans Pelicans","NYK":"New York Knicks","OKC":"Oklahoma City Thunder",
    "ORL":"Orlando Magic","PHI":"Philadelphia 76ers","PHX":"Phoenix Suns",
    "POR":"Portland Trail Blazers","SAC":"Sacramento Kings","SAS":"San Antonio Spurs",
    "TOR":"Toronto Raptors","UTA":"Utah Jazz","WAS":"Washington Wizards",
}


def normalize_player_name(s) -> str:
    """Lowercase, NFKD-fold, strip diacritics, drop punctuation/suffixes."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[\.\,\']", "", s)
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\b\.?", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _load_oof() -> pd.DataFrame:
    folds = sorted(OOF_ROOT.glob("fold-*-oof/fold_*.parquet"),
                   key=lambda p: int(p.parent.name.split("-")[1]))
    if not folds:
        raise SystemExit(f"FATAL: no fold parquets at {OOF_ROOT}")
    df = pd.concat([pd.read_parquet(p) for p in folds], ignore_index=True)
    df["game_date"] = df["game_date"].astype(str).str[:10]
    return df


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("Build OOF player×game crosswalk")
    print("=" * 72)

    oof = _load_oof()
    print(f"OOF rows total: {len(oof):,}; date range "
          f"{oof.game_date.min()} → {oof.game_date.max()}")
    pairs = oof[["game_id", "game_date", "player_id"]].drop_duplicates().reset_index(drop=True)
    print(f"Unique (game_id, player_id): {len(pairs):,}")

    if not PGS_PATH.exists():
        raise SystemExit(f"FATAL: {PGS_PATH} missing — needed for player/team join")
    pgs = pd.read_parquet(PGS_PATH)
    pgs["game_date"] = pgs["game_date"].astype(str).str[:10]
    pgs_keys = (pgs[["game_id", "player_id", "player_name",
                     "team_id", "team_abbr",
                     "home_team_id", "visitor_team_id"]]
                .drop_duplicates(["game_id", "player_id"]))
    print(f"player_game_stats unique (game_id, player_id): {len(pgs_keys):,}")

    crosswalk = pairs.merge(pgs_keys, on=["game_id", "player_id"], how="left")

    team_id_to_abbr = {
        int(t): str(a)
        for t, a in pgs.dropna(subset=["team_id", "team_abbr"])
                       .drop_duplicates("team_id")[["team_id", "team_abbr"]]
                       .itertuples(index=False, name=None)
    }

    def _opp_id(row):
        h = row.get("home_team_id")
        v = row.get("visitor_team_id")
        t = row.get("team_id")
        if pd.isna(h) or pd.isna(v) or pd.isna(t):
            return np.nan
        h, v, t = int(h), int(v), int(t)
        return v if t == h else h

    crosswalk["opponent_team_id"] = crosswalk.apply(_opp_id, axis=1)
    crosswalk["opponent_abbr"] = crosswalk["opponent_team_id"].map(
        lambda v: team_id_to_abbr.get(int(v)) if pd.notna(v) else None
    )
    crosswalk["team"] = crosswalk["team_abbr"].map(NBA_ABBR_TO_NAME).fillna(crosswalk["team_abbr"])
    crosswalk["opponent"] = crosswalk["opponent_abbr"].map(NBA_ABBR_TO_NAME).fillna(crosswalk["opponent_abbr"])
    crosswalk["normalized_player_name"] = crosswalk["player_name"].map(normalize_player_name)
    crosswalk["source_file"] = "data/player_game_stats.parquet"
    crosswalk["source_confidence"] = np.where(
        crosswalk["player_name"].notna() & (crosswalk["player_name"].astype(str) != ""),
        1.0, 0.0,
    )

    final_cols = [
        "game_id", "game_date", "player_id", "player_name",
        "normalized_player_name",
        "team", "opponent", "team_abbr", "opponent_abbr",
        "source_file", "source_confidence",
    ]
    crosswalk = crosswalk[final_cols].copy()

    parquet_path = OUT_DIR / "oof_player_game_crosswalk.parquet"
    csv_path = OUT_DIR / "oof_player_game_crosswalk.csv"
    crosswalk.to_parquet(parquet_path, index=False)
    crosswalk.to_csv(csv_path, index=False)
    print(f"\nWrote {parquet_path.relative_to(REPO_ROOT)}  "
          f"({parquet_path.stat().st_size:,} B)")
    print(f"Wrote {csv_path.relative_to(REPO_ROOT)}  ({csv_path.stat().st_size:,} B)")

    # Report
    print(f"\n=== Crosswalk report ===")
    print(f"rows:                          {len(crosswalk):,}")
    print(f"unique player_id:              {crosswalk.player_id.nunique():,}")
    print(f"unique game_id:                {crosswalk.game_id.nunique():,}")
    print(f"missing player_name:           "
          f"{int(crosswalk['player_name'].isna().sum() + (crosswalk['player_name'].astype(str) == '').sum()):,}")
    print(f"missing team_abbr:             {int(crosswalk['team_abbr'].isna().sum()):,}")
    print(f"missing opponent_abbr:         {int(crosswalk['opponent_abbr'].isna().sum()):,}")
    # Conflicts: same player_id with multiple normalized names
    multi = (crosswalk.dropna(subset=["normalized_player_name"])
                       .groupby("player_id")["normalized_player_name"].nunique())
    conflicts = int((multi > 1).sum())
    print(f"player_id with >1 normalized name (alias drift): {conflicts}")
    if conflicts:
        sample_conflict_ids = multi[multi > 1].index.tolist()[:5]
        for pid in sample_conflict_ids:
            names = sorted(crosswalk[crosswalk.player_id == pid]["normalized_player_name"].unique().tolist())
            print(f"    player_id={pid}: {names}")

    print(f"\nSample 20 rows:")
    print(crosswalk[["game_date","game_id","player_id","player_name",
                     "normalized_player_name","team_abbr","opponent_abbr"]]
          .head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
