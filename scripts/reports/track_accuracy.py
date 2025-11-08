#!/usr/bin/env python3
"""
PREDICTION ACCURACY TRACKER
Tracks daily prediction results and maintains cumulative accuracy records

Usage:
  1. After games complete, enter actual results:
     python track_accuracy.py --date 2025-11-08 --enter-results

  2. View accuracy summary:
     python track_accuracy.py --summary

  3. View detailed history:
     python track_accuracy.py --history
"""

import pandas as pd
import argparse
from datetime import datetime, timedelta
import os
import json

# File paths
PREDICTIONS_DIR = 'predictions'
ACCURACY_LOG = 'accuracy_tracking/accuracy_log.csv'
DAILY_RESULTS = 'accuracy_tracking/daily_results'
ACCURACY_SUMMARY = 'accuracy_tracking/ACCURACY_SUMMARY.md'

def ensure_directories():
    """Create necessary directories"""
    os.makedirs('accuracy_tracking', exist_ok=True)
    os.makedirs(DAILY_RESULTS, exist_ok=True)

def get_prediction_file(date_str):
    """Find the prediction file for a given date"""
    # Try different possible filenames
    possible_files = [
        f'{PREDICTIONS_DIR}/tonight_INJURY_ADJUSTED_{date_str.replace("-", "")}.csv',
        f'{PREDICTIONS_DIR}/daily_{date_str}.csv',
        f'{PREDICTIONS_DIR}/top_props_{date_str}.csv'
    ]

    for file in possible_files:
        if os.path.exists(file):
            return file

    return None

def enter_results_interactive(date_str):
    """Interactive mode to enter actual game results"""

    print("="*80)
    print(f"ENTERING RESULTS FOR {date_str}")
    print("="*80)

    # Load predictions
    pred_file = get_prediction_file(date_str)

    if not pred_file:
        print(f"\n❌ No predictions found for {date_str}")
        print("Available prediction files:")
        for f in os.listdir(PREDICTIONS_DIR):
            if date_str.replace("-", "") in f:
                print(f"  {f}")
        return

    preds = pd.read_csv(pred_file)

    # Filter to high-confidence predictions (70-80%)
    tracked_preds = preds[
        (preds['prob_over'] >= 0.70) &
        (preds['prob_over'] <= 0.80)
    ].copy()

    print(f"\nFound {len(tracked_preds)} predictions to track (70-80% confidence)")
    print("\nYou can either:")
    print("  1. Enter results manually (interactive)")
    print("  2. Load results from CSV file")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == '2':
        # Load from CSV
        csv_file = input("Enter path to results CSV file: ").strip()
        if os.path.exists(csv_file):
            actual_results = pd.read_csv(csv_file)
            print(f"✓ Loaded {len(actual_results)} actual results")
        else:
            print(f"❌ File not found: {csv_file}")
            return
    else:
        # Manual entry
        print("\nEnter actual stats for each prediction")
        print("Format: player,prop,actual_value")
        print("Example: LeBron James,PTS,28")
        print("Enter 'done' when finished\n")

        actual_data = []
        while True:
            line = input("➡️  ").strip()
            if line.lower() == 'done':
                break

            try:
                player, prop, value = line.split(',')
                actual_data.append({
                    'player': player.strip(),
                    'prop': prop.strip().upper(),
                    'actual_value': float(value.strip())
                })
            except:
                print("Invalid format. Use: player,prop,value")

        if not actual_data:
            print("No results entered.")
            return

        actual_results = pd.DataFrame(actual_data)

    # Match predictions with actual results
    results = []

    for idx, pred in tracked_preds.iterrows():
        # Find matching actual result
        actual_match = actual_results[
            (actual_results['player'] == pred['player']) &
            (actual_results['prop'] == pred['prop'])
        ]

        if len(actual_match) == 0:
            continue

        actual_value = actual_match.iloc[0]['actual_value']
        predicted_value = pred['expected_value']
        line = pred['line']
        prob_over = pred['prob_over']

        # Did prediction hit?
        prediction_correct = (actual_value > line)

        results.append({
            'date': date_str,
            'player': pred['player'],
            'team': pred.get('team', ''),
            'prop': pred['prop'],
            'line': line,
            'predicted_value': predicted_value,
            'actual_value': actual_value,
            'prob_over': prob_over,
            'prediction_correct': 1 if prediction_correct else 0,
            'error': abs(predicted_value - actual_value)
        })

    if not results:
        print("\n⚠️  No matching results found")
        return

    results_df = pd.DataFrame(results)

    # Save daily results
    daily_file = f'{DAILY_RESULTS}/results_{date_str}.csv'
    results_df.to_csv(daily_file, index=False)

    # Update master log
    if os.path.exists(ACCURACY_LOG):
        master_log = pd.read_csv(ACCURACY_LOG)
        # Remove any existing entries for this date
        master_log = master_log[master_log['date'] != date_str]
        master_log = pd.concat([master_log, results_df], ignore_index=True)
    else:
        master_log = results_df

    master_log.to_csv(ACCURACY_LOG, index=False)

    # Print summary
    correct = results_df['prediction_correct'].sum()
    total = len(results_df)
    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"\n✓ Results saved for {date_str}")
    print(f"  Correct: {correct}/{total} ({accuracy:.1f}%)")
    print(f"  Average Error: {results_df['error'].mean():.2f}")
    print(f"  Saved to: {daily_file}")

    # Update summary
    generate_summary()

