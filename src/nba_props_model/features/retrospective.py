"""
retrospective_features.py — Retrospective Role & Absence Feature Builder

Derives historically-recoverable injury/role context features from
player_game_stats.parquet without requiring external injury reports.

Features built (all strictly backward-looking, leakage-free):
    did_not_play_last_team_game   — absent from team's previous game
    returned_from_absence         — first appearance after 1+ missed games
    games_since_return            — consecutive appearances since last return
    limited_return_game           — first game back after 2+ game absence
    is_stable_role_player         — low rolling minutes CV over last 20 games
    is_recent_rotation_change     — short vs long window minutes delta
    is_high_minutes_uncertainty   — high volatility or recent return
    is_bench_fragile_minutes      — low minutes + high volatility
    opp_pace_context              — opponent rolling team scoring last 10 games
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MIN_GAMES_FOR_STABILITY  = 10
STABLE_ROLE_CV_THRESHOLD = 0.35
ROTATION_CHANGE_DELTA    = 5.0
BENCH_FRAGILE_MAX_MIN    = 22.0
BENCH_FRAGILE_MIN_CV     = 0.45
MULTI_GAME_ABSENCE_MIN   = 2


def build_retrospective_features(pgs_df: pd.DataFrame) -> pd.DataFrame:
    df = pgs_df.copy()
    df['game_date'] = pd.to_datetime(df['game_date'])
    if 'min_numeric' not in df.columns:
        df['min_numeric'] = pd.to_numeric(df['min'], errors='coerce').fillna(0)

    logger.info(f"Building retrospective features: {len(df)} rows, {df['player_id'].nunique()} players")

    # ── Team game schedule from observed appearances ───────────────────────────
    team_games = (
        df[['team_id','game_id','game_date']]
        .drop_duplicates()
        .sort_values(['team_id','game_date'])
    )

    # ── Player×team schedule join ──────────────────────────────────────────────
    # Each player joined to all games their team played
    player_team = (
        df[['player_id','team_id','game_date']]
        .sort_values(['player_id','game_date'])
        .drop_duplicates(['player_id','team_id'])
    )
    player_sched = pd.merge(player_team, team_games, on='team_id', how='left',
                            suffixes=('_join',''))
    player_sched = player_sched.drop(columns=['game_date_join'])

    appeared = df[['player_id','game_id']].copy()
    appeared['appeared'] = 1
    player_sched = pd.merge(player_sched, appeared,
                             on=['player_id','game_id'], how='left')
    player_sched['appeared'] = player_sched['appeared'].fillna(0).astype(int)
    player_sched = player_sched.sort_values(['player_id','team_id','game_date'])

    # ── Absence features ───────────────────────────────────────────────────────
    absence_rows = []
    for (pid, tid), grp in player_sched.groupby(['player_id','team_id']):
        grp = grp.sort_values('game_date').reset_index(drop=True)
        app = grp['appeared'].values
        gids = grp['game_id'].values

        for i in range(len(grp)):
            if app[i] == 0:
                continue  # only for games player played

            prior_app = app[:i]
            gid = gids[i]

            if len(prior_app) == 0:
                absence_rows.append({'player_id':pid,'game_id':gid,
                    'did_not_play_last_team_game':0,'returned_from_absence':0,
                    'games_since_return':0,'limited_return_game':0})
                continue

            dnp_last = int(prior_app[-1] == 0)

            # consecutive absences immediately before this game
            consec_absent = 0
            for v in reversed(prior_app):
                if v == 0: consec_absent += 1
                else: break

            # consecutive appearances immediately before this game
            consec_appeared = 0
            for v in reversed(prior_app):
                if v == 1: consec_appeared += 1
                else: break

            absence_rows.append({
                'player_id': pid,
                'game_id':   gid,
                'did_not_play_last_team_game': dnp_last,
                'returned_from_absence':       int(consec_absent > 0),
                'games_since_return':          consec_appeared,
                'limited_return_game':         int(consec_absent >= MULTI_GAME_ABSENCE_MIN),
            })

    absence_df = pd.DataFrame(absence_rows)
    logger.info(f"  Absence features: {len(absence_df)} rows")
    logger.info(f"  dnp_last_game rate:      {absence_df['did_not_play_last_team_game'].mean():.1%}")
    logger.info(f"  returned_from_absence:   {absence_df['returned_from_absence'].mean():.1%}")
    logger.info(f"  limited_return_game:     {absence_df['limited_return_game'].mean():.1%}")

    # ── Rolling minutes stability features ─────────────────────────────────────
    df_s = df.sort_values(['player_id','game_date']).reset_index(drop=True)
    stability_rows = []

    for pid, grp in df_s.groupby('player_id'):
        grp = grp.sort_values('game_date').reset_index(drop=True)
        mins = grp['min_numeric'].values
        gids = grp['game_id'].values

        for i in range(len(grp)):
            gid = gids[i]
            prior = mins[:i]

            if len(prior) < MIN_GAMES_FOR_STABILITY:
                stability_rows.append({'player_id':pid,'game_id':gid,
                    'is_stable_role_player':0,'is_recent_rotation_change':0,
                    'is_high_minutes_uncertainty':0,'is_bench_fragile_minutes':0})
                continue

            l5  = prior[-5:]  if len(prior) >= 5  else prior
            l10 = prior[-10:] if len(prior) >= 10 else prior
            l20 = prior[-20:] if len(prior) >= 20 else prior

            m20 = np.mean(l20); s20 = np.std(l20)
            m5  = np.mean(l5);  m10 = np.mean(l10); s10 = np.std(l10)
            cv20 = s20/m20 if m20 > 2 else 1.0

            is_stable     = int(cv20 < STABLE_ROLE_CV_THRESHOLD and m20 > 15)
            is_rot_change = int(abs(m5 - m10) > ROTATION_CHANGE_DELTA and len(l10) >= 5)
            is_high_unc   = int(cv20 > 0.50 and m20 > 5)
            is_fragile    = int(m10 < BENCH_FRAGILE_MAX_MIN and
                                (s10/m10 > BENCH_FRAGILE_MIN_CV if m10 > 2 else False))

            stability_rows.append({'player_id':pid,'game_id':gid,
                'is_stable_role_player':    is_stable,
                'is_recent_rotation_change':is_rot_change,
                'is_high_minutes_uncertainty':is_high_unc,
                'is_bench_fragile_minutes': is_fragile})

    stability_df = pd.DataFrame(stability_rows)
    logger.info(f"  Stability features: {len(stability_df)} rows")
    logger.info(f"  is_stable_role_player:      {stability_df['is_stable_role_player'].mean():.1%}")
    logger.info(f"  is_recent_rotation_change:  {stability_df['is_recent_rotation_change'].mean():.1%}")
    logger.info(f"  is_bench_fragile_minutes:   {stability_df['is_bench_fragile_minutes'].mean():.1%}")

    # ── Merge ──────────────────────────────────────────────────────────────────
    result = pd.merge(absence_df, stability_df, on=['player_id','game_id'], how='outer')

    # Boost uncertainty flag for players who just returned
    result['is_high_minutes_uncertainty'] = np.maximum(
        result['is_high_minutes_uncertainty'].fillna(0),
        result['returned_from_absence'].fillna(0)
    ).astype(int)

    logger.info(f"Retrospective features complete: {len(result)} rows")
    return result


def build_opp_pace_context(pgs_df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    df = pgs_df.copy()
    df['game_date'] = pd.to_datetime(df['game_date'])
    team_pts = (
        df.groupby(['team_id','game_id','game_date'])['pts']
        .sum().reset_index()
        .sort_values(['team_id','game_date'])
    )
    team_pts['opp_pace_context'] = (
        team_pts.groupby('team_id')['pts']
        .transform(lambda x: x.shift(1).rolling(window, min_periods=3).mean())
    )
    season_mean = team_pts['pts'].mean()
    team_pts['opp_pace_context'] = team_pts['opp_pace_context'].fillna(season_mean)
    return team_pts[['team_id','game_id','opp_pace_context']]


if __name__ == "__main__":
    import sys
    pgs_path = Path('data/player_game_stats.parquet')
    if not pgs_path.exists():
        print("ERROR: data/player_game_stats.parquet not found"); sys.exit(1)

    pgs = pd.read_parquet(pgs_path)
    print(f"Loaded {len(pgs)} rows")

    features  = build_retrospective_features(pgs)
    opp_pace  = build_opp_pace_context(pgs)

    # Validation
    print("\n=== Validation ===")
    feat_keys = set(zip(features['player_id'], features['game_id']))
    pgs_keys  = set(zip(pgs['player_id'], pgs['game_id']))
    orphans   = feat_keys - pgs_keys
    print(f"Orphan rows: {len(orphans)} (should be 0)")
    assert (features['games_since_return'] >= 0).all()
    print("games_since_return >= 0 ✓")
    lrg_invalid = ((features['limited_return_game']==1) & (features['returned_from_absence']==0)).sum()
    print(f"limited_return implies returned: {lrg_invalid==0} ✓")

    # Save
    Path('data').mkdir(exist_ok=True)
    features.to_parquet('data/retrospective_features.parquet', index=False)
    opp_pace.to_parquet('data/opp_pace_context.parquet', index=False)
    print(f"\n✓ data/retrospective_features.parquet — {len(features)} rows")
    print(f"✓ data/opp_pace_context.parquet — {len(opp_pace)} rows")

    print("\n=== Feature Rates ===")
    for col in ['did_not_play_last_team_game','returned_from_absence',
                'limited_return_game','is_stable_role_player',
                'is_recent_rotation_change','is_high_minutes_uncertainty',
                'is_bench_fragile_minutes']:
        print(f"  {col}: {features[col].mean():.1%}")
    print(f"  games_since_return: mean={features['games_since_return'].mean():.1f}")
