# Repair recommendations — dates_24c1750e26ad

## Failure mode counts

```
{
  "model_prob_too_high_or_overconfident_side": 29,
  "mean_too_low": 6,
  "model_logloss_not_better": 1,
  "variance_too_narrow": 1
}
```

## Ranked actions

1. **Logloss / Brier vs market:** tighten PMF location-scale calibration by stat-role on OOF; rebalance sparse tails for stl/blk.
2. **Mean vs actual:** review minutes → usage mapping and combo joint sampler means for pa/pr/ra/pra roles.
3. **Variance too narrow:** increase simulation variance or hierarchical shrinkage where segment `pmf_var_mean << actual_var`.
4. **Sample instability:** segments with low `n_loss_rows_used` should be excluded from eligibility, not verifier-gated away silently.