def generate_summary():
    """Generate accuracy summary report"""

    if not os.path.exists(ACCURACY_LOG):
        print("No tracking data yet.")
        return

    log = pd.read_csv(ACCURACY_LOG)

    # Overall stats
    total_predictions = len(log)
    total_correct = log['prediction_correct'].sum()
    overall_accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0

    # By prop type
    by_prop = log.groupby('prop').agg({
        'prediction_correct': ['sum', 'count'],
        'error': 'mean'
    }).round(2)

    by_prop.columns = ['Correct', 'Total', 'Avg Error']
    by_prop['Accuracy %'] = (by_prop['Correct'] / by_prop['Total'] * 100).round(1)

    # Daily stats
    by_date = log.groupby('date').agg({
        'prediction_correct': ['sum', 'count']
    })
    by_date.columns = ['Correct', 'Total']
    by_date['Accuracy %'] = (by_date['Correct'] / by_date['Total'] * 100).round(1)

    # Create markdown summary
    lines = []
    lines.append("# NBA PLAYER PROPS MODEL - ACCURACY TRACKING")
    lines.append(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p ET')}")
    lines.append("")
    lines.append("## OVERALL PERFORMANCE")
    lines.append("")
    lines.append(f"**Total Predictions Tracked:** {total_predictions}")
    lines.append(f"**Total Correct:** {total_correct}")
    lines.append(f"**Total Incorrect:** {total_predictions - total_correct}")
    lines.append(f"**Overall Accuracy:** {overall_accuracy:.1f}%")
    lines.append("")

    lines.append("## PERFORMANCE BY PROP TYPE")
    lines.append("")
    lines.append("| Prop | Correct | Total | Accuracy | Avg Error |")
    lines.append("|------|---------|-------|----------|-----------|")

    for prop, row in by_prop.iterrows():
        lines.append(f"| {prop} | {int(row['Correct'])} | {int(row['Total'])} | {row['Accuracy %']:.1f}% | {row['Avg Error']:.2f} |")

    lines.append("")
    lines.append("## DAILY RESULTS")
    lines.append("")
    lines.append("| Date | Correct | Total | Accuracy |")
    lines.append("|------|---------|-------|----------|")

    for date, row in by_date.sort_index(ascending=False).iterrows():
        lines.append(f"| {date} | {int(row['Correct'])} | {int(row['Total'])} | {row['Accuracy %']:.1f}% |")

    lines.append("")
    lines.append("## RECENT HIGHLIGHTS")
    lines.append("")

    # Get last 10 predictions
    recent = log.sort_values('date', ascending=False).head(10)

    lines.append("| Date | Player | Prop | Line | Predicted | Actual | Result |")
    lines.append("|------|--------|------|------|-----------|--------|--------|")

    for idx, row in recent.iterrows():
        result = "✅" if row['prediction_correct'] == 1 else "❌"
        lines.append(f"| {row['date']} | {row['player']} | {row['prop']} | {row['line']:.1f} | {row['predicted_value']:.1f} | {row['actual_value']:.1f} | {result} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*This is a public record of model performance.*")
    lines.append("")
    lines.append("**Model Details:**")
    lines.append("- Trained on 9,573 real NBA games")
    lines.append("- Features: Real opponent defensive ratings, injury-adjusted usage")
    lines.append("- Only tracking predictions with 70-80% confidence")
    lines.append("")

    summary_text = "\n".join(lines)

    with open(ACCURACY_SUMMARY, 'w') as f:
        f.write(summary_text)

    print(f"\n✓ Summary updated: {ACCURACY_SUMMARY}")

    # Print to console
    print("\n" + summary_text)

def view_history():
    """View detailed prediction history"""

    if not os.path.exists(ACCURACY_LOG):
        print("No tracking data yet.")
        return

    log = pd.read_csv(ACCURACY_LOG)

    print("\n" + "="*80)
    print("PREDICTION HISTORY")
    print("="*80)

    for date in sorted(log['date'].unique(), reverse=True):
        date_log = log[log['date'] == date]
        correct = date_log['prediction_correct'].sum()
        total = len(date_log)
        acc = (correct / total * 100) if total > 0 else 0

        print(f"\n{date}: {correct}/{total} ({acc:.1f}%)")

        for idx, row in date_log.iterrows():
            result = "✅" if row['prediction_correct'] == 1 else "❌"
            print(f"  {result} {row['player']:>25} {row['prop']} Over {row['line']:.1f}: Predicted {row['predicted_value']:.1f}, Actual {row['actual_value']:.1f}")

def main():
    parser = argparse.ArgumentParser(description='Track prediction accuracy')
    parser.add_argument('--date', default=None, help='Date (YYYY-MM-DD)')
    parser.add_argument('--enter-results', action='store_true', help='Enter actual results')
    parser.add_argument('--summary', action='store_true', help='Generate summary report')
    parser.add_argument('--history', action='store_true', help='View detailed history')

    args = parser.parse_args()

    ensure_directories()

    if args.enter_results:
        if not args.date:
            # Default to yesterday (since games just finished)
            args.date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        enter_results_interactive(args.date)

    elif args.history:
        view_history()

    else:
        # Default: generate summary
        generate_summary()

if __name__ == '__main__':
    main()
