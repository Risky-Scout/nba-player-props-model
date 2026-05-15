# Guarded event calibration rollback diagnosis — dates_24c1750e26ad

- **selected (summary):** n_selected=0
- **rollbacks (summary):** n_rollbacks=32

## Methods attempted (candidate_results)

```
{
  "none": 12
}
```

## Rollback reasons

```
{
  "small_fold": 16,
  "rollback_fold_worse": 14,
  "insufficient_rows_or_no_dates": 2
}
```

## Interpretation

- **`rollback_fold_worse`:** calibrator improved in-sample but hurt held-out logloss/Brier → treat as **overfit / too few fold rows**.
- **`small_fold`:** not enough dated rows per segment for stable CV.
- **Next candidate types:** lighter Platt / temperature scaling with stronger L2; hierarchical pooling across stat; skip line-aware until base passes.

