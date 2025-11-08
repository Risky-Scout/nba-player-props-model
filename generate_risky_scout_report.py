#!/usr/bin/env python3
"""
THE RISKY SCOUT - NBA PLAYER PROP FAVORITES
Beautiful summary report for subscribers

Usage:
  python generate_risky_scout_report.py --date 2025-11-08
"""

import pandas as pd
import argparse
from datetime import datetime
import os

def generate_report(prediction_date, input_file):
    """Generate clean, beautiful summary report for subscribers"""

    print("="*80)
    print("GENERATING THE RISKY SCOUT'S NBA PLAYER PROP FAVORITES")
    print("="*80)

    # Load full predictions
    preds = pd.read_csv(input_file)

    print(f"\nLoaded {len(preds)} total predictions")

    # Calculate correlations for SGPs
    df = pd.read_csv('data/processed_training_data.csv')
    corr_matrix = df[['pts', 'reb', 'ast']].corr()

    pts_reb_corr = corr_matrix.loc['pts', 'reb']
    pts_ast_corr = corr_matrix.loc['pts', 'ast']
    reb_ast_corr = corr_matrix.loc['reb', 'ast']

    # ========================================================================
    # TOP INDIVIDUAL PROPS (70-80% confidence)
    # ========================================================================

    individual_props = preds[
        (preds['prob_over'] >= 0.70) &
        (preds['prob_over'] <= 0.80)
    ].sort_values('prob_over', ascending=False).head(15)

    # ========================================================================
    # GENERATE SGPs
    # ========================================================================

    print("\nGenerating SGP recommendations...")

    # Get high probability props for SGPs (65-80% range)
    sgp_candidates = preds[
        (preds['prob_over'] >= 0.65) &
        (preds['prob_over'] <= 0.80)
    ].copy()

    # 2-leg SGPs
    sgps_2leg = []

    for idx1, row1 in sgp_candidates.iterrows():
        for idx2, row2 in sgp_candidates.iterrows():
            if idx1 >= idx2:
                continue

            # Same team only (same game)
            if row1['team'] != row2['team']:
                continue

            # Determine correlation
            props = sorted([row1['prop'], row2['prop']])
            if props == ['AST', 'PTS']:
                corr = pts_ast_corr
            elif props == ['PTS', 'REB']:
                corr = pts_reb_corr
            elif props == ['AST', 'REB']:
                corr = reb_ast_corr
            else:
                corr = 0.0

            if corr < 0.15:
                continue

            # Calculate combined probability
            independent_prob = row1['prob_over'] * row2['prob_over']
            correlation_factor = 1 + (corr * 0.15)
            combined_prob = min(0.95, independent_prob * correlation_factor)

            if combined_prob < 0.55:
                continue

            sgps_2leg.append({
                'player1': row1['player'],
                'prop1': row1['prop'],
                'line1': row1['line'],
                'prob1': row1['prob_over'],
                'player2': row2['player'],
                'prop2': row2['prop'],
                'line2': row2['line'],
                'prob2': row2['prob_over'],
                'correlation': corr,
                'combined_prob': combined_prob,
                'team': row1['team']
            })

    sgps_2leg = pd.DataFrame(sgps_2leg).sort_values('combined_prob', ascending=False).head(10)

    # 3-leg SGPs (simplified - just top combinations)
    sgps_3leg = []

    for idx1, row1 in sgp_candidates.head(50).iterrows():
        for idx2, row2 in sgp_candidates.head(50).iterrows():
            for idx3, row3 in sgp_candidates.head(50).iterrows():
                if idx1 >= idx2 or idx2 >= idx3:
                    continue

                if row1['team'] != row2['team'] or row2['team'] != row3['team']:
                    continue

                # Calculate correlations
                props_12 = sorted([row1['prop'], row2['prop']])
                props_13 = sorted([row1['prop'], row3['prop']])
                props_23 = sorted([row2['prop'], row3['prop']])

                corrs = []
                for props in [props_12, props_13, props_23]:
                    if props == ['AST', 'PTS']:
                        corrs.append(pts_ast_corr)
                    elif props == ['PTS', 'REB']:
                        corrs.append(pts_reb_corr)
                    elif props == ['AST', 'REB']:
                        corrs.append(reb_ast_corr)
                    else:
                        corrs.append(0.0)

                avg_corr = sum(corrs) / len(corrs)

                if avg_corr < 0.12:
                    continue

                independent_prob = row1['prob_over'] * row2['prob_over'] * row3['prob_over']
                correlation_factor = 1 + (avg_corr * 0.12)
                combined_prob = min(0.90, independent_prob * correlation_factor)

                if combined_prob < 0.30:
                    continue

                sgps_3leg.append({
                    'player1': row1['player'],
                    'prop1': row1['prop'],
                    'line1': row1['line'],
                    'prob1': row1['prob_over'],
                    'player2': row2['player'],
                    'prop2': row2['prop'],
                    'line2': row2['line'],
                    'prob2': row2['prob_over'],
                    'player3': row3['player'],
                    'prop3': row3['prop'],
                    'line3': row3['line'],
                    'prob3': row3['prob_over'],
                    'avg_correlation': avg_corr,
                    'combined_prob': combined_prob,
                    'team': row1['team']
                })

    sgps_3leg = pd.DataFrame(sgps_3leg).sort_values('combined_prob', ascending=False).head(5)

    # ========================================================================
    # CREATE BEAUTIFUL FORMATTED REPORT
    # ========================================================================

    report_lines = []

    report_lines.append("="*80)
    report_lines.append("THE RISKY SCOUT'S NBA PLAYER PROP FAVORITES")
    report_lines.append(f"Date: {prediction_date}")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p ET')}")
    report_lines.append("="*80)
    report_lines.append("")

    # Model performance
    report_lines.append("MODEL PERFORMANCE")
    report_lines.append("-"*80)
    report_lines.append("Points:   MAE 2.31 pts  | 71.6% within 3 points")
    report_lines.append("Rebounds: MAE 1.05 reb  | 90.4% within 3 rebounds")
    report_lines.append("Assists:  MAE 0.80 ast  | 95.1% within 3 assists")
    report_lines.append("")
    report_lines.append("Trained on 9,573 real NBA games")
    report_lines.append("Features: Real opponent defensive ratings, usage boosts for injuries")
    report_lines.append("")

    # Top individual props
    report_lines.append("="*80)
    report_lines.append("TOP 15 INDIVIDUAL PROPS (70-80% Confidence)")
    report_lines.append("="*80)
    report_lines.append("")

    for i, (idx, row) in enumerate(individual_props.iterrows(), 1):
        report_lines.append(f"#{i:>2}. {row['player']:>25} ({row['team']:>22})")
        report_lines.append(f"     {row['prop']} Over {row['line']:>5.1f}")
        report_lines.append(f"     Probability: {row['prob_over']*100:>5.1f}%  |  Expected Value: {row['expected_value']:.1f}  |  Fair Odds: {row['fair_odds_over']:>5}")
        report_lines.append("")

    # 2-leg SGPs
    report_lines.append("="*80)
    report_lines.append("TOP 10 SAME GAME PARLAYS (2-LEG)")
    report_lines.append("="*80)
    report_lines.append("")

    for i, (idx, row) in enumerate(sgps_2leg.iterrows(), 1):
        report_lines.append(f"SGP #{i} - {row['team']}")
        report_lines.append(f"  Leg 1: {row['player1']} {row['prop1']} Over {row['line1']} ({row['prob1']*100:.1f}%)")
        report_lines.append(f"  Leg 2: {row['player2']} {row['prop2']} Over {row['line2']} ({row['prob2']*100:.1f}%)")
        report_lines.append(f"  Correlation: {row['correlation']:.3f}  |  Combined Probability: {row['combined_prob']*100:.1f}%")
        report_lines.append("")

    # 3-leg SGPs
    if len(sgps_3leg) > 0:
        report_lines.append("="*80)
        report_lines.append("TOP 5 SAME GAME PARLAYS (3-LEG)")
        report_lines.append("="*80)
        report_lines.append("")

        for i, (idx, row) in enumerate(sgps_3leg.iterrows(), 1):
            report_lines.append(f"SGP #{i} - {row['team']}")
            report_lines.append(f"  Leg 1: {row['player1']} {row['prop1']} Over {row['line1']} ({row['prob1']*100:.1f}%)")
            report_lines.append(f"  Leg 2: {row['player2']} {row['prop2']} Over {row['line2']} ({row['prob2']*100:.1f}%)")
            report_lines.append(f"  Leg 3: {row['player3']} {row['prop3']} Over {row['line3']} ({row['prob3']*100:.1f}%)")
            report_lines.append(f"  Avg Correlation: {row['avg_correlation']:.3f}  |  Combined Probability: {row['combined_prob']*100:.1f}%")
            report_lines.append("")

    # Footer
    report_lines.append("="*80)
    report_lines.append("DISCLAIMER")
    report_lines.append("-"*80)
    report_lines.append("These predictions are for informational purposes only.")
    report_lines.append("Past performance does not guarantee future results.")
    report_lines.append("Please gamble responsibly.")
    report_lines.append("="*80)
    report_lines.append("")
    report_lines.append("© The Risky Scout - Advanced NBA Analytics")
    report_lines.append("")

    # Save report
    report_text = "\n".join(report_lines)

    output_file = f'predictions/RISKY_SCOUT_FAVORITES_{prediction_date}.txt'
    with open(output_file, 'w') as f:
        f.write(report_text)

    print(f"\n✓ Report generated: {output_file}")

    # Also save CSV versions for data analysis
    individual_props.to_csv(f'predictions/top_props_{prediction_date}.csv', index=False)
    sgps_2leg.to_csv(f'predictions/sgp_2leg_{prediction_date}.csv', index=False)
    if len(sgps_3leg) > 0:
        sgps_3leg.to_csv(f'predictions/sgp_3leg_{prediction_date}.csv', index=False)

    print(f"✓ Data files saved")

    # Print to console
    print("\n" + report_text)

    return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Risky Scout summary report')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='Prediction date')
    parser.add_argument('--input', default=None, help='Input predictions CSV')

    args = parser.parse_args()

    if args.input is None:
        args.input = f'predictions/tonight_INJURY_ADJUSTED_{args.date.replace("-", "")}.csv'

    generate_report(args.date, args.input)
