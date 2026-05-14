"""Run M8.6 event-market stack for Phase 8 / run_diagnostics integration."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _run(repo: Path, py: str, args: list[str]) -> int:
    r = subprocess.run([py, *args], cwd=str(repo))
    return int(r.returncode)


def ensure_inventory(
    repo: Path,
    py: str,
    *,
    start_date: str,
    end_date: str,
    snapshot_substr: str,
) -> Path:
    out = repo / "artifacts" / "model_diagnostics" / "event_market_backtest_date_inventory.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rc = _run(
        repo,
        py,
        [
            str(repo / "scripts" / "find_available_event_market_backtest_dates.py"),
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--snapshot-substr",
            snapshot_substr,
        ],
    )
    if rc != 0 or not out.exists():
        raise RuntimeError(f"EVENT_MARKET_INVENTORY_FAIL rc={rc} expected={out}")
    return out


def run_event_market_stack(
    repo: Path,
    py: str,
    *,
    dates_file: Path,
    snapshot_substr: str,
    allow_provisional_block: bool,
) -> dict:
    """Run loss rows → audit → stat-role → promotion → verifier. Returns summary dict."""
    inv = Path(dates_file)
    if not inv.exists():
        raise FileNotFoundError(f"dates_file missing: {inv}")

    steps: list[dict] = []
    scripts_seq: list[tuple[str, list[str]]] = [
        (
            "build_backtest_delivery_range.py",
            [
                str(repo / "scripts" / "build_backtest_delivery_range.py"),
                "--dates-file",
                str(inv),
                "--skip-existing",
                "--no-public-export",
            ],
        ),
        (
            "build_event_market_loss_rows.py",
            [
                str(repo / "scripts" / "build_event_market_loss_rows.py"),
                "--dates-file",
                str(inv),
                "--snapshot-substr",
                snapshot_substr,
            ],
        ),
        (
            "audit_event_market_coverage_by_stat.py",
            [
                str(repo / "scripts" / "audit_event_market_coverage_by_stat.py"),
                "--dates-file",
                str(inv),
                "--snapshot-substr",
                snapshot_substr,
            ],
        ),
        (
            "build_stat_role_market_superiority_report.py",
            [
                str(repo / "scripts" / "build_stat_role_market_superiority_report.py"),
                "--dates-file",
                str(inv),
            ],
        ),
        (
            "build_promotion_claim_report.py",
            [
                str(repo / "scripts" / "build_promotion_claim_report.py"),
                "--dates-file",
                str(inv),
            ],
        ),
    ]
    for name, cmd in scripts_seq:
        rc = _run(repo, py, cmd)
        steps.append({"script": name, "rc": rc})
        if rc != 0:
            return {"ok": False, "failed_script": name, "steps": steps}

    sys.path.insert(0, str(repo / "scripts"))
    from event_market_date_selection import (  # noqa: WPS433
        dates_fingerprint,
        load_dates_from_inventory_csv,
    )

    dates, _df = load_dates_from_inventory_csv(inv, eligible_only=True)
    label = f"dates_{dates_fingerprint(dates)}"
    eml = repo / "artifacts" / "model_diagnostics" / f"event_market_loss_rows_{label}.parquet"
    meta_path = Path(str(eml) + ".meta.json")
    n_rows = n_matched = n_scored = 0
    if eml.exists():
        combo = pd.read_parquet(eml)
        n_rows = int(len(combo))
        if "join_status" in combo.columns:
            n_matched = int((combo["join_status"] == "matched").sum())
        if len(combo) and "model_prob_over" in combo.columns:
            sm = (
                combo["model_prob_over"].notna()
                & combo.get("market_prob_over_no_vig", pd.Series(np.nan, index=combo.index)).notna()
                & combo["hit_result"].notna()
            )
            if "model_event_logloss" in combo.columns:
                sm &= combo["model_event_logloss"].notna() & combo["market_event_logloss"].notna()
            n_scored = int(sm.sum())
    meta: dict = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    sup = repo / "artifacts" / "model_diagnostics" / f"event_market_superiority_{label}" / "summary.json"
    summ: dict = {}
    if sup.exists():
        summ = json.loads(sup.read_text(encoding="utf-8"))

    strict_cmd = [
        str(repo / "scripts" / "verify_market_superiority_by_stat_role_contract.py"),
        "--dates-file",
        str(inv),
    ]
    strict_rc = _run(repo, py, strict_cmd)
    prov_rc = None
    if allow_provisional_block:
        prov_rc = _run(repo, py, strict_cmd + ["--allow-provisional-block"])

    return {
        "ok": True,
        "dates_file": str(inv.relative_to(repo)),
        "label": label,
        "dates_used": dates,
        "n_event_market_rows": n_rows,
        "n_matched_rows": n_matched,
        "n_scored_rows": n_scored,
        "eml_meta": meta,
        "superiority_summary": summ,
        "strict_verifier_exit_code": strict_rc,
        "provisional_verifier_exit_code": prov_rc,
        "steps": steps,
    }
