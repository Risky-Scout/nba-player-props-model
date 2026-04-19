# NBA Props Model — Architecture (post-rebuild)

This document describes the architecture of the rebuilt NBA Props Model
as it stands after Phases 1 through 9 of the rebuild. It is authoritative
for anyone new to the codebase and for any future Claude Code session
that needs a single page to come up to speed.

## 1. The question the model tries to answer

For every player-game-stat combination that appears in the offered
market on a given day, output:

  1. a calibrated discrete PMF over the integer stat support,
  2. a fair over/under probability at every offered line,
  3. fair American odds,
  4. an uncertainty tier,
  5. a calibrator version tag.

Model quality is judged on the PMF, not on bet P&L. Bet-selection
decisions happen in a layer downstream and do not mutate the model's
probabilities.

## 2. End-to-end data + inference flow

```
                 data/nba_injury_reports.parquet
                 data/player_game_stats.parquet
                 data/player_positions.parquet
                            │
                            ▼
         nba_props_model.features.availability_asof
                            │
               data/player_availability_asof.parquet
                            │
                            ▼
         ┌─────────────────┴─────────────────┐
         │                                    │
    training path                        prediction path
         │                                    │
         ▼                                    ▼
 state-aware minutes model ◄──┐     state-aware minutes model
 minutes_state_classifier     │         (inference)
 minutes_limited_q*           │              │
 minutes_normal_q*            │              ▼
                              │       MinutesDistribution
 rate quantile models   ──────┤              │
 rate_{pts,reb,ast,tov}_q*    │              ├──────────────┐
                              │              │              │
 sparse hurdle models    ─────┤              │              │
 hurdle_{stl,blk}_zero        │              │              │
 hurdle_{stl,blk}_pos_q*      │              │              │
                              │     ┌────────┴────┐   ┌─────┴─────┐
 FG3M hurdle            ──────┤     │  main stats │   │  sparse   │
                              │     │  simulation │   │  hurdle   │
 correlation engine    ───────┤     │ (pts, reb,  │   │ (stl, blk,│
 (within-player Sigma)        │     │  ast, tov)  │   │  stocks)  │
                              │     └──────┬──────┘   └─────┬─────┘
 pmf_calibration       ◄──────┘            │                │
 pmf_cal_{stat}.pkl               ┌────────┴────────────────┤
                                  │        combos            │
                                  │  pra, pr, pa, ra         │
                                  │  (via copula on main     │
                                  │   stats using the        │
                                  │   correlation engine)    │
                                  └─────────────┬────────────┘
                                                │
                                                ▼
                                  ┌─────────────────────────┐
                                  │  per-stat calibrated PMF │
                                  │  nba_props_model.pipelines│
                                  │      .pmf_predict         │
                                  └─────────────┬────────────┘
                                                │
                                                ▼
                                  ┌─────────────────────────┐
                                  │  bet-selection layer     │
                                  │  nba_props_model         │
                                  │      .selection          │
                                  └─────────────┬────────────┘
                                                │
                                                ▼
                                     predictions/{date}/*.json
                                     predictions/all_props_*.parquet
```

## 3. Module responsibilities

### nba_props_model/features
- `engineering.py` — legacy 1932-line feature monolith. Stable surface:
  `build_player_game_features`, `get_feature_cols_for_stat`, `STATS`,
  `COMBO_STATS`, `ALL_TARGETS`. Split incrementally as phases touch
  specific feature families.
- `retrospective.py` — role and absence features used in training.
- `availability_asof.py` — the Phase 2 rebuild: strict as-of
  availability + teammate-absence features. Output table is
  `data/player_availability_asof.parquet`. Features emitted per row:
  availability_status, prob_active, confidence tier, games_since_last_played,
  days_since_last_played, is_returning_from_absence,
  minutes_restriction_flag, num_teammates_out_total, vacated_fga_total,
  plus per-archetype teammate_out_count_* and vacated_minutes_*.

