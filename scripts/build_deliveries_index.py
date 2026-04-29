"""Build deliveries/README.md and deliveries/index.html.

One row per delivery date with finality_status, row counts, freshness,
TOV status, after-game scoring status, and links to the canonical files
in each per-date package. Reads only from on-disk delivery folders and
each delivery's `wizard_of_odds/run_manifest.json`. Never re-runs the
build.

Dates with no `wizard_of_odds/run_manifest.json` are recorded as
`NOT_DELIVERABLE_READY` with an explanation rather than skipped — that
is what makes the index honest.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEL_DIR = REPO_ROOT / "deliveries"
PRED_DIR = REPO_ROOT / "predictions"

# Canonical link layout per Phase 11C Part B.
DEREK_LINKS = [
    ("01_START_HERE.html", "pmf_model_review_package/01_START_HERE.html"),
    ("03_PMF_DISTRIBUTION_VIEWER.html",
     "pmf_model_review_package/03_PMF_DISTRIBUTION_VIEWER.html"),
    ("04_PROP_SUMMARY.csv", "pmf_model_review_package/04_PROP_SUMMARY.csv"),
    ("05_FULL_PMF_WIDE.csv", "pmf_model_review_package/05_FULL_PMF_WIDE.csv"),
    ("06_OUTCOME_LEVEL_PROBABILITIES.csv",
     "pmf_model_review_package/06_OUTCOME_LEVEL_PROBABILITIES.csv"),
    ("machine_readable/model_only.parquet",
     "pmf_model_review_package/machine_readable/model_only.parquet"),
    ("MODEL_PERFORMANCE_AND_CALIBRATION.md",
     "pmf_model_review_package/MODEL_PERFORMANCE_AND_CALIBRATION.md"),
]
WOO_LINKS = [
    ("README.md", "wizard_of_odds/README.md"),
    ("fair_odds_board.csv", "wizard_of_odds/fair_odds_board.csv"),
    ("full_pmfs_wide.csv", "wizard_of_odds/full_pmfs_wide.csv"),
    ("full_pmfs_outcome_level.csv",
     "wizard_of_odds/full_pmfs_outcome_level.csv"),
    ("market_comparison.csv", "wizard_of_odds/market_comparison.csv"),
    ("publishable_edges.csv", "wizard_of_odds/publishable_edges.csv"),
    ("run_manifest.json", "wizard_of_odds/run_manifest.json"),
]
AFTER_GAME_LINKS = [
    ("after_game_summary.md", "after_game_scoring/after_game_summary.md"),
    ("after_game_scoring.csv", "after_game_scoring/after_game_scoring.csv"),
    ("calibration_by_stat.csv", "after_game_scoring/calibration_by_stat.csv"),
    ("calibration_by_role_bucket.csv",
     "after_game_scoring/calibration_by_role_bucket.csv"),
    ("clv_by_stat.csv", "after_game_scoring/clv_by_stat.csv"),
    ("clv_by_book.csv", "after_game_scoring/clv_by_book.csv"),
    ("after_game_status.json",
     "after_game_scoring/after_game_status.json"),
]


def _now_utc_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _scan_dates() -> list[str]:
    if not DEL_DIR.exists():
        return []
    out = []
    for p in sorted(DEL_DIR.iterdir()):
        if p.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", p.name):
            out.append(p.name)
    return out


def _row_for_date(date: str) -> dict:
    base = DEL_DIR / date
    woo = base / "wizard_of_odds"
    derek = base / "pmf_model_review_package"
    after = base / "after_game_scoring"
    pred = PRED_DIR / f"all_props_{date}.parquet"

    manifest_path = woo / "run_manifest.json"
    manifest = None
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception as e:
            manifest = {"_read_error": repr(e)}

    after_status = "n/a"
    after_status_payload = after / "after_game_status.json"
    if after_status_payload.exists():
        try:
            after_status = json.loads(after_status_payload.read_text()).get(
                "after_game_status", "unknown")
        except Exception:
            after_status = "unknown"

    finality_status = (manifest.get("finality_status")
                        if isinstance(manifest, dict) else None)
    finality_blocker_codes = (manifest.get("finality_blocker_codes")
                               if isinstance(manifest, dict) else None)

    if not woo.exists():
        if not pred.exists():
            classification = "NOT_DELIVERABLE_READY"
            reason = ("predictions/all_props_{date}.parquet missing — "
                       "predict.py must run before this date can ship")
        else:
            classification = "NOT_DELIVERABLE_READY"
            reason = ("predictions present but build_daily_pmf_delivery.py "
                       "has not produced the wizard_of_odds package yet")
    elif finality_status == "final":
        classification = "FINAL_DELIVERABLE_READY"
        reason = ""
    elif finality_status:
        classification = "PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS"
        reason = ", ".join(finality_blocker_codes or [])
    else:
        classification = "NOT_DELIVERABLE_READY"
        reason = "wizard_of_odds/run_manifest.json present but unreadable"

    return {
        "date": date,
        "classification": classification,
        "reason": reason,
        "manifest": manifest,
        "after_status": after_status,
        "exists": {
            "predictions": pred.exists(),
            "derek": derek.exists(),
            "woo": woo.exists(),
            "after_game": after.exists(),
        },
    }


def _row_metrics(row: dict) -> dict:
    m = row.get("manifest") or {}
    rc = m.get("row_counts") or {}
    qr = m.get("quality_rollup") or {}
    od = _safe_get(m, "sources", "odds_snapshot", default={}) or {}
    fm = m.get("freshness_manifest") or {}
    return {
        "props": rc.get("full_pmfs_wide"),
        "outcome_rows": (rc.get("full_pmfs_wide") and rc.get("full_pmfs_wide") * "?")
                          or None,
        "fair_odds": rc.get("fair_odds_board"),
        "market_comparison": rc.get("market_comparison"),
        "publishable_edges": rc.get("publishable_edges"),
        "pmf_valid_ok_pct": qr.get("pmf_valid_ok_pct"),
        "odds_status": fm.get("odds_status") or od.get("fetch_status"),
        "market_coverage": od.get("coverage_status"),
        "injury_freshness": fm.get("availability_freshness_status"),
        "lineup_freshness_rollup": qr.get("lineup_freshness_status"),
        "tov_status": m.get("tov_status"),
        "model_version": m.get("model_version"),
    }


# ── README writer ─────────────────────────────────────────────────────────


def _md_link(text: str, target_path: Path, *, base: Path) -> str:
    """`base` is the directory the README/index lives in (used to build
    a *relative* link). Strikethrough when the target is missing so the
    index is always honest about what is on disk."""
    if not target_path.exists():
        return f"~~{text}~~"
    rel = target_path.relative_to(base)
    return f"[{text}]({rel})"


def _build_readme(rows: list[dict]) -> str:
    out: list[str] = []
    out.append("# Deliveries\n")
    out.append(f"_Index regenerated {_now_utc_iso()} by "
               f"`scripts/build_deliveries_index.py`._\n\n")
    out.append("Each row links to the per-date Derek (`pmf_model_review_package/`), "
               "Wizard of Odds (`wizard_of_odds/`), and after-game "
               "(`after_game_scoring/`) packages.\n\n")
    out.append("Classification key: **FINAL_DELIVERABLE_READY** · "
               "**PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS** · "
               "**NOT_DELIVERABLE_READY**.\n\n")

    out.append("| date | classification | props | fair_odds | market_comparison | publishable_edges | market_coverage | injury_fresh | tov_status | after_game | model_version |\n")
    out.append("|---|---|---:|---:|---:|---:|---|---|---|---|---|\n")
    for r in rows:
        m = _row_metrics(r)
        out.append(
            f"| **{r['date']}** | `{r['classification']}` | "
            f"{m['props'] if m['props'] is not None else '—'} | "
            f"{m['fair_odds'] if m['fair_odds'] is not None else '—'} | "
            f"{m['market_comparison'] if m['market_comparison'] is not None else '—'} | "
            f"{m['publishable_edges'] if m['publishable_edges'] is not None else '—'} | "
            f"`{m['market_coverage'] or '—'}` | "
            f"`{m['injury_freshness'] or '—'}` | "
            f"`{m['tov_status'] or '—'}` | "
            f"`{r['after_status']}` | "
            f"`{m['model_version'] or '—'}` |\n"
        )
    out.append("\n## Per-date links\n\n")
    for r in rows:
        date = r["date"]
        base = DEL_DIR / date
        out.append(f"### {date} — `{r['classification']}`\n\n")
        if r["reason"]:
            out.append(f"_{r['reason']}_\n\n")
        if r["exists"]["derek"]:
            out.append("**Derek (PMF model review)**\n\n")
            for label, rel in DEREK_LINKS:
                target = base / rel
                out.append(f"- {_md_link(label, target, base=DEL_DIR)}\n")
            out.append("\n")
        if r["exists"]["woo"]:
            out.append("**Wizard of Odds**\n\n")
            for label, rel in WOO_LINKS:
                target = base / rel
                out.append(f"- {_md_link(label, target, base=DEL_DIR)}\n")
            out.append("\n")
        if r["exists"]["after_game"]:
            out.append(f"**After-game scoring** (`{r['after_status']}`)\n\n")
            for label, rel in AFTER_GAME_LINKS:
                target = base / rel
                out.append(f"- {_md_link(label, target, base=DEL_DIR)}\n")
            out.append("\n")
        if not r["exists"]["woo"]:
            out.append("_No wizard_of_odds/ package on disk for this date._\n\n")
            status_md = DEL_DIR / date / "STATUS.md"
            if status_md.exists():
                out.append(f"See [`STATUS.md`]({date}/STATUS.md) for the "
                            f"cause and the required-to-resolve checklist.\n\n")
    out.append("\n## Honest framing\n\n")
    out.append("- All emitted PMFs are **model-only**; market columns are reference only.\n")
    out.append("- TOV PMFs (when emitted) come from Phase 8 calibrators — "
               "**no Phase 10D / 10D.2 overlay is wired into production**.\n")
    out.append("- Freshness, role provenance, and after-game scoring status are recorded "
               "verbatim from each delivery's `wizard_of_odds/run_manifest.json` — "
               "no fabrication.\n")
    out.append("- See `docs/daily_pmf_delivery_spec.md` for the row schema and "
               "validation contract, and `docs/daily_data_freshness_runbook.md` "
               "for the freshness manifest.\n")
    return "".join(out)


def _build_index_html(rows: list[dict]) -> str:
    css = """
