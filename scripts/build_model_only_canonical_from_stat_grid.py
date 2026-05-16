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

from build_daily_pmf_delivery import (  # noqa: E402
    MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS,
    MODEL_ONLY_PUBLISH_ID_STAT_COLUMNS,
    _stat_grid_rows,
    _validate_production_model_only,
)
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

# M8.4: full 11-stat mission canonical set. Sorted for deterministic
# order in the rectangularize gate. Previous 5-stat set
# (ast/fg3m/pts/reb/tov) silently dropped stl/blk/stocks/pa/pr/pra
# rows from the canonical MODEL_ONLY parquet even when upstream
# stat_grid emitted them. No ra/reb_ast (non-mission).
REQUIRED_TARGET_STATS = sorted(MISSION_REQUIRED_TARGETS_CANONICAL)

MODEL_ONLY_PUBLISH_COLUMNS = MODEL_ONLY_PUBLISH_ID_STAT_COLUMNS + list(
    MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS
)

# Join these from artifacts/minutes_predictions/{date}/minutes_predictions_eligible.parquet
ENRICH_COLUMNS_FROM_ELIGIBLE = [
    c for c in MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS if c != "player_game_eligible"
]


def _normalize_minutes_q_to_p_aliases(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    swaps = (
        ("minutes_q10", "minutes_p10"),
        ("minutes_q50", "minutes_p50"),
        ("minutes_q90", "minutes_p90"),
    )
    for src, dst in swaps:
        if dst not in out.columns and src in out.columns:
            out[dst] = out[src]
    return out


def _inject_slate_date(df: pd.DataFrame, slate_date: str) -> pd.DataFrame:
    out = df.copy()
    sd = str(slate_date).strip()
    if "slate_date" not in out.columns:
        out["slate_date"] = sd
    out["slate_date"] = out["slate_date"].astype(str).str[:10]
    return out


def _numeric_join_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["game_id"] = pd.to_numeric(out["game_id"], errors="coerce").astype("int64")
    out["player_id"] = pd.to_numeric(out["player_id"], errors="coerce").astype("int64")
    out["slate_date"] = out["slate_date"].astype(str).str[:10]
    return out


def _require_join_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure slate_date / game_id / player_id exist and have no nulls."""
    keys = ["slate_date", "game_id", "player_id"]
    missing_cols = [k for k in keys if k not in df.columns]
    if missing_cols:
        raise SystemExit(
            "MODEL_ONLY_JOIN_KEYS_MISSING "
            f"missing={missing_cols} present={list(df.columns)}"
        )
    work = df.copy()
    work["slate_date"] = work["slate_date"].astype(str).str[:10]
    work["game_id"] = pd.to_numeric(work["game_id"], errors="coerce")
    work["player_id"] = pd.to_numeric(work["player_id"], errors="coerce")
    bad = work[keys].isna().any(axis=1)
    if bool(bad.any()):
        raise SystemExit(
            "MODEL_ONLY_JOIN_KEYS_MISSING "
            f"missing=null_row_values rows={int(bad.sum())} keys={keys} "
            f"present={list(work.columns)} "
            f"sample={work.loc[bad, keys].head(12).to_dict('records')}"
        )
    work["game_id"] = work["game_id"].astype("int64")
    work["player_id"] = work["player_id"].astype("int64")
    return work


def _needs_eligibility_fill(df: pd.DataFrame) -> bool:
    for col in MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS:
        if col not in df.columns:
            return True
        if df[col].isna().any():
            return True
    return False


def _gap_columns_summary(df: pd.DataFrame) -> list[str]:
    gaps: list[str] = []
    for col in MODEL_ONLY_ELIGIBILITY_MINUTES_COLUMNS:
        if col not in df.columns:
            gaps.append(f"missing:{col}")
            continue
        if df[col].isna().any():
            gaps.append(f"null:{col}")
    return sorted(gaps)


def merge_eligibility_minutes_into_model_only(
    df: pd.DataFrame,
    *,
    delivery_date: str,
    repo_root: Path,
    minutes_eligible_path: Path | None = None,
) -> pd.DataFrame:
    """Fill MODEL_ONLY eligibility/minutes columns from stat-grid or eligible join."""
    out = df.copy()
    keys = ["slate_date", "game_id", "player_id"]
    eligible_path = minutes_eligible_path or (
        repo_root / "artifacts" / "minutes_predictions" / delivery_date /
        "minutes_predictions_eligible.parquet"
    )

    needs_fill = _needs_eligibility_fill(out)

    if not needs_fill:
        bad = ~out["player_game_eligible"].astype(bool)
        if bool(bad.any()):
            sample = (
                out.loc[
                    bad,
                    [c for c in keys + ["stat", "player_name"] if c in out.columns],
                ]
                .head(15)
                .to_dict("records")
            )
            raise SystemExit(
                "MODEL_ONLY_INELIGIBLE_ROWS_PRESENT "
                f"count={int(bad.sum())} sample_rows={sample}"
            )
        return _numeric_join_keys(out)

    if not eligible_path.is_file():
        raise SystemExit(
            "MODEL_ONLY_ELIGIBILITY_JOIN_SOURCE_MISSING "
            f"path={eligible_path.resolve()} "
            f"stat_grid_gap_columns={_gap_columns_summary(out)} "
            f"present={list(out.columns)}"
        )

    elig = pd.read_parquet(eligible_path)
    if elig.empty:
        raise SystemExit(
            "MODEL_ONLY_ELIGIBILITY_JOIN_SOURCE_MISSING "
            f"path={eligible_path.resolve()} reason=empty_file "
            f"stat_grid_gap_columns={_gap_columns_summary(out)}"
        )

    elig = _normalize_minutes_q_to_p_aliases(elig)
    if "slate_date" not in elig.columns:
        elig = elig.copy()
        elig["slate_date"] = str(delivery_date)
    elig["slate_date"] = elig["slate_date"].astype(str).str[:10]
    elig["game_id"] = pd.to_numeric(elig["game_id"], errors="coerce").astype("int64")
    elig["player_id"] = pd.to_numeric(elig["player_id"], errors="coerce").astype("int64")

    if "projected_role" not in elig.columns and "role_bucket" in elig.columns:
        elig = elig.copy()
        elig["projected_role"] = elig["role_bucket"]

    missing_need = sorted(set(ENRICH_COLUMNS_FROM_ELIGIBLE) - set(elig.columns))
    if missing_need:
        raise SystemExit(
            "MODEL_ONLY_ELIGIBILITY_JOIN_SOURCE_MISSING "
            f"path={eligible_path.resolve()} eligible_missing_columns={missing_need}"
        )

    take_cols = list(ENRICH_COLUMNS_FROM_ELIGIBLE)
    if "player_game_eligible" in elig.columns:
        take_cols.append("player_game_eligible")

    rename_map = {c: f"_eg_{c}" for c in take_cols}
    take = (
        elig[keys + take_cols]
        .drop_duplicates(subset=keys)
        .rename(columns=rename_map)
    )

    base = _numeric_join_keys(out)
    merged = base.merge(take, on=keys, how="left", validate="many_to_one")

    for col in ENRICH_COLUMNS_FROM_ELIGIBLE:
        left_series = (
            merged[col]
            if col in merged.columns
            else pd.Series(pd.NA, index=merged.index)
        )
        elig_series = merged[f"_eg_{col}"]
        merged[col] = left_series.where(left_series.notna(), elig_series)

    if "_eg_player_game_eligible" in merged.columns:
        sg_pe = (
            merged["player_game_eligible"]
            if "player_game_eligible" in merged.columns
            else pd.Series(pd.NA, index=merged.index)
        )
        merged["player_game_eligible"] = sg_pe.where(sg_pe.notna(), merged["_eg_player_game_eligible"])

    eg_drop = [c for c in merged.columns if c.startswith("_eg_")]
    merged = merged.drop(columns=eg_drop)

    for col in ENRICH_COLUMNS_FROM_ELIGIBLE:
        if merged[col].isna().any():
            nmiss = int(merged[col].isna().sum())
            raise SystemExit(
                "FATAL: MODEL_ONLY enrichment left_join incomplete "
                f"column={col!r} null_rows={nmiss} "
                "(stat-grid player-game not in minutes_predictions_eligible)"
            )

    if "player_game_eligible" not in merged.columns:
        merged["player_game_eligible"] = True
    else:
        merged["player_game_eligible"] = merged["player_game_eligible"].fillna(True).astype(bool)
    bad = ~merged["player_game_eligible"]
    if bool(bad.any()):
        sample = (
            merged.loc[
                bad,
                [c for c in keys + ["stat"] if c in merged.columns],
            ]
            .head(15)
            .to_dict("records")
        )
        raise SystemExit(
            "MODEL_ONLY_INELIGIBLE_ROWS_PRESENT "
            f"count={int(bad.sum())} sample_rows={sample}"
        )

    return merged


def _assert_publish_schema_preflight(df: pd.DataFrame, path: Path | str) -> None:
    need = MODEL_ONLY_PUBLISH_COLUMNS
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(
            "MODEL_ONLY_SCHEMA_MISSING_COLUMNS "
            f"path={path} missing={missing} present={list(df.columns)}"
        )


def _reload_and_verify_model_only_parquet(path: Path) -> None:
    r = pd.read_parquet(path)
    _assert_publish_schema_preflight(r, path.resolve())
    _validate_production_model_only(r, path.resolve())
    print(f"MODEL_ONLY_SCHEMA_PASS path={path.resolve()} rows={len(r)}")


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
    ap.add_argument(
        "--minutes-eligible-path",
        default=None,
        help=(
            "minutes_predictions_eligible.parquet "
            "(default: artifacts/minutes_predictions/{date}/minutes_predictions_eligible.parquet)"
        ),
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
    # Canonical MODEL_ONLY is the authoritative model surface and must
    # only ever be built from the validated 12-stat stat-grid. Refuse to
    # build it from either the sparse raw predictions/all_props_*.parquet
    # snapshot OR the identity-only pre-canonical slate universe seed —
    # both are pre-stat-grid and would silently downgrade the canonical
    # source contract.
    if "predictions/all_props_" in posix_path:
        print(
            "FATAL: CANONICAL_SOURCE_CONTRACT_VIOLATION "
            "all_props_is_sparse_not_stat_grid",
            file=sys.stderr,
        )
        return 1
    if "precanonical_slate_universe_" in posix_path:
        print(
            "FATAL: CANONICAL_SOURCE_CONTRACT_VIOLATION "
            "precanonical_seed_is_identity_only_not_stat_grid",
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

    melig_in = Path(args.minutes_eligible_path) if args.minutes_eligible_path else None
    if melig_in is not None and not melig_in.is_absolute():
        melig_in = (REPO_ROOT / melig_in).resolve()

    df = pd.DataFrame(rows)
    df = _normalize_minutes_q_to_p_aliases(df)
    df = _inject_slate_date(df, date)
    df = _require_join_keys(df)
    df = merge_eligibility_minutes_into_model_only(
        df,
        delivery_date=date,
        repo_root=REPO_ROOT,
        minutes_eligible_path=melig_in,
    )
    df = _enforce_complete_stat_grid(df)

    pq_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    jsonl_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.jsonl"
    csv_path = out_dir / "player_prop_pmfs_tonight_MODEL_ONLY.csv"
    alias_path = out_dir / "all_props_model_only.parquet"

    df = _m8_6_densify_atom_pmf_column(df)

    pq_resolved = pq_path.resolve()
    _assert_publish_schema_preflight(df, pq_resolved)
    _validate_production_model_only(df, pq_resolved)

    df.to_parquet(pq_path, index=False)
    df.to_parquet(alias_path, index=False)
    _reload_and_verify_model_only_parquet(pq_path.resolve())
    _reload_and_verify_model_only_parquet(alias_path.resolve())
    print(
        "CANONICAL_MODEL_ONLY_DUAL_WRITE "
        f"primary={pq_path.relative_to(REPO_ROOT)} "
        f"alias={alias_path.relative_to(REPO_ROOT)} rows={len(df)}"
    )
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