### nba_props_model/models
- `minutes.py` — state-aware minutes. Binary classifier for
  P(normal | active); conditional LightGBM quantile ladders for LIMITED
  and NORMAL states. `MinutesDistribution` object exposes cdf,
  quantile, mean, std, sample. P(INACTIVE) sourced from
  availability.prob_active so the three-way state distribution is
  honest about what the box-score history can and cannot observe.
  Back-compat `predict_minutes(...)` dict keys preserved.
- `rate_models.py` — per-minute rate quantile ladders for
  `pts, reb, ast, tov`. Training: `train_rate_models(training_df)`.
  Inference: `rate_quantiles(stat, feature_row)` returns the ladder
  the simulation layer samples from.
- `simulation.py` — `MinutesDistribution × per-minute rate` →
  discrete stat PMF. `StatPMF` object carries cdf/prob_over/prob_under.
  A Poisson noise layer discretises the rate-times-minutes continuous
  total into an integer count.
- `sparse_hurdle.py` — hurdle models for `stl`, `blk`. P(zero)
  classifier plus conditional positive-count quantile ladder. Full
  PMF returned by `hurdle_pmf`. `stocks_pmf` derives stl+blk via
  discrete convolution of component PMFs — **never** an independent
  direct model.
- `fg3m_hurdle.py` — three-stage archetype-aware hurdle. Now exposes
  `.pmf(features)` returning the full {0, ..., 15} discrete PMF.
- `combos.py` — `pra, pr, pa, ra` PMFs derived from component PMFs.
  Two modes: independence convolution, Gaussian-copula simulation
  using the within-player residual-correlation matrix from the SGP
  correlation engine. Combos are **derived**, never directly modeled.

### nba_props_model/calibration
- `pmf_calibration.py` — walk-forward CDF-level isotonic calibration,
  per stat. Training signal: randomized PIT values aggregated across
  28-day OOF folds. Monotone-preserving by construction.
- `stat_side_platt.py` — legacy side-level Platt. **Retained only as
  a diagnostic fallback** during the rebuild transition.
- `residual_centering.py` — learned additive bias correction from
  graded history.

### nba_props_model/correlation
- `sgp_engine.py` — within-player residual correlation matrix,
  Gaussian copula SGP pricing, and utilities consumed by
  `combos.py` for copula-based within-game combo derivation.

### nba_props_model/selection
- `bet_selection.py` — pure filter pipeline. Edge threshold,
  probability floor, sparse-stat transitional floor, liquidity gate,
  vig ceiling, disagreement cap. Portfolio caps: singles/day,
  singles/player, singles/game. Every rejection carries a structured
  reject_reason so `evaluation.diagnostics` can report abstention
  breakdown.

### nba_props_model/evaluation
- `grading.py` — nightly grading and CLV (unchanged from v1).
- `diagnostics.py` — full-universe diagnostics for walk-forward
  OOS evaluation. log_score, discrete CRPS, randomized PIT + KS,
  Brier, ECE, calibration slope/intercept, market-relative log-score
  lift, edge-decile monotonicity, bootstrap ROI CIs. Report written
  to `artifacts/docs/diagnostics_{date}.md`.

### nba_props_model/pipelines
- `train.py` — training orchestration. Currently trains the
  state-aware minutes model, the legacy quantile ladder, the FG3M
  hurdle, the correlation engine, and the residual centerer. Rate
  models and sparse-stat hurdle training are called via their
  public `train_*` functions; see MIGRATION.md for the wire-up.
- `predict.py` — live daily prediction. Produces `singles_*`,
  `sgps_*`, `pmf_display_*`, `all_props_*.parquet`. Reads legacy
  quantile artifacts and the state-aware minutes artifacts.
- `pmf_predict.py` — new PMF-first orchestration. Builds per-player
  PMFs across all stats, applies `pmf_calibration`, scores against
  offered lines, invokes `bet_selection`. Silently no-ops when its
  upstream artifacts are missing.

