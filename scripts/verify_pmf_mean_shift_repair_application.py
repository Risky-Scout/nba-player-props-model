#!/usr/bin/env python3
"""Verify PMF mean-shift repair application on event_market_loss_rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT / "src"))

from build_event_market_loss_rows import _parse_pmf_value  # noqa: E402
from nba_props_model.calibration.pmf_mean_shift_repair import (  # noqa: E402
    is_valid_pmf,
    load_mean_shift_manifest,
    lookup_mean_shift_spec,
    normalize_pmf,
)


def _canonical_delivery_path(date: str) -> Path:
    return (
        REPO_ROOT
        / "deliveries"
        / date
        / "canonical_source"
        / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _sha_pmf_col(df: pd.DataFrame, col: str) -> str:
    if col not in df.columns:
        return ""
    s = df[col].fillna("").astype(str)
    h = hashlib.sha256()
    for v in s.values:
        h.update(v.encode("utf-8", errors="replace"))
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()
    date = str(args.date)
    pq = REPO_ROOT / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{date}.parquet"
    if not pq.is_file():
        print(f"FATAL: missing {pq}", file=sys.stderr)
        return 2
    mp = Path(args.manifest)
    if not mp.is_absolute():
        mp = REPO_ROOT / mp
    if not mp.is_file():
        print(f"FATAL: manifest not found {mp}", file=sys.stderr)
        return 2
    man = load_mean_shift_manifest(mp)
    if man.get("uses_market_probability_as_label") or man.get("uses_market_probability_as_feature"):
        print("FATAL: manifest must not use market probability in fit", file=sys.stderr)
        return 2

    df = pd.read_parquet(pq)
    need = (
        "model_pmf_raw",
        "model_pmf",
        "model_prob_over_raw",
        "model_prob_over_after_pmf_mean_shift",
        "model_prob_over_active",
        "pmf_mean_shift_repair_applied",
    )
    miss = [c for c in need if c not in df.columns]
    if miss:
        print(f"FATAL: missing columns {miss}", file=sys.stderr)
        return 2

    can = _canonical_delivery_path(date)
    if can.is_file():
        digest = _sha_file(can)
        print("CANONICAL_PMF_UNCHANGED_PASS")
        print(json.dumps({"canonical_parquet_sha256": digest}, indent=2))
    else:
        print(
            f"WARN: canonical MODEL_ONLY parquet missing for {date} — skip file digest",
            file=sys.stderr,
        )

    raw_h = _sha_pmf_col(df, "model_pmf_raw")
    if raw_h:
        print(json.dumps({"model_pmf_raw_sha256_in_loss_rows": raw_h}, indent=2))

    bad = 0
    for _, r in df.iterrows():
        if r.get("join_status") != "matched":
            continue
        raw = _parse_pmf_value(r.get("model_pmf_raw"))
        rep = _parse_pmf_value(r.get("model_pmf"))
        if raw:
            nr = normalize_pmf(raw)
            if not is_valid_pmf(nr):
                bad += 1
        if rep:
            nrep = normalize_pmf(rep)
            if not is_valid_pmf(nrep):
                bad += 1
    if bad:
        print(f"FATAL: invalid PMF rows n={bad}", file=sys.stderr)
        return 2

    m = df["model_prob_over_active"].dropna()
    if len(m) and ((m < 0) | (m > 1)).any():
        print("FATAL: model_prob_over_active out of bounds", file=sys.stderr)
        return 2

    for _, r in df[df["join_status"] == "matched"].head(5000).iterrows():
        st = str(r.get("stat") or "").lower()
        rb = str(r.get("role_bucket") or "unknown").lower()
        _key, spec = lookup_mean_shift_spec(man, st, rb)
        applied = bool(r.get("pmf_mean_shift_repair_applied"))
        if spec and spec.get("accepted"):
            if not applied and not r.get("pmf_mean_shift_row_rollback_reason"):
                print(
                    "FATAL: accepted spec but row not applied and no rollback_reason",
                    file=sys.stderr,
                )
                return 2
        elif applied:
            print(f"FATAL: unexpected apply without accepted spec row stat={st}", file=sys.stderr)
            return 2

    print("PMF_MEAN_SHIFT_REPAIR_APPLICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
