#!/usr/bin/env bash
set -euo pipefail

mkdir -p .cursor/rules
mkdir -p .cursor/agents
mkdir -p scripts

cat > .cursor/rules/nba-pmf-market-superiority.mdc <<'EOF'
---
alwaysApply: true
---

# NBA PMF market-superiority rules

Target branch:
m8-6-calibration-market-superiority-20260512

The model predicts a full discrete PMF q_i(k) for NBA player prop outcome X_i.

For every eligible stat × role_bucket cell c, market superiority requires:

UCB95(model_logloss - market_logloss) < -0.0025

and

UCB95(model_brier - market_brier) < -0.0010

Lower loss is better. Therefore model-minus-market deltas must be negative.

Calibration gate:

ECE_c <= 0.025
PIT_KS_c <= 0.075
abs(mean_error_c) <= 0.15
abs(variance_error_c) <= 0.20

Never claim market superiority unless scripts/verify_stat_role_ucb_contract.py exits 0.

Never improve metrics by:
- dropping losing stat-role cells
- filtering hard rows
- using post-outcome features
- using full-data OOF leakage
- changing thresholds to pass
- using closing odds for earlier snapshots unless that snapshot is close-lock

When fixing failures, classify each failing stat-role cell as one of:

1. mean bias
2. variance / dispersion failure
3. p0 / hurdle failure
4. threshold-CDF calibration failure
5. role/minutes failure
6. sharpness failure versus market
7. insufficient sample

Preferred repair order:

1. fix leakage
2. fix PMF validity
3. fix p0/hurdle for sparse roles
4. fix CDF threshold calibration
5. fix mean shift
6. fix variance temperature
7. fix role/minutes features
8. only then test guarded market anchoring

Required verification after any change:

python -m compileall src scripts
python scripts/build_event_market_loss_rows.py --date 2026-05-12
python scripts/build_stat_role_market_superiority_report.py --date 2026-05-12 --include-ineligible --min-scored-rows 100 --min-market-joined-rows 100
python scripts/verify_stat_role_ucb_contract.py --label 2026-05-12 --min-n 100
EOF

cat > .cursor/agents/calibration-theorist.md <<'EOF'
---
name: calibration-theorist
description: Use for PMF calibration, ECE, PIT KS, CDF calibration, p0/hurdle calibration, mean shift, variance temperature, and stat-role calibration gates.
model: inherit
readonly: false
---

You are a probability calibration theorist for discrete NBA player-prop PMFs.

Your goal is to make every eligible stat × role_bucket cell satisfy:

ECE <= 0.025
PIT_KS <= 0.075
abs(mean_error) <= 0.15
abs(variance_error) <= 0.20

and help market superiority:

UCB95(model_logloss - market_logloss) < -0.0025
UCB95(model_brier - market_brier) < -0.0010

Workflow:

1. Read the latest calibration and market-superiority artifacts.
2. Rank failing stat-role cells by severity.
3. Diagnose each failure as:
   - mean bias
   - variance/dispersion
   - p0/hurdle
   - CDF/ECE
   - role/minutes
   - sharpness versus market
   - insufficient sample
4. Implement the smallest safe repair.
5. Preserve PMF validity:
   - finite probabilities
   - nonnegative probabilities
   - sum to 1
   - monotone CDF
6. Run the verification commands.

Do not claim success unless the verifier passes.
EOF

cat > .cursor/agents/feature-overhaul-engineer.md <<'EOF'
---
name: feature-overhaul-engineer
description: Use for feature engineering that improves NBA PMF accuracy by stat and role: minutes, usage, lineup, injury, opponent, pace, market, sparse-stat, and role features.
model: inherit
readonly: false
---

You are an NBA player-prop feature engineer.

Your goal is not generic accuracy. Your goal is lower OOF PMF loss and lower market-relative event loss in every eligible stat × role_bucket cell.

Target inequality:

UCB95(model_logloss - market_logloss) < -0.0025
UCB95(model_brier - market_brier) < -0.0010