## 4. Artifact layout

```
artifacts/models/
    minutes_state_classifier.pkl        binary (normal | active)
    minutes_state_aware_features.pkl    feature order
    minutes_state_aware_meta.json       training diagnostics
    minutes_limited_q{10,25,50,75,90}.pkl
    minutes_normal_q{10,25,50,75,90}.pkl

    minutes_q{10..90}.pkl               legacy quantile ladder (fallback)
    minutes_features.pkl                legacy feature order (fallback)

    rate_{pts,reb,ast,tov}_q{10..90}.pkl
    rate_{pts,reb,ast,tov}_features.pkl
    rate_models_meta.json

    hurdle_{stl,blk}_zero.pkl           binary zero-classifier
    hurdle_{stl,blk}_pos_q{10..90}.pkl  conditional positive quantiles
    hurdle_{stl,blk}_features.pkl
    hurdle_sparse_meta.json

    fg3m_hurdle.pkl                     three-stage archetype hurdle

    pmf_cal_{stat}.pkl                  per-stat isotonic CDF calibrator
    pmf_cal_meta.json

    within_player_corr_engine.pkl       residual correlation matrices
    correlation_audit.json

    platt_{over,under}.pkl              diagnostic fallback only

    residual_centerer_{pts,reb,ast,fg3m}.pkl
    residual_scaler_{pts,reb,ast,fg3m}.pkl

    q{10..90}_{stat}.pkl                legacy direct-total quantile ladder,
    features_{stat}.pkl                 retained during the transition
                                        (deprecated by pmf_predict)

artifacts/graded/                       graded history + closing-line snapshots
artifacts/docs/                         diagnostics reports

data/                                   raw + as-of historical data
predictions/                            daily outputs (web/SFTP path)
```

## 5. Contract summary

| Caller | Function | Input | Output |
|---|---|---|---|
| train.py | minutes.train_minutes_model(stats_df) | box-score + availability | state-aware pkls |
| train.py | rate_models.train_rate_models(training_df) | engineered per-player-game | rate_*.pkl |
| train.py | sparse_hurdle.train_sparse_hurdle(training_df) | engineered per-player-game | hurdle_*.pkl |
| train.py | fg3m_hurdle.FG3MHurdleModel().fit(fg3m_df) | fg3m subset | fg3m_hurdle.pkl |
| train.py | pmf_calibration.fit_all(per_stat_inputs) | OOF pmfs+outcomes+dates | pmf_cal_*.pkl |
| predict.py | minutes.minutes_distribution(...) | prior stats + avail | MinutesDistribution |
| predict.py | pmf_predict.build_prop_pmfs(...) | MinutesDistribution + features | {stat: PropPMF} |
| predict.py | pmf_predict.score_full_universe(...) | universe + PMFs + market | DataFrame |
| grade.py | evaluation.diagnostics.evaluate_fold(...) | pmfs + outcomes + market | FoldMetrics |

## 6. Principles enforced

- **No silent NaN.** Every feature either has a value or an explicit
  confidence tier.
- **No train/inference mismatch.** Availability features are joined
  from the same `data/player_availability_asof.parquet` table in both
  paths.
- **No post-hoc side calibration as the primary correction.** Side-
  level Platt is retained only as a diagnostic fallback; the primary
  correction is CDF-level isotonic calibration on the full universe.
- **Sparse stats are hurdle / zero-inflated.** No ordinary quantile
  regression on stl/blk. `stocks` derives from the component PMFs.
- **Combos are derived, not modeled.** pra/pr/pa/ra come from component
  PMFs via the correlation engine.
- **Main stats are generated, not direct.** pts/reb/ast/tov PMFs come
  from minutes × per-minute rate simulation.
- **Walk-forward OOF only.** All calibration and evaluation splits
  respect game_date strictly.

## 7. What the model still does not do

See the "Frank statement" section of MIGRATION.md.
