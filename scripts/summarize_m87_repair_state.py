#!/usr/bin/env python3
"""Summarize M8.7 repair manifests, diagnostics, and verifier state (read-only)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ART = REPO_ROOT / "artifacts" / "model_diagnostics"
MODELS = REPO_ROOT / "artifacts" / "models"


def _read_json(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _git_ts(path: str) -> int | None:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", path],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return int(out) if out else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    label = str(args.label)

    ev_path = MODELS / f"event_neutral_probability_scale_repair_{label}.json"
    ms_path = MODELS / f"pmf_mean_shift_repair_{label}.json"
    led_path = ART / f"market_superiority_repair_{label}" / "repair_ledger.csv"
    pmf_dir = ART / f"pmf_mean_shift_repair_{label}"
    sup_dir = ART / f"event_market_superiority_{label}"
    math_summ = ART / f"market_superiority_math_contract_{label}" / "summary.json"
    loss_pq = ART / f"event_market_loss_rows_{label}.parquet"
    prom_path = sup_dir / f"promotion_claim_report_{label}.json"

    ev = _read_json(ev_path)
    ms = _read_json(ms_path)
    n_ev_accept = 0
    if ev and isinstance(ev.get("segments"), dict):
        n_ev_accept = sum(1 for s in ev["segments"].values() if isinstance(s, dict) and s.get("accepted"))
    n_ms_accept = 0
    n_ms_roll = 0
    if ms and isinstance(ms.get("segments"), dict):
        for s in ms["segments"].values():
            if not isinstance(s, dict):
                continue
            if s.get("accepted"):
                n_ms_accept += 1
    summ_ms = _read_json(pmf_dir / "summary.json")
    if summ_ms:
        n_ms_roll = int(summ_ms.get("n_rolled_back", 0))

    sr_path = sup_dir / "stat_role_market_superiority.csv"
    n_pass = n_fail = n_elig = None
    if sr_path.is_file():
        sr = pd.read_csv(sr_path)
        if "market_superiority_pass" in sr.columns:
            n_pass = int(sr["market_superiority_pass"].sum())
            n_fail = int((~sr["market_superiority_pass"]).sum())
        if "market_superiority_eligible" in sr.columns:
            n_elig = int(sr["market_superiority_eligible"].sum())

    math = _read_json(math_summ) or {}
    strict_last = "unknown"
    if sup_dir.joinpath("summary.json").is_file():
        s = _read_json(sup_dir / "summary.json") or {}
        strict_last = "PASS" if s.get("global_market_superiority_ok") else "FAIL_OR_BLOCKED"

    prom = _read_json(prom_path) if prom_path.is_file() else {}
    claim_allowed = bool(prom.get("claim_allowed", False))

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    loss_mtime = int(loss_pq.stat().st_mtime) if loss_pq.is_file() else None
    build_ts = _git_ts("scripts/build_event_market_loss_rows.py")
    stale_risk = False
    if loss_mtime and build_ts and loss_mtime < build_ts:
        stale_risk = True

    out = {
        "label": label,
        "source_git_head": head,
        "event_neutral_manifest_path": str(ev_path.relative_to(REPO_ROOT)) if ev_path.is_file() else None,
        "event_neutral_manifest_exists": ev_path.is_file(),
        "event_neutral_accepted_calibrators": n_ev_accept,
        "pmf_mean_shift_manifest_path": str(ms_path.relative_to(REPO_ROOT)) if ms_path.is_file() else None,
        "pmf_mean_shift_manifest_exists": ms_path.is_file(),
        "pmf_mean_shift_accepted_transforms": n_ms_accept,
        "pmf_mean_shift_rollback_count": n_ms_roll,
        "strict_summary_global_ok": (sup_dir / "summary.json").is_file()
        and bool((_read_json(sup_dir / "summary.json") or {}).get("global_market_superiority_ok")),
        "strict_last_classifier": strict_last,
        "math_global_pass": bool(math.get("global_math_pass")),
        "math_failures_n": math.get("failures_n"),
        "claim_allowed": claim_allowed,
        "stat_role_passing_segments": n_pass,
        "stat_role_failing_segments": n_fail,
        "stat_role_eligible_segments": n_elig,
        "loss_rows_parquet_exists": loss_pq.is_file(),
        "artifacts_stale_risk_loss_rows_older_than_build_script_commit": stale_risk,
    }

    out_dir = ART / f"m87_repair_state_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# M8.7 repair state (`{label}`)",
        "",
        f"- **HEAD**: `{head}`",
        f"- **Event-neutral manifest**: {'yes' if out['event_neutral_manifest_exists'] else 'no'} — accepted segments: **{n_ev_accept}**",
        f"- **PMF mean-shift manifest**: {'yes' if out['pmf_mean_shift_manifest_exists'] else 'no'} — accepted: **{n_ms_accept}**, rollbacks: **{n_ms_roll}**",
        f"- **Strict global OK**: {out['strict_summary_global_ok']}",
        f"- **Math global pass**: {out['math_global_pass']} (failures_n={out.get('math_failures_n')})",
        f"- **claim_allowed**: {claim_allowed}",
        f"- **Stat-role pass / fail / eligible**: {n_pass} / {n_fail} / {n_elig}",
        f"- **Stale risk** (loss parquet older than last `build_event_market_loss_rows.py` commit): **{stale_risk}**",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {out_dir.relative_to(REPO_ROOT)}/summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
