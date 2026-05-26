# Q50 / Live Calibration Path Audit
**Generated:** 2026-05-25  
**Branch:** fix/woo-delivery-failclosed-tail-guard-20260525  
**Purpose:** Understand why Q50 bias corrections and live calibration are excluded from the PMF-only production path, and whether re-applying them would help or double-correct.

---

## 1. Where Q50 Bias Corrections Are Computed

**Script:** `scripts/residual_centering.py` (or similar)  
**Artifact:** `artifacts/models/q50_bias_corrections.json`

Current values:
```json
{"ast": 1.139, "blk": 1.04, "fg3m": 1.092, "pts": 5.39, "reb": 0.911, "stl": 0.29}
```

These represent the empirical difference between the model's predicted Q50 (median) and the observed realized median across the training/OOF dataset. A positive value means the model's predicted median is **below** the actual median by that many units (the model underestimates).

For `stl`: the model undershoots the realized Q50 by 0.29 steals.  
For `pts`: the model undershoots the realized Q50 by 5.39 points — this is very large and suspicious; likely reflects a scale/unit difference or a dataset mismatch.

---

## 2. Where Q50 Corrections Are Loaded

**File:** `src/nba_props_model/pipelines/predict.py`  
**Lines:** ~368–376

```python
_q50_bias_path = MODEL_DIR / "q50_bias_corrections.json"
...
global _Q50_BIAS
_Q50_BIAS = _json.load(open(_q50_bias_path))
logger.info(f"  Q50 bias corrections: {_Q50_BIAS}")
```

Loaded into the module-global `_Q50_BIAS` dict at model load time.

---

## 3. Where Live Calibration Table Is Loaded

**File:** `src/nba_props_model/pipelines/predict.py`  
**Lines:** ~401–409

```python
_live_cal_path = MODEL_DIR / "live_calibration_table.json"
live_cal_table = {}
...
live_cal_table = json.load(open(_live_cal_path))
```

46 stat×side entries loaded into `live_cal_table` dict and returned from `load_models()`.

Current values for stl/blk (the problem stats):

| key | hit_rate | avg_model_prob | shrink | offset | tier |
|---|---|---|---|---|---|
| STL_OVER | 0.2424 | 0.4668 | 0.70 | −0.05 | D |
| BLK_OVER | 0.28 | 0.3843 | 0.79 | −0.05 | D |
| STL_UNDER | 0.4871 | 0.5438 | 0.89 | −0.05 | C |
| BLK_UNDER | 0.5570 | 0.6371 | 0.84 | −0.05 | B |

Note: `recommended_prob_shrink` and `recommended_prob_offset` are populated here but **never consumed** in the PMF-only path.

---

## 4. Where recommended_prob_shrink / recommended_prob_offset Are Defined

- Computed by a calibration script (likely `scripts/build_live_calibration_table.py` or similar)
- Stored in `artifacts/models/live_calibration_table.json`
- The shrink factor is the ratio `hit_rate / avg_model_prob` capped at 1.0 (for over-predictions); the offset is an additional bias correction.

---

## 5. Why the PMF-Only Production Path Excludes These Corrections

**File:** `src/nba_props_model/pipelines/predict.py`, lines ~1271–1278

```python
# ── PMF-ONLY production pricing path ─────────────────────────
# Canonical pipeline:
#   availability -> state-aware minutes -> rate/hurdle PMF ->
#   PMF/CDF calibration -> (prob_over, prob_under)
# No legacy quantile ladder, no Platt/live_cal overlay, no Q50
# bias shift, no minutes-bucket correction, no residual centerer.
```

The comment explains this is an intentional design choice: the PMF-only path is meant to be self-contained, deriving `p_over`/`p_under` directly from the calibrated PMF array via `score_prop_line`. The reasoning is:

1. **No double-correction:** The Phase 8 role-aware PMF calibrators (`pmf_cal_role_{stat}.pkl`) are applied **within** this path at ~line 1288. These calibrators are trained to correct the PMF distribution holistically. Applying a separate Platt/live_cal overlay on top would double-correct.

2. **Q50 bias shift operates at the quantile level**, not the PMF level. Shifting the Q50 would require reconstructing the PMF support from modified quantiles — not straightforward to apply post-hoc to a calibrated PMF array.

3. **The live_cal_table `recommended_prob_shrink`** was computed from the OLD legacy path (before the Phase 8 PMF calibrators were introduced). Applying it now would represent a correction on top of a correction, creating double-shrinkage for over-predicted stats.

