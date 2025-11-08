"""
AUTOMATED MODEL TRAINING PIPELINE
Trains meta-ensemble model on latest NBA data
"""
import pandas as pd
import numpy as np
from meta_ensemble_model import MetaEnsemblePlayerPropModel
import warnings
warnings.filterwarnings('ignore')

def train_current_model(data_file='data/nba_current_season.csv'):
    """Train model on current season data"""

    print("="*80)
    print("NBA PLAYER PROPS MODEL - TRAINING PIPELINE")
    print("="*80)

    # Load data
    print("\nLoading current season data...")
    df = pd.read_csv(data_file)

    print(f"✓ Loaded {len(df)} games")
    print(f"✓ Players: {df['PLAYER_NAME'].nunique()}")
    print(f"✓ Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")

    # Remove DNP games (no minutes)
    df = df[df['MIN'] > 0].copy()
    print(f"✓ After removing DNP: {len(df)} games")

    # Define features
    feature_cols = [
        'HOME_GAME', 'REST_DAYS', 'GAMES_LAST_7',
        'MIN', 'OPP_DEF_RATING', 'OPP_OFF_RATING', 'OPP_PACE',
        'PTS_L7', 'REB_L7', 'AST_L7', 'MIN_L7',
        'FG_PCT_L7', 'FG3_PCT_L7', 'FT_PCT_L7'
    ]

    print(f"✓ Features: {len(feature_cols)}")

    # Create train/test split (80/20 temporal split)
    df = df.sort_values('GAME_DATE')
    split_idx = int(len(df) * 0.8)

    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    print(f"\n{'='*80}")
    print("DATA SPLIT")
    print(f"{'='*80}")
    print(f"Train: {len(train_df)} games ({train_df['GAME_DATE'].min()} to {train_df['GAME_DATE'].max()})")
    print(f"Test:  {len(test_df)} games ({test_df['GAME_DATE'].min()} to {test_df['GAME_DATE'].max()})")

    # Initialize model
    model = MetaEnsemblePlayerPropModel(cache_dir="./model_cache")

    # Train global models for each prop
    print(f"\n{'='*80}")
    print("TRAINING GLOBAL ENSEMBLE MODELS")
    print(f"{'='*80}")

    for prop in ['PTS', 'REB', 'AST']:
        print(f"\n{'='*80}")
        print(f"Training {prop} Model")
        print(f"{'='*80}")

        global_model = model.train_global_model(
            training_data=train_df,
            prop_stat=prop,
            features=feature_cols
        )

        model.global_models[prop.lower()] = global_model

    # Train player-specific models for high-volume players
    print(f"\n{'='*80}")
    print("TRAINING PLAYER-SPECIFIC MODELS")
    print(f"{'='*80}")

    player_game_counts = train_df.groupby(['PLAYER_ID', 'PLAYER_NAME']).size()
    high_volume_players = player_game_counts[player_game_counts >= 30].reset_index()

    print(f"Players with 30+ games: {len(high_volume_players)}")

    for idx, row in high_volume_players.iterrows():
        player_id = row['PLAYER_ID']
        player_name = row['PLAYER_NAME']
        n_games = row[0]

        print(f"\n[{idx+1}/{len(high_volume_players)}] {player_name} ({n_games} games)")

        player_history = train_df[train_df['PLAYER_ID'] == player_id].copy()

        for prop in ['PTS', 'REB', 'AST']:
            player_model = model.train_player_specific_model(
                player_id=str(player_id),
                player_name=player_name,
                player_history=player_history,
                prop_stat=prop
            )

            if player_model:
                key = f"{player_id}_{prop.lower()}"
                model.player_models[key] = player_model

    # Evaluate on test set
    print(f"\n{'='*80}")
    print("MODEL EVALUATION")
    print(f"{'='*80}")

    test_results = {}

    for prop in ['PTS', 'REB', 'AST']:
        prop_lower = prop.lower()

        if prop_lower not in model.global_models:
            continue

        model_info = model.global_models[prop_lower]
        X_test = test_df[feature_cols].fillna(0)
        y_test = test_df[prop]

        X_test_scaled = model_info['scaler'].transform(X_test)
        y_pred = model_info['model'].predict(X_test_scaled)

        mae = np.mean(np.abs(y_test - y_pred))
        test_results[prop] = mae

        print(f"{prop} MAE: {mae:.2f}")

    # Save model
    print(f"\n{'='*80}")
    print("SAVING MODEL")
    print(f"{'='*80}")

    model.save_models('model_cache/latest_model.pkl')

    print(f"\n{'='*80}")
    print("✓ TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"Global models: {len(model.global_models)}")
    print(f"Player models: {len(model.player_models)}")
    print(f"Test MAE:")
    for prop, mae in test_results.items():
        print(f"  {prop}: {mae:.2f}")
    print(f"{'='*80}")

    return model, test_results

if __name__ == "__main__":
    model, results = train_current_model()