Feature priorities by stat:

PTS:
- projected minutes distribution
- usage under current lineup
- teammate-out usage transfer
- implied team total
- pace
- spread / blowout risk
- starter confirmation
- market line / no-vig probability when timestamp-valid

REB:
- rebound opportunity
- opponent missed-shot volume
- opponent shot profile
- frontcourt teammate availability
- minutes volatility
- blowout risk

AST:
- ballhandler role
- teammate shot-making
- lineup without primary initiators
- potential assists proxy
- pace
- team total
- opponent assist profile

FG3M:
- 3PA rate
- minutes and usage volatility
- opponent 3PA allowed
- p0/hurdle for low-minute roles
- high-volume shooter tail control

Inactive/fringe/bench:
- P(active)
- P(minutes bucket)
- conditional PMF if active
- strong shrinkage
- explicit zero-mass calibration

Accept a feature only if it improves walk-forward OOF loss and does not worsen worst-cell market-relative UCB.
EOF

cat > .cursor/agents/market-superiority-verifier.md <<'EOF'
---
name: market-superiority-verifier
description: Use after every calibration or feature change to verify strict stat-role market-superiority inequalities.
model: inherit
readonly: true
---

You are a skeptical market-superiority verifier.

Verify for every eligible stat × role_bucket cell:

UCB95(model_logloss - market_logloss) < -0.0025
UCB95(model_brier - market_brier) < -0.0010

Procedure:

1. Read event market loss rows.
2. Compute row-level model-minus-market logloss delta.
3. Compute row-level model-minus-market Brier delta.
4. Bootstrap mean delta inside each stat-role cell.
5. Compute 95% upper confidence bound.
6. Fail any eligible cell whose upper bound is not below the negative margin.
7. Report exact failing cells.

Do not edit code.
Do not relax thresholds.
Do not ignore losing cells.
EOF

cat > scripts/verify_stat_role_ucb_contract.py <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_loss_rows(label: str) -> pd.DataFrame:
    candidates = [
        REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet",
        REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.csv",
    ]
    for p in candidates:
        if p.exists():
            if p.suffix == ".parquet":
                return pd.read_parquet(p)
            return pd.read_csv(p)
    raise SystemExit(f"Could not find event market loss rows for label/date {label}")


def bootstrap_ucb95(x: np.ndarray, reps: int, seed: int) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan
    mean = float(np.mean(x))
    if len(x) == 1:
        return mean, mean

    rng = np.random.default_rng(seed)
    n = len(x)
    boot = np.empty(reps, dtype=float)

    for j in range(reps):
        idx = rng.integers(0, n, size=n)
        boot[j] = float(np.mean(x[idx]))

    return mean, float(np.quantile(boot, 0.95))


