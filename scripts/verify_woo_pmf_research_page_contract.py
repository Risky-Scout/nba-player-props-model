#!/usr/bin/env python3
"""M8.6O v5 — verify nba-pmf-research.html and pmf_research.json
match the atom-PMF contract.

Hard-fails if:
  G_TEMPLATE_FORBIDDEN_COPY  — template has forbidden phrases
  G_RENDERED_FORBIDDEN_COPY  — rendered HTML has forbidden phrases
  G_JS_USES_ROWS             — JS references `data.rows` (we use `players`)
  G_JSON_NOT_PLAYERS         — pmf_research.json lacks `players` array
  G_JS_NO_ATOM_FIELD_ACCESS  — JS doesn't reference atom_pmf, support, or probs
  G_POLICY_NOT_DECLARED      — JSON missing atom_pmf_policy

Pass: M8_6O_WOO_PMF_RESEARCH_PAGE_CONTRACT_PASS
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_COPY_PATTERNS = [
    re.compile(r'\breconstruct(?:s|ed|ing|ion)?\s+(?:the\s+)?(?:production\s+)?p[_\s]?ge', re.IGNORECASE),
    re.compile(r'\bp[_\s]?ge[_\s]?ladder\b', re.IGNORECASE),
    re.compile(r'\breconstructed\s+(?:PMF|distribution)\b', re.IGNORECASE),
    re.compile(r'\bladder\s+reconstruction\b', re.IGNORECASE),
    re.compile(r'\bsurvival\s+ladder\b', re.IGNORECASE),
    re.compile(r'\bcdf\s+ladder\b', re.IGNORECASE),
    re.compile(r'\bcumulative\s+probabilit', re.IGNORECASE),
]


def _fail(g, d):
    print(f"M8_6O_WOO_PMF_RESEARCH_PAGE_CONTRACT_FAILED gate={g} detail={d}", file=sys.stderr)
    sys.exit(1)


def _scan_html_for_forbidden(path):
    if not path.exists(): return None
    src = path.read_text()
    hits = []
    for rx in FORBIDDEN_COPY_PATTERNS:
        for m in rx.finditer(src):
            ctx = src[max(0, m.start()-30):min(len(src), m.end()+30)].replace("\n", " ")
            hits.append(f"{path.name}: '{m.group(0)}' in context '...{ctx}...'")
            if len(hits) >= 25: break
        if len(hits) >= 25: break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    date = args.date

    # Template + rendered HTML
    tpl = REPO_ROOT / "predictions" / "_template_nba_pmf_research.html"
    rendered = REPO_ROOT / "predictions" / "nba-pmf-research.html"
    scanned_any = False
    for path in (tpl, rendered):
        hits = _scan_html_for_forbidden(path)
        if hits is None:
            print(f"::warning::PAGE_NOT_FOUND {path}", file=sys.stderr)
            continue
        scanned_any = True
        if hits:
            gate = "G_TEMPLATE_FORBIDDEN_COPY" if path == tpl else "G_RENDERED_FORBIDDEN_COPY"
            _fail(gate, "; ".join(hits))

    # JS schema check — search either file (whichever exists) for `data.rows`
    js_uses_rows = False
    js_atom_access = False
    for path in (tpl, rendered):
        if not path.exists(): continue
        src = path.read_text()
        if re.search(r'\bdata\.rows\b', src) or re.search(r"['\"]rows['\"]\s*:\s*\[", src):
            # If the JSON has a top-level `rows` key, we'd see it being parsed.
            # We allow such reference IF `players` is also referenced.
            if not re.search(r'\bdata\.players\b', src) and not re.search(r"['\"]players['\"]", src):
                js_uses_rows = True
        if re.search(r'\batom_pmf\b', src) or re.search(r'\bsupport\b', src) and re.search(r'\bprobs\b', src):
            js_atom_access = True

    if js_uses_rows:
        _fail("G_JS_USES_ROWS",
              "page references data.rows without data.players — schema mismatch")

    # JSON contract
    json_path = None
    for c in (REPO_ROOT/"public_export"/"wizard_of_odds"/date/"pmf_research.json",
              REPO_ROOT/"public_export"/"wizard_of_odds"/"latest"/"pmf_research.json",
              REPO_ROOT/"public_export"/"wizard_of_odds"/"pmf_research.json"):
        if c.exists(): json_path = c; break
    if json_path is None:
        _fail("G_JSON_MISSING", "pmf_research.json not found under public_export/wizard_of_odds")

    try: data = json.loads(json_path.read_text())
    except Exception as e: _fail("G_JSON_PARSE", f"{json_path}: {e}")

    if not isinstance(data, dict) or "players" not in data \
       or not isinstance(data["players"], list):
        _fail("G_JSON_NOT_PLAYERS",
              f"{json_path}: top-level must have `players` array "
              f"(got keys={list(data.keys()) if isinstance(data,dict) else type(data).__name__})")

    policy = str(data.get("atom_pmf_policy", "")).lower()
    if policy != "atom_source_only_no_ladder_fallback":
        _fail("G_POLICY_NOT_DECLARED", f"atom_pmf_policy={policy!r}")

    # Hard-fail: if any HTML was scanned but no JS accesses atom_pmf/support/probs,
    # the page will not render atoms. v6→v7: this was a warning, now it is a hard fail.
    if scanned_any and not js_atom_access:
        _fail("G_JS_NO_ATOM_FIELD_ACCESS",
              "page HTML exists but JS does not reference atom_pmf, support, or "
              "probs — the page cannot render true atom probabilities. "
              "Patch the page/template to consume the atom fields.")

    print("M8_6O_WOO_PMF_RESEARCH_PAGE_CONTRACT_PASS")
    print(f"  date={date} json={json_path.relative_to(REPO_ROOT)} players={len(data['players'])}")
    print(f"  template_scanned={tpl.exists()} rendered_scanned={rendered.exists()}")
    print(f"  policy={policy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
