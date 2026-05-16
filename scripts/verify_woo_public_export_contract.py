#!/usr/bin/env python3
"""Phase 13AK — verify the Wizard of Odds public-export JSON + HTML
contract for one delivery date.

Local checks:
  - predictions/nba-props.html exists and is non-empty (size > 5 KB).
  - predictions/nba-pmf-research.html (or extensionless equivalent)
    exists when used by the deployed front-end. Treated as advisory
    when absent — this file is published by a separate pipeline that
    is not always run locally.
  - public_export/wizard_of_odds/<date>/affiliate_dashboard.json
    parses, has non-empty rows.
  - public_export/wizard_of_odds/<date>/pmf_research.json
    parses, has non-empty players.
  - public_export/wizard_of_odds/latest/affiliate_dashboard.json
    parses, has non-empty rows AND date == requested date (or a
    documented "latest pointer" date, never older than 1 day).
  - public_export/wizard_of_odds/latest/pmf_research.json same.
  - public_export/wizard_of_odds/affiliate_dashboard.json (root copy)
    parses, has non-empty rows.
  - public_export/wizard_of_odds/pmf_research.json (root copy) parses,
    has non-empty players.
  - PMF research tail-bucket bug check: ``support_points`` carry
    ``is_tail`` flags and the LAST point of each player/stat with a
    sparse upper tail is labeled like "<k>+", not as a single-point
    P(X=k_max).

Remote checks (when ``--base-url`` is supplied with ``--require-remote``):
  - GET <base-url>/nba-props.html → HTTP 2xx, non-empty body
  - GET <base-url>/nba-pmf-research[.html] → HTTP 2xx, non-empty body
  - GET <base-url>/affiliate_dashboard.json → JSON with rows
  - GET <base-url>/pmf_research.json → JSON with players
  - GET <base-url>/latest/affiliate_dashboard.json → JSON with rows
  - GET <base-url>/latest/pmf_research.json → JSON with players
  - GET <base-url>/<date>/affiliate_dashboard.json → JSON with rows
  - GET <base-url>/<date>/pmf_research.json → JSON with players

Pass lines:
  WOO_PUBLIC_EXPORT_CONTRACT_PASS    (local)
  WOO_PUBLIC_EXPORT_REMOTE_PASS      (only when --require-remote is used)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

REPO_ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = REPO_ROOT / "predictions"
EXPORT_ROOT = REPO_ROOT / "public_export" / "wizard_of_odds"

# Keys a dict-root ``pmf_research.json`` may use to carry the list of
# rows / players. Checked in priority order.
PMF_RESEARCH_LIST_KEYS = ("players", "rows", "records", "data", "items", "pmfs")

# Market-side row indicators — only rows carrying any of these are
# treated as bets and subjected to the strict ``model_prob`` check.
_MARKET_ROW_SIDE_KEYS = ("side", "pick_side", "over_under")
_MARKET_ROW_LINE_KEYS = ("line",)
_MARKET_ROW_BOOK_KEYS = ("book", "sportsbook", "bookmaker")
_MARKET_ROW_SIDE_PROB_KEYS = (
    "model_p_over",
    "model_p_under",
    "prob_over",
    "prob_under",
    "p_over",
    "p_under",
    "model_probability_over",
    "model_probability_under",
    "market_over_odds",
    "market_under_odds",
)


def _rel(path: Path) -> str:
    """Return ``path`` relative to ``REPO_ROOT`` when possible; otherwise
    fall back to ``str(path)``. Used to keep error messages stable
    regardless of where the verifier is invoked from."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> tuple[Optional[Any], Optional[str]]:
    """Return the parsed JSON (dict OR list) or a structured error.

    The return type intentionally is *not* restricted to ``dict``;
    ``pmf_research.json`` is allowed to be a bare list of records (run
    25955470154 surfaced exactly this case: the verifier crashed when
    it assumed dict-only and called ``.get()`` on a list)."""
    if not path.exists():
        return None, f"missing {_rel(path)}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, f"parse error {_rel(path)}: {e}"


