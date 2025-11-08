"""
TRAIN ELITE MODEL ON REAL NBA DATA
World-class accuracy - best in the business
"""
import pandas as pd
import numpy as np
from meta_ensemble_model import MetaEnsemblePlayerPropModel
import warnings
warnings.filterwarnings('ignore')

def train_elite_model(data_path='data/nba_training_data_real.csv',
                      output_path='model_cache/latest_model.pkl'):
    """
    Train the elite model on real NBA data

    Args:
        data_path: Path to training data
        output_path: Where to save trained model

    Returns:
        dict: Training results and metrics
    """
    print("="*80)
    print("TRAINING ELITE NBA PLAYER PROPS MODEL")
    print("="*80)
    print("Target: Best-in-world accuracy")
    print("="*80)

    # Load data
    print("\n[1/4] Loading training data...")
    df = pd.read_csv(data_path)
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])

    print(f"✓ Loaded {len(df)} games")
    print(f"✓ Players: {df['PLAYER_NAME'].nunique()}")
    print(f"✓ Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
    print(f"✓ Seasons: {', '.join(df['SEASON'].unique())}")

    # Temporal split for validation
    print("\n[2/4] Creating temporal train/validation split...")

    # Use 80% for training, 20% for validation (maintaining temporal order)
    split_idx = int(len(df) * 0.8)
    df_sorted = df.sort_values('GAME_DATE')

    train_df = df_sorted.iloc[:split_idx]
    val_df = df_sorted.iloc[split_idx:]

    print(f"✓ Training games: {len(train_df)}")
    print(f"✓ Validation games: {len(val_df)}")
    print(f"✓ Train date range: {train_df['GAME_DATE'].min()} to {train_df['GAME_DATE'].max()}")
    print(f"✓ Val date range: {val_df['GAME_DATE'].min()} to {val_df['GAME_DATE'].max()}")

    # Initialize and train model
    print("\n[3/4] Training 6-layer meta-ensemble model...")
    print("This may take 5-10 minutes...")

    model = MetaEnsemblePlayerPropModel()

    # Train on each prop type
    results = {}
    for prop_type in ['PTS', 'REB', 'AST']:
        print(f"\n  Training {prop_type} predictor...")

        # Train model
        model.train(train_df, prop_type=prop_type, cross_validate=True)

        # Validate
        val_predictions = model.predict(val_df, prop_type=prop_type)
        val_actuals = val_df[prop_type].values

        mae = np.mean(np.abs(val_predictions - val_actuals))
        rmse = np.sqrt(np.mean((val_predictions - val_actuals)**2))

        within_3 = np.mean(np.abs(val_predictions - val_actuals) <= 3) * 100

        print(f"    MAE: {mae:.2f}")
        print(f"    RMSE: {rmse:.2f}")
        print(f"    Within 3: {within_3:.1f}%")

        results[prop_type] = {
            'mae': mae,
            'rmse': rmse,
            'within_3': within_3
        }

    # Save model
    print("\n[4/4] Saving trained model...")
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save_models(output_path)
    print(f"✓ Model saved: {output_path}")

    # Print summary
    print("\n" + "="*80)
    print("TRAINING COMPLETE - MODEL READY")
    print("="*80)
    print("\nValidation Results:")
    print("-"*80)
    for prop_type, metrics in results.items():
        print(f"{prop_type:4s}  MAE: {metrics['mae']:5.2f}  RMSE: {metrics['rmse']:5.2f}  Within 3: {metrics['within_3']:5.1f}%")

    print("\n" + "="*80)
    print("Ready to generate elite predictions!")
    print("="*80)

    return results


if __name__ == "__main__":
    import sys

    data_path = sys.argv[1] if len(sys.argv) > 1 else 'data/nba_training_data_real.csv'

    results = train_elite_model(data_path)
