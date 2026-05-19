#!/usr/bin/env python3
import os
import sys

dunks = (
    os.getenv("DUNKS_AND_THREES_API_KEY")
    or os.getenv("DUNKS_API_KEY")
    or os.getenv("DNT_API_KEY")
    or os.getenv("DUNKS_THREES_API_KEY")
)

checks = {
    "BDL_API_KEY": os.getenv("BDL_API_KEY"),
    "ODDS_API_KEY": os.getenv("ODDS_API_KEY"),
    "DUNKS_AND_THREES_API_KEY_OR_ALIAS": dunks,
}

missing = [k for k, v in checks.items() if not str(v or "").strip()]

if missing:
    print("CRITICAL_DELIVERY_SOURCES_FAIL")
    for k in missing:
        print(f"missing={k}")
    sys.exit(1)

print("CRITICAL_DELIVERY_SOURCES_PASS")
print(f"BDL_API_KEY length={len(os.getenv('BDL_API_KEY', ''))}")
print(f"ODDS_API_KEY length={len(os.getenv('ODDS_API_KEY', ''))}")
print(f"DUNKS key length={len(dunks)}")
