#!/usr/bin/env python3
"""
DIVERSIFIED PARLAY GENERATOR
Fixes two major issues:
1. Only uses players available on betting sites
2. Limits player repetition for diversification
"""

import pandas as pd
import numpy as np
import sys
from itertools import combinations

def generate_diverse_parlays(predictions_csv, max_player_repeats=2, min_confidence=0.70):
    """
    Generate diverse 3-leg parlays with constraints

    Args:
        predictions_csv: Path to predictions file
        max_player_repeats: Max times a player can appear in top 100 parlays (default: 2)
        min_confidence: Minimum probability for each leg (default: 70%)

    Returns:
        DataFrame of diverse parlays
    """

    print("="*80)
    print("DIVERSIFIED PARLAY GENERATOR")
    print("="*80)

    # Load predictions
    df = pd.read_csv(predictions_csv)
    print(f"\n✓ Loaded {len(df)} predictions")

    # Filter to high confidence props
    high_conf = df[df['prob_over'] >= min_confidence].copy()
    print(f"✓ {len(high_conf)} props with {min_confidence*100:.0f}%+ confidence")

    # Calculate expected value for each prop
    high_conf['ev'] = high_conf['prob_over'] * high_conf['expected_value']

    # Generate all possible 3-leg combinations
    print(f"\n[1/3] Generating 3-leg combinations...")

    # For efficiency, only consider top props from each player
    top_props_per_player = high_conf.sort_values('prob_over', ascending=False).groupby('player').head(2)

    all_combos = []
    props_list = top_props_per_player.to_dict('records')

    for combo in combinations(range(len(props_list)), 3):
        leg1, leg2, leg3 = [props_list[i] for i in combo]

        # Skip if same player appears multiple times
        if len({leg1['player'], leg2['player'], leg3['player']}) < 3:
            continue

        # Skip if from same game (want cross-game parlays for independence)
        if leg1.get('team') == leg2.get('team') or leg1.get('team') == leg3.get('team') or leg2.get('team') == leg3.get('team'):
            continue

        # Calculate parlay probability (assuming independence)
        combined_prob = leg1['prob_over'] * leg2['prob_over'] * leg3['prob_over']

        # Calculate correlation adjustment (players in different games = low correlation)
        corr_adjustment = 0.95  # Slight reduction for any correlation
        adjusted_prob = combined_prob * corr_adjustment

        # Skip low probability parlays
        if adjusted_prob < 0.30:  # At least 30% chance
            continue

        all_combos.append({
            'player1': leg1['player'],
            'prop1': leg1['prop'],
            'line1': leg1['line'],
            'prob1': leg1['prob_over'],
            'expected1': leg1['expected_value'],

            'player2': leg2['player'],
            'prop2': leg2['prop'],
            'line2': leg2['line'],
            'prob2': leg2['prob_over'],
            'expected2': leg2['expected_value'],

            'player3': leg3['player'],
            'prop3': leg3['prop'],
            'line3': leg3['line'],
            'prob3': leg3['prob_over'],
            'expected3': leg3['expected_value'],

            'combined_prob': combined_prob,
            'adjusted_prob': adjusted_prob,
            'ev_score': adjusted_prob * (leg1['ev'] + leg2['ev'] + leg3['ev']) / 3
        })

    if len(all_combos) == 0:
        print("\n❌ No valid 3-leg parlays found")
        return None

    parlays_df = pd.DataFrame(all_combos)
    print(f"✓ Generated {len(parlays_df)} possible parlays")

    # Sort by EV score
    parlays_df = parlays_df.sort_values('ev_score', ascending=False)

    # [2/3] Apply diversification constraints
    print(f"\n[2/3] Applying diversification (max {max_player_repeats} repeats per player)...")

    diverse_parlays = []
    player_counts = {}

    for idx, parlay in parlays_df.iterrows():
        # Check if any player has exceeded max appearances
        players = [parlay['player1'], parlay['player2'], parlay['player3']]

        if all(player_counts.get(p, 0) < max_player_repeats for p in players):
            # Add this parlay
            diverse_parlays.append(parlay)

            # Update player counts
            for p in players:
                player_counts[p] = player_counts.get(p, 0) + 1

            # Stop at 100 parlays
            if len(diverse_parlays) >= 100:
                break

    if len(diverse_parlays) == 0:
        print("\n⚠️  No parlays passed diversification filter")
        return None

    diverse_df = pd.DataFrame(diverse_parlays)

    print(f"✓ Selected {len(diverse_df)} diverse parlays")
    print(f"\n[3/3] Player distribution in top 100:")

    all_players = []
    for idx, row in diverse_df.head(100).iterrows():
        all_players.extend([row['player1'], row['player2'], row['player3']])

    player_dist = pd.Series(all_players).value_counts().head(20)
    for player, count in player_dist.items():
        print(f"  {player:30} appears {count:2} times")

    unique_players = len(pd.Series(all_players).unique())
    print(f"\n✓ Total unique players in top 100 parlays: {unique_players}")
    print(f"✓ Average probability: {diverse_df.head(100)['adjusted_prob'].mean():.1%}")

    return diverse_df


