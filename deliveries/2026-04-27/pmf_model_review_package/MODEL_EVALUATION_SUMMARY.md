# Model evaluation summary — 2026-04-27 late slate PMF delivery

## 1. Executive summary

This delivery is a snapshot of the standalone calibrated player-prop PMF
model for tonight's two NBA games tipping after 20:29 ET (OKC @ PHX,
21:30 ET; MIN @ DEN, 22:30 ET). The canonical export is
`player_prop_pmfs_tonight_MODEL_ONLY.parquet` — 61 rows, full PMFs per
(player × stat).

The model is role-aware and active-conditioned. Calibration was fit on
the Phase 8 walk-forward 247,625-row OOF universe (15 folds × 5 stats).
PMFs are valid (finite, non-negative, sum-to-1) for every row.

We do not claim the standalone model beats the closing market. We claim
the model is internally well-calibrated for PTS/REB/AST/TOV and FG3M
after a validated tail correction.

## 2. What is proven

- **Valid calibrated PMFs**. 247,625 / 247,625 OOF rows pass validity
  (finite, non-negative, sum-to-1, no degenerate collapse). 61 / 61
  tonight rows pass validity.
- **Role-aware calibration**. The Phase 8 calibrators are
  `RoleAwarePMFCalibrator` instances (`pmf_cal_role_*.pkl`), fit per
  stat with one global isotonic CDF map plus six per-bucket
  (`inactive_risk`, `fringe`, `bench`, `rotation`, `core`, `starter`)
  calibrators blended via shrinkage on bucket sample size.
- **Active-conditioned calibration target**. `pmf_cal_meta.json` declares
  `calibration_target = "active_conditioned_prop_live"`, version
  `role_aware_pmf_cal_v1`. Tonight's export applies
  `active_condition_pmf(raw_pmf, p_inactive)` before `cal.apply()` so the
  input distribution matches the calibrator's training contract.
- **Strong OOF calibration for PTS/REB/AST/TOV**. Stat-level NLL
  improved on every stat (Δnll −0.028 to −0.073 vs raw). Calibrated mean
  matched observed mean within ~1% on OOF for all four. Calibrated
  `p_over` at standard prop lines was within 0.005 of observed. All 30
  (stat × role_bucket) cells improved.
- **FG3M tail issue fixed via time-safe validation**. The role-aware
  calibrator over-inflated FG3M k≥7 mass (cal P(k≥7)=2.7% vs observed
  0.7%). A grid search over `k_tail ∈ {5, 7}` × `w ∈ {0.2, 0.3, 0.5, 0.7}`
  identified `k_tail=7, w=0.2` as the configuration that minimized NLL,
  tied for lowest RPS, and reduced mean error from +0.293 to +0.012 and
  P(k≥7) error from +0.020 to −0.001. Tonight's export applies this fix
  for FG3M only.

## 3. What is NOT proven

- **No standalone closing-market superiority**. A matched closing-line
  audit on 3,818 player-game-stat-line offers (with 95% bootstrap CIs)
  found the de-vigged closing market beats the standalone calibrated
  model on log-loss in 9 of 11 cohorts. Overall Δll(cal − market) =
  +0.051 [+0.039, +0.063]. A small number of narrow line ranges (REB
  3.5–4.5, AST 3.5–5.5, FG3M 1.5–2.5) tied within CI.
- **No opening-line edge proven**. The opening-line snapshots on disk
  are game totals/spreads only, not player-prop offerings. No proper
  opening → closing CLV comparison has been run.
- **No CLV claim yet**. Tonight's `market_fair_over_prob` references the
  morning predict-pipeline de-vigged consensus, not entry-time grades
  against closing lines.
- **Tonight's source is the morning run, not a final injury / lineup
  refresh**. Source `all_props_2026-04-27.parquet` mtime is
  `2026-04-27T14:27:23` ET. The local `player_availability_asof.parquet`
  had 0 rows for 2026-04-27 (last refreshed 2026-04-18). Late scratches
  and starter/inactive changes after ~14:27 ET are NOT reflected.

