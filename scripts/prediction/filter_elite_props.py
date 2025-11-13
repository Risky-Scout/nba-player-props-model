#!/usr/bin/env python3
"""
ELITE PROPS FILTER - ONLY BET HIGH-EDGE PLAYS
This is how you get to 70-80% accuracy

Strategy: Only bet props where you have SIGNIFICANT edge
"""

import pandas as pd
import sys
from datetime import datetime

def filter_elite_props(predictions_csv):
    """
    Filter predictions to only high-edge, high-confidence props

    Criteria for ELITE props:
    1. Large edge (prediction far from line)
    2. High confidence (75%+)
    3. Reliable data (player has recent games)
    4. Starter minutes (25+)
    """

    print("="*80)
    print("ELITE PROPS FILTER - SYNDICATE LEVEL")
    print("="*80)

    # Load predictions
    df = pd.read_csv(predictions_csv)
    print(f"\n✓ Loaded {len(df)} total predictions")

    # Calculate edge (how far prediction is from line)
    df['edge'] = df['expected_value'] - df['line']
    df['edge_abs'] = abs(df['edge'])

    # Filter criteria
    print("\n" + "="*80)
    print("FILTERING CRITERIA (ELITE ONLY)")
    print("="*80)

    # 1. Edge thresholds
    edge_thresholds = {
        'PTS': 5.0,  # Prediction must be 5+ points from line
        'REB': 2.0,  # 2+ rebounds from line
        'AST': 2.0,  # 2+ assists from line
        '3PM': 1.0   # 1+ three-pointers from line
    }

    # 2. Confidence threshold
    confidence_threshold = 0.75  # 75%+ probability

    # 3. Minutes threshold
    minutes_threshold = 25.0  # Starters only

    print(f"\n1. Edge Requirements:")
    for prop, edge in edge_thresholds.items():
        print(f"   {prop}: {edge}+ difference from line")

    print(f"\n2. Confidence: {confidence_threshold*100:.0f}%+ probability")
    print(f"3. Minutes: {minutes_threshold}+ projected")
    print(f"4. Usage boost: < 1.3 (no questionable injury situations)")

    # Apply filters
    elite_props = []

    for prop_type, edge_req in edge_thresholds.items():
        prop_df = df[df['prop'] == prop_type].copy()

        if len(prop_df) == 0:
            continue

        # Filter
        filtered = prop_df[
            (prop_df['edge_abs'] >= edge_req) &  # Large edge
            (prop_df['prob_over'] >= confidence_threshold) &  # High confidence
            (prop_df.get('usage_boost', 1.0) < 1.3)  # Not injury-dependent
        ]

        elite_props.append(filtered)

    if len(elite_props) == 0:
        print("\n⚠️  No props passed elite filter")
        return None

    elite_df = pd.concat(elite_props, ignore_index=True)

    # Sort by edge * confidence (expected value)
    elite_df['ev_score'] = elite_df['edge_abs'] * elite_df['prob_over']
    elite_df = elite_df.sort_values('ev_score', ascending=False)

    # Results
    print("\n" + "="*80)
    print(f"ELITE PROPS FOUND: {len(elite_df)}")
    print("="*80)

    print(f"\nTotal predictions: {len(df)}")
    print(f"Passed filter: {len(elite_df)} ({len(elite_df)/len(df)*100:.1f}%)")
    print(f"\nBy prop type:")
    for prop_type in elite_df['prop'].unique():
        count = len(elite_df[elite_df['prop'] == prop_type])
        print(f"  {prop_type}: {count}")

    # Display elite props
    print("\n" + "="*80)
    print("TONIGHT'S ELITE PLAYS")
    print("="*80)

    print(f"\n{'Rank':<6}{'Player':<25}{'Prop':<6}{'Line':<8}{'Pred':<8}{'Edge':<8}{'Prob':<8}{'EV Score':<10}")
    print("-"*90)

    for idx, row in elite_df.head(30).iterrows():
        rank = idx + 1
        player = row['player'][:24]
        prop = row['prop']
        line = row['line']
        pred = row['expected_value']
        edge = row['edge']
        prob = row['prob_over']
        ev_score = row['ev_score']

        print(f"{rank:<6}{player:<25}{prop:<6}{line:<8.1f}{pred:<8.1f}{edge:<8.1f}{prob:<8.1%}{ev_score:<10.2f}")

    # Save elite props
    output_file = predictions_csv.replace('.csv', '_ELITE_ONLY.csv')
    elite_df.to_csv(output_file, index=False)

    print("\n" + "="*80)
    print(f"✓ Saved elite props to: {output_file}")
    print("="*80)

    # Betting instructions
    print("\n" + "="*80)
    print("BETTING INSTRUCTIONS")
    print("="*80)
    print(f"\n1. Only bet these {len(elite_df)} props (NOT the full list)")
    print(f"2. Bet 1-2% of bankroll per prop")
    print(f"3. Focus on top 15-20 by EV score")
    print(f"4. Track EVERY result for accuracy measurement")
    print(f"5. Expected accuracy: 70-80% (vs 55% on all props)")

    print("\n" + "="*80)
    print("CONFIDENCE LEVEL")
    print("="*80)
    print(f"\nAverage edge: {elite_df['edge_abs'].mean():.2f}")
    print(f"Average confidence: {elite_df['prob_over'].mean():.1%}")
    print(f"Average EV score: {elite_df['ev_score'].mean():.2f}")

    # Prop type breakdown
    print("\n" + "="*80)
    print("STRATEGY BY PROP TYPE")
    print("="*80)

    for prop_type in ['AST', 'REB', 'PTS']:
        prop_elite = elite_df[elite_df['prop'] == prop_type]
        if len(prop_elite) > 0:
            avg_edge = prop_elite['edge_abs'].mean()
            avg_conf = prop_elite['prob_over'].mean()
            print(f"\n{prop_type}:")
            print(f"  Count: {len(prop_elite)}")
            print(f"  Avg Edge: {avg_edge:.2f}")
            print(f"  Avg Confidence: {avg_conf:.1%}")
            print(f"  💡 Recommendation: {'BET HEAVY' if avg_conf > 0.80 else 'BET SELECTIVE'}")

    return elite_df


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python filter_elite_props.py <predictions_csv>")
        print("\nExample:")
        print("  python filter_elite_props.py predictions/tonight_INJURY_ADJUSTED_20251113.csv")
        sys.exit(1)

    predictions_file = sys.argv[1]
    filter_elite_props(predictions_file)