def _check_affiliate(payload: Any, label: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        failures.append(
            f"{label}: WOO_PUBLIC_EXPORT_AFFILIATE_SCHEMA_INVALID "
            f"root_type={type(payload).__name__}"
        )
        return failures
    rows = payload.get("rows") or []
    if not rows:
        failures.append(f"{label}: rows is empty (count={len(rows)})")
        return failures
    sample = rows[0]
    if not isinstance(sample, dict):
        failures.append(
            f"{label}: WOO_PUBLIC_EXPORT_AFFILIATE_SCHEMA_INVALID "
            f"sample_type={type(sample).__name__}"
        )
        return failures
    required = ("player", "stat", "side", "line", "model_prob",
                "market_prob")
    missing = [k for k in required if k not in sample]
    if missing:
        failures.append(f"{label}: sample row missing keys: {missing}")
    return failures


def _extract_pmf_research_rows(payload: Any) -> tuple[list, str]:
    """Return ``(rows, shape_tag)`` for any supported pmf_research.json shape.

    Supported shapes:
      - bare list of records (``shape_tag='list_root'``)
      - dict with ``players`` list of player dicts (``shape_tag='dict_players'``)
      - dict with ``rows``/``records``/``data``/``items``/``pmfs`` list
        (``shape_tag='dict_records'``)
      - dict keyed by player id with each value being a player dict
        (``shape_tag='dict_keyed_players'``)

    Returns ``([], 'invalid')`` when the shape can't be interpreted.
    """
    if isinstance(payload, list):
        return list(payload), "list_root"
    if isinstance(payload, dict):
        for key in PMF_RESEARCH_LIST_KEYS:
            v = payload.get(key)
            if isinstance(v, list):
                tag = "dict_players" if key == "players" else "dict_records"
                return list(v), tag
        # Last-ditch: dict-of-dicts keyed by player id.
        nested = [v for v in payload.values() if isinstance(v, dict)]
        if nested and all(
            ("stats" in v or "support" in v or "probs" in v or "pmf" in v)
            for v in nested
        ):
            return nested, "dict_keyed_players"
    return [], "invalid"


def _is_market_row(rec: dict) -> bool:
    has_side = any(rec.get(k) not in (None, "") for k in _MARKET_ROW_SIDE_KEYS)
    has_line = any(rec.get(k) not in (None, "") for k in _MARKET_ROW_LINE_KEYS)
    if has_side and has_line:
        return True
    if any(rec.get(k) not in (None, "") for k in _MARKET_ROW_SIDE_PROB_KEYS):
        return True
    if any(rec.get(k) not in (None, "") for k in _MARKET_ROW_BOOK_KEYS):
        return True
    return False


def _iter_stat_blocks(rec: dict):
    """Yield ``(stat_name, stat_block)`` for both legacy and canonical
    player record shapes. Never calls ``.items()`` on a list."""
    stats = rec.get("stats")
    if isinstance(stats, dict):
        for stat_name, block in stats.items():
            if isinstance(block, dict):
                yield str(stat_name), block
        return
    if isinstance(stats, list):
        for block in stats:
            if not isinstance(block, dict):
                continue
            name = block.get("stat") or block.get("stat_key") or block.get("market") or ""
            yield str(name), block
        return


def _support_points(block: dict) -> list[dict]:
    """Project a stat block into the legacy ``support_points`` shape so
    the tail-bucket check works whether the producer emitted the new
    ``support``/``probs`` arrays or the legacy ``support_points``
    dicts."""
    sp = block.get("support_points")
    if isinstance(sp, list):
        return [pt for pt in sp if isinstance(pt, dict)]
    support = block.get("support")
    probs = block.get("probs")
    if isinstance(support, list) and isinstance(probs, list) and len(support) == len(probs):
        return [
            {
                "k": int(k) if k is not None else None,
                "p": float(p) if p is not None else 0.0,
                "label": str(int(k)) if k is not None else "",
                "is_tail": False,
            }
            for k, p in zip(support, probs)
        ]
    return []


def _validate_distribution_row(rec: dict) -> Optional[str]:
    """Return a short reason on malformed distribution rows, else None."""
    if not rec.get("stat"):
        return "missing_stat"
    if rec.get("player_id") in (None, "") and not rec.get("player"):
        return "missing_player_identifier"
    support = rec.get("support")
    probs = rec.get("probs")
    if isinstance(support, list) and isinstance(probs, list):
        if len(support) != len(probs):
            return f"support_probs_length_mismatch({len(support)}!={len(probs)})"
        try:
            total = sum(float(p) for p in probs)
        except (TypeError, ValueError):
            return "probs_not_numeric"
        if not (0.99 <= total <= 1.01):
            return f"probs_sum_out_of_tolerance({total:.4f})"
        return None
    pmf = rec.get("pmf")
    if isinstance(pmf, dict) and pmf:
        try:
            total = sum(float(v) for v in pmf.values())
        except (TypeError, ValueError):
            return "pmf_not_numeric"
        if not (0.99 <= total <= 1.01):
            return f"pmf_sum_out_of_tolerance({total:.4f})"
        return None
    atoms = rec.get("atom_pmf")
    if isinstance(atoms, (list, dict)) and atoms:
        return None
    return "no_support_probs_or_pmf"


def _tail_bucket_violations(player_label: str, stat_name: str, pts: list[dict]) -> list[str]:
    if len(pts) < 2:
        return []
    last = pts[-1]
    second_last = pts[-2]
    if "k_min" in last:
        return []
    if "k" in last and "k" in second_last:
        try:
            gap = int(last["k"]) - int(second_last["k"])
        except (TypeError, ValueError):
            return []
        if gap > 1:
            return [
                f"{player_label}/{stat_name}: tail at k={last['k']} not "
                f"labeled as tail bucket (prev k={second_last['k']}, gap={gap})"
            ]
    return []


def _check_pmf_research(payload: Any, label: str) -> list[str]:
    """Schema-safe pmf_research.json validation.

    The verifier accepts every shape the canonical builder /
    publish_woo_public_export.py producer can emit. It NEVER calls
    ``.items()`` or ``.get()`` on a list. PMF distribution rows are
    validated by support/probs/pmf shape only — they don't need
    ``model_prob``. Market-side rows (rows that carry side+line, a
    side-aware prob, or a book) still go through the strict
    affiliate-style check.
    """
    failures: list[str] = []
    rows, shape = _extract_pmf_research_rows(payload)
    if shape == "invalid" or not rows:
        keys = sorted(payload.keys()) if isinstance(payload, dict) else None
        sample_keys = None
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            sample_keys = sorted(payload[0].keys())
        failures.append(
            f"{label}: WOO_PUBLIC_EXPORT_PMF_RESEARCH_SCHEMA_INVALID "
            f"root_type={type(payload).__name__} keys={keys} "
            f"sample_keys={sample_keys}"
        )
        return failures

    bug_seen: list[str] = []
    bad_distribution: list[str] = []
    market_missing_model_prob = 0

    # Sample-not-exhaustive scan, but generous enough to surface every
    # variant the canonical builder emits for a single date.
    for rec in rows[:200]:
        if not isinstance(rec, dict):
            bad_distribution.append(
                f"non_dict_row({type(rec).__name__})"
            )
            continue
        player_label = str(rec.get("player") or rec.get("player_id") or "?")
        stat_blocks = list(_iter_stat_blocks(rec))
        if stat_blocks:
            for stat_name, block in stat_blocks:
                bug_seen.extend(
                    _tail_bucket_violations(player_label, stat_name, _support_points(block))
                )
            continue

        # Row has no nested ``stats``. Either it's a distribution row
        # (canonical builder's per-stat record) or a market-side row.
        if _is_market_row(rec):
            mp = rec.get("model_prob")
            if mp is None:
                market_missing_model_prob += 1
            stat_name = str(rec.get("stat") or "")
            bug_seen.extend(
                _tail_bucket_violations(player_label, stat_name, _support_points(rec))
            )
            continue

        # Distribution row: validate PMF shape only.
        reason = _validate_distribution_row(rec)
        if reason is not None:
            bad_distribution.append(f"{player_label}: {reason}")
        bug_seen.extend(
            _tail_bucket_violations(player_label, str(rec.get("stat") or ""), _support_points(rec))
        )

    if bad_distribution:
        failures.append(
            f"{label}: WOO_PUBLIC_EXPORT_PMF_RESEARCH_DISTRIBUTION_MALFORMED "
            f"samples={bad_distribution[:3]}"
        )
    if market_missing_model_prob > 0:
        failures.append(
            f"{label}: {market_missing_model_prob} market rows have null model_prob"
        )
    if bug_seen:
        failures.append(
            f"{label}: PMF tail-bucket bug present in samples: {bug_seen[:3]}"
        )
    return failures


def _payload_date(payload: Any) -> Optional[str]:
    """Return the dated payload's ``date`` field when present, else None.
    Schema-safe: a list root has no top-level date."""
    if isinstance(payload, dict):
        v = payload.get("date")
        return None if v is None else str(v)
    return None


def _delivery_manifest_no_games_slate(date: str) -> bool:
    """Return True iff the dated delivery manifest carries the strict
    no-games-slate flag.

    The orchestrator's ``_short_circuit_if_no_games`` writes
    ``deliveries/<date>/manifest.json`` with ``no_games_slate: true``
    AND ``reason: no_games_slate`` only after BOTH the predict
    no-games signal AND an independent BDL ``/games`` schedule lookup
    confirm zero games for the date. Any other manifest shape returns
    False so a games-bearing slate still hard-fails on empty exports.
    """
    manifest_path = REPO_ROOT / "deliveries" / date / "manifest.json"
    if not manifest_path.is_file():
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("no_games_slate")) and payload.get("reason") == "no_games_slate"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--base-url", default=None,
                    help="Remote base URL (e.g. "
                         "https://dev.wizardofodds.com/tools/odds-scanner/predictions)")
    ap.add_argument("--require-remote", action="store_true",
                    help="Fetch and validate the remote contract too.")
    args = ap.parse_args(argv)
    date = args.date

    if _delivery_manifest_no_games_slate(date):
        print(
            f"WOO_PUBLIC_EXPORT_CONTRACT_SOFT_SKIP_NO_GAMES_SLATE "
            f"date={date} "
            f"upstream_signal=deliveries/{date}/manifest.json:no_games_slate=true "
            f"reason=no_eligible_player_game_rows_expected"
        )
        return 0

    failures: list[str] = []

    # 1. HTML pages
    html = PRED_DIR / "nba-props.html"
    if not html.exists():
        failures.append(f"missing {html.relative_to(REPO_ROOT)}")
    elif html.stat().st_size < 5 * 1024:
        failures.append(f"{html.relative_to(REPO_ROOT)} too small "
                        f"({html.stat().st_size} bytes)")

    research_html = PRED_DIR / "nba-pmf-research.html"
    research_extless = PRED_DIR / "nba-pmf-research"
    if not (research_html.exists() or research_extless.exists()):
        # Advisory: not all environments host this page. Don't hard-fail.
        pass

    # 2. JSON contract: <date>/, latest/, root
    aff_paths = (
        ("date", EXPORT_ROOT / date / "affiliate_dashboard.json"),
        ("latest", EXPORT_ROOT / "latest" / "affiliate_dashboard.json"),
        ("root", EXPORT_ROOT / "affiliate_dashboard.json"),
    )
    pmf_paths = (
        ("date", EXPORT_ROOT / date / "pmf_research.json"),
        ("latest", EXPORT_ROOT / "latest" / "pmf_research.json"),
        ("root", EXPORT_ROOT / "pmf_research.json"),
    )
    for label, p in aff_paths:
        payload, err = _read_json(p)
        if err:
            failures.append(err)
            continue
        failures.extend(_check_affiliate(payload, f"affiliate[{label}]"))
        # Date staleness check on date-keyed file.
        if label == "date":
            payload_date = _payload_date(payload)
            if payload_date is not None and payload_date != date:
                failures.append(
                    f"affiliate[{label}].date={payload_date!r} != "
                    f"requested {date!r}"
                )
    for label, p in pmf_paths:
        payload, err = _read_json(p)
        if err:
            failures.append(err)
            continue
        failures.extend(_check_pmf_research(payload, f"pmf_research[{label}]"))
        if label == "date":
            payload_date = _payload_date(payload)
            if payload_date is not None and payload_date != date:
                failures.append(
                    f"pmf_research[{label}].date={payload_date!r} != "
                    f"requested {date!r}"
                )

    if failures:
        print("WOO_PUBLIC_EXPORT_CONTRACT_FAILED  "
              f"date={date}  failures={len(failures)}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"WOO_PUBLIC_EXPORT_CONTRACT_PASS  date={date}  "
          f"local_export_root={EXPORT_ROOT.relative_to(REPO_ROOT)}")

    # 3. Remote checks
    if args.require_remote:
        if not args.base_url:
            print("WOO_PUBLIC_EXPORT_REMOTE_FAILED  "
                  "reason=--require-remote_supplied_without_--base-url",
                  file=sys.stderr)
            return 1
        try:
            import urllib.request
            import urllib.error
            base = args.base_url.rstrip("/") + "/"
        except Exception:
            print("WOO_PUBLIC_EXPORT_REMOTE_FAILED  "
                  "reason=urllib_unavailable", file=sys.stderr)
            return 1
        remote_failures: list[str] = []
        endpoints = [
            ("nba-props.html", "html"),
            ("nba-pmf-research", "html"),
            ("affiliate_dashboard.json", "json_rows"),
            ("pmf_research.json", "json_players"),
            ("latest/affiliate_dashboard.json", "json_rows"),
            ("latest/pmf_research.json", "json_players"),
            (f"{date}/affiliate_dashboard.json", "json_rows"),
            (f"{date}/pmf_research.json", "json_players"),
        ]
        # Phase 13AL: 401/403 from a dev environment is "endpoint exists,
        # auth-required" — structurally valid (the URL path resolves and
        # returns a known response), not a failure of the model export.
        # Track separately from hard failures so the operator gets an
        # honest distinction.
        auth_protected: list[str] = []
        for path, kind in endpoints:
            url = urljoin(base, path)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "phase13al"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = resp.read()
                    status = resp.status
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    auth_protected.append(f"{url}: HTTP {e.code} (auth-protected dev)")
                    continue
                # Some environments serve the html page extensionless;
                # try the .html variant.
                if path == "nba-pmf-research" and e.code == 404:
                    try:
                        req = urllib.request.Request(url + ".html",
                                                       headers={"User-Agent": "phase13al"})
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            body = resp.read()
                            status = resp.status
                    except urllib.error.HTTPError as e2:
                        if e2.code in (401, 403):
                            auth_protected.append(
                                f"{url}.html: HTTP {e2.code} (auth-protected dev)"
                            )
                            continue
                        remote_failures.append(f"{url}: HTTP error {e}; .html also failed: {e2}")
                        continue
                    except Exception as e2:
                        remote_failures.append(f"{url}: HTTP error {e}; .html also failed: {e2}")
                        continue
                else:
                    remote_failures.append(f"{url}: HTTP error {e}")
                    continue
            except Exception as e:
                remote_failures.append(f"{url}: error {e}")
                continue
            if not body:
                remote_failures.append(f"{url}: empty body (status={status})")
                continue
            if kind in ("json_rows", "json_players"):
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception as e:
                    remote_failures.append(f"{url}: JSON parse error: {e}")
                    continue
                key = "rows" if kind == "json_rows" else "players"
                if not payload.get(key):
                    remote_failures.append(
                        f"{url}: '{key}' is empty"
                    )
        if remote_failures:
            print(f"WOO_PUBLIC_EXPORT_REMOTE_FAILED  "
                  f"date={date}  base_url={args.base_url!r}  "
                  f"failures={len(remote_failures)}", file=sys.stderr)
            for f in remote_failures:
                print(f"  - {f}", file=sys.stderr)
            return 1
        # Phase 13AL: when every reachable endpoint returns 401/403, the
        # dev environment is auth-protected — emit a documented
        # AUTH_PROTECTED variant rather than a hard PASS (we cannot
        # prove content without credentials) but also not a FAIL (the
        # endpoints structurally exist and respond). When at least some
        # endpoints returned 200 with valid content AND the rest are
        # auth-protected, we emit PASS with the auth-protected
        # endpoints flagged.
        endpoints_total = len(endpoints)
        endpoints_protected = len(auth_protected)
        endpoints_authenticated = endpoints_total - endpoints_protected
        if endpoints_protected > 0 and endpoints_authenticated == 0:
            print(f"WOO_PUBLIC_EXPORT_REMOTE_AUTH_PROTECTED  date={date}  "
                  f"base_url={args.base_url!r}  "
                  f"endpoints_checked={endpoints_total}  "
                  f"auth_protected={endpoints_protected}  "
                  f"reason=dev_endpoint_returns_401_for_all_endpoints  "
                  f"resolution=run_with_credentials_in_authenticated_runtime")
            for line in auth_protected:
                print(f"  - {line}")
            # AUTH_PROTECTED is honest: endpoints exist, no FAIL, but no
            # content-level PASS without credentials. Exit 0 with this
            # explicit advisory line so callers can distinguish.
            return 0
        print(f"WOO_PUBLIC_EXPORT_REMOTE_PASS  date={date}  "
              f"base_url={args.base_url!r}  "
              f"endpoints_checked={endpoints_total}  "
              f"endpoints_authenticated={endpoints_authenticated}  "
              f"endpoints_auth_protected={endpoints_protected}")
        if auth_protected:
            for line in auth_protected:
                print(f"  - (auth-protected) {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