## 4. Accuracy / calibration summary

| Item | Result |
|---|---|
| Phase 8 OOF rows | 247,625 (15 folds × 5 stats × ~3,300 rows/fold/stat) |
| Validity failures (raw + calibrated, all stats) | 0 / 247,625 |
| Stat-level Δnll (cal − raw), all 5 stats | −0.028 to −0.073 (uniformly improved) |
| (stat × role_bucket) cells improved | 30 / 30 |
| Calibrated mean error vs observed (PTS/REB/AST/TOV) | < 1% |
| Calibrated p_over at standard prop lines | within 0.005 of observed |
| FG3M tail-shrink validated config | `k_tail=7, w=0.2` (lowest NLL, lowest RPS; mean Δ +0.012; P(k≥7) Δ −0.001) |
| Matched closing-line market eval (n=3,818) | market beats standalone cal on log-loss in 9/11 cohorts (95% CI) |
| Tonight bundle PMF validity | 61 / 61 valid; 0 model-only rows tagged with `+market_tilt` |
| Tonight `model_edge_vs_market` distribution | range [−0.264, +0.251], mean −0.077 (real disagreement preserved) |

## 5. Tonight file guide

**Canonical** (use this for standalone-model evaluation):
- `player_prop_pmfs_tonight_MODEL_ONLY.parquet`
- `player_prop_pmfs_tonight_MODEL_ONLY.csv`
- `player_prop_pmfs_tonight_MODEL_ONLY.jsonl`

In these files:
- `pmf_json` is the standalone-model PMF: active-conditioned + role-aware
  calibrated; for FG3M, plus the validated tail shrink (k≥7, w=0.2).
- `mean`, `p0`, `p_ge_*`, `p_over_line`, `p_over_line_model` are derived
  from `pmf_json`. They are NOT market-anchored.
- `pmf_source` ∈ `{cal_role_aware_v1:{role_bucket}, cal_role_aware_v1+fg3m_tail_shrink_k7_w0.2}`.
- `market_*` columns are reference fields only and do not modify
  `pmf_json`. `model_edge_vs_market = p_over_line_model − market_fair_over_prob`.

**Reference, NOT for standalone-model evaluation**:
- `player_prop_pmfs_tonight_MARKET_ANCHORED_REFERENCE.parquet` (and `.csv`, `.jsonl`)

In these files, `pmf_json` is mass-preservingly tilted so the CDF passes
through `market_fair_over_prob` at the offered line. Use only for visual
comparison of the model's PMF *shape* against a market-anchored CDF.

**Calibrator bundle**:
- `pmf_calibrators/pmf_cal_role_*.pkl` — Phase 8 role-aware calibrators
  (pts/reb/ast/tov/fg3m)
- `pmf_calibrators/pmf_cal_meta.json` — metadata (target, version,
  bucket counts)

## 6. Production roadmap

To enable proper market-beating claims and CLV measurement, the
production pipeline still needs:

- **Pre-close and close line snapshots** captured at fixed times
  (e.g., 6 PM ET pre-close, exact-tip close) for every player-prop
  offering on every game.
- **Every regular AND alternate line** for each (player × stat), not
  only the main book line. Alternate-ladder snapshots enable
  reconstruction of a market-implied PMF and head-to-head full-PMF
  comparison.
- **Odds and no-vig probabilities** from ≥3 books per offering;
  consensus de-vig with book-weighting.
- **Injury / lineup state** captured at lock time per player
  (active / questionable / out / starter / bench / minutes restriction).
- **Model PMF at lock time** — requires the predict pipeline cron to
  fire after the final inactives are posted, not at 8 AM ET.
- **Realized outcomes** + **CLV** =
  `model_prob_at_lock − closing_no_vig_prob`, graded against the actual
  stat outcome per player-game.

When these are wired together, Derek's evaluation can be a proper
time-and-state-aligned comparison. Tonight's delivery represents what
the current standalone model believes about each prop distribution; it
is NOT yet graded against closing market or actual outcomes.
