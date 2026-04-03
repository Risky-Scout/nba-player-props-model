# NBA Props Model

Player prop markets are priced by books that have access to the same box scores, injury reports, and line movement data you do. The edge, if it exists, comes from building a better conditional distribution — not from finding information asymmetry. This model is an attempt to do that rigorously.

The core question is not "will this player go over?" It's "does the market's implied probability materially differ from the true probability, and in which direction?" CLV is the primary performance metric for exactly this reason. Win rate on -110 juice is close to meaningless at sample sizes under a few thousand picks.

**Live output:** [dev.wizardofodds.com](https://dev.wizardofodds.com/tools/odds-scanner/predictions/nba-props.html)

---

## What the model actually does

It trains 11 independent LightGBM quantile regressors per stat target at τ ∈ {0.10, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90}, yielding a full conditional distribution for each player-game-stat combination. The probability that a player exceeds any posted line is recovered by piecewise linear CDF interpolation between adjacent quantile knots — no parametric assumptions about the shape of the distribution.

This matters because player stat distributions are not Gaussian. Points distributions are roughly lognormal with a left tail from DNPs. Blocks and steals are zero-inflated with high right skew. FG3M is a mixture of a point mass at zero (players who don't attempt) and a Binomial conditional on attempts. A model that assumes normality is wrong in ways that compound at the tails, which is exactly where the high-EV lines live.

The FG3M market gets its own two-part hurdle model: a calibrated classifier for P(attempts ≥ 1) and a Binomial model for P(makes ≥ k | attempts), with archetype-aware shrinkage priors (non-shooting big / low-volume wing / moderate shooter / high-volume shooter). Direct quantile regression on a zero-inflated count with this much heterogeneity produces badly miscalibrated tails.

---

## Architecture

### Data pipeline
BallDontLie GOAT API provides box scores, advanced tracking stats, and injury reports. The Odds API provides consensus totals, spreads, and implied team totals via daily morning snapshots. ~840k training rows covering 797 players from 2023 to present. Advanced stats backfill: 364k per-game rows deduped to the period=0 game-total row — periods 1-4 are per-quarter splits that inflate row counts and corrupt rolling windows if not filtered.

### Feature engineering
The design philosophy is: rolling windows for player-side features, EWMA for opponent defensive environment. Per-minute rates are computed for all counting stats before rolling — this separates the minutes effect from the efficiency effect and lets the model price each independently. The minutes model runs first and injects its full projected distribution (mp_q25, mp_q75, mp_pred_floor, mp_pred_ceiling, mp_vol, exp_mp) as features into every downstream stat model.

Opponent defensive features are computed at team-game level, not player-game level. Using player-game level averages inflates the denominator by roughly 10x and produces factor features that are meaningless. The EWMA over the opponent's last 10 game-level allowed totals is the correct construction — a true exponentially weighted moving average with alpha=0.15, not a plain average mislabeled as EWMA.

Market features: implied team total, consensus spread, and has-market-data flag are injected per game via a team-date keyed index. When no odds are available the quantile distribution is shrunk 30% toward the median — the EV calculation is unreliable without a market anchor and picks should reflect that uncertainty.

Zero-inflation features for sparse stats: P(stl=0), P(blk=0), P(tov=0), P(fg3m=0) over the last 10 games. These directly encode the structural mass at zero that LightGBM must otherwise infer from the feature space.

### Training
Strict temporal holdout — no shuffling, split computed on sorted unique dates. Walk-forward OOS calibration across 28-day folds with season boundaries respected. Production model is refit on all available data through yesterday before deployment.

After training: FG3M hurdle model fit on the fg3m subset, residual centerer fit on graded history, Platt calibrators refit on walk-forward OOF predictions. All automated via GitHub Actions retrain workflow.

### Prediction
1. Fetch prop lines and game odds from BallDontLie and The Odds API
2. Build feature vector per player using rolling history through yesterday
3. Project Q10→Q90 via quantile ensemble, enforce monotonicity
4. Apply residual centering — systematic bias correction learned from graded history
5. CDF interpolation to produce P(over) and P(under) at posted line
6. Platt scaling — stat-side specific when sufficient graded data, global OVER/UNDER otherwise
7. EV calculation against vig-free market probability
8. Kelly sizing at 15% fraction, hard cap at 1.5 units per single
9. Portfolio limits: 25 picks/day, 2/player, 4/game

SGPs priced via Gaussian copula on within-player residual z-scores, sampled with 50k Monte Carlo draws after Cholesky decomposition of the PSD-projected correlation matrix.

### Daily schedule
- 8:00 AM ET — predictions generated and graded picks from prior day scored
- 9:00 AM ET — opening line snapshot captured
- 6:00 PM ET — closing line snapshot captured for CLV computation

---

## Performance

The model entered full production on April 3, 2026 following a complete data pipeline rebuild. CLV and win rate tracking begins from this date. Prior paper trading results are not reported — the previous pipeline had two silent data failures that made those results invalid as a measure of the current model's capability. Forward performance is tracked in `graded/performance_log.csv`.

CLV is the primary metric. A model with positive mean CLV is finding prices that the sharpest market participants subsequently confirm by moving the line in the predicted direction. That is the professional standard for demonstrating genuine edge.

---

## What is still missing

Position-specific opponent matchup features would materially improve blocks and steals. A center facing the Pacers should have different defensive context than a center facing the Grizzlies, even if both teams allow similar raw block totals.

Learned EWMA alphas per stat — alpha=0.15 is applied uniformly. The optimal recency weight almost certainly differs between minutes (high temporal stability) and blocks (high game-to-game variance).

NBA Stats API integration for play-type data — post touches, pick-and-roll frequency, contested vs open shot rates — would improve the FG3M and 3PA models specifically.

On/off splits for key teammates. When the primary ball-handler sits, assist numbers for everyone else change dramatically. The injury vacancy features model this coarsely but not at the pairing level.

---

## Repository
```
train.py                    Main training pipeline
predict.py                  Daily prediction pipeline
feature_engineering.py      Feature computation and game context
correlation_engine.py       Within-player correlation, SGP pricing
minutes_model.py            Minutes projection model (LightGBM quantile)
fg3m_hurdle.py              Two-part hurdle model for 3PM
residual_centering.py       Learned bias correction from graded history
calibrate_stat_side.py      Walk-forward Platt calibration pipeline
grade.py                    Nightly grading, CLV computation, diagnostics
bdl_client.py               BallDontLie GOAT API client
retrospective_features.py   Leakage-free role and absence features
historical_odds_backfill.py Odds API historical fetch
snapshot_opening_lines.py   Opening line snapshots (9 AM ET)
snapshot_closing_lines.py   Closing line snapshots (6 PM ET)
```

Data in `data/` as Parquet. Trained artifacts in `model_cache/`. Daily predictions in `predictions/`. Graded results in `graded/`.

Retrain runs on manual dispatch and weekly schedule via GitHub Actions. Daily predictions run automatically at 8 AM ET.
