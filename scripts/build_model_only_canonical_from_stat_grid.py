#!/usr/bin/env python3
"""Build canonical MODEL_ONLY PMF parquet from predictions/stat_grid_DATE.parquet.

This is the PMF-only bridge for Derek/WoO delivery automation:
  build_stat_grid_pmfs.py
  -> build_model_only_canonical_from_stat_grid.py
  -> build_daily_pmf_delivery.py --model-only ...

It does not rename or remove fields. It reuses the canonical stat-grid row
mapping already defined in build_daily_pmf_delivery.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from build_daily_pmf_delivery import _stat_grid_rows
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402
import shutil


# M8.4: full 11-stat mission canonical set. Sorted for deterministic
# order in the rectangularize gate. Previous 5-stat set
# (ast/fg3m/pts/reb/tov) silently dropped stl/blk/stocks/pa/pr/pra
# rows from the canonical MODEL_ONLY parquet even when upstream
# stat_grid emitted them. No ra/reb_ast (non-mission).
REQUIRED_TARGET_STATS = sorted(MISSION_REQUIRED_TARGETS_CANONICAL)


def _enforce_complete_stat_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Drop incomplete player-game pairs so MODEL_ONLY has even stat counts."""
    stat_col = "stat" if "stat" in df.columns else "target_stat" if "target_stat" in df.columns else None
    if stat_col is None:
        raise SystemExit("FATAL: STAT_GRID_RECTANGULARIZE_FAILED missing stat/target_stat column")

    key_options = [
        ["game_id", "player_id"],
        ["event_id", "player_id"],
        ["game_id", "player_name"],
        ["event_id", "player_name"],
        ["player_id", "team", "opponent"],
        ["player_name", "team", "opponent"],
        ["player_name", "team_abbr", "opponent_abbr"],
    ]
    key_cols = next((cols for cols in key_options if all(c in df.columns for c in cols)), None)
    if key_cols is None:
        raise SystemExit(
            "FATAL: STAT_GRID_RECTANGULARIZE_FAILED missing player-game key columns "
            f"columns={list(df.columns)}"
        )

    work = df.copy()
    work[stat_col] = work[stat_col].astype(str)
    work = work.drop_duplicates(key_cols + [stat_col], keep="first")

    before_rows = len(work)
    before_pairs = work[key_cols].drop_duplicates().shape[0]
    before_counts = work[stat_col].value_counts().sort_index().to_dict()

    present = set(work[stat_col].dropna().astype(str))
    missing = sorted(set(REQUIRED_TARGET_STATS) - present)
    if missing:
        raise SystemExit(
            "FATAL: STAT_GRID_RECTANGULARIZE_FAILED missing required target stats "
            f"missing={missing} present={sorted(present)}"
        )

    complete = (
        work.groupby(key_cols, dropna=False)[stat_col]
        .agg(lambda x: set(x))
        .reset_index(name="_stats")
    )
    complete = complete[
        complete["_stats"].apply(lambda stats: set(REQUIRED_TARGET_STATS).issubset(stats))
    ].drop(columns=["_stats"])

    if len(complete) == before_pairs:
        print(
            "STAT_GRID_RECTANGULARIZE_PASS "
            f"rows={before_rows} pairs={before_pairs} counts={before_counts}"
        )
        return work

    filtered = work.merge(complete, on=key_cols, how="inner")
    after_counts = filtered[stat_col].value_counts().sort_index().to_dict()
    after_pairs = filtered[key_cols].drop_duplicates().shape[0]

    print(
        "STAT_GRID_RECTANGULARIZE_WARN "
        f"key_cols={key_cols} before_rows={before_rows} after_rows={len(filtered)} "
        f"before_pairs={before_pairs} after_pairs={after_pairs} "
        f"dropped_incomplete_pairs={before_pairs - after_pairs} "
        f"before_counts={before_counts} after_counts={after_counts}"
    )

    if set(after_counts) != set(REQUIRED_TARGET_STATS) or len(set(after_counts.values())) != 1:
        raise SystemExit(
            "FATAL: STAT_GRID_RECTANGULARIZE_FAILED uneven counts remain "
            f"after_counts={after_counts}"
        )

    return filtered



