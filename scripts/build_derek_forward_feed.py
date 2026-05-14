"""Build Derek's forward-looking daily PMF feed.

Emits one row per (player, stat) for each available market line, plus a
model-only row for every PMF without a corresponding market quote. PMFs
are sourced from `deliveries/{date}/pmf_model_review_package/machine_readable/model_only.parquet`
(canonical, model-only, never market-anchored). Market lines are
sourced from `deliveries/{date}/wizard_of_odds/market_comparison.parquet`
as reference-only fields.

Outputs land under `deliveries/{date}/derek_forward_feed/` and never
fabricate predictions, lineups, role buckets, or odds. If a lineup
snapshot package is unavailable the builder writes
`lineup_snapshot_status.json` with an honest status code; it never
synthesises lineup data.

Phase 12C — `--snapshot {morning,lineup,both}` controls which snapshot
files are produced. The builder reads only existing on-disk packages
and the run manifest; any field that cannot be sourced from the
manifest is left null rather than imputed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEL_DIR = REPO_ROOT / "deliveries"
FRESH_DIR = REPO_ROOT / "data" / "freshness_manifest"

P_GE_KEYS = [f"p_ge_{i}" for i in range(1, 21)]

IDENTITY_COLS = [
    "snapshot_type",
    "snapshot_time_utc",
    "delivery_date",
    "game_id",
    "game_start_time_utc",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "is_home",
    "stat",
]
PMF_COLS = (
    ["pmf_json", "mean", "median", "mode", "p0"]
    + P_GE_KEYS
    + [
        "model_version",
        "pmf_source",
        "calibration_source",
        "role_bucket",
        "role_source",
        "calibration_confidence",
    ]
)
MARKET_COLS = [
    "sportsbook",
    "book",
    "market_key",
    "line",
    "over_price_american",
    "under_price_american",
    "market_no_vig_over_prob",
    "market_no_vig_under_prob",
    "model_p_over",
    "model_p_under",
    "fair_over_odds_american",
    "fair_under_odds_american",
    "edge",
    "edge_over",
    "edge_under",
    "market_snapshot_time_utc",
    "market_coverage_status",
]
QUALITY_COLS = [
    "finality_status",
    "finality_blocker_codes",
    "injury_freshness_status",
    "availability_freshness_status",
    "lineup_freshness_status",
    "role_freshness_status",
    "odds_freshness_status",
    "outcomes_freshness_status",
    "tov_status",
    "pmf_valid",
    "pmf_sum_error",
]

FEED_COLS = IDENTITY_COLS + PMF_COLS + MARKET_COLS + QUALITY_COLS


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"  warning: could not parse {path}: {e!r}", file=sys.stderr)
        return None


def _coerce_blocker_codes(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, list):
        return ",".join(str(x) for x in v) if v else None
    return str(v)


def _role_source_from_freshness(role_freshness: Any) -> str | None:
    if not role_freshness or (isinstance(role_freshness, float) and math.isnan(role_freshness)):
        return None
    if role_freshness == "derived_from_projected_minutes":
        return "projected_minutes"
    if role_freshness == "missing":
        return None
    return str(role_freshness)


def _validate_pmf(pmf_json: Any) -> tuple[str, float]:
    """Return (pmf_valid, pmf_sum_error). pmf_valid is 'ok' if PMF sums to
    1 within 1e-6, has no negatives, and no non-finite values; otherwise
    one of {'invalid_negative', 'invalid_non_finite', 'invalid_sum'}."""
    if not pmf_json:
        return ("missing", float("nan"))
    try:
        d = json.loads(pmf_json) if isinstance(pmf_json, str) else dict(pmf_json)
    except Exception:
        return ("invalid_json", float("nan"))
    total = 0.0
    for v in d.values():
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            return ("invalid_non_finite", float("nan"))
        if v < 0:
            return ("invalid_negative", float(abs(1.0 - sum(d.values()))))
        total += float(v)
    err = abs(1.0 - total)
    if err > 1e-6:
        return ("invalid_sum", err)
    return ("ok", err)


def _market_key_for_stat(stat: str) -> str:
    return f"player_{stat}_over_under"


def _none_if_nan(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _row_template() -> dict:
    return {c: None for c in FEED_COLS}


def _populate_identity_pmf_quality(
    row: dict,
    mo_row: pd.Series,
    *,
    snapshot_type: str,
    snapshot_time_utc: str,
    delivery_date: str,
    finality_status: str | None,
    finality_blocker_codes: str | None,
    availability_freshness_status: str | None,
    odds_freshness_status: str | None,
    outcomes_freshness_status: str | None,
) -> None:
    pmf_json = mo_row.get("pmf_json")
    pmf_valid, pmf_sum_error = _validate_pmf(pmf_json)

    role_freshness = _none_if_nan(mo_row.get("role_freshness_status"))

    row.update(
        {
            "snapshot_type": snapshot_type,
            "snapshot_time_utc": snapshot_time_utc,
            "delivery_date": delivery_date,
            "game_id": _none_if_nan(mo_row.get("game_id")),
            "game_start_time_utc": _none_if_nan(mo_row.get("game_start_time")),
            "player_id": _none_if_nan(mo_row.get("player_id")),
            "player_name": _none_if_nan(mo_row.get("player_name")),
            "team": _none_if_nan(mo_row.get("team")),
            "opponent": _none_if_nan(mo_row.get("opponent")),
            "is_home": _none_if_nan(mo_row.get("is_home")),
            "stat": _none_if_nan(mo_row.get("stat")),
            "pmf_json": pmf_json,
            "mean": _none_if_nan(mo_row.get("mean")),
            "median": _none_if_nan(mo_row.get("median")),
            "mode": _none_if_nan(mo_row.get("mode")),
            "p0": _none_if_nan(mo_row.get("p0")),
            **{k: _none_if_nan(mo_row.get(k)) for k in P_GE_KEYS},
            "model_version": _none_if_nan(mo_row.get("model_version")),
            "pmf_source": _none_if_nan(mo_row.get("pmf_source")),
            "calibration_source": _none_if_nan(mo_row.get("calibration_source")),
            "role_bucket": _none_if_nan(mo_row.get("role_bucket")),
            "role_source": _role_source_from_freshness(role_freshness),
            "calibration_confidence": _none_if_nan(mo_row.get("calibration_confidence")),
            "finality_status": finality_status,
            "finality_blocker_codes": finality_blocker_codes,
            "injury_freshness_status": _none_if_nan(mo_row.get("injury_freshness_status")),
            "availability_freshness_status": availability_freshness_status,
            "lineup_freshness_status": _none_if_nan(mo_row.get("lineup_freshness_status")),
            "role_freshness_status": role_freshness,
            "odds_freshness_status": odds_freshness_status,
            "outcomes_freshness_status": outcomes_freshness_status,
            "tov_status": _none_if_nan(mo_row.get("tov_status")),
            "pmf_valid": pmf_valid,
            "pmf_sum_error": pmf_sum_error,
        }
    )


def _populate_market(
    row: dict,
    mc_row: pd.Series | None,
    *,
    market_snapshot_time_utc: str | None,
) -> None:
    if mc_row is None:
        # Model-only row — leave market fields blank but stamp coverage.
        row["market_key"] = _market_key_for_stat(str(row["stat"]))
        row["market_coverage_status"] = "no_market"
        # model_p_over/under remain None for model-only rows: there's no
        # line to evaluate against. Do not impute.
        return

    line = _none_if_nan(mc_row.get("line"))
    book = _none_if_nan(mc_row.get("book"))
    over_price = _none_if_nan(mc_row.get("market_over_odds"))
    under_price = _none_if_nan(mc_row.get("market_under_odds"))
    no_vig_over = _none_if_nan(mc_row.get("market_no_vig_over_prob"))
    no_vig_under = (
        None if no_vig_over is None else max(0.0, min(1.0, 1.0 - float(no_vig_over)))
    )
    model_p_over = _none_if_nan(mc_row.get("model_p_over"))
    model_p_under = (
        None if model_p_over is None else max(0.0, min(1.0, 1.0 - float(model_p_over)))
    )
    edge_over = _none_if_nan(mc_row.get("edge"))
    edge_under = None if edge_over is None else -float(edge_over)

    row.update(
        {
            "sportsbook": book,
            "book": book,
            "market_key": _market_key_for_stat(str(row["stat"])),
            "line": line,
            "over_price_american": over_price,
            "under_price_american": under_price,
            "market_no_vig_over_prob": no_vig_over,
            "market_no_vig_under_prob": no_vig_under,
            "model_p_over": model_p_over,
            "model_p_under": model_p_under,
            "fair_over_odds_american": _none_if_nan(mc_row.get("fair_over_odds_american")),
            "fair_under_odds_american": _none_if_nan(mc_row.get("fair_under_odds_american")),
            "edge": edge_over,
            "edge_over": edge_over,
            "edge_under": edge_under,
            "market_snapshot_time_utc": market_snapshot_time_utc,
            "market_coverage_status": _none_if_nan(mc_row.get("market_coverage_status"))
            or "full",
        }
    )


def build_rows(
    *,
    model_only: pd.DataFrame,
    market_comparison: pd.DataFrame | None,
    snapshot_type: str,
    snapshot_time_utc: str,
    delivery_date: str,
    finality_status: str | None,
    finality_blocker_codes: str | None,
    availability_freshness_status: str | None,
    odds_freshness_status: str | None,
    outcomes_freshness_status: str | None,
    market_snapshot_time_utc: str | None,
) -> list[dict]:
    """Assemble one row per (player, stat, book, line) where market exists,
    plus one model-only row for every (player, stat) without a market match."""
    rows: list[dict] = []
    mc_keys: set[tuple] = set()
    if market_comparison is not None and not market_comparison.empty:
        # Dedup market_comparison by (player_id, stat, book, line) so one
        # repeated quote doesn't double-count.
        mc = market_comparison.drop_duplicates(
            subset=["player_id", "stat", "book", "line"], keep="first"
        ).copy()
        mc_lookup = mc.set_index(["player_id", "stat"], drop=False)
        mc_keys = set(zip(mc["player_id"], mc["stat"]))
    else:
        mc_lookup = None

    for _, mo_row in model_only.iterrows():
        key = (mo_row.get("player_id"), mo_row.get("stat"))
        market_matches: list[pd.Series] = []
        if mc_lookup is not None and key in mc_keys:
            try:
                sub = mc_lookup.loc[[key]]
                # When .loc[[key]] returns a DataFrame iterate rows; when it
                # returns a single Series wrap it.
                if isinstance(sub, pd.DataFrame):
                    market_matches = [r for _, r in sub.iterrows()]
                else:
                    market_matches = [sub]
            except KeyError:
                market_matches = []
        if market_matches:
            for mc_row in market_matches:
                row = _row_template()
                _populate_identity_pmf_quality(
                    row,
                    mo_row,
                    snapshot_type=snapshot_type,
                    snapshot_time_utc=snapshot_time_utc,
                    delivery_date=delivery_date,
                    finality_status=finality_status,
                    finality_blocker_codes=finality_blocker_codes,
                    availability_freshness_status=availability_freshness_status,
                    odds_freshness_status=odds_freshness_status,
                    outcomes_freshness_status=outcomes_freshness_status,
                )
                _populate_market(
                    row,
                    mc_row,
                    market_snapshot_time_utc=market_snapshot_time_utc,
                )
                rows.append(row)
        else:
            row = _row_template()
            _populate_identity_pmf_quality(
                row,
                mo_row,
                snapshot_type=snapshot_type,
                snapshot_time_utc=snapshot_time_utc,
                delivery_date=delivery_date,
                finality_status=finality_status,
                finality_blocker_codes=finality_blocker_codes,
                availability_freshness_status=availability_freshness_status,
                odds_freshness_status=odds_freshness_status,
                outcomes_freshness_status=outcomes_freshness_status,
            )
            _populate_market(
                row,
                None,
                market_snapshot_time_utc=market_snapshot_time_utc,
            )
            rows.append(row)
    return rows


def write_feed_files(
    *,
    rows: list[dict],
    out_dir: Path,
    basename: str,
    write_jsonl: bool,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=FEED_COLS)

    csv_path = out_dir / f"{basename}.csv"
    parquet_path = out_dir / f"{basename}.parquet"
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    df.to_parquet(parquet_path, index=False)

    written = {"csv": str(csv_path.relative_to(REPO_ROOT)),
               "parquet": str(parquet_path.relative_to(REPO_ROOT)),
               "rows": len(df)}

    if write_jsonl:
        jsonl_path = out_dir / f"{basename}.jsonl"
        with jsonl_path.open("w") as f:
            for r in rows:
                # Ensure JSON-safe (no NaN / inf).
                clean = {
                    k: (None if isinstance(v, float) and not math.isfinite(v) else v)
                    for k, v in r.items()
                }
                f.write(json.dumps(clean, default=str) + "\n")
        written["jsonl"] = str(jsonl_path.relative_to(REPO_ROOT))

    return written


def write_latest_available(
    *,
    rows: list[dict],
    out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=FEED_COLS)
    csv_path = out_dir / "latest_available_snapshot.csv"
    parquet_path = out_dir / "latest_available_snapshot.parquet"
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    df.to_parquet(parquet_path, index=False)
    return {
        "csv": str(csv_path.relative_to(REPO_ROOT)),
        "parquet": str(parquet_path.relative_to(REPO_ROOT)),
        "rows": len(df),
    }


def write_feed_readme(out_dir: Path, *, delivery_date: str, manifests: dict) -> Path:
    p = out_dir / "FEED_README.md"
    morning = manifests.get("morning", {})
    lineup = manifests.get("lineup", {})
    lineup_status = manifests.get("lineup_status", {})
    text = []
    text.append(f"# Derek forward feed — {delivery_date}\n\n")
    text.append(
        "This package is the forward-looking PMF feed for the dated slate. "
        "All PMFs are **model-only** and were never market-anchored. "
        "Market columns are reference-only.\n\n"
    )
    text.append("## Files Derek should archive daily\n\n")
    text.append(
        "Open these in order. Archive the entire `derek_forward_feed/` "
        "folder per date.\n\n"
    )
    text.append("- `feed_manifest.json` — provenance, row counts, finality.\n")
    text.append("- `morning_snapshot.csv` — pre-lineup snapshot (canonical).\n")
    text.append("- `morning_snapshot.parquet` — same data, columnar.\n")
    text.append("- `morning_snapshot.jsonl` — same data, one JSON record per line.\n")
    text.append(
        "- `latest_available_snapshot.csv` / `.parquet` — convenience pointer "
        "to the freshest snapshot on disk for this date "
        "(lineup_snapshot when available, else morning_snapshot).\n"
    )
    text.append(
        "- `lineup_snapshot.{csv,parquet,jsonl}` — official-lineup / near-tip "
        "snapshot when produced.\n"
    )
    text.append(
        "- `lineup_snapshot_status.json` — present only when no lineup snapshot "
        "package exists yet; documents the honest reason.\n\n"
    )
    text.append("## Snapshot summary\n\n")
    if morning:
        text.append(
            f"- **morning** rows: {morning.get('rows', '—')}  "
            f"snapshot_time_utc: `{morning.get('snapshot_time_utc', '—')}`\n"
        )
    else:
        text.append("- **morning**: not produced\n")
    if lineup:
        text.append(
            f"- **lineup**  rows: {lineup.get('rows', '—')}  "
            f"snapshot_time_utc: `{lineup.get('snapshot_time_utc', '—')}`\n"
        )
    elif lineup_status:
        text.append(
            f"- **lineup**: not available — status `{lineup_status.get('status')}`\n"
        )
    else:
        text.append("- **lineup**: not requested\n")
    text.append("\n## Schema (per row)\n\n")
    text.append(
        "Identity, model PMF, market reference, quality/finality. The full "
        "column list is documented in the feed_manifest.json `schema` block.\n"
    )
    text.append(
        "- One row per (player, stat, book, line) where a market quote exists.\n"
    )
    text.append(
        "- One model-only row per (player, stat) where no market exists "
        "(book and line blank).\n"
    )
    text.append(
        "- TOV PMFs (when present in canonical) appear as model-only rows.\n\n"
    )
    text.append("## Hard rules\n\n")
    text.append(
        "- PMFs are sourced from `pmf_model_review_package/machine_readable/"
        "model_only.parquet` — the canonical model-only file.\n"
    )
    text.append(
        "- Market fields come from `wizard_of_odds/market_comparison.parquet`. "
        "Market is reference-only; PMFs are never market-anchored.\n"
    )
    text.append(
        "- Phase 10D / 10D.2 TOV overlays are **not** wired in. TOV PMFs "
        "(when emitted) come from Phase 8 calibrators; see the run manifest's "
        "`tov_overlay` and `tov_status`.\n"
    )
    text.append(
        "- After-game outcomes are scored separately under "
        "`deliveries/{date}/after_game_scoring/` once finals are available.\n"
    )
    p.write_text("".join(text))
    return p


def _git_sha_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _discrete_pmf_stats(pmf_json: Any) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    """Return (mean, variance, p10, p50, p90) from a sparse PMF dict."""

    if pmf_json is None or (isinstance(pmf_json, float) and math.isnan(pmf_json)):
        return None, None, None, None, None
    try:
        d = json.loads(pmf_json) if isinstance(pmf_json, str) else dict(pmf_json)
    except Exception:
        return None, None, None, None, None
    if not d:
        return None, None, None, None, None
    ks: list[int] = []
    ps: list[float] = []
    for k, v in d.items():
        try:
            kk = int(k)
            vv = float(v)
        except Exception:
            continue
        if math.isfinite(vv) and vv > 0:
            ks.append(kk)
            ps.append(vv)
    if not ks:
        return None, None, None, None, None
    s = sum(ps)
    if s <= 0:
        return None, None, None, None, None
    ps = [p / s for p in ps]
    mean = float(sum(k * p for k, p in zip(ks, ps)))
    ex2 = float(sum((k * k) * p for k, p in zip(ks, ps)))
    var = max(ex2 - mean * mean, 0.0)
    pairs = sorted(zip(ks, ps), key=lambda x: x[0])
    cdf = 0.0
    qvals = {0.1: None, 0.5: None, 0.9: None}
    for k, p in pairs:
        cdf += p
        for thr in (0.1, 0.5, 0.9):
            if qvals[thr] is None and cdf >= thr - 1e-12:
                qvals[thr] = float(k)
    return mean, var, qvals[0.1], qvals[0.5], qvals[0.9]


def write_m88_unified_feed(
    *,
    date: str,
    out_dir: Path,
    df: pd.DataFrame | None,
    run_mode: str,
    lineup_status: dict | None,
) -> dict | None:
    """Emit ``derek_forward_feed.{parquet,csv,jsonl}`` + ``manifest.json`` (M8.8)."""

    if df is None or df.empty:
        skip = {
            "delivery_date": date,
            "unified_feed_status": "skipped_no_rows",
            "reason": "No latest snapshot dataframe on disk for this run.",
            "checked_at_utc": _now_utc_iso(),
        }
        (out_dir / "derek_forward_feed_unified_skip.json").write_text(
            json.dumps(skip, indent=2) + "\n", encoding="utf-8"
        )
        return None

    stamp_path = out_dir / "feed_manifest.champion_stamp.json"
    stamp = _read_json(stamp_path) or {}
    model_hash = str(stamp.get("champion_model_id") or stamp.get("calibration_run_id") or "")

    official = "not_available_yet"
    unavail_parts: list[str] = []
    if isinstance(lineup_status, dict):
        st = str(lineup_status.get("status") or "")
        if st == "confirmed_lineup_snapshot":
            official = "confirmed_bdl_or_equivalent"
        elif st == "near_tip_projected_lineup_snapshot":
            official = "projected_near_tip_not_bdl_confirmed"
            unavail_parts.append(lineup_status.get("reason") or st)
        elif st == "pending_lineup_snapshot":
            official = "not_available_yet"
            unavail_parts.append(lineup_status.get("reason") or st)

    run_id = str(uuid.uuid4())
    gen_at = _now_utc_iso()
    run_date = gen_at[:10]
    pipe_ver = _git_sha_short()
    has_min_mean = "minutes_mean" in df.columns
    has_min_q50 = "minutes_q50" in df.columns

    rows_out: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        pmf_json = r.get("pmf_json")
        pmean, pvar, p10, p50, p90 = _discrete_pmf_stats(pmf_json)
        m_over = r.get("model_p_over")
        m_over_f = float(m_over) if m_over is not None and not (isinstance(m_over, float) and math.isnan(m_over)) else None
        role = str(r.get("role_bucket") or "")
        inactive = 1.0 if role == "inactive_risk" else 0.0
        mkt = str(r.get("market_coverage_status") or "unknown")
        if mkt in {"", "none", "nan"}:
            mkt_status = "no_offered_market" if r.get("line") is None or (isinstance(r.get("line"), float) and math.isnan(r.get("line"))) else "missing_raw_snapshot"
        else:
            mkt_status = mkt
        fair_o = r.get("fair_over_odds_american")
        fair_u = r.get("fair_under_odds_american")
        inj = str(r.get("injury_freshness_status") or "unknown")
        lin_f = str(r.get("lineup_freshness_status") or "unknown")
        stale_inj = "stale" in inj.lower()
        stale_lin = "stale" in lin_f.lower()
        u_reason = None
        if unavail_parts:
            u_reason = "; ".join(unavail_parts)[:2000]
        if p10 is None or p50 is None:
            u_reason = (u_reason + " | " if u_reason else "") + "pmf_quantiles_derived_from_sparse_pmf_json"

        mu = r.get("model_p_under")
        mu_f = (
            float(mu)
            if mu is not None and not (isinstance(mu, float) and math.isnan(mu))
            else None
        )
        row = {
            "game_date": str(r.get("delivery_date") or date),
            "run_date": run_date,
            "run_id": run_id,
            "run_mode": run_mode,
            "generated_at_utc": gen_at,
            "pipeline_version": pipe_ver,
            "model_version": str(r.get("model_version") or ""),
            "model_artifact_hash": model_hash,
            "source_data_asof_utc": str(r.get("snapshot_time_utc") or gen_at),
            "player_id": r.get("player_id"),
            "player_name": r.get("player_name"),
            "team": r.get("team"),
            "opponent": r.get("opponent"),
            "game_id": r.get("game_id"),
            "event_id": None,
            "stat": r.get("stat"),
            "line": r.get("line"),
            "role_bucket": r.get("role_bucket"),
            "hard_role_bucket": r.get("role_bucket"),
            "role_mixture_enabled": bool(r.get("role_mixture_enabled", True)),
            "role_mixture_weights_json": r.get("role_mixture_weights_json"),
            "role_entropy": r.get("role_entropy"),
            "role_bucket_confidence": r.get("role_bucket_confidence"),
            "projected_minutes": r.get("minutes_mean") if has_min_mean else None,
            "minutes_q10": None,
            "minutes_q50": r.get("minutes_q50") if has_min_q50 else None,
            "minutes_q90": None,
            "inactive_risk": inactive,
            "expected_lineup_status": lin_f,
            "official_lineup_status": official,
            "injury_status": inj,
            "injury_source": "bdl_availability_freshness_manifest",
            "injury_last_updated_utc": None,
            "lineup_source": "bdl_lineup_freshness_manifest",
            "lineup_last_updated_utc": None,
            "stale_injury_flag": stale_inj,
            "stale_lineup_flag": stale_lin,
            "model_prob_over_raw": m_over_f,
            "model_prob_over_active": m_over_f,
            "model_prob_under_active": mu_f,
            "fair_over_odds": fair_o,
            "fair_under_odds": fair_u,
            "pmf_mean": pmean if pmean is not None else r.get("mean"),
            "pmf_variance": pvar,
            "pmf_p10": p10,
            "pmf_p50": p50 if p50 is not None else r.get("median"),
            "pmf_p90": p90,
            "market_prob_over": r.get("market_no_vig_over_prob"),
            "no_vig_market_prob_over": r.get("market_no_vig_over_prob"),
            "edge": r.get("edge"),
            "market_status": mkt_status,
            "delivery_status": "ready",
            "unavailable_reason": u_reason,
            "calculation_source": "build_derek_forward_feed:v1_model_only_plus_market_reference",
            "calculation_status": "ok",
        }
        rows_out.append(row)

    out_df = pd.DataFrame(rows_out)
    pq_out = out_dir / "derek_forward_feed.parquet"
    csv_out = out_dir / "derek_forward_feed.csv"
    jl_out = out_dir / "derek_forward_feed.jsonl"
    out_df.to_parquet(pq_out, index=False)
    out_df.to_csv(csv_out, index=False, quoting=csv.QUOTE_MINIMAL)
    with jl_out.open("w", encoding="utf-8") as f:
        for rec in rows_out:
            f.write(json.dumps(rec, default=str) + "\n")
    man = {
        "delivery_date": date,
        "run_mode": run_mode,
        "generated_at_utc": gen_at,
        "row_count": int(len(out_df)),
        "schema": "m88_derek_unified_v1",
        "lineup_status": lineup_status,
        "files": {
            "parquet": str(pq_out.relative_to(REPO_ROOT)),
            "csv": str(csv_out.relative_to(REPO_ROOT)),
            "jsonl": str(jl_out.relative_to(REPO_ROOT)),
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(man, indent=2, default=str) + "\n", encoding="utf-8")
    return man


def build_snapshot(
    *,
    date: str,
    snapshot_label: str,
    snapshot_type_value: str,
    out_dir: Path,
    write_jsonl: bool = True,
) -> dict | None:
    """Build a single snapshot (`morning` or `lineup`). Returns the
    feed_manifest entry for this snapshot, or None if the inputs are
    missing."""
    base = DEL_DIR / date
    review_pkg = base / "pmf_model_review_package" / "machine_readable"
    woo = base / "wizard_of_odds"
    model_only_path = review_pkg / "model_only.parquet"
    market_comparison_path = woo / "market_comparison.parquet"
    run_manifest_path = woo / "run_manifest.json"
    freshness_path = FRESH_DIR / f"{date}.json"

    if not model_only_path.exists():
        print(
            f"  [{snapshot_label}] missing {model_only_path.relative_to(REPO_ROOT)}; "
            "no source PMFs",
            file=sys.stderr,
        )
        return None

    model_only = pd.read_parquet(model_only_path)
    market_comparison = (
        pd.read_parquet(market_comparison_path)
        if market_comparison_path.exists()
        else None
    )
    run_manifest = _read_json(run_manifest_path) or {}
    freshness_manifest = _read_json(freshness_path) or {}

    # Stamp the snapshot_type for this snapshot (overrides whatever was
    # baked into model_only by the upstream build for the morning row).
    finality_status = run_manifest.get("finality_status")
    finality_blocker_codes = _coerce_blocker_codes(
        run_manifest.get("finality_blocker_codes")
    )
    snapshot_time_utc = run_manifest.get("snapshot_time_utc") or _now_utc_iso()
    market_snapshot_time_utc = (
        run_manifest.get("sources", {}).get("odds_snapshot", {}).get("mtime_utc")
    )
    availability_freshness_status = freshness_manifest.get(
        "availability_freshness_status"
    )
    odds_freshness_status = (
        freshness_manifest.get("odds", {}).get("status")
        if isinstance(freshness_manifest.get("odds"), dict)
        else None
    )
    outcomes_freshness_status = (
        freshness_manifest.get("finals", {}).get("finality_status")
        if isinstance(freshness_manifest.get("finals"), dict)
        else None
    )

    rows = build_rows(
        model_only=model_only,
        market_comparison=market_comparison,
        snapshot_type=snapshot_type_value,
        snapshot_time_utc=snapshot_time_utc,
        delivery_date=date,
        finality_status=finality_status,
        finality_blocker_codes=finality_blocker_codes,
        availability_freshness_status=availability_freshness_status,
        odds_freshness_status=odds_freshness_status,
        outcomes_freshness_status=outcomes_freshness_status,
        market_snapshot_time_utc=market_snapshot_time_utc,
    )

    written = write_feed_files(
        rows=rows,
        out_dir=out_dir,
        basename=f"{snapshot_label}_snapshot",
        write_jsonl=write_jsonl,
    )

    return {
        "snapshot_type": snapshot_type_value,
        "snapshot_time_utc": snapshot_time_utc,
        "rows": len(rows),
        "model_only_rows_used": len(model_only),
        "market_rows_referenced": (
            0 if market_comparison is None else int(len(market_comparison))
        ),
        "files": written,
        "model_only_source": str(model_only_path.relative_to(REPO_ROOT)),
        "market_comparison_source": (
            str(market_comparison_path.relative_to(REPO_ROOT))
            if market_comparison_path.exists()
            else None
        ),
        "run_manifest_source": (
            str(run_manifest_path.relative_to(REPO_ROOT))
            if run_manifest_path.exists()
            else None
        ),
        "freshness_manifest_source": (
            str(freshness_path.relative_to(REPO_ROOT))
            if freshness_path.exists()
            else None
        ),
        "rows_with_market": sum(1 for r in rows if r.get("line") is not None),
        "rows_model_only": sum(1 for r in rows if r.get("line") is None),
        "tov_rows": sum(1 for r in rows if r.get("stat") == "tov"),
    }


def _lineup_snapshot_present(date: str) -> bool:
    """True only when an upstream lineup-locked package exists. We do not
    fabricate a lineup snapshot from morning data."""
    base = DEL_DIR / date
    woo = base / "wizard_of_odds"
    rm = _read_json(woo / "run_manifest.json")
    if not isinstance(rm, dict):
        return False
    return rm.get("snapshot_type") in {"pre_close", "close_lock", "lineup"}


def _resolve_lineup_snapshot_type(date: str) -> tuple[str, str | None]:
    """Phase 12D — when the upstream wizard_of_odds package is a
    pre_close / close_lock build but BDL has not yet posted confirmed
    lineups, the Derek snapshot should be labelled `near_tip` (with the
    honest lineup_freshness_status), not `lineup`. Returns (snapshot_type,
    lineup_freshness_rollup_summary)."""
    base = DEL_DIR / date
    rm = _read_json(base / "wizard_of_odds" / "run_manifest.json") or {}
    qr = rm.get("quality_rollup") or {}
    rollup = qr.get("lineup_freshness_status") or {}
    if not isinstance(rollup, dict):
        return ("near_tip", None)
    statuses = set(rollup.keys())
    summary = ",".join(f"{k}={v}" for k, v in rollup.items())
    if "confirmed_bdl" in statuses or "confirmed" in statuses:
        return ("lineup", summary)
    return ("near_tip", summary)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, help="delivery date YYYY-MM-DD")
    ap.add_argument(
        "--run-mode",
        default="unspecified",
        help="M8.8 stamp for unified Derek feed (morning_expected|t25|t5|final_after_game|backtest|unspecified).",
    )
    ap.add_argument(
        "--snapshot",
        choices=["morning", "lineup", "both"],
        default="both",
        help="which snapshot to build",
    )
    args = ap.parse_args()

    out_dir = DEL_DIR / args.date / "derek_forward_feed"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"derek forward feed — date={args.date}  snapshot={args.snapshot}")
    print(f"  out_dir={out_dir.relative_to(REPO_ROOT)}")
    print("=" * 72)

    morning_entry: dict | None = None
    lineup_entry: dict | None = None
    lineup_status_payload: dict | None = None
    latest_rows: list[dict] | None = None
    latest_label = None

    if args.snapshot in {"morning", "both"}:
        morning_entry = build_snapshot(
            date=args.date,
            snapshot_label="morning",
            snapshot_type_value="morning",
            out_dir=out_dir,
        )
        if morning_entry is None:
            print(
                "  morning: cannot build — model_only.parquet missing for this date",
                file=sys.stderr,
            )
            blocker = (
                f"# Derek forward feed blocker — {args.date}\n\n"
                "morning snapshot could not be built because\n"
                f"`deliveries/{args.date}/pmf_model_review_package/machine_readable/"
                "model_only.parquet` is missing. Run `predict.py` and "
                "`build_daily_pmf_delivery.py` for this date first.\n"
            )
            (DEL_DIR / "DEREK_FORWARD_FEED_BLOCKERS.md").write_text(blocker)
            return 2

    if args.snapshot in {"lineup", "both"}:
        if _lineup_snapshot_present(args.date):
            snapshot_type_value, lineup_rollup = _resolve_lineup_snapshot_type(
                args.date)
            lineup_entry = build_snapshot(
                date=args.date,
                snapshot_label="lineup",
                snapshot_type_value=snapshot_type_value,
                out_dir=out_dir,
            )
            # Always write a status file alongside the lineup snapshot so
            # Derek can see at a glance whether lineups were confirmed.
            lineup_status_payload = {
                "status": (
                    "confirmed_lineup_snapshot"
                    if snapshot_type_value == "lineup"
                    else "near_tip_projected_lineup_snapshot"
                ),
                "snapshot_type_emitted": snapshot_type_value,
                "lineup_freshness_rollup": lineup_rollup,
                "reason": (
                    "Confirmed BDL lineup data was present in the upstream "
                    "wizard_of_odds package."
                    if snapshot_type_value == "lineup"
                    else "Upstream wizard_of_odds package contains projected "
                    "(not BDL-confirmed) lineup data; snapshot labelled "
                    "near_tip to keep Derek's archive honest."
                ),
                "checked_at_utc": _now_utc_iso(),
            }
            (out_dir / "lineup_snapshot_status.json").write_text(
                json.dumps(lineup_status_payload, indent=2)
            )
            print(
                f"  lineup: emitted as snapshot_type={snapshot_type_value!r}"
            )
        else:
            lineup_status_payload = {
                "status": "pending_lineup_snapshot",
                "reason": (
                    "No pre_close/close_lock/lineup snapshot is on disk for "
                    f"deliveries/{args.date}/wizard_of_odds/. The current "
                    "wizard_of_odds/run_manifest.json snapshot_type is "
                    "'morning'. Run scripts/run_daily_delivery_pipeline.py "
                    f"--date {args.date} --mode pre_close (or close_lock) "
                    "to produce a lineup-aware delivery."
                ),
                "checked_at_utc": _now_utc_iso(),
            }
            (out_dir / "lineup_snapshot_status.json").write_text(
                json.dumps(lineup_status_payload, indent=2)
            )
            print(
                "  lineup: not present — wrote lineup_snapshot_status.json "
                "(no fabrication)"
            )

    # latest_available_snapshot — copy of the most recent snapshot we
    # actually produced. Read the rows back from the snapshot files we
    # just wrote (avoids re-running build_rows).
    if lineup_entry is not None:
        latest_label = "lineup"
        latest_rows_df = pd.read_parquet(out_dir / "lineup_snapshot.parquet")
    elif morning_entry is not None:
        latest_label = "morning"
        latest_rows_df = pd.read_parquet(out_dir / "morning_snapshot.parquet")
    else:
        latest_rows_df = None

    latest_files = None
    if latest_rows_df is not None:
        # Re-emit rather than copy so the file modification time reflects
        # this run.
        latest_files = write_latest_available(
            rows=latest_rows_df.to_dict(orient="records"),
            out_dir=out_dir,
        )

    feed_manifest = {
        "delivery_date": args.date,
        "built_at_utc": _now_utc_iso(),
        "snapshot": args.snapshot,
        "morning": morning_entry,
        "lineup": lineup_entry,
        "lineup_status": lineup_status_payload,
        "latest_available_snapshot": {
            "points_to": latest_label,
            "files": latest_files,
        },
        "schema": {
            "columns": FEED_COLS,
            "identity": IDENTITY_COLS,
            "pmf": PMF_COLS,
            "market": MARKET_COLS,
            "quality": QUALITY_COLS,
        },
        "rules": {
            "pmf_source": "model_only.parquet (canonical)",
            "market_source": "market_comparison.parquet (reference-only)",
            "no_market_anchoring": True,
            "tov_overlay_phase10d": "off",
        },
    }
    (out_dir / "feed_manifest.json").write_text(json.dumps(feed_manifest, indent=2, default=str))
    write_feed_readme(
        out_dir,
        delivery_date=args.date,
        manifests={
            "morning": morning_entry,
            "lineup": lineup_entry,
            "lineup_status": lineup_status_payload,
        },
    )

    write_m88_unified_feed(
        date=args.date,
        out_dir=out_dir,
        df=latest_rows_df,
        run_mode=str(args.run_mode),
        lineup_status=lineup_status_payload,
    )

    print("\nfeed manifest summary:")
    if morning_entry:
        print(
            f"  morning rows={morning_entry['rows']}  "
            f"with_market={morning_entry['rows_with_market']}  "
            f"model_only={morning_entry['rows_model_only']}  "
            f"tov={morning_entry['tov_rows']}"
        )
    if lineup_entry:
        print(
            f"  lineup  rows={lineup_entry['rows']}  "
            f"with_market={lineup_entry['rows_with_market']}  "
            f"model_only={lineup_entry['rows_model_only']}  "
            f"tov={lineup_entry['tov_rows']}"
        )
    elif lineup_status_payload:
        print(f"  lineup  status={lineup_status_payload['status']}")
    if latest_files:
        print(
            f"  latest_available -> {latest_label}  rows={latest_files['rows']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
