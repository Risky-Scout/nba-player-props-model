"""Phase 13W Part C — strict BDL fetch proof verifier.

For each Derek snapshot under
``deliveries/<delivery_date>/derek_game_snapshots/<game_id>/<snapshot_type>/``
asserts that snapshot_manifest.json contains explicit (non-null)
BDL fetch fields. Never prints API keys.

Required manifest fields (per snapshot):

  * BDL_lineup_fetch_attempted (bool)
  * BDL_lineup_fetch_status (str)
  * BDL_lineup_rows (int)
  * BDL_lineup_endpoint (str)
  * BDL_lineup_fetched_at_utc (str when attempted)
  * BDL_injury_fetch_attempted (bool)
  * BDL_injury_fetch_status (str)
  * BDL_injury_rows (int)
  * BDL_injury_endpoint or deferred_source (str)

Pass line:  PHASE13W_BDL_FETCH_PROOF_PASS
Fail line:  PHASE13W_BDL_FETCH_PROOF_FAILED
Pending:    PHASE13W_BDL_FETCH_PROOF_PENDING (no snapshots present)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES = REPO_ROOT / "deliveries"
HEALTH = REPO_ROOT / "artifacts" / "automation_health"


REQUIRED_BOOL = (
    "BDL_lineup_fetch_attempted",
    "BDL_injury_fetch_attempted",
)
REQUIRED_STR = (
    "BDL_lineup_fetch_status",
    "BDL_lineup_endpoint",
    "BDL_injury_fetch_status",
    "BDL_injury_endpoint",
)
REQUIRED_INT = (
    "BDL_lineup_rows",
    "BDL_injury_rows",
)


def _audit_snapshot(snap_dir: Path) -> tuple[list[str], dict]:
    issues: list[str] = []
    m_path = snap_dir / "snapshot_manifest.json"
    if not m_path.exists():
        return ["snapshot_manifest.json missing"], {}
    try:
        m = json.loads(m_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot parse snapshot_manifest.json: {exc}"], {}
    facts: dict = {}
    for f in REQUIRED_BOOL:
        v = m.get(f)
        facts[f] = v
        if not isinstance(v, bool):
            issues.append(f"{f} not bool (got {type(v).__name__}={v!r})")
    for f in REQUIRED_STR:
        v = m.get(f)
        facts[f] = v
        if v is None or not isinstance(v, str) or not v:
            issues.append(f"{f} not a non-empty string (got {v!r})")
    for f in REQUIRED_INT:
        v = m.get(f)
        facts[f] = v
        if not isinstance(v, int):
            issues.append(f"{f} not int (got {type(v).__name__}={v!r})")
    # When fetch attempted, fetched_at_utc must be present.
    if m.get("BDL_lineup_fetch_attempted") is True:
        ts = m.get("BDL_lineup_fetched_at_utc")
        facts["BDL_lineup_fetched_at_utc"] = ts
        if not ts:
            issues.append("BDL_lineup_fetched_at_utc missing despite attempted")
    # API key invariants — manifest must NOT carry literal keys.
    blob = json.dumps(m)
    for keyname in ("BDL_API_KEY=", "ODDS_API_KEY="):
        if keyname in blob:
            issues.append(f"manifest leaks {keyname[:-1]} value")
    return issues, facts


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    HEALTH.mkdir(parents=True, exist_ok=True)
    base = DELIVERIES / args.delivery_date / "derek_game_snapshots"
    payload: dict = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "snapshots": [],
    }

    if not base.exists():
        payload["outcome"] = "pending"
        payload["reason"] = (
            f"derek_game_snapshots dir missing for {args.delivery_date}"
        )
        (HEALTH / f"bdl_fetch_proof_{args.delivery_date}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        print("PHASE13W_BDL_FETCH_PROOF_PENDING")
        print(f"  reason={payload['reason']}")
        return 0

    failures = 0
    counted = 0
    for game_dir in sorted(base.iterdir()):
        if not game_dir.is_dir():
            continue
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            sd = game_dir / snap_type
            if not (sd / "snapshot_manifest.json").exists():
                continue
            counted += 1
            issues, facts = _audit_snapshot(sd)
            payload["snapshots"].append({
                "game_id": game_dir.name,
                "snapshot_type": snap_type,
                "issues": issues,
                "facts": facts,
            })
            if issues:
                failures += 1

    if counted == 0:
        payload["outcome"] = "pending"
        payload["reason"] = "no snapshots present yet"
        (HEALTH / f"bdl_fetch_proof_{args.delivery_date}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        print("PHASE13W_BDL_FETCH_PROOF_PENDING")
        print(f"  reason={payload['reason']}")
        return 0

    payload["outcome"] = "fail" if failures else "pass"
    payload["snapshot_count"] = counted
    payload["failure_count"] = failures
    out_json = HEALTH / f"bdl_fetch_proof_{args.delivery_date}.json"
    out_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    out_md = HEALTH / f"bdl_fetch_proof_{args.delivery_date}.md"
    md = [
        f"# BDL fetch proof — {args.delivery_date}",
        "",
        f"- snapshots: **{counted}**",
        f"- failures: **{failures}**",
        "",
        "## Per-snapshot findings",
        "",
    ]
    for s in payload["snapshots"]:
        md.append(f"### {s['game_id']}/{s['snapshot_type']}")
        md.append("")
        md.append("```")
        for k, v in s["facts"].items():
            md.append(f"  {k}={v!r}")
        md.append("```")
        if s["issues"]:
            md.append("**issues:**")
            for i in s["issues"]:
                md.append(f"  - {i}")
        md.append("")
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    if failures:
        print("PHASE13W_BDL_FETCH_PROOF_FAILED", file=sys.stderr)
        for s in payload["snapshots"]:
            for i in s["issues"]:
                print(f"  - {s['game_id']}/{s['snapshot_type']}: {i}", file=sys.stderr)
        return 1
    print("PHASE13W_BDL_FETCH_PROOF_PASS")
    print(f"  delivery_date={args.delivery_date} snapshots={counted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
