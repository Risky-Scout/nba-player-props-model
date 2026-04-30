"""Fetch player/team predictions from Dunks & Threes (dunksandthrees.com).

CLI fetcher used by `scripts/refresh_daily_inputs.py`. Pulls:
  - /api/v1/epm                  (per-player EPM rows for the given date)
  - /api/v1/team-epm             (per-team EPM rows)
  - /api/v1/game-predictions     (per-game predicted score / pace)
  - /api/v1/game-predictions-box (per-game per-player projected box rows)

Authentication
--------------
Reads the API key from `DUNKS_AND_THREES_API_KEY` (preferred) or
`DUNKS_API_KEY`. The key is sent in the `Authorization` header per the
canonical D&T spec used elsewhere in this repo
(see `Live Model Dashboard for WoO/.../clients/dunks.py`). The key is
NEVER logged or written to disk.

Outputs
-------
Each endpoint is written to `data/dunks_and_threes/{date}/{endpoint}.json`.
Output files are NOT staged in git (raw API data; see `.gitignore` rules).
The caller is responsible for staging derived artifacts.

CLI:
    python scripts/fetch_dunks_and_threes.py --date 2026-04-29
    python scripts/fetch_dunks_and_threes.py --date 2026-04-29 \
        --endpoints epm team-epm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "dunks_and_threes"
BASE_URL = "https://dunksandthrees.com/api/v1"

ENDPOINTS = (
    "epm",
    "team-epm",
    "game-predictions",
    "game-predictions-box",
)


def _now_utc_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _api_key() -> str:
    key = (os.environ.get("DUNKS_AND_THREES_API_KEY")
           or os.environ.get("DUNKS_API_KEY") or "").strip()
    if not key:
        raise SystemExit(
            "FATAL: neither DUNKS_AND_THREES_API_KEY nor DUNKS_API_KEY is set"
        )
    return key


def _get(endpoint: str, params: dict | None, *, key: str,
         max_retries: int = 4, timeout: float = 25.0) -> tuple[int, str]:
    cleaned = {k: v for k, v in (params or {}).items() if v is not None}
    qs = "&".join(f"{k}={v}" for k, v in cleaned.items())
    url = f"{BASE_URL}/{endpoint}" + (f"?{qs}" if qs else "")
    req = urllib.request.Request(url, headers={
        "Authorization": key, "Accept": "application/json"})
    last_status, last_body = -1, ""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_status = e.code
            try:
                last_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                last_body = ""
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            return e.code, last_body
        except Exception as e:
            last_status, last_body = -1, str(e)
            time.sleep(2 ** attempt)
    return last_status, last_body


def fetch_endpoint(endpoint: str, *, date: str | None,
                    key: str, out_dir: Path) -> dict:
    """Fetch one endpoint. Returns a per-endpoint summary dict.
    Writes raw JSON under `out_dir/{endpoint}.json` on success."""
    started = _now_utc_iso()
    status, body = _get(endpoint, {"date": date}, key=key)
    summary = {
        "endpoint": endpoint,
        "url": f"{BASE_URL}/{endpoint}",
        "date_param": date,
        "status_code": status,
        "started_at_utc": started,
        "ended_at_utc": _now_utc_iso(),
        "rows": 0,
        "bytes": len(body),
        "wrote_path": None,
        "error": None,
    }
    if status != 200:
        summary["error"] = (
            f"HTTP {status}: {body[:240].replace(chr(10), ' ')}"
        )
        return summary
    try:
        parsed = json.loads(body)
    except Exception as e:
        summary["error"] = f"json decode failed: {e}"
        return summary

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{endpoint}.json"
    out_path.write_text(json.dumps(parsed, indent=2))
    summary["wrote_path"] = str(out_path.relative_to(REPO_ROOT))
    if isinstance(parsed, list):
        summary["rows"] = len(parsed)
    elif isinstance(parsed, dict):
        # Some D&T endpoints wrap rows under a key; sniff most common.
        for k in ("data", "rows", "results"):
            if isinstance(parsed.get(k), list):
                summary["rows"] = len(parsed[k])
                break
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True,
                     help="YYYY-MM-DD slate date (US/Eastern)")
    ap.add_argument("--endpoints", nargs="+", default=list(ENDPOINTS),
                     choices=list(ENDPOINTS),
                     help="subset of endpoints to fetch (default: all)")
    ap.add_argument("--out-root", default=str(RAW_DIR),
                     help=f"raw output root (default: {RAW_DIR})")
    args = ap.parse_args()

    key = _api_key()
    out_root = Path(args.out_root)
    out_dir = out_root / args.date

    print(f"fetch_dunks_and_threes — date={args.date}")
    print(f"  endpoints={args.endpoints}")
    print(f"  out_dir={out_dir.relative_to(REPO_ROOT)}")
    print("-" * 64)

    summaries = []
    any_failed = False
    for ep in args.endpoints:
        s = fetch_endpoint(ep, date=args.date, key=key, out_dir=out_dir)
        summaries.append(s)
        flag = "OK" if s["status_code"] == 200 else "FAIL"
        print(f"  [{flag}] {ep:24s} status={s['status_code']:>4}  "
              f"rows={s['rows']:>5}  bytes={s['bytes']:>7}  "
              f"path={s['wrote_path']}")
        if s["error"]:
            print(f"        error: {s['error']}")
        if s["status_code"] != 200:
            any_failed = True

    manifest_path = out_dir / "_fetch_manifest.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "date": args.date,
        "fetched_at_utc": _now_utc_iso(),
        "base_url": BASE_URL,
        "endpoints": summaries,
        "any_failed": any_failed,
    }, indent=2))
    print(f"\nwrote manifest: {manifest_path.relative_to(REPO_ROOT)}")
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