def pick_col(df: pd.DataFrame, names: list[str]) -> str:
    for n in names:
        if n in df.columns:
            return n
    raise SystemExit(f"Missing one of required columns: {names}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--min-n", type=int, default=100)
    ap.add_argument("--tau-logloss", type=float, default=0.0025)
    ap.add_argument("--tau-brier", type=float, default=0.0010)
    ap.add_argument("--bootstrap-reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260512)
    args = ap.parse_args()

    df = read_loss_rows(args.label)

    if "join_status" in df.columns:
        df = df[df["join_status"].astype(str).eq("matched")].copy()

    stat_col = pick_col(df, ["stat", "prop_stat"])
    role_col = "role_bucket" if "role_bucket" in df.columns else None

    model_logloss_col = pick_col(df, ["model_event_logloss", "model_logloss", "model_nll"])
    market_logloss_col = pick_col(df, ["market_event_logloss", "market_logloss", "market_nll"])
    model_brier_col = pick_col(df, ["model_brier", "model_event_brier"])
    market_brier_col = pick_col(df, ["market_brier", "market_event_brier"])

    if role_col is None:
        df["role_bucket"] = "unknown"
        role_col = "role_bucket"

    rows = []
    failures = []

    group_keys = [
        df[stat_col].astype(str).str.lower(),
        df[role_col].fillna("unknown").astype(str),
    ]

    for (stat, role), sub in df.groupby(group_keys, dropna=False):
        s = sub[
            sub[model_logloss_col].notna()
            & sub[market_logloss_col].notna()
            & sub[model_brier_col].notna()
            & sub[market_brier_col].notna()
        ].copy()

        n = int(len(s))

        d_log = (
            pd.to_numeric(s[model_logloss_col], errors="coerce")
            - pd.to_numeric(s[market_logloss_col], errors="coerce")
        ).to_numpy()

        d_brier = (
            pd.to_numeric(s[model_brier_col], errors="coerce")
            - pd.to_numeric(s[market_brier_col], errors="coerce")
        ).to_numpy()

        row_seed = args.seed + len(rows) * 31
        log_mean, log_ucb = bootstrap_ucb95(d_log, args.bootstrap_reps, row_seed)
        brier_mean, brier_ucb = bootstrap_ucb95(d_brier, args.bootstrap_reps, row_seed + 1)

        eligible = n >= args.min_n
        log_pass = bool(log_ucb < -args.tau_logloss) if np.isfinite(log_ucb) else False
        brier_pass = bool(brier_ucb < -args.tau_brier) if np.isfinite(brier_ucb) else False
        gate_pass = bool(eligible and log_pass and brier_pass)

        if not eligible:
            reason = "insufficient_n"
        elif not log_pass:
            reason = "logloss_ucb_not_better"
        elif not brier_pass:
            reason = "brier_ucb_not_better"
        else:
            reason = ""

        row = {
            "label": args.label,
            "stat": stat,
            "role_bucket": role,
            "n": n,
            "eligible": eligible,
            "logloss_delta_mean_model_minus_market": log_mean,
            "logloss_delta_ucb95_model_minus_market": log_ucb,
            "brier_delta_mean_model_minus_market": brier_mean,
            "brier_delta_ucb95_model_minus_market": brier_ucb,
            "tau_logloss": args.tau_logloss,
            "tau_brier": args.tau_brier,
            "gate_pass": gate_pass,
            "failure_reason": reason,
        }

        rows.append(row)

        if eligible and not gate_pass:
            failures.append(row)

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics" / f"stat_role_ucb_contract_{args.label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out = pd.DataFrame(rows).sort_values(
        ["eligible", "gate_pass", "stat", "role_bucket"],
        ascending=[False, True, True, True],
    )
    out.to_csv(out_dir / "stat_role_ucb_contract.csv", index=False)

    pd.DataFrame(failures).to_csv(out_dir / "failures.csv", index=False)

    eligible_df = out[out["eligible"] == True]
    summary = {
        "label": args.label,
        "min_n": args.min_n,
        "eligible_cells": int(len(eligible_df)),
        "passed_cells": int(eligible_df["gate_pass"].sum()) if len(eligible_df) else 0,
        "failed_cells": int((~eligible_df["gate_pass"]).sum()) if len(eligible_df) else 0,
        "global_pass": bool(len(eligible_df) > 0 and eligible_df["gate_pass"].all()),
        "tau_logloss": args.tau_logloss,
        "tau_brier": args.tau_brier,
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"wrote {out_dir}")

    if failures:
        print("\nWorst failing cells:")
        fail_df = pd.DataFrame(failures)
        fail_df["badness"] = (
            fail_df["logloss_delta_ucb95_model_minus_market"].clip(lower=0)
            + fail_df["brier_delta_ucb95_model_minus_market"].clip(lower=0)
        )
        cols = [
            "stat",
            "role_bucket",
            "n",
            "failure_reason",
            "logloss_delta_ucb95_model_minus_market",
            "brier_delta_ucb95_model_minus_market",
        ]
        print(fail_df.sort_values("badness", ascending=False)[cols].head(20).to_string(index=False))

    return 0 if summary["global_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x scripts/verify_stat_role_ucb_contract.py

echo "Installed core Cursor NBA PMF market-superiority plugins."
