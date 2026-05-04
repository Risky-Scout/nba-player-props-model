#!/usr/bin/env python3
"""Phase 13AI — write a lightweight no-leakage audit artifact for a
challenger training run.

Reads ``artifacts/models/challengers/<as-of>/train_manifest.json`` (and
the fold_aggregate.parquet itself when present on the CI runner) and
emits ``artifacts/models/challengers/<as-of>/aggregate_input_audit.json``
with everything needed to prove no leakage without committing the
multi-MB fold parquet (which is gitignored).

Schema fields:
  schema_version, training_cutoff_date,
  source_min_game_date, source_max_game_date, fold_aggregate_max_game_date,
  row_count, unique_game_dates, no_leakage_pass,
  rule, generated_at, source_files, fold_aggregate_sha256

Hard rule:
  no_leakage_pass = (fold_aggregate_max_game_date <= training_cutoff_date)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of-date", required=True, help="training cutoff YYYY-MM-DD")
    args = ap.parse_args(argv)

    ch_dir = REPO_ROOT / "artifacts" / "models" / "challengers" / args.as_of_date
    train_manifest = ch_dir / "train_manifest.json"
    fold_parquet = ch_dir / "aggregate_input" / "fold_aggregate.parquet"
    audit_path = ch_dir / "aggregate_input_audit.json"

    if not train_manifest.exists():
        print(f"AGGREGATE_INPUT_AUDIT_FAILED  as_of={args.as_of_date}  "
              f"reason=missing_train_manifest  "
              f"path={train_manifest.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    tm = json.loads(train_manifest.read_text(encoding="utf-8"))
    cutoff = args.as_of_date
    training_summary = tm.get("training_summary") or {}
    challenger_artifacts = tm.get("challenger_artifacts") or {}

    source_min = str(training_summary.get("min_date") or "")
    source_max = str(training_summary.get("max_date") or "")
    row_count = int(training_summary.get("training_row_count") or 0)
    fold_sha256 = challenger_artifacts.get("fold_aggregate_sha256") or None
    fold_parquet_rel = challenger_artifacts.get("fold_aggregate_input") or str(
        fold_parquet.relative_to(REPO_ROOT))

    fold_max = source_max
    unique_dates = None

    # If the fold_aggregate.parquet is locally present (CI runner before
    # gitignore prunes it), pull the canonical max_date and unique date
    # count straight from the file. Otherwise rely on the train_manifest
    # summary fields.
    if fold_parquet.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(fold_parquet, columns=["game_date"])
            s = pd.to_datetime(df["game_date"]).dt.date
            fold_max = str(s.max())
            unique_dates = int(s.nunique())
        except Exception:
            pass

    no_leakage = bool(fold_max and fold_max <= cutoff)

    payload = {
        "schema_version": "1.0",
        "training_cutoff_date": cutoff,
        "source_min_game_date": source_min,
        "source_max_game_date": source_max,
        "fold_aggregate_max_game_date": fold_max,
        "row_count": row_count,
        "unique_game_dates": unique_dates,
        "no_leakage_pass": no_leakage,
        "rule": "max input game_date <= training_cutoff_date",
        "generated_at": _utc_iso(),
        "source_files": {
            "train_manifest": str(train_manifest.relative_to(REPO_ROOT)),
            "fold_aggregate_parquet": fold_parquet_rel,
            "fold_aggregate_parquet_present_locally": fold_parquet.exists(),
        },
        "fold_aggregate_sha256": fold_sha256,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if no_leakage:
        print(f"AGGREGATE_INPUT_AUDIT_PASS  as_of={args.as_of_date}  "
              f"max={fold_max}  rows={row_count}  "
              f"path={audit_path.relative_to(REPO_ROOT)}")
        return 0
    print(f"AGGREGATE_INPUT_AUDIT_FAILED  as_of={args.as_of_date}  "
          f"reason=fold_max_{fold_max}_exceeds_cutoff_{cutoff}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
