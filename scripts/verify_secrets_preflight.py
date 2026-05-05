#!/usr/bin/env python3
"""Phase 13AL/13AN — mode-specific secrets preflight.

Checks that the env vars production scripts/workflows depend on are set.
NEVER prints secret values; only presence + length signature.

Modes (selected via ``--mode``):

    training      — nightly training/calibration. Hard-requires
                    BDL_API_KEY. Deploy/odds keys are advisory.
    daily         — daily PMF delivery + predictions. Hard-requires
                    BDL_API_KEY and ODDS_API_KEY. Lineup/injury
                    provider key (Dunks & Threes) is hard-required
                    when --require-lineup-source is set.
    ftp_deploy    — Wizard of Odds FTP deploy. Hard-requires
                    WOO_FTP_HOST, WOO_FTP_USER, WOO_FTP_PASSWORD.
                    SFTP keys are not required.
    sftp_deploy   — predictions SFTP upload. Hard-requires SFTP_HOST,
                    SFTP_USER, SFTP_PASS, SFTP_PATH. WOO_FTP keys are
                    not required.
    custom        — empty defaults; only what --require / --recommend add.

Pass line: SECRETS_PREFLIGHT_PASS  mode=<mode>
Fail line: SECRETS_PREFLIGHT_FAILED  mode=<mode>  missing=...

Phase 13AN also adds support for the canonical Dunks & Threes secret
name with deterministic precedence over the legacy aliases:

    1. DUNKS_AND_THREES_API_KEY   (canonical)
    2. DNT_API_KEY                (legacy alias)
    3. DUNKS_API_KEY              (legacy alias)
    4. DUNKS_THREES_API_KEY       (legacy alias)

When ``--mode daily --require-lineup-source`` is passed, at least one
of these must be present and non-empty, or the preflight fails.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

# Canonical and legacy aliases for the Dunks & Threes lineup/injury feed
# secret. Precedence is left-to-right: the first non-empty hit wins.
DUNKS_AND_THREES_PRECEDENCE: tuple[str, ...] = (
    "DUNKS_AND_THREES_API_KEY",
    "DNT_API_KEY",
    "DUNKS_API_KEY",
    "DUNKS_THREES_API_KEY",
)

# Per-mode required/recommended sets. ``required`` are hard failures.
MODE_PROFILES: dict[str, dict[str, tuple[str, ...]]] = {
    "training": {
        "required": ("BDL_API_KEY",),
        "recommended": ("ODDS_API_KEY",),
    },
    "daily": {
        "required": ("BDL_API_KEY", "ODDS_API_KEY"),
        "recommended": (
            # SFTP for predictions upload is recommended in daily but
            # not strictly required (some operators upload manually).
            "SFTP_HOST", "SFTP_USER", "SFTP_PASS", "SFTP_PATH",
        ),
    },
    "ftp_deploy": {
        "required": ("WOO_FTP_HOST", "WOO_FTP_USER", "WOO_FTP_PASSWORD"),
        "recommended": ("WOO_FTP_REMOTE_DIR",),
    },
    "sftp_deploy": {
        "required": ("SFTP_HOST", "SFTP_USER", "SFTP_PASS", "SFTP_PATH"),
        "recommended": (),
    },
    "custom": {
        "required": (),
        "recommended": (),
    },
}


def _signature(value: str) -> str:
    """Return a non-reversible signature so logs prove "this is the same
    secret" without revealing its content."""
    if not value:
        return "<empty>"
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"len={len(value)}  sha256_prefix={h}"


def _resolve_dunks_and_threes() -> tuple[str | None, str | None]:
    """Return (canonical_value, source_var_name) from the precedence
    list. Both are None if no value is present."""
    for name in DUNKS_AND_THREES_PRECEDENCE:
        v = (os.environ.get(name) or "").strip()
        if v:
            return v, name
    return None, None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--mode",
        choices=tuple(MODE_PROFILES.keys()),
        default="training",
        help="Which production profile to enforce (default: training).",
    )
    ap.add_argument(
        "--require",
        action="append",
        default=[],
        help="Additional hard-required env var(s)",
    )
    ap.add_argument(
        "--recommend",
        action="append",
        default=[],
        help="Additional recommended env var(s)",
    )
    ap.add_argument(
        "--require-lineup-source",
        action="store_true",
        help=(
            "Hard-require at least one Dunks & Threes secret "
            "(canonical: DUNKS_AND_THREES_API_KEY) under the "
            "documented precedence chain."
        ),
    )
    args = ap.parse_args(argv)

    profile = MODE_PROFILES[args.mode]
    required = list(profile["required"]) + list(args.require or [])
    recommended = list(profile["recommended"]) + list(args.recommend or [])

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

    # Dunks & Threes resolution.
    dnt_value, dnt_source = _resolve_dunks_and_threes()
    if args.require_lineup_source:
        if dnt_value:
            present_required.append(
                f"DUNKS_AND_THREES_API_KEY (via {dnt_source}): "
                f"{_signature(dnt_value)}"
            )
        else:
            missing_required.append(
                "DUNKS_AND_THREES_API_KEY (or aliases: "
                + ", ".join(DUNKS_AND_THREES_PRECEDENCE[1:])
                + ")"
            )
    else:
        if dnt_value:
            present_recommended.append(
                f"DUNKS_AND_THREES_API_KEY (via {dnt_source}): "
                f"{_signature(dnt_value)}"
            )
        else:
            # Only mention as missing/recommended for daily mode where
            # the lineup/injury feed is structurally relevant.
            if args.mode == "daily":
                missing_recommended.append(
                    "DUNKS_AND_THREES_API_KEY (or any alias)"
                )

    print(f"Secrets preflight (mode={args.mode}; values are never printed):")
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
        print(
            f"SECRETS_PREFLIGHT_FAILED  mode={args.mode}  "
            f"missing={missing_required}",
            file=sys.stderr,
        )
        return 1

    if missing_recommended:
        print(
            f"SECRETS_PREFLIGHT_PASS  mode={args.mode}  "
            f"required_present={len(present_required)}  "
            f"recommended_missing={missing_recommended}"
        )
    else:
        print(
            f"SECRETS_PREFLIGHT_PASS  mode={args.mode}  "
            f"required_present={len(present_required)}  "
            f"recommended_present={len(present_recommended)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
