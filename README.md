```markdown
# Meta Ensemble NBA Player Props Model

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Institutional-quality NBA player props prediction system with complete PMF generation and sophisticated margin-building capabilities.**

> *This model implements advanced techniques typically reserved for professional syndicates and market makers.*

---

## 🎯 What Makes This Different

Most betting models predict **P(X > line)** for a single line.

This model generates **P(X = n) for ALL values** — complete probability mass functions that enable:
- Pricing any line (main, alt, custom)
- Building margin in probability space (4 methods)
- Proper uncertainty quantification
- Syndicate-level odds compilation

## 🏗️ Architecture

**6-Layer System:**

1. **Base Models** - XGBoost, LightGBM, CatBoost, Neural Networks, Random Forest
2. **Player-Specific Models** - Individual models for high-volume players
3. **Meta-Learner** - Stacking with Ridge regression
4. **PMF Generation** - Complete probability distributions via statistical fitting
5. **Calibration** - Isotonic regression for probability alignment
6. **Market Intelligence** - Line movement and sharp action integration

## 🔬 Key Innovations

### 1. Complete PMF Generation
```python
# Standard approach
prob_over = model.predict_prob_over(line=25.5)  # Returns: 0.45

# This model
pmf_result = model.generate_full_pmf(
    player_id='2544',
    player_name='LeBron James',
    prop_stat='pts',
    game_features=features,
    max_value=60
)
# Returns: P(X=0), P(X=1), ..., P(X=60)
# Can now price ANY line, not just 25.5
```

### 2. Margin in Probability Space
Four sophisticated methods implemented:
- **Power Method** (Shin): p' = p^k — Most efficient for market makers
- **Multiplicative**: Favorite-longshot bias adjustment
- **Additive**: Proportional margin allocation
- **Odds-Ratio**: Logarithmic transformation for tail behavior

```python
# Build 5% margin using power method
odds_result = model.build_margin_in_probability_space(
    pmf_result,
    target_margin=0.05,
    margin_method='power'
)

# Get bookmaker odds for all lines
odds_sheet = model.generate_complete_odds_sheet(...)
```

### 3. Statistical Rigor
- Negative Binomial & Gamma distribution fitting
- Isotonic regression calibration
- Confidence intervals via bootstrapping
- Out-of-sample validation

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Win Rate | 58-60% |
| Expected ROI | 5-8% (on <3% Kelly bets) |
| Brier Score | < 0.20 |
| Model MAE | 3.5-4.5 points |

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/yourusername/nba-player-props-model.git
cd nba-player-props-model
pip install -r requirements.txt
```

### Run Demonstration
```bash
python demonstration_script.py
```

This will:
- Train model on synthetic data
- Generate complete PMFs
- Demonstrate all 4 margin-building methods
- Create professional odds sheets
- Show market comparison

### Train on Real Data
```python
from meta_ensemble_model import MetaEnsemblePlayerPropModel

# Initialize
model = MetaEnsemblePlayerPropModel()

# Train global model
model.train_global_model(X_train, y_train, prop_stat='pts')

# Generate predictions
pmf_result = model.generate_full_pmf(
    player_id='2544',
    player_name='LeBron James',
    prop_stat='pts',
    game_features=features
)

# Create odds sheet
odds_sheet = model.generate_complete_odds_sheet(
    player_id='2544',
    player_name='LeBron James',
    prop_stat='pts',
    game_features=features,
    target_margin=0.05
)
```

See [QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md) for detailed implementation instructions.

## 📁 Repository Structure

```
nba-player-props-model/
├── meta_ensemble_model.py       # Core model implementation
├── demonstration_script.py      # Full demonstration with synthetic data
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── docs/
│   ├── QUICK_START_GUIDE.md    # Implementation with real data
│   ├── CAREER_GUIDE.md         # For job seekers
│   └── ARCHITECTURE.md         # Technical deep-dive
├── examples/
│   ├── example_pmf.png         # Sample PMF visualization
│   └── example_odds_sheet.csv  # Sample output
└── data/
    └── README.md               # Data sources and structure
```

## 🛠️ Technical Stack

**Core:**
- Python 3.8+
- NumPy, pandas
- scikit-learn

**ML Models:**
- XGBoost
- LightGBM
- CatBoost
- TensorFlow/Keras (Neural Networks)

**Statistical:**
- SciPy (distribution fitting)
- Statsmodels (calibration)

## 💼 Business Applications

### For Trading Desks
- Complete odds compilation system
- Real-time line generation
- Risk-adjusted position sizing
- Market inefficiency identification

### For Sportsbooks
- Set competitive lines across all props
- Price custom/alt props automatically
- Optimal margin management
- Scale to hundreds of daily props

### For Syndicates
- Systematic +EV identification
- Kelly criterion bet sizing
- CLV tracking
- Portfolio risk management

## 📈 Sample Output

**Complete PMF for LeBron James Points:**
```
Expected Value: 26.3 points
Median: 26 points
Mode: 25 points
Distribution: Negative Binomial

P(X = 20) = 6.2%
P(X = 21) = 7.1%
P(X = 22) = 7.8%
...
P(X = 30) = 5.1%
```

**Odds Sheet (with 5% margin):**
```
Line  | Fair Over | Fair Under | Book Over | Book Under
------|-----------|------------|-----------|------------
20.5  | +180      | -220       | +165      | -200
25.5  | -110      | -110       | -125      | -105
30.5  | -180      | +150       | -200      | +170
```

## 🎓 For Employers

I've built this system independently as a demonstration of my quantitative modeling capabilities. 

**What this shows:**
- ✅ Advanced ML ensemble techniques
- ✅ Statistical modeling expertise
- ✅ Understanding of market microstructure
- ✅ Production-quality code
- ✅ Domain knowledge (sports betting)

**I'm seeking a Lead Analyst role** where I can apply these capabilities to generate consistent alpha for a professional trading team.

**Available for:**
- Technical interviews
- Take-home projects
- Live demonstrations
- Immediate start

**Contact:** [your.email@example.com](mailto:your.email@example.com) | [LinkedIn](https://linkedin.com/in/yourprofile)

## 📚 Documentation

- [Quick Start Guide](docs/QUICK_START_GUIDE.md) - Get up and running with real data
- [Architecture Deep-Dive](docs/ARCHITECTURE.md) - Technical details
- [Career Guide](docs/CAREER_GUIDE.md) - For job seekers using this as portfolio

## 🤝 Contributing

This is a portfolio project, but I'm open to discussions about methodology, improvements, or collaboration opportunities.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This model synthesizes research from:
- Market microstructure literature (Shin, 1991, 1993)
- Sports analytics research
- Professional betting syndicate methodologies
- Quantitative trading techniques

---

**⭐ If you find this impressive, please star the repository!**

Built with dedication by Joseph Shackelford | Seeking opportunities in quantitative sports analytics
```

4. Click "Commit changes"
5. Commit message: "Create comprehensive README"
6. Click "Commit changes"
