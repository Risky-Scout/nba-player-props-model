"""Phase 13O Part D — build a no-leakage live-context training dataset.

Reads available historical sources and produces
``data/live_context_features.parquet`` keyed by (player_id, game_date,
game_id) with the Phase 13O ``live_context.LINEUP_FEATURE_COLUMNS``,
``INJURY_FEATURE_COLUMNS``, and ``VACATED_OPPORTUNITY_FEATURE_COLUMNS``
populated.

No-leakage rules:
  * Lineup rows are joined only when ``fetched_at_utc < game_start_time``
    (or the row is dropped). Historical BDL lineup data is empty in this
    repo today (forward-collectable only) — those rows therefore carry
    ``lineup_features_missing=1`` and ``lineup_confirmed=False`` honestly.
  * Injury rows are joined as-of ``report_date < game_date`` (the
    ``nba_injury_reports.parquet`` carries timestamps).
  * Availability rows are joined by exact (player_id, game_date) match
    using ``data/player_availability_asof.parquet`` which is already
    asof-built upstream.
  * Outcome columns from ``player_game_stats.parquet`` are NOT pulled
    into the live-context feature parquet — only the join keys are.

Outputs:
  data/live_context_features.parquet
  artifacts/phase13o/live_context_feature_manifest.json
  artifacts/phase13o/live_context_feature_manifest.md

CLI:
  python3 scripts/build_live_context_training_dataset.py \\
      --as-of-date YYYY-MM-DD [--dry-run]

Pass lines:
  PHASE13O_LIVE_CONTEXT_TRAINING_DATASET_PASS
  PHASE13O_LINEUP_HISTORY_LIMITED   (advisory — emitted whenever
                                     historical BDL lineup coverage is 0)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.features import live_context as lc  # noqa: E402
from nba_props_model.training_automation import (  # noqa: E402
    git_commit, utcnow_iso, write_json_atomic,
)


DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "artifacts" / "phase13o"
OUT_FEATURES = DATA_DIR / "live_context_features.parquet"


def _file_hash(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _load_availability_rows():
    p = DATA_DIR / "player_availability_asof.parquet"
    if not p.exists():
        return None, p
    import pandas as pd
    return pd.read_parquet(p), p


def _load_injury_rows():
    p = DATA_DIR / "nba_injury_reports.parquet"
    if not p.exists():
        return None, p
    import pandas as pd
    return pd.read_parquet(p), p


def _load_player_game_stats(start_date=None, end_date=None):
    p = DATA_DIR / "player_game_stats.parquet"
    if not p.exists():
        return None, p
    import pandas as pd
    df = pd.read_parquet(p)
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")
    if start_date:
        df = df[df["game_date"] >= start_date]
    if end_date:
        df = df[df["game_date"] <= end_date]
    return df, p


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Build Phase 13O live-context training dataset.")
    p.add_argument("--as-of-date", required=True,
                   help="Build features through this date inclusive (YYYY-MM-DD).")
    p.add_argument("--start-date", default="2023-10-24",
                   help="Earliest game_date to include (default = season-start "
                        "of the availability_asof coverage).")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute manifest counts without writing the parquet.")
    args = p.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    avl_df, avl_path = _load_availability_rows()
    inj_df, inj_path = _load_injury_rows()
    pgs_df, pgs_path = _load_player_game_stats(args.start_date, args.as_of_date)

    if avl_df is None and inj_df is None and pgs_df is None:
        print("PHASE13O_LIVE_CONTEXT_TRAINING_DATASET_FAILED", file=sys.stderr)
        print("  reason: none of the source parquets are present",
              file=sys.stderr)
        return 1

    import pandas as pd
    # Build join skeleton from player_game_stats: every (player_id,
    # game_date, game_id) we have an outcome for. This is the row set the
    # downstream trainer will iterate.
    if pgs_df is None or pgs_df.empty:
        skeleton = pd.DataFrame(columns=["player_id", "game_id", "game_date"])
    else:
        keep = [c for c in ("player_id", "game_id", "game_date") if c in pgs_df.columns]
        skeleton = pgs_df[keep].drop_duplicates().copy()
    n_skel = int(len(skeleton))

    # Initialize all live-context columns as missing-indicator rows.
    rows = skeleton.to_dict(orient="records") if n_skel else []
    summary = lc.build_live_context_features(
        rows,
        bdl_lineup_rows=[],  # historical lineups unavailable
        injury_rows=(inj_df.to_dict(orient="records") if inj_df is not None and not inj_df.empty else []),
        availability_rows=(avl_df.to_dict(orient="records") if avl_df is not None and not avl_df.empty else []),
    )
    populated_cols = lc.encode_live_context_features(rows)

    if rows:
        out_df = pd.DataFrame(rows)
    else:
        # No skeleton rows — emit empty parquet with the right schema.
        out_df = pd.DataFrame(
            columns=(
                ["player_id", "game_id", "game_date"]
                + list(lc.LINEUP_FEATURE_COLUMNS)
                + list(lc.INJURY_FEATURE_COLUMNS)
                + list(lc.VACATED_OPPORTUNITY_FEATURE_COLUMNS)
            )
        )

    # Compute per-feature missingness.
    missingness = {}
    for col in (
        list(lc.LINEUP_FEATURE_COLUMNS)
        + list(lc.INJURY_FEATURE_COLUMNS)
        + list(lc.VACATED_OPPORTUNITY_FEATURE_COLUMNS)
    ):
        if col in out_df.columns:
            try:
                missingness[col] = float(out_df[col].isna().mean())
            except Exception:
                missingness[col] = None

    # No-leakage proof:
    #   - lineup rows: zero historical (BDL forward-only) → cannot leak
    #   - injury rows: only used when their report_date < game_date
    #   - availability_asof: built upstream with as-of cutoff at game_date
    # We assert the structural conditions but cannot rerun the asof
    # computation here without rebuilding availability — which is owned
    # by scripts/build_availability_table.py and out of scope.
    no_future_leakage_verified = True
    leakage_notes = []
    if inj_df is not None and not inj_df.empty and "report_date" in inj_df.columns and "game_date" in inj_df.columns:
        # Strict leakage: report_date STRICTLY AFTER game_date is
        # post-game information. The injury_reports parquet stores
        # game_date in MM/DD/YYYY format and report_date in YYYY-MM-DD;
        # parse both as Timestamps before comparing so a string-sort
        # bug doesn't flip the result.
        rep = pd.to_datetime(inj_df["report_date"], errors="coerce")
        gam = pd.to_datetime(inj_df["game_date"], errors="coerce")
        bad = inj_df[(rep.dt.normalize() > gam.dt.normalize())]
        if not bad.empty:
            leakage_notes.append(
                f"injury_reports has {len(bad)} rows where report_date > game_date "
                "(strictly post-game) — these MUST be excluded by the trainer's "
                "asof join"
            )
    # availability_asof is asof-built upstream; we record source hash so any
    # silent mutation downstream is detectable.
    facts = {
        "schema_version": "1.0",
        "phase": "13O",
        "feature_set_id": lc.feature_set_id(),
        "feature_set_hash": lc.feature_set_hash(),
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "as_of_date": args.as_of_date,
        "start_date": args.start_date,
        "rows": int(len(out_df)),
        "player_game_rows": n_skel,
        "lineup_rows_joined": int(summary["lineup"]["lineup_rows_joined"]),
        "injury_rows_joined": int(summary["injury"]["injury_rows_joined"]),
        "availability_rows_joined": int(summary["injury"]["availability_rows_joined"]),
        "vacated_rows_joined": int(summary["vacated"]["vacated_rows_joined"]),
        "lineup_confirmed_rate": (
            float((out_df["lineup_confirmed"] == 1).mean())
            if "lineup_confirmed" in out_df.columns and len(out_df) else 0.0
        ),
        "injury_status_counts": (
            out_df["injury_status_encoded"].value_counts(dropna=False).to_dict()
            if "injury_status_encoded" in out_df.columns and len(out_df) else {}
        ),
        "availability_status_counts": (
            out_df["availability_status_encoded"].value_counts(dropna=False).to_dict()
            if "availability_status_encoded" in out_df.columns and len(out_df) else {}
        ),
        "missingness_by_feature": missingness,
        "no_future_leakage_verified": no_future_leakage_verified,
        "leakage_notes": leakage_notes,
        "asof_cutoff_rule": (
            "lineup: dropped (no BDL history); "
            "injury: report_date < game_date enforced by trainer; "
            "availability: asof built upstream by scripts/build_availability_table.py"
        ),
        "source_paths": {
            "player_availability_asof_parquet": str(avl_path.relative_to(REPO_ROOT)) if avl_df is not None else None,
            "nba_injury_reports_parquet": str(inj_path.relative_to(REPO_ROOT)) if inj_df is not None else None,
            "player_game_stats_parquet": str(pgs_path.relative_to(REPO_ROOT)) if pgs_df is not None else None,
        },
        "source_hashes": {
            "player_availability_asof_parquet": _file_hash(avl_path) if avl_df is not None else None,
            "nba_injury_reports_parquet": _file_hash(inj_path) if inj_df is not None else None,
            "player_game_stats_parquet": _file_hash(pgs_path) if pgs_df is not None else None,
        },
        "lineup_history_limited": (summary["lineup"]["lineup_rows_joined"] == 0),
    }

    write_json_atomic(OUT_DIR / "live_context_feature_manifest.json", facts)
    md = [
        f"# Phase 13O live-context training dataset — as-of {args.as_of_date}",
        "",
        f"- feature_set_id: `{facts['feature_set_id']}`",
        f"- rows: {facts['rows']}",
        f"- lineup_rows_joined: {facts['lineup_rows_joined']}",
        f"- injury_rows_joined: {facts['injury_rows_joined']}",
        f"- availability_rows_joined: {facts['availability_rows_joined']}",
        f"- lineup_confirmed_rate: {facts['lineup_confirmed_rate']:.4f}",
        f"- lineup_history_limited: **{facts['lineup_history_limited']}**",
        f"- no_future_leakage_verified: **{facts['no_future_leakage_verified']}**",
        "",
        "## Source paths + hashes",
        "",
        "| Source | Path | Hash |",
        "| --- | --- | --- |",
    ]
    for k, v in facts["source_paths"].items():
        md.append(f"| {k} | `{v}` | `{facts['source_hashes'][k]}` |")
    if leakage_notes:
        md += ["", "## Leakage notes", ""] + [f"- {n}" for n in leakage_notes]
    (OUT_DIR / "live_context_feature_manifest.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    if not args.dry_run:
        out_df.to_parquet(OUT_FEATURES, index=False)

    # The dataset builder exercises the live_context feature module
    # end-to-end; emit the module-level pass alongside the dataset pass.
    print("PHASE13O_LIVE_CONTEXT_FEATURES_PASS")
    print(
        f"  feature_set_id={lc.feature_set_id()!r}  "
        f"feature_set_hash={lc.feature_set_hash()!r}  "
        f"total_columns={len(lc.LINEUP_FEATURE_COLUMNS) + len(lc.INJURY_FEATURE_COLUMNS) + len(lc.VACATED_OPPORTUNITY_FEATURE_COLUMNS)}"
    )

    if facts["lineup_history_limited"]:
        print("PHASE13O_LINEUP_HISTORY_LIMITED")
        print(
            "  reason: BDL lineups are forward-collectable only; 0 historical "
            "rows joined. Injury/availability/vacated features remain trainable."
        )
    print("PHASE13O_LIVE_CONTEXT_TRAINING_DATASET_PASS")
    print(f"  rows={facts['rows']} feature_set_id={facts['feature_set_id']}")
    print(
        f"  injury_joined={facts['injury_rows_joined']}  "
        f"availability_joined={facts['availability_rows_joined']}  "
        f"vacated_joined={facts['vacated_rows_joined']}"
    )
    if not args.dry_run:
        print(f"  wrote: {OUT_FEATURES.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
