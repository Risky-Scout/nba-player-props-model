#!/usr/bin/env python3
"""Audit ``deliveries/<DATE>/`` trees against ``delivery_contract`` (M8.8)."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.delivery.delivery_contract import (  # noqa: E402
    FilePresence,
    RunMode,
    banned_placeholder_tokens,
    delivery_file_specs,
    explicit_status_tokens,
    infer_run_mode_for_delivery_date,
)

OPTIONAL_AFTER_GAME_PLACEHOLDER_REL = (
    "after_game_scoring/after_game_scoring_placeholder_manifest.json"
)


def _read_json(p: Path) -> dict[str, Any]:
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _daterange(start: str, end: str) -> list[str]:
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    out: list[str] = []
    cur = d0
    while cur <= d1:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _effective_presence(
    rel: str,
    base_pres: FilePresence,
    mode: RunMode,
    delivery_root: Path,
) -> tuple[FilePresence, str | None]:
    """Downgrade Derek unified requirements when no lineup snapshot exists."""

    if rel.startswith("derek_forward_feed/derek_forward_feed.") and mode in (
        RunMode.T25,
        RunMode.T5,
    ):
        ls = delivery_root / "derek_forward_feed" / "lineup_snapshot.parquet"
        if not ls.is_file():
            return FilePresence.OPTIONAL, "lineup_snapshot_absent_unified_feed_skipped"
    return base_pres, None


def _after_game_bundle_ok(mode: RunMode, delivery_root: Path) -> tuple[bool, str | None]:
    ag = delivery_root / "after_game_scoring"
    ph = ag / "after_game_scoring_placeholder_manifest.json"
    st = ag / "after_game_status.json"
    pq = ag / "after_game_scoring.parquet"
    sm = ag / "scoring_manifest.json"

    if pq.is_file():
        try:
            if len(pd.read_parquet(pq)) > 0:
                return True, None
        except Exception as exc:
            return False, f"after_game_scoring_unreadable:{exc}"

    if ph.is_file():
        return True, "pending_placeholder"

    if sm.is_file():
        return True, "scoring_inputs_manifest_present"

    j = _read_json(st)
    status = str(j.get("after_game_status") or "")
    if mode == RunMode.FINAL_AFTER_GAME:
        if status == "pending_outcomes":
            return True, "pending_outcomes"
        if status == "scored" and int(j.get("n_scored_pmf_rows") or 0) > 0:
            return True, None
        if status == "scored" and int(j.get("n_scored_pmf_rows") or 0) == 0:
            return True, "scored_zero_rows_waiting_reload"
        return False, "final_after_game_missing_status_or_scores"

    if st.is_file() and status:
        return True, status

    return False, "after_game_scoring_missing_bundle"


def _scan_placeholders_text(path: Path) -> list[str]:
    hits: list[str] = []
    banned = banned_placeholder_tokens()
    try:
        txt = path.read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        return ["unreadable_file"]
    for b in banned:
        if b in txt:
            hits.append(b)
    return hits


def _scan_placeholders_parquet(path: Path, max_rows: int = 8000) -> list[str]:
    hits: list[str] = []
    banned = [b.lower() for b in banned_placeholder_tokens()]
    try:
        df = pd.read_parquet(path)
    except Exception:
        return ["parquet_unreadable"]
    obj_cols = [c for c in df.columns if df[c].dtype == object]
    sample = df[obj_cols].head(max_rows) if obj_cols else pd.DataFrame()
    for col in sample.columns:
        for v in sample[col].dropna().astype(str).str.lower().unique():
            for b in banned:
                if b in v:
                    hits.append(f"{col}:{b}")
    return hits


def _check_columns(
    path: Path,
    required: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    miss = []
    bad_null = []
    if not required:
        return miss, bad_null
    try:
        if path.suffix == ".parquet":
            df = pd.read_parquet(path, columns=None)
            cols = {str(c).lower() for c in df.columns}
            miss = [c for c in required if str(c).lower() not in cols]
            if "unavailable_reason" in cols:
                ur_col = next(x for x in df.columns if str(x).lower() == "unavailable_reason")
                for c in required:
                    ccol = next(
                        (x for x in df.columns if str(x).lower() == str(c).lower()),
                        None,
                    )
                    if ccol is None or ccol == ur_col:
                        continue
                    m = df[ccol].isna() & df[ur_col].isna()
                    if m.any():
                        bad_null.append(str(ccol))
        elif path.suffix == ".csv":
            df = pd.read_csv(path, nrows=5000)
            cols = {str(c).lower() for c in df.columns}
            miss = [c for c in required if str(c).lower() not in cols]
        elif path.suffix == ".jsonl":
            miss = list(required)
        else:
            return [], []
    except Exception as exc:
        return [f"read_error:{exc}"], []
    return miss, bad_null


def audit_date(
    delivery_root: Path,
    delivery_date: str,
    mode: RunMode | None,
    *,
    include_current: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mode_eff = mode or infer_run_mode_for_delivery_date(REPO_ROOT, delivery_date)
    today_et = datetime.now().strftime("%Y-%m-%d")
    for spec in delivery_file_specs():
        rel = spec.relative_path
        path = delivery_root / rel
        pres, pres_note = _effective_presence(rel, spec.presence[mode_eff], mode_eff, delivery_root)
        row_base = {
            "date": delivery_date,
            "run_mode": mode_eff.value,
            "folder": str(Path(rel).parent),
            "file": Path(rel).name,
            "relative_path": rel,
            "expected": pres.value,
            "presence_override": pres_note,
            "exists": path.is_file(),
            "row_count": None,
            "required_columns_present": None,
            "missing_required_columns": "",
            "unexpected_null_required_columns": "",
            "placeholder_value_count": 0,
            "llm_generated_value_suspected": False,
            "pmf_validity_pass": None,
            "market_columns_present": None,
            "injury_columns_present": None,
            "lineup_columns_present": None,
            "role_minutes_columns_present": None,
            "derek_feed_ready": None,
            "failure_reason": "",
        }

        if pres == FilePresence.NOT_APPLICABLE:
            row_base["failure_reason"] = "not_applicable"
            rows.append(row_base)
            continue

        if pres == FilePresence.PENDING_MANIFEST_OK and rel.startswith("after_game_scoring/"):
            ok, reason = _after_game_bundle_ok(mode_eff, delivery_root)
            if not ok:
                row_base["exists"] = False
                row_base["failure_reason"] = reason or "after_game_fail"
                rows.append(row_base)
                continue
            if not path.is_file():
                row_base["exists"] = False
                row_base["failure_reason"] = ""
                rows.append(row_base)
                continue
            # fall through — validate on-disk artifacts when present

        if pres == FilePresence.OPTIONAL and not path.is_file():
            row_base["failure_reason"] = "optional_missing"
            rows.append(row_base)
            continue

        if pres in (FilePresence.REQUIRED, FilePresence.OPTIONAL) and not path.is_file():
            if pres == FilePresence.OPTIONAL:
                row_base["failure_reason"] = "optional_missing"
            else:
                row_base["failure_reason"] = "missing_required_file"
            rows.append(row_base)
            continue

        if path.suffix in {".parquet", ".csv"} and spec.required_columns:
            miss, badn = _check_columns(path, spec.required_columns)
            row_base["required_columns_present"] = len(miss) == 0
            row_base["missing_required_columns"] = "|".join(miss)
            row_base["unexpected_null_required_columns"] = "|".join(badn)
            if "pmf_valid" in spec.required_columns and path.suffix == ".parquet":
                try:
                    df = pd.read_parquet(path, columns=["pmf_valid"])
                    row_base["pmf_validity_pass"] = bool((df["pmf_valid"] == "ok").mean() > 0.95)
                except Exception:
                    row_base["pmf_validity_pass"] = False

        if path.suffix == ".parquet":
            try:
                row_base["row_count"] = int(len(pd.read_parquet(path)))
            except Exception:
                row_base["row_count"] = -1
        elif path.suffix == ".csv":
            try:
                row_base["row_count"] = sum(1 for _ in open(path, encoding="utf-8")) - 1
            except Exception:
                row_base["row_count"] = -1

        phits: list[str] = []
        if path.suffix in {".csv", ".jsonl", ".md", ".html", ".json"}:
            phits = _scan_placeholders_text(path)
        elif path.suffix == ".parquet":
            phits = _scan_placeholders_parquet(path)
        row_base["placeholder_value_count"] = len(phits)
        if phits:
            # The ``after_game_scoring_placeholder_manifest.json`` file
            # is an intentional pre-game stub whose content literally
            # contains the word "placeholder" (e.g. the ``reason``
            # field reads "...placeholder until scripts/score_daily_
            # pmf_delivery_after_game.py runs."). The audit's
            # banned-token scan otherwise reads that legitimate
            # content as ``placeholder_or_banned_token`` and fails
            # the run (run 26012478679 — daily_pmf_delivery on
            # delivery_date=2026-05-18 failed at
            # DAILY_DELIVERY_COMPLETENESS_AUDIT_FAIL because the
            # exemption below only fired in ``morning_expected`` mode,
            # not in ``t25`` / ``t5`` / pre-tipoff runs where the same
            # legitimate placeholder file is also present).
            #
            # Exempt the placeholder manifest from the banned-token
            # scan in EVERY pre-game mode. In ``FINAL_AFTER_GAME`` the
            # placeholder manifest is genuinely stale (the real
            # ``after_game_scoring.parquet`` should have replaced it),
            # so the scan keeps biting there and surfaces a real
            # post-game pipeline regression.
            pregame_modes = (
                RunMode.MORNING_EXPECTED,
                RunMode.T25,
                RunMode.T5,
                RunMode.BACKTEST,
            )
            if (
                rel == OPTIONAL_AFTER_GAME_PLACEHOLDER_REL
                and mode_eff in pregame_modes
                and pres == FilePresence.OPTIONAL
            ):
                row_base["optional_after_game_placeholder_warn"] = True
                row_base["failure_reason"] = ""
            else:
                row_base["failure_reason"] = "placeholder_or_banned_token"
        if "derek_forward_feed" in rel and rel.endswith(".parquet"):
            miss = row_base["missing_required_columns"]
            row_base["derek_feed_ready"] = path.is_file() and not miss
            row_base["injury_columns_present"] = None
            row_base["lineup_columns_present"] = None
            if path.is_file() and not miss:
                try:
                    df = pd.read_parquet(path, columns=["injury_status", "official_lineup_status"])
                    row_base["injury_columns_present"] = True
                    row_base["lineup_columns_present"] = True
                except Exception:
                    row_base["injury_columns_present"] = False

        if spec.min_rows and row_base["row_count"] is not None and row_base["row_count"] < spec.min_rows:
            row_base["failure_reason"] = row_base["failure_reason"] or "min_rows_not_met"

        rows.append(row_base)

    if include_current and delivery_date == today_et:
        ag = delivery_root / "after_game_scoring"
        st = _read_json(ag / "after_game_status.json")
        if st.get("after_game_status") == "pending_outcomes":
            rows.append(
                {
                    "date": delivery_date,
                    "run_mode": mode_eff.value,
                    "folder": "after_game_scoring",
                    "file": "same_day_pending",
                    "relative_path": "after_game_scoring/pending_actuals_note",
                    "expected": "info",
                    "presence_override": None,
                    "exists": True,
                    "failure_reason": "pending_actuals_same_day_slate",
                }
            )

    return rows


def _passes(rows: list[dict[str, Any]]) -> bool:
    explicit_ok = {"optional_missing", "not_applicable", "pending_placeholder", ""}
    for r in rows:
        fr = str(r.get("failure_reason") or "")
        exp = str(r.get("expected") or "")
        if exp == "optional" and fr == "optional_missing":
            continue
        if exp == "pending_manifest_ok" and fr in explicit_ok:
            continue
        if exp == "pending_manifest_ok" and r.get("exists"):
            continue
        if fr and fr not in explicit_ok:
            if fr == "pending_actuals_same_day_slate":
                continue
            return False
        if str(r.get("expected")) == "required" and not r.get("exists"):
            return False
        if r.get("required_columns_present") is False:
            return False
        if int(r.get("placeholder_value_count") or 0) > 0:
            if r.get("optional_after_game_placeholder_warn"):
                continue
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument(
        "--include-current-if-present",
        action="store_true",
        help="Annotate same-day pending actuals when delivery date is today (ET clock not enforced here).",
    )
    ap.add_argument(
        "--run-mode",
        choices=[m.value for m in RunMode],
        default=None,
        help="Force a single run mode for every date (default: infer from artifacts).",
    )
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    forced = RunMode(args.run_mode) if args.run_mode else None
    all_rows: list[dict[str, Any]] = []
    for d in _daterange(args.start_date, args.end_date):
        root = REPO_ROOT / "deliveries" / d
        if not root.is_dir():
            all_rows.append(
                {
                    "date": d,
                    "run_mode": "missing_delivery_root",
                    "folder": "",
                    "file": "",
                    "relative_path": "",
                    "expected": "required",
                    "exists": False,
                    "failure_reason": "missing_delivery_date_folder",
                }
            )
            continue
        all_rows.extend(
            audit_date(
                root,
                d,
                forced,
                include_current=bool(args.include_current_if_present),
            )
        )

    inv_path = out_dir / "delivery_inventory.csv"
    with inv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in all_rows for k in r.keys()}))
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    missing = [r for r in all_rows if r.get("failure_reason") == "missing_required_file"]
    with (out_dir / "missing_files.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in missing for k in r.keys()}))
        w.writeheader()
        for r in missing:
            w.writerow(r)

    mcol = [r for r in all_rows if r.get("missing_required_columns")]
    with (out_dir / "missing_columns.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in mcol for k in r.keys()}))
        w.writeheader()
        for r in mcol:
            w.writerow(r)

    badv = [r for r in all_rows if int(r.get("placeholder_value_count") or 0) > 0]
    with (out_dir / "invalid_values.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in badv for k in r.keys()}))
        w.writeheader()
        for r in badv:
            w.writerow(r)

    ok = _passes(all_rows)
    summ = {
        "start_date": args.start_date,
        "end_date": args.end_date,
        "n_inventory_rows": len(all_rows),
        "pass_all": ok,
        "n_missing_files": len(missing),
        "n_missing_column_rows": len(mcol),
        "n_placeholder_hits": len(badv),
        "explicit_status_tokens": sorted(explicit_status_tokens()),
    }
    (out_dir / "summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8")
    md = [
        f"# Daily delivery completeness ({args.start_date} … {args.end_date})",
        "",
        f"- **pass_all**: `{ok}`",
        f"- Missing files: **{len(missing)}**",
        f"- Missing-column audit rows: **{len(mcol)}**",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if any(bool(r.get("optional_after_game_placeholder_warn")) for r in all_rows):
        print("DAILY_DELIVERY_COMPLETENESS_OPTIONAL_PLACEHOLDER_WARN")
    if ok:
        print("DAILY_DELIVERY_COMPLETENESS_AUDIT_PASS")
    else:
        print("DAILY_DELIVERY_COMPLETENESS_AUDIT_FAIL")
    print(f"  wrote: {out_dir.relative_to(REPO_ROOT)}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
