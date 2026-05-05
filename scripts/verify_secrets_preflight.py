#!/usr/bin/env python3
"""Phase 13AL — secrets preflight.

Checks that the env vars production scripts/workflows depend on are set.
NEVER prints secret values; only presence + length signature.

Required (hard fail if missing):
  BDL_API_KEY

Recommended (soft warn if missing — script still passes, but logs the gap):
  ODDS_API_KEY            — daily predictions / Derek snapshot odds fetch
  WOO_FTP_HOST            — WoO FTP deploy
  WOO_FTP_USER
  WOO_FTP_PASSWORD
  SFTP_HOST               — predictions FTP upload
  SFTP_USER
  SFTP_PASS
  SFTP_PATH

Pass line: SECRETS_PREFLIGHT_PASS
Fail line: SECRETS_PREFLIGHT_FAILED  missing=...
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

REQUIRED = ("BDL_API_KEY",)
RECOMMENDED = (
    "ODDS_API_KEY",
    "WOO_FTP_HOST", "WOO_FTP_USER", "WOO_FTP_PASSWORD",
    "SFTP_HOST", "SFTP_USER", "SFTP_PASS", "SFTP_PATH",
)


def _signature(value: str) -> str:
    """Return a non-reversible signature so logs prove "this is the same
    secret" without revealing its content. Uses sha256[:8] over the
    value+name pair so two different secrets with the same length give
    different signatures."""
    if not value:
        return "<empty>"
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"len={len(value)}  sha256_prefix={h}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--require", action="append", default=[],
                    help="Additional required env var(s)")
    ap.add_argument("--recommend", action="append", default=[],
                    help="Additional recommended env var(s)")
    args = ap.parse_args(argv)

    required = list(REQUIRED) + list(args.require or [])
    recommended = list(RECOMMENDED) + list(args.recommend or [])

    missing_required: list[str] = []
    present_required: list[str] = []
    for name in required:
        v = (os.environ.get(name) or "").strip()
        if not v:
            missing_required.append(name)
        else:
            present_required.append(f"{name}: {_signature(v)}")

    missing_recommended: list[str] = []
    present_recommended: list[str] = []
    for name in recommended:
        v = (os.environ.get(name) or "").strip()
        if not v:
            missing_recommended.append(name)
        else:
            present_recommended.append(f"{name}: {_signature(v)}")

    print("Secrets preflight (no secret values are ever printed):")
    if present_required:
        print("  Required (present):")
        for line in present_required:
            print(f"    - {line}")
    if missing_required:
        print("  Required (MISSING):")
        for name in missing_required:
            print(f"    - {name}")
    if present_recommended:
        print("  Recommended (present):")
        for line in present_recommended:
            print(f"    - {line}")
    if missing_recommended:
        print("  Recommended (missing — soft warn):")
        for name in missing_recommended:
            print(f"    - {name}")

    if missing_required:
        print(f"SECRETS_PREFLIGHT_FAILED  missing={missing_required}",
              file=sys.stderr)
        return 1

    if missing_recommended:
        print(f"SECRETS_PREFLIGHT_PASS  required_present={len(present_required)}  "
              f"recommended_missing={missing_recommended}")
    else:
        print(f"SECRETS_PREFLIGHT_PASS  "
              f"required_present={len(present_required)}  "
              f"recommended_present={len(present_recommended)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