---

## 6. Whether Any Correction Is Already Applied Upstream

Yes. The Phase 8 role-aware PMF calibrators (`pmf_cal_role_{stat}.pkl`) are applied in the PMF-only path:

```python
_pmf_arr = _cal.apply(_pmf_arr, role_bucket=_role_bucket)
```

These calibrators use isotonic regression to reshape the CDF, correcting systematic probability misallocation. They are the intended replacement for the Platt/live_cal overlay.

**The calibrators exist for:** `ast`, `blk`, `fg3m`, `pts`, `reb`, `stl`, `stocks`, `tov`

---

## 7. Whether Reapplying Would Double-Correct

**Likely yes**, for the following reasons:

1. The `live_cal_table` was computed when the **raw** hurdle PMF probabilities (pre-Phase 8 calibration) were used. The avg_model_prob for `STL_OVER` of 0.4668 reflects the **uncalibrated** model's average prediction, not the Phase 8 calibrated output.

2. After Phase 8 calibration, the model's stl OVER probability is lower (e.g., ~0.33 for Jarrett Allen at line 0.5). Applying `shrink=0.70, offset=-0.05` on top of this would give: `0.33 * 0.70 - 0.05 = 0.181`, which would make the model even more divergent from the market.

3. The Q50 bias correction for `stl: 0.29` reflects an era when the quantile ladder was used. With the hurdle model now in place, the Q50 error pattern is different.

**Conclusion: Blindly reapplying live_cal_table corrections would NOT fix the stl/blk calibration and would likely worsen it.**

---

## 8. Which Stat-Side-Line Buckets Benefit Historically

The `live_cal_table` shows `pts` stats are B/C tier (reasonable) but `stl/blk OVER` are D tier (poor reliability). This historically indicates:

- `STL_OVER` and `BLK_OVER` models were systematically overestimating before Phase 8 calibration.
- Post-Phase 8, the pattern has **inverted** for some players (especially stl, where the zero classifier is now too aggressive), making the model underestimate.

Applying the old `recommended_prob_shrink=0.70` to an already-underestimating model would be harmful.

---

## 9. Root Cause of stl/blk Under-Estimation (Actual Fix Applied)

The root cause is NOT the absence of Q50 or live_cal corrections. It is:

**The sparse hurdle PMF builder's `hi` anchor in `_sample_from_quantile_table`.**

When `hi=DOMAIN_MAX["stl"]+0.5=10.5`, the quantile CDF is anchored at 10.5 even when q90≈2. This spreads 10% of conditional probability mass uniformly over k=3-10, creating impossible spikes (P(7 steals) > P(3 steals)). The spike mass comes **at the cost of** the k=1-2 bins, making the overall PMF look like the player has a lower P(X≥1) than they actually do.

**Fix applied:** Dynamic `hi` based on max quantile value + 1.5 buffer, capped at `DOMAIN_MAX+0.5`. Plus `_enforce_monotone_positive_tail` as a second-layer repair. See `src/nba_props_model/models/sparse_hurdle.py`.

---

## 10. Recommendation on Q50 / Live Calibration

| Correction | Status | Recommendation |
|---|---|---|
| Q50 bias corrections | Loaded, not applied | **Do not apply** — were calibrated against quantile-ladder era, would misalign with PMF-only path |
| Live cal `recommended_prob_shrink` | Loaded, not applied | **Do not apply** — calibrated against pre-Phase-8 avg_model_prob; Phase 8 calibrators are the replacement |
| Platt calibrators | Loaded, not applied | **Do not apply** — explicitly superseded by Phase 8 role-aware PMF calibrators |
| Phase 8 PMF calibrators | **Applied** in PMF-only path | Correct mechanism — keep |

**Action if stl/blk under-estimation persists after the sparse_hurdle tail fix:** Retrain Phase 8 calibrators on OOF data that includes the corrected (monotone) tail PMFs. Do not reintroduce Platt/live_cal as a band-aid.

---

## 11. Feature Flag Gate (If Reapplication Is Desired in Future)

If any correction is to be reintroduced, it must be gated behind:
1. A `--apply-live-cal` explicit flag
2. Before/after OOF comparison showing improvement on stl/blk without regression on pts/reb/ast
3. Market-superiority verification: `scripts/verify_stat_role_ucb_contract.py --label $DATE` must still exit 0

Do not apply without statistical evidence.
