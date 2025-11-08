git add BACKTEST_SUMMARY.md
git commit -m "Add backtest results summary"
git push origin main
cd ~/Desktop/nba-player-props-model
git checkout main
git pull origin main

# Create the data files manually
# The data is too big to paste, so download from GitHub
curl -o data/nba_data_2024.csv https://raw.githubusercontent.com/Risky-Scout/nba-player-props-model/52e70f14841b272d154b3a38398dae393754305b/data/nba_data_2024.csv

# Or just regenerate it (takes 10 seconds)
python generate_sample_nba_data.py --games 2000 --output data/nba_data_2024.csv

# Then commit
git add data/nba_data_2024.csv
git commit -m "Add NBA training data (2,000 games)"
git push origin main
