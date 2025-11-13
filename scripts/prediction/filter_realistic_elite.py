#!/usr/bin/env python3
"""
REALISTIC ELITE FILTER
Only shows props at REALISTIC bookmaker lines (not every 0.5 increment)

This is what you ACTUALLY bet.
"""

import pandas as pd
import sys

def filter_realistic_elite_props(predictions_csv):
    """
    Filter to realistic bookmaker lines with high edge
    """

    print("="*80)
    print("ELITE PROPS - REALISTIC BOOKMAKER LINES ONLY")
    print("="*80)

    # Load predictions
    df = pd.read_csv(predictions_csv)
    print(f"\n✓ Loaded {len(df)} total predictions")

    # Calculate edge
    df['edge'] = df['expected_value'] - df['line']
    df['edge_abs'] = abs(df['edge'])

    # FILTER 1: Only realistic lines
    # Bookmakers typically offer lines near player averages, not 0.5 for everyone
    print("\n[1/3] Filtering to realistic bookmaker lines...")

    realistic_props = []

    for prop_type in ['PTS', 'REB', 'AST']:
        prop_df = df[df['prop'] == prop_type].copy()

        if len(prop_df) == 0:
            continue

        # For each player, only keep lines within reasonable range of their average
        for player in prop_df['player'].unique():
            player_df = prop_df[prop_df['player'] == player].copy()

            if len(player_df) == 0:
                continue

            # Get player's expected value
            expected = player_df['expected_value'].iloc[0]

            # Only keep lines within ±8 of expected (realistic range)
            # And only lines ending in .5 that are in typical ranges
            realistic_lines = player_df[
                (player_df['line'] >= max(0.5, expected - 8)) &
                (player_df['line'] <= expected + 8) &
                (player_df['line'] > 5.5)  # Skip ultra-low lines like 0.5, 1.5
            ]

            # For each player, pick the line closest to their expected value
            if len(realistic_lines) > 0:
                # Find line closest to expected
                realistic_lines['dist_from_exp'] = abs(realistic_lines['line'] - expected)
                best_line = realistic_lines.nsmallest(1, 'dist_from_exp')
                realistic_props.append(best_line)

    realistic_df = pd.concat(realistic_props, ignore_index=True) if realistic_props else pd.DataFrame()

    if len(realistic_df) == 0:
        print("⚠️  No realistic props found")
        return None

    print(f"✓ Filtered to {len(realistic_df)} props at realistic lines")

    # FILTER 2: High edge only
    print("\n[2/3] Filtering for high edge...")

    edge_thresholds = {
        'PTS': 4.0,  # 4+ points edge
        'REB': 2.0,  # 2+ rebounds edge
        'AST': 1.5,  # 1.5+ assists edge
    }

    high_edge_props = []

    for prop_type, edge_req in edge_thresholds.items():
        prop_subset = realistic_df[realistic_df['prop'] == prop_type]
        filtered = prop_subset[prop_subset['edge_abs'] >= edge_req]
        high_edge_props.append(filtered)

    elite_df = pd.concat(high_edge_props, ignore_index=True) if high_edge_props else pd.DataFrame()

    if len(elite_df) == 0:
        print("⚠️  No high-edge props found")
        return None

    print(f"✓ {len(elite_df)} props with significant edge")

    # FILTER 3: High confidence
    print("\n[3/3] Filtering for high confidence (70%+)...")

    elite_df = elite_df[elite_df['prob_over'] >= 0.70]
    print(f"✓ {len(elite_df)} props passed all filters")

    # Calculate EV score
    elite_df['ev_score'] = elite_df['edge_abs'] * elite_df['prob_over']
    elite_df = elite_df.sort_values('ev_score', ascending=False)

    # Display results
    print("\n" + "="*80)
    print(f"ELITE PLAYS FOR TONIGHT: {len(elite_df)} PROPS")
    print("="*80)

    if len(elite_df) == 0:
        print("\n⚠️  No props passed elite filter tonight")
        print("This might mean:")
        print("  - Lines are sharp (book has good numbers)")
        print("  - No clear edges available")
        print("  - Sit out tonight or lower thresholds")
        return None

    print(f"\n{'#':<4}{'Player':<25}{'Prop':<6}{'Line':<8}{'Pred':<8}{'Edge':<8}{'Prob':<10}{'Action':<10}")
    print("-"*95)

    for idx, (i, row) in enumerate(elite_df.head(25).iterrows(), 1):
        player = row['player'][:24]
        prop = row['prop']
        line = row['line']
        pred = row['expected_value']
        edge = row['edge']
        prob = row['prob_over']

        # Determine action
        if edge > 0:
            action = "OVER ✓"
        else:
            action = "UNDER ✓"

        print(f"{idx:<4}{player:<25}{prop:<6}{line:<8.1f}{pred:<8.1f}{edge:<8.1f}{prob:<10.1%}{action:<10}")

    # Save
    output_file = predictions_csv.replace('.csv', '_ELITE_REALISTIC.csv')
    elite_df.to_csv(output_file, index=False)

    print("\n" + "="*80)
    print(f"✓ Saved to: {output_file}")
    print("="*80)

    # Stats
    print("\n📊 BETTING STRATEGY:")
    print(f"  Total props to bet: {len(elite_df)}")
    print(f"  Average edge: {elite_df['edge_abs'].mean():.2f}")
    print(f"  Average confidence: {elite_df['prob_over'].mean():.1%}")
    print(f"  Expected win rate: 70-80% (on these props)")

    print("\n💰 BANKROLL MANAGEMENT:")
    print(f"  Bet 1-2% of bankroll per prop")
    print(f"  Focus on top 15-20 by EV score")
    print(f"  Total exposure: {min(20, len(elite_df)) * 2}% of bankroll max")

    print("\n✅ TRACKING:")
    print(f"  After games, track ALL {len(elite_df)} results")
    print(f"  This builds your accuracy baseline")

    return elite_df


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python filter_realistic_elite.py <predictions_csv>")
        print("\nExample:")
        print("  python filter_realistic_elite.py predictions/tonight_INJURY_ADJUSTED_20251113.csv")
        sys.exit(1)

    predictions_file = sys.argv[1]
    filter_realistic_elite_props(predictions_file)