# M8.6: canonical PMFs must expose every atom in support_min..support_max.
# This is not ladder/CDF reconstruction. It only preserves explicit zero-mass
# atoms inside the model's own declared atom support.
def _m8_6_densify_atom_pmf_column(df):
    import json
    import math

    atom_cols = [c for c in ("pmf_active", "model_full_pmf", "pmf", "pmf_json") if c in df.columns]
    if not atom_cols:
        return df

    col = atom_cols[0]

    def parse_obj(v):
        if v is None:
            return None
        if isinstance(v, str):
            txt = v.strip()
            if not txt:
                return None
            return json.loads(txt)
        return v

    def as_int(v, default=None):
        try:
            if v is None:
                return default
            f = float(v)
            if not math.isfinite(f):
                return default
            return int(round(f))
        except Exception:
            return default

    def densify(row):
        obj = parse_obj(row[col])

        if obj is None:
            return row[col]

        raw = {}

        if isinstance(obj, dict):
            for k, v in obj.items():
                try:
                    kk = int(round(float(k)))
                    vv = float(v)
                except Exception:
                    continue
                if kk >= 0 and math.isfinite(vv) and vv >= 0:
                    raw[kk] = vv

        elif isinstance(obj, list):
            for kk, v in enumerate(obj):
                try:
                    vv = float(v)
                except Exception:
                    continue
                if math.isfinite(vv) and vv >= 0:
                    raw[kk] = vv

        if not raw:
            return row[col]

        support_min = as_int(row.get("support_min", min(raw.keys())), min(raw.keys()))
        support_max = as_int(row.get("support_max", max(raw.keys())), max(raw.keys()))

        support_min = min(support_min, min(raw.keys()))
        support_max = max(support_max, max(raw.keys()))

        dense = {str(k): float(raw.get(k, 0.0)) for k in range(support_min, support_max + 1)}

        total = sum(dense.values())
        if total > 0 and math.isfinite(total):
            dense = {k: float(v / total) for k, v in dense.items()}

        return json.dumps(dense, sort_keys=False)

    df = df.copy()
    df[col] = df.apply(densify, axis=1)

    print(f"M8_6_DENSIFY_CANONICAL_ATOM_PMF_PASS column={col} rows={len(df)}")
    return df

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument(
        "--stat-grid-path",
        default=None,
        help=(
            "Path to predictions/stat_grid_{date}.parquet (prod contract). "
            "Default: predictions/stat_grid_{--date}.parquet"
        ),
    )
    ap.add_argument(
        "--canonical-dir",
        default=None,
        help="default: deliveries/{date}/canonical_source",
    )
    args = ap.parse_args(argv)

    date = args.date
    stat_grid_path = (
        Path(args.stat_grid_path)
        if args.stat_grid_path
        else REPO_ROOT / "predictions" / f"stat_grid_{date}.parquet"
    )
    if not stat_grid_path.is_absolute():
        stat_grid_path = REPO_ROOT / stat_grid_path
    stat_grid_path = stat_grid_path.resolve()

    posix_path = stat_grid_path.as_posix()
    if "predictions/all_props_" in posix_path:
        print(
            "FATAL: CANONICAL_SOURCE_CONTRACT_VIOLATION "
            "all_props_is_sparse_not_stat_grid",
            file=sys.stderr,
        )
        return 1

    if not stat_grid_path.exists():
        print(
            f"FATAL: missing stat_grid parquet {stat_grid_path}",
            file=sys.stderr,
        )
        return 1

    rows = _stat_grid_rows(date, stat_grid_path=stat_grid_path)
    try:
        _sg_rel = str(stat_grid_path.relative_to(REPO_ROOT))
    except ValueError:
        _sg_rel = str(stat_grid_path)
    if not rows:
        print(
            f"FATAL: no canonical rows produced from {_sg_rel}",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(args.canonical_dir or REPO_ROOT / "deliveries" / date / "canonical_source")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df = _enforce_complete_stat_grid(df)

    pq_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    jsonl_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.jsonl"
    csv_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.csv"

    df = _m8_6_densify_atom_pmf_column(df)
    df.to_parquet(pq_path, index=False)

    # M8.6 canonical alias contract:
    # Downstream WoO builders/verifiers may read all_props_model_only.parquet,
    # but the true source is player_prop_pmfs_tonight_MODEL_ONLY.parquet.
    # Keep the alias as an exact file copy to avoid schema/order/PMF drift.
    alias_path = pq_path.parent / "all_props_model_only.parquet"
    shutil.copy2(pq_path, alias_path)
    print(f"CANONICAL_MODEL_ONLY_ALIAS_WRITTEN {alias_path}")
    df.to_json(jsonl_path, orient="records", lines=True)
    df.to_csv(csv_path, index=False)

    print("=" * 72)
    print(f"build_model_only_canonical_from_stat_grid — date={date}")
    try:
        _src_rel = str(stat_grid_path.relative_to(REPO_ROOT))
    except ValueError:
        _src_rel = str(stat_grid_path)
    print(f"source: {_src_rel}")
    print(f"rows: {len(df)}")
    if "stat" in df.columns:
        print("stat_counts:")
        print(df["stat"].astype(str).value_counts().sort_index().to_string())
    if "player_id" in df.columns:
        print(f"players: {df['player_id'].nunique()}")
    print(f"wrote: {pq_path.relative_to(REPO_ROOT)}")
    print("=" * 72)

    return 0




# M8_6_CANONICAL_MANIFEST_WRAPPER
def _m8_6_write_canonical_manifest_from_outputs() -> None:
    import sys, json, hashlib
    from pathlib import Path
    from datetime import datetime, timezone
    import pandas as pd

    date = None
    argv = list(sys.argv)
    for flag in ("--date", "--target-date", "--delivery-date"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 < len(argv):
                date = argv[i + 1]
                break
    if not date:
        for a in argv:
            if isinstance(a, str) and len(a) == 10 and a[4] == "-" and a[7] == "-":
                date = a
                break
    if not date:
        return

    cs = Path("deliveries") / date / "canonical_source"
    pq = cs / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    if not pq.exists():
        return

    df = pd.read_parquet(pq)
    allowed = ["model_full_pmf", "pmf", "pmf_active", "pmf_json"]
    atom_cols = [c for c in allowed if c in df.columns]
    if not atom_cols:
        raise SystemExit(f"M8_6_CANONICAL_MANIFEST_FAIL no atom PMF column in {pq}")

    atom_col = atom_cols[0]
    sha = hashlib.sha256(pq.read_bytes()).hexdigest()

    payload = {
        "schema_version": "m8_6m_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "date": date,
        "canonical_source_type": "MODEL_ONLY_TRUE_ATOM_PMF",
        "atom_pmf_policy": "atom_source_only_no_ladder_fallback",
        "model_only_parquet": str(pq),
        "model_only_parquet_path": str(pq),
        "canonical_pmf_source_path": str(pq),
        "source_graph_id": "build_stat_grid_pmfs_to_model_only_canonical_to_delivery_m8_6",
        "atom_pmf_present": True,
        "atom_pmf_column": atom_col,
        "atom_pmf_columns": atom_cols,
        "canonical_outputs": {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "model_only_parquet": str(pq),
            "model_only_parquet_path": str(pq),
            "parquet_path": str(pq),
            "parquet_sha256": sha,
            "atom_pmf_present": True,
            "atom_pmf_column": atom_col,
            "atom_pmf_columns": atom_cols,
            "stats": sorted(map(str, df["stat"].dropna().unique())) if "stat" in df.columns else [],
            "players": int(df["player_id"].nunique()) if "player_id" in df.columns else None,
        },
        "forbidden_pmf_sources": ["ladder", "p_ge", "survival", "cdf", "cumulative", "reconstructed", "threshold"],
    }

    (cs / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"M8_6_CANONICAL_MANIFEST_WRITTEN_PASS rows={len(df)} atom_col={atom_col}")


def _m8_6_main_with_manifest():
    rc = main()
    if rc is None or rc == 0:
        _m8_6_write_canonical_manifest_from_outputs()
    return 0 if rc is None else rc


if __name__ == "__main__":
    raise SystemExit(_m8_6_main_with_manifest())

# M8_6_DIRECT_SOURCE_GRAPH_AUDIT_MARKER
