# Root-cause recommendations — `dates_e2c73f0cb39d`

Heuristic tags aggregate row-level `_classify_row` outputs; validate on held-out dates before model changes.

## pts|core
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0500, ΔBrier=0.0235, n=431).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## pts|starter
- **Dominant row tag:** `unknown`; **segment heuristic:** `model_prob_too_low_vs_outcome` (Δlogloss=0.1172, ΔBrier=0.0541, n=348).
  - **Repair:** lift under-side probability mass; review hurdle/p0 for low props.

## reb|core
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0221, ΔBrier=0.0073, n=274).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## reb|rotation
- **Dominant row tag:** `model_prob_too_low`; **segment heuristic:** `model_prob_too_low` (Δlogloss=0.1253, ΔBrier=0.0591, n=112).
  - **Repair:** lift under-side probability mass; review hurdle/p0 for low props.

## ast|core
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0159, ΔBrier=0.0068, n=194).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## ast|starter
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0032, ΔBrier=0.0018, n=193).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## fg3m|core
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0196, ΔBrier=0.0088, n=174).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## fg3m|starter
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0359, ΔBrier=0.0114, n=181).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## pa|starter
- **Dominant row tag:** `unknown`; **segment heuristic:** `mean_bias_pmf_vs_actual` (Δlogloss=0.0817, ΔBrier=0.0402, n=150).
  - **Repair:** align PMF location/shape with realized box scores; check role-aware means.
  - **Concentration:** book share 0.73 — verify multi-book de-vig stability.

## pr|starter
- **Dominant row tag:** `unknown`; **segment heuristic:** `mean_bias_pmf_vs_actual` (Δlogloss=0.0848, ΔBrier=0.0395, n=173).
  - **Repair:** align PMF location/shape with realized box scores; check role-aware means.
  - **Concentration:** book share 0.77 — verify multi-book de-vig stability.

## ra|core
- **Dominant row tag:** `unknown`; **segment heuristic:** `distribution_mismatch_unclassified` (Δlogloss=0.0149, ΔBrier=0.0110, n=106).
  - **Repair:** inspect top `worst_rows` for book/snapshot concentration; consider line transform audit and minutes/role join quality.

## pra|starter
- **Dominant row tag:** `unknown`; **segment heuristic:** `mean_bias_pmf_vs_actual` (Δlogloss=0.0658, ΔBrier=0.0300, n=226).
  - **Repair:** align PMF location/shape with realized box scores; check role-aware means.
  - **Concentration:** book share 0.62 — verify multi-book de-vig stability.