body{font-family:system-ui;max-width:1300px;margin:1.5rem auto;padding:0 1rem;color:#222}
h1{margin-top:0}h2{margin-top:1.6rem;border-bottom:1px solid #ccc;padding-bottom:0.2rem}
table{border-collapse:collapse;margin:0.6rem 0;width:100%;font-size:0.92em}
th,td{padding:0.35rem 0.55rem;border:1px solid #ddd;text-align:left}
th{background:#f0f0f0}
td.right{text-align:right}
.cls-final{background:#dff5dd}
.cls-prov{background:#fff7d6}
.cls-no{background:#ffe0e0}
code{background:#f3f3f3;padding:0.05em 0.3em;border-radius:3px;font-size:0.9em}
.callout{background:#fff8d6;border-left:4px solid #d4a900;padding:0.5rem 0.9rem;margin:0.8rem 0}
"""
    body: list[str] = []
    body.append(f"<p>Index regenerated {_now_utc_iso()} by "
                 f"<code>scripts/build_deliveries_index.py</code>.</p>\n")
    body.append('<table>\n<tr>'
                 '<th>date</th><th>classification</th>'
                 '<th>props</th><th>fair_odds</th><th>market_comparison</th>'
                 '<th>publishable_edges</th><th>coverage</th>'
                 '<th>injury_fresh</th><th>tov_status</th>'
                 '<th>after_game</th><th>model_version</th></tr>\n')
    for r in rows:
        m = _row_metrics(r)
        cls_class = ("cls-final" if r["classification"] == "FINAL_DELIVERABLE_READY"
                      else "cls-prov" if r["classification"]
                      == "PROVISIONAL_DELIVERABLE_READY_WITH_WARNINGS"
                      else "cls-no")
        body.append(
            f'<tr class="{cls_class}">'
            f"<td><b>{r['date']}</b></td>"
            f"<td><code>{r['classification']}</code></td>"
            f"<td class=right>{m['props'] if m['props'] is not None else '&mdash;'}</td>"
            f"<td class=right>{m['fair_odds'] if m['fair_odds'] is not None else '&mdash;'}</td>"
            f"<td class=right>{m['market_comparison'] if m['market_comparison'] is not None else '&mdash;'}</td>"
            f"<td class=right>{m['publishable_edges'] if m['publishable_edges'] is not None else '&mdash;'}</td>"
            f"<td><code>{m['market_coverage'] or '&mdash;'}</code></td>"
            f"<td><code>{m['injury_freshness'] or '&mdash;'}</code></td>"
            f"<td><code>{m['tov_status'] or '&mdash;'}</code></td>"
            f"<td><code>{r['after_status']}</code></td>"
            f"<td><code>{m['model_version'] or '&mdash;'}</code></td>"
            f"</tr>\n")
    body.append("</table>\n")
    body.append('<div class="callout">All PMFs are model-only. TOV PMFs (when '
                "emitted) come from Phase 8 calibrators — no Phase 10D / 10D.2 "
                "overlay is wired into production.</div>\n")
    for r in rows:
        date = r["date"]
        base = DEL_DIR / date
        body.append(f"<h2>{date} — <code>{r['classification']}</code></h2>\n")
        if r["reason"]:
            body.append(f'<p><i>{r["reason"]}</i></p>\n')
        if r["exists"]["derek"]:
            body.append("<p><b>Derek</b> ")
            body.append(" &middot; ".join(
                f'<a href="{(base / rel).relative_to(DEL_DIR)}">{label}</a>'
                for label, rel in DEREK_LINKS
                if (base / rel).exists()))
            body.append("</p>\n")
        if r["exists"]["woo"]:
            body.append("<p><b>Wizard of Odds</b> ")
            body.append(" &middot; ".join(
                f'<a href="{(base / rel).relative_to(DEL_DIR)}">{label}</a>'
                for label, rel in WOO_LINKS
                if (base / rel).exists()))
            body.append("</p>\n")
        if r["exists"]["after_game"]:
            body.append(f"<p><b>After-game</b> "
                          f"(<code>{r['after_status']}</code>) ")
            body.append(" &middot; ".join(
                f'<a href="{(base / rel).relative_to(DEL_DIR)}">{label}</a>'
                for label, rel in AFTER_GAME_LINKS
                if (base / rel).exists()))
            body.append("</p>\n")
    return (f'<!doctype html><html><head><meta charset=utf-8>'
            f'<title>NBA PMF deliveries index</title>'
            f'<style>{css}</style></head><body>'
            f'<h1>NBA PMF deliveries</h1>{"".join(body)}</body></html>')


def main() -> int:
    dates = _scan_dates()
    rows = [_row_for_date(d) for d in dates]
    DEL_DIR.mkdir(parents=True, exist_ok=True)
    (DEL_DIR / "README.md").write_text(_build_readme(rows))
    (DEL_DIR / "index.html").write_text(_build_index_html(rows))
    print(f"wrote {(DEL_DIR / 'README.md').relative_to(REPO_ROOT)}")
    print(f"wrote {(DEL_DIR / 'index.html').relative_to(REPO_ROOT)}")
    print(f"  dates indexed: {len(rows)}")
    for r in rows:
        print(f"   - {r['date']}  {r['classification']}"
              + (f"  ({r['reason']})" if r['reason'] else ""))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
