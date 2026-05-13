#!/usr/bin/env python3
"""Diagnose uneven MODEL_ONLY per-stat row counts before daily PMF delivery."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from nba_props_model.targets import MISSION_REQUIRED_TARGETS_CANONICAL  # noqa: E402

REQUIRED = [str(s).lower() for s in MISSION_REQUIRED_TARGETS_CANONICAL]


def _key_cols(df: pd.DataFrame) -> list[str] | None:
    for cols in (["game_id", "player_id"], ["event_id", "player_id"]):
        if all(c in df.columns for c in cols):
            return cols
    return None


def _stat_counts(df: pd.DataFrame, label: str) -> dict[str, int]:
    if df.empty or "stat" not in df.columns:
        return {}
    return df["stat"].astype(str).str.lower().value_counts().to_dict()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    d = str(args.date).strip()[:10]

    stat_grid_p = REPO_ROOT / "predictions" / f"stat_grid_{d}.parquet"
    canon_p = (
        REPO_ROOT / "deliveries" / d / "canonical_source" / "player_prop_pmfs_tonight_MODEL_ONLY.parquet"
    )
    all_props_p = REPO_ROOT / "predictions" / f"all_props_{d}.parquet"
    backtest_json = REPO_ROOT / "artifacts" / "model_diagnostics" / f"backtest_delivery_range_{d}_{d}.json"

    rows_out: list[dict] = []
    md_lines: list[str] = [
        f"# Daily PMF delivery stat-count mismatch — `{d}`",
        "",
        "## Sources",
        f"- stat_grid: `{stat_grid_p.relative_to(REPO_ROOT)}` exists={stat_grid_p.is_file()}",
        f"- canonical MODEL_ONLY: `{canon_p.relative_to(REPO_ROOT)}` exists={canon_p.is_file()}",
        f"- all_props: `{all_props_p.relative_to(REPO_ROOT)}` exists={all_props_p.is_file()}",
        f"- backtest report (optional): `{backtest_json.relative_to(REPO_ROOT)}` exists={backtest_json.is_file()}",
        "",
    ]

    sg = pd.read_parquet(stat_grid_p) if stat_grid_p.is_file() else pd.DataFrame()
    cn = pd.read_parquet(canon_p) if canon_p.is_file() else pd.DataFrame()
    ap_df = pd.read_parquet(all_props_p) if all_props_p.is_file() else pd.DataFrame()

    sg_counts = _stat_counts(sg, "stat_grid")
    cn_counts = _stat_counts(cn, "canonical")
    ap_counts = _stat_counts(ap_df, "all_props")

    md_lines.append("## Per-stat row counts")
    md_lines.append("| stat | stat_grid | all_props | canonical |")
    md_lines.append("|------|-----------|-----------|-----------|")
    for st in sorted(set(REQUIRED) | set(sg_counts) | set(cn_counts) | set(ap_counts)):
        md_lines.append(
            f"| {st} | {sg_counts.get(st, '—')} | {ap_counts.get(st, '—')} | {cn_counts.get(st, '—')} |"
        )
    md_lines.append("")

    # Missing fg3m-style diff: players with pts but no fg3m in canonical
    kc_sg = _key_cols(sg) if len(sg) else None
    kc_cn = _key_cols(cn) if len(cn) else None
    if kc_sg and kc_cn and len(sg) and len(cn):
        sgg = sg.copy()
        sgg["stat"] = sgg["stat"].astype(str).str.lower()
        cng = cn.copy()
        cng["stat"] = cng["stat"].astype(str).str.lower()
        for base, miss in (("pts", "fg3m"), ("pts", "tov")):
            if base not in REQUIRED or miss not in REQUIRED:
                continue
            a = (
                sgg[sgg["stat"] == base][kc_sg].drop_duplicates().astype(str).agg("|".join, axis=1)
            )
            b = (
                sgg[sgg["stat"] == miss][kc_sg].drop_duplicates().astype(str).agg("|".join, axis=1)
            )
            only_base = set(a) - set(b)
            rows_out.append(
                {
                    "layer": "stat_grid",
                    "comparison": f"{base}_without_{miss}",
                    "n_keys_with_base_only": len(only_base),
                }
            )
            md_lines.append(f"## stat_grid: keys with `{base}` but no `{miss}`: {len(only_base)}")
            if only_base and len(only_base) <= 30:
                md_lines.extend(f"- `{x}`" for x in sorted(only_base)[:30])
            md_lines.append("")

    # Root cause narrative
    root = (
        "If canonical is uneven while stat_grid is rectangular, the usual cause is "
        "`build_daily_pmf_delivery.py --rebuild-canonical`, which merges `all_props` "
        "(sparse per-stat) with stat_grid append-only dedupe, producing unequal "
        "`stat` value_counts. Fix: use stat_grid-built canonical without "
        "`--rebuild-canonical`, and/or run `_enforce_complete_stat_grid` after "
        "`build_canonical_from_predictions`."
    )
    md_lines.append("## Likely root cause")
    md_lines.append(root)
    md_lines.append("")

    out_dir = REPO_ROOT / "artifacts" / "model_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_p = out_dir / f"daily_pmf_delivery_stat_count_mismatch_{d}.csv"
    md_p = out_dir / f"daily_pmf_delivery_stat_count_mismatch_{d}.md"
    pd.DataFrame(rows_out).to_csv(csv_p, index=False)
    md_p.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"DIAGNOSE_STAT_COUNT_MISMATCH wrote {csv_p.relative_to(REPO_ROOT)}")
    print(f"DIAGNOSE_STAT_COUNT_MISMATCH wrote {md_p.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
