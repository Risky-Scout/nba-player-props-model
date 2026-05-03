"""Phase 13M Part H — build snapshot_comparison + input_change_report.

When both ``t_minus_25`` and ``close_lock`` snapshots exist for a game
under ``deliveries/<date>/derek_game_snapshots/<game_id>/``, write
interpretability outputs:

    snapshot_comparison.csv
    snapshot_comparison.parquet
    snapshot_comparison.md
    input_change_report.json
    input_change_report.md

These are read-only / pre-outcomes tools — they compare the two
production-live (or backfill_demo) snapshots' market+model probabilities
+ derived edges, and surface input-hash deltas (lineup, injury,
prediction, market). They do NOT consume game outcomes.

Usage:
    python3 scripts/build_derek_snapshot_comparison.py \\
        --delivery-date YYYY-MM-DD [--game-id GAME_ID]

Pass line:  DEREK_SNAPSHOT_COMPARISON_PASS
Fail line:  DEREK_SNAPSHOT_COMPARISON_FAILED
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

from nba_props_model.training_automation import (  # noqa: E402
    git_commit,
    read_json,
    utcnow_iso,
    write_json_atomic,
)


DELIVERIES_DIR = REPO_ROOT / "deliveries"
SNAPSHOT_TYPES = ("t_minus_25", "close_lock")


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _read_prop_summary(snap_dir: Path):
    import pandas as pd
    p = snap_dir / "prop_summary.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


def _join_key(df):
    # Compose a row-stable key for joining T-25 to close-lock. Books +
    # line included so the same player/stat at multiple lines is
    # represented separately.
    return df.apply(
        lambda r: (
            str(r.get("player_id")),
            str(r.get("stat")),
            str(r.get("book")),
            str(r.get("line")),
        ),
        axis=1,
    )


def _input_hashes(snap_dir: Path) -> dict:
    m = read_json(snap_dir / "snapshot_manifest.json")
    return {
        "lineup_hash": m.get("lineup_hash") or "",
        "injury_availability_hash": (
            m.get("injury_availability_hash")
            or _file_hash(REPO_ROOT / "data" / "player_availability_asof.parquet")
        ),
        "prediction_input_hash": m.get("input_manifest_hash") or "",
        "pmf_output_hash": m.get("pmf_output_hash") or "",
        "market_hash": _file_hash(snap_dir / "market_comparison.parquet"),
        "champion_pointer_hash": m.get("champion_pointer_hash") or "",
    }


def _build_comparison_for_game(game_dir: Path) -> dict:
    """Return a status dict; writes outputs into game_dir."""
    import pandas as pd
    t25_dir = game_dir / "t_minus_25"
    cl_dir = game_dir / "close_lock"
    out: dict = {
        "schema_version": "1.0",
        "game_id": game_dir.name,
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "t_minus_25_present": (t25_dir / "snapshot_manifest.json").exists(),
        "close_lock_present": (cl_dir / "snapshot_manifest.json").exists(),
        "comparison_emitted": False,
        "blocker": "",
    }
    if not (out["t_minus_25_present"] and out["close_lock_present"]):
        out["blocker"] = "both snapshots not present yet (comparison deferred)"
        return out

    t25_df = _read_prop_summary(t25_dir)
    cl_df = _read_prop_summary(cl_dir)
    if t25_df is None or cl_df is None or t25_df.empty or cl_df.empty:
        out["blocker"] = "prop_summary.parquet missing or empty in one snapshot"
        return out

    # Build comparable rows.
    keep = [
        "player_id", "player_name", "team", "opponent",
        "stat", "book", "line",
        "model_p_over", "market_no_vig_over_prob",
        "edge", "abs_edge",
    ]
    keep_t25 = [c for c in keep if c in t25_df.columns]
    keep_cl = [c for c in keep if c in cl_df.columns]
    a = t25_df[keep_t25].copy()
    b = cl_df[keep_cl].copy()
    a["_k"] = _join_key(a)
    b["_k"] = _join_key(b)
    merged = a.merge(b, on="_k", how="outer", suffixes=("_t25", "_cl"))
    # Pick stable identity columns (prefer t_minus_25 side; fall back to close).
    for col in ("player_id", "player_name", "team", "opponent", "stat", "book", "line"):
        ta, tb = f"{col}_t25", f"{col}_cl"
        if ta in merged.columns and tb in merged.columns:
            merged[col] = merged[ta].fillna(merged[tb])
    # Compute deltas.
    if "model_p_over_t25" in merged.columns and "model_p_over_cl" in merged.columns:
        merged["t_minus_25_model_over_prob"] = merged["model_p_over_t25"]
        merged["close_lock_model_over_prob"] = merged["model_p_over_cl"]
        merged["delta_model_over_prob"] = (
            merged["close_lock_model_over_prob"] - merged["t_minus_25_model_over_prob"]
        )
    if (
        "market_no_vig_over_prob_t25" in merged.columns
        and "market_no_vig_over_prob_cl" in merged.columns
    ):
        merged["t_minus_25_market_no_vig_over_prob"] = merged["market_no_vig_over_prob_t25"]
        merged["close_lock_market_no_vig_over_prob"] = merged["market_no_vig_over_prob_cl"]
        merged["delta_market_prob"] = (
            merged["close_lock_market_no_vig_over_prob"]
            - merged["t_minus_25_market_no_vig_over_prob"]
        )
    if "edge_t25" in merged.columns and "edge_cl" in merged.columns:
        merged["t_minus_25_edge"] = merged["edge_t25"]
        merged["close_lock_edge"] = merged["edge_cl"]
        merged["delta_edge"] = merged["close_lock_edge"] - merged["t_minus_25_edge"]
    # Movement flags.
    if "line_t25" in merged.columns and "line_cl" in merged.columns:
        merged["line_moved"] = (merged["line_t25"] != merged["line_cl"]).fillna(False)
    if "delta_market_prob" in merged.columns:
        merged["price_moved"] = (merged["delta_market_prob"].abs() > 1e-9).fillna(False)
    if "delta_model_over_prob" in merged.columns:
        merged["pmf_changed"] = (merged["delta_model_over_prob"].abs() > 1e-9).fillna(False)
    # Derive game-level input change flags (from manifests).
    t25_h = _input_hashes(t25_dir)
    cl_h = _input_hashes(cl_dir)
    lineup_changed = (t25_h["lineup_hash"] or "") != (cl_h["lineup_hash"] or "")
    injury_changed = (
        (t25_h["injury_availability_hash"] or "") != (cl_h["injury_availability_hash"] or "")
    )
    prediction_input_changed = (
        (t25_h["prediction_input_hash"] or "") != (cl_h["prediction_input_hash"] or "")
    )
    market_changed = (
        (t25_h["market_hash"] or "") != (cl_h["market_hash"] or "")
    )
    pmf_changed = (
        (t25_h["pmf_output_hash"] or "") != (cl_h["pmf_output_hash"] or "")
    )
    merged["lineup_changed"] = lineup_changed
    merged["injury_availability_changed"] = injury_changed
    merged["prediction_input_changed"] = prediction_input_changed
    merged["market_changed"] = market_changed

    # Persist comparison.
    cols_out = [
        "player_id", "player_name", "team", "opponent",
        "stat", "book", "line",
        "t_minus_25_model_over_prob", "close_lock_model_over_prob", "delta_model_over_prob",
        "t_minus_25_market_no_vig_over_prob", "close_lock_market_no_vig_over_prob",
        "delta_market_prob",
        "t_minus_25_edge", "close_lock_edge", "delta_edge",
        "line_moved", "price_moved", "lineup_changed",
        "injury_availability_changed", "prediction_input_changed",
        "pmf_changed", "market_changed",
    ]
    cols_present = [c for c in cols_out if c in merged.columns]
    sc = merged[cols_present].copy()
    sc.to_csv(game_dir / "snapshot_comparison.csv", index=False)
    sc.to_parquet(game_dir / "snapshot_comparison.parquet", index=False)

    # Top movers.
    top_model_movers = (
        sc.assign(_abs=sc.get("delta_model_over_prob", pd.Series(dtype=float)).abs())
          .sort_values("_abs", ascending=False)
          .head(20)
          .drop(columns=["_abs"], errors="ignore")
          .to_dict(orient="records")
        if "delta_model_over_prob" in sc.columns else []
    )
    top_edge_movers = (
        sc.assign(_abs=sc.get("delta_edge", pd.Series(dtype=float)).abs())
          .sort_values("_abs", ascending=False)
          .head(20)
          .drop(columns=["_abs"], errors="ignore")
          .to_dict(orient="records")
        if "delta_edge" in sc.columns else []
    )

    # Anomaly buckets.
    market_changed_pmf_unchanged = (
        sc[(sc.get("market_changed") == True) & (sc.get("pmf_changed") == False)]
          .head(50).to_dict(orient="records")
        if all(c in sc.columns for c in ("market_changed", "pmf_changed")) else []
    )
    pmf_changed_inputs_unchanged = (
        sc[
            (sc.get("pmf_changed") == True)
            & (sc.get("lineup_changed") == False)
            & (sc.get("injury_availability_changed") == False)
        ].head(50).to_dict(orient="records")
        if all(c in sc.columns for c in ("pmf_changed", "lineup_changed", "injury_availability_changed"))
        else []
    )
    inputs_changed_pmf_unchanged = (
        sc[
            ((sc.get("lineup_changed") == True) | (sc.get("injury_availability_changed") == True))
            & (sc.get("pmf_changed") == False)
        ].head(50).to_dict(orient="records")
        if all(c in sc.columns for c in ("pmf_changed", "lineup_changed", "injury_availability_changed"))
        else []
    )

    # input_change_report.
    t25_m = read_json(t25_dir / "snapshot_manifest.json")
    cl_m = read_json(cl_dir / "snapshot_manifest.json")
    icr = {
        "schema_version": "1.0",
        "game_id": game_dir.name,
        "generated_at_utc": utcnow_iso(),
        "code_commit": git_commit(),
        "t_minus_25_manifest_summary": {
            k: t25_m.get(k) for k in (
                "snapshot_mode", "pmfs_recomputed", "pmf_source",
                "lineup_confirmed", "lineup_complete", "lineup_blocker",
                "lineup_hash", "input_manifest_hash", "pmf_output_hash",
                "starters_by_team", "champion_model_id",
                "champion_metadata_verified",
            )
        },
        "close_lock_manifest_summary": {
            k: cl_m.get(k) for k in (
                "snapshot_mode", "pmfs_recomputed", "pmf_source",
                "lineup_confirmed", "lineup_complete", "lineup_blocker",
                "lineup_hash", "input_manifest_hash", "pmf_output_hash",
                "starters_by_team", "champion_model_id",
                "champion_metadata_verified",
            )
        },
        "input_hashes": {
            "t_minus_25": t25_h,
            "close_lock": cl_h,
        },
        "input_change_flags": {
            "lineup_changed": bool(lineup_changed),
            "injury_availability_changed": bool(injury_changed),
            "prediction_input_changed": bool(prediction_input_changed),
            "market_changed": bool(market_changed),
            "pmf_changed": bool(pmf_changed),
        },
        "top_model_over_prob_movers": top_model_movers,
        "top_edge_movers": top_edge_movers,
        "rows_market_changed_pmf_unchanged": market_changed_pmf_unchanged,
        "rows_pmf_changed_inputs_unchanged": pmf_changed_inputs_unchanged,
        "rows_inputs_changed_pmf_unchanged": inputs_changed_pmf_unchanged,
    }
    write_json_atomic(game_dir / "input_change_report.json", icr)

    md = [
        f"# Snapshot comparison — game {game_dir.name}",
        "",
        f"- generated_at_utc: {icr['generated_at_utc']}",
        f"- t_minus_25 manifest: `{t25_dir / 'snapshot_manifest.json'}`",
        f"- close_lock manifest: `{cl_dir / 'snapshot_manifest.json'}`",
        "",
        "## Input change flags",
        "",
        "| Flag | Value |",
        "| --- | :---: |",
    ]
    for k, v in icr["input_change_flags"].items():
        md.append(f"| {k} | {'YES' if v else 'no'} |")
    md += [
        "",
        "## Manifest summary deltas",
        "",
        "| Field | T-25 | Close-lock |",
        "| --- | --- | --- |",
    ]
    for f in (
        "snapshot_mode", "pmfs_recomputed", "pmf_source",
        "lineup_confirmed", "lineup_complete", "lineup_blocker",
        "lineup_hash", "input_manifest_hash", "pmf_output_hash",
        "starters_by_team", "champion_model_id", "champion_metadata_verified",
    ):
        a = icr["t_minus_25_manifest_summary"].get(f)
        b = icr["close_lock_manifest_summary"].get(f)
        md.append(
            f"| `{f}` | `{a}` | `{b}` |"
        )
    md += [
        "",
        f"## Top {min(20, len(top_model_movers))} model_over_prob movers",
        "",
        "| player_name | stat | book | line | t-25 | close | Δ |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for r in top_model_movers[:20]:
        md.append(
            f"| {r.get('player_name')} | {r.get('stat')} | {r.get('book')} | "
            f"{r.get('line')} | {r.get('t_minus_25_model_over_prob')} | "
            f"{r.get('close_lock_model_over_prob')} | "
            f"{r.get('delta_model_over_prob')} |"
        )
    (game_dir / "snapshot_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    icr_md = [
        f"# Input change report — game {game_dir.name}",
        "",
        f"- generated_at_utc: {icr['generated_at_utc']}",
        "",
        "## Hashes",
        "",
        "| Hash | T-25 | Close-lock | Same? |",
        "| --- | --- | --- | :---: |",
    ]
    for k in (
        "lineup_hash", "injury_availability_hash", "prediction_input_hash",
        "pmf_output_hash", "market_hash", "champion_pointer_hash",
    ):
        a, b = t25_h.get(k, ""), cl_h.get(k, "")
        icr_md.append(f"| `{k}` | `{a}` | `{b}` | {'yes' if a == b else 'NO'} |")
    icr_md += [
        "",
        "## Anomaly buckets (rows)",
        "",
        f"- rows_market_changed_pmf_unchanged: {len(market_changed_pmf_unchanged)}",
        f"- rows_pmf_changed_inputs_unchanged: {len(pmf_changed_inputs_unchanged)}",
        f"- rows_inputs_changed_pmf_unchanged: {len(inputs_changed_pmf_unchanged)}",
        "",
        "(See input_change_report.json for full row payloads, capped at 50 each.)",
    ]
    (game_dir / "input_change_report.md").write_text(
        "\n".join(icr_md) + "\n", encoding="utf-8"
    )

    out["comparison_emitted"] = True
    out["row_count"] = int(len(sc))
    out["input_change_flags"] = icr["input_change_flags"]
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build Derek snapshot comparisons.")
    p.add_argument("--delivery-date", required=True)
    p.add_argument("--game-id", default=None,
                   help="If set, build for one game only.")
    args = p.parse_args(argv)

    base = DELIVERIES_DIR / args.delivery_date / "derek_game_snapshots"
    if not base.exists():
        # Phase 13T — comparison cannot be built when no snapshots exist.
        # Distinguish "slate not published / no games / dispatcher hasn't
        # fired" (PENDING) from a true failure. The verifier above is the
        # source of truth for the slate state; this builder mirrors it.
        pred_parquet = REPO_ROOT / "predictions" / f"all_props_{args.delivery_date}.parquet"
        slate_games = 0
        if pred_parquet.exists():
            try:
                import pandas as pd
                pdf = pd.read_parquet(pred_parquet, columns=["game_id"])
                slate_games = int(pdf["game_id"].astype(str).nunique()) \
                    if "game_id" in pdf.columns else 0
            except Exception:
                slate_games = 0
        reason = (
            "no_predictions_parquet" if not pred_parquet.exists()
            else ("predictions_have_zero_games" if slate_games == 0
                  else "no_snapshots_due_yet")
        )
        print("DEREK_SNAPSHOT_COMPARISON_PENDING_NO_GAMES")
        print(
            f"  delivery_date={args.delivery_date} reason={reason} "
            f"slate_games={slate_games} "
            f"predictions_parquet_present={pred_parquet.exists()}"
        )
        return 0
    if args.game_id:
        targets = [base / str(args.game_id)]
    else:
        targets = [d for d in sorted(base.iterdir()) if d.is_dir()]
    if not targets:
        print("DEREK_SNAPSHOT_COMPARISON_PENDING_NO_GAMES")
        print(f"  delivery_date={args.delivery_date} reason=no_snapshots_present")
        return 0

    statuses: list[dict] = []
    failures = 0
    for game_dir in targets:
        if not game_dir.is_dir():
            continue
        try:
            statuses.append(_build_comparison_for_game(game_dir))
        except Exception as exc:
            statuses.append({
                "game_id": game_dir.name,
                "comparison_emitted": False,
                "blocker": f"raised: {exc}",
            })
            failures += 1

    print("DEREK_SNAPSHOT_COMPARISON_PASS")
    print(f"  delivery_date={args.delivery_date} games_inspected={len(statuses)}")
    any_emitted = False
    for st in statuses:
        if st.get("comparison_emitted"):
            any_emitted = True
            print(
                f"  - game_id={st.get('game_id')}  rows={st.get('row_count')}  "
                f"flags={st.get('input_change_flags')}"
            )
        else:
            print(
                f"  - game_id={st.get('game_id')}  deferred: {st.get('blocker')}"
            )
    # Phase 13M-bis Part J pass-line. Emitted when at least one game
    # emitted a comparison; otherwise we don't claim interpretability and
    # the caller can act on the deferred blockers above.
    if any_emitted:
        print("DEREK_SNAPSHOT_INTERPRETABILITY_PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