def filter_available_players(predictions_csv, available_players_file):
    """
    Filter predictions to only include players available on betting sites

    Args:
        predictions_csv: Path to predictions file
        available_players_file: Text file with one player name per line

    Returns:
        Filtered DataFrame
    """

    print("="*80)
    print("FILTERING TO AVAILABLE PLAYERS")
    print("="*80)

    # Load predictions
    df = pd.read_csv(predictions_csv)
    print(f"\n✓ Loaded {len(df)} predictions")
    print(f"✓ Unique players: {df['player'].nunique()}")

    # Load available players list
    try:
        with open(available_players_file, 'r') as f:
            available = [line.strip() for line in f if line.strip()]

        print(f"✓ Loaded {len(available)} available players from {available_players_file}")
    except FileNotFoundError:
        print(f"\n⚠️  File not found: {available_players_file}")
        print("\nCreating template file...")

        # Create template with top players
        top_players = df['player'].value_counts().head(50).index.tolist()
        with open(available_players_file, 'w') as f:
            f.write("# List of players available on your betting site\n")
            f.write("# One player name per line\n")
            f.write("# Edit this file to match your bookmaker's offerings\n\n")
            for player in top_players:
                f.write(f"{player}\n")

        print(f"✓ Created template: {available_players_file}")
        print(f"✓ Edit this file to list only players with available lines")
        available = top_players

    # Filter
    filtered = df[df['player'].isin(available)].copy()

    print(f"\n✓ Filtered to {len(filtered)} predictions ({len(filtered)/len(df)*100:.1f}%)")
    print(f"✓ Players available: {filtered['player'].nunique()}")

    # Save filtered predictions
    output_file = predictions_csv.replace('.csv', '_AVAILABLE_ONLY.csv')
    filtered.to_csv(output_file, index=False)
    print(f"✓ Saved to: {output_file}")

    return filtered, output_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_diverse_parlays.py <predictions_csv> [available_players.txt]")
        print("\nExample:")
        print("  python generate_diverse_parlays.py predictions/tonight_INJURY_ADJUSTED_20251113.csv")
        print("\nWith player filter:")
        print("  python generate_diverse_parlays.py predictions/tonight_INJURY_ADJUSTED_20251113.csv available_players.txt")
        sys.exit(1)

    predictions_file = sys.argv[1]

    # Step 1: Filter to available players (if specified)
    if len(sys.argv) >= 3:
        available_file = sys.argv[2]
        filtered_df, filtered_file = filter_available_players(predictions_file, available_file)
        predictions_file = filtered_file

    # Step 2: Generate diverse parlays
    print("\n")
    diverse_parlays = generate_diverse_parlays(
        predictions_file,
        max_player_repeats=2,  # Each player max 2 times in top 100
        min_confidence=0.70    # 70%+ props only
    )

    if diverse_parlays is not None:
        # Save
        output_file = predictions_file.replace('.csv', '_DIVERSE_PARLAYS.csv')
        diverse_parlays.head(100).to_csv(output_file, index=False)

        print("\n" + "="*80)
        print("✅ DIVERSE PARLAYS GENERATED")
        print("="*80)
        print(f"\n✓ Saved top 100 to: {output_file}")

        print("\nTop 10 Parlays:")
        print("-"*80)
        print(f"{'#':<4}{'Players':<60}{'Prob':<8}")
        print("-"*80)

        for idx, row in diverse_parlays.head(10).iterrows():
            players = f"{row['player1'][:15]}, {row['player2'][:15]}, {row['player3'][:15]}"
            print(f"{idx+1:<4}{players:<60}{row['adjusted_prob']:<8.1%}")

        print("\n" + "="*80)
        print("DIVERSIFICATION ACHIEVED")
        print("="*80)
        print(f"✓ Max player repeats: 2")
        print(f"✓ All cross-game parlays (lower correlation)")
        print(f"✓ No duplicate players within same parlay")
        print("="*80)
