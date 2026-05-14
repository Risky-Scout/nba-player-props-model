#!/bin/bash
# ============================================================================
# fw3_status_flag_patch.sh
#
# Purpose: Fix the affiliate_dashboard.json contradiction where
# market_superiority_claim_allowed=false coexists with
# accuracy_support_status="supported" and calibration_support_status="supported".
#
# Patches scripts/publish_woo_public_export.py:
#   1. Row builder (~line 786): gate status flags on market_superiority_claim_allowed
#   2. Counter (~line 873): compute supported counts from actual row data, not len(df)
#
# Run from repo root after restructure has landed (or before — it's independent):
#   cd ~/repos/nba-player-props-model-pmf-fix
#   bash fw3_status_flag_patch.sh
# ============================================================================

set -u

REPO_ROOT="$(pwd)"
TARGET="scripts/publish_woo_public_export.py"
GIT_AUTHOR="Joseph Shackelford <josephshack@gmail.com>"
COMMIT_TAG="fw3-status-flag-gate"

cBOLD="\033[1m"; cRED="\033[31m"; cGRN="\033[32m"; cYLW="\033[33m"; cBLU="\033[34m"; cRST="\033[0m"
say()  { printf "${cBOLD}%s${cRST}\n" "$*"; }
ok()   { printf "${cGRN}OK${cRST}: %s\n" "$*"; }
warn() { printf "${cYLW}WARN${cRST}: %s\n" "$*"; }
err()  { printf "${cRED}ERROR${cRST}: %s\n" "$*" >&2; }
ask()  { printf "${cBLU}>>${cRST} %s " "$*"; }
hr()   { printf '%s\n' "------------------------------------------------------------------------"; }

confirm() {
  local prompt="$1"; local answer=""
  ask "$prompt (type 'yes' to continue, anything else to abort):"
  read -r answer
  if [ "$answer" = "yes" ]; then return 0; fi
  err "User did not type 'yes'. Aborting."
  return 1
}

# ----------------------------------------------------------------------------
# Sanity
# ----------------------------------------------------------------------------
say "FW3 status-flag patch for $TARGET"
hr

if [ ! -f "$TARGET" ]; then
  err "$TARGET not found. Are you in the repo root?"
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  err "Not in a git repo."
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
say "Branch: $CURRENT_BRANCH"
say "HEAD  : $(git rev-parse --short HEAD)"

# Check working tree state
if ! git diff --quiet -- "$TARGET" || ! git diff --cached --quiet -- "$TARGET"; then
  warn "$TARGET already has uncommitted changes."
  git diff -- "$TARGET" | head -30
  if ! confirm "Continue and stack this patch on top?"; then
    exit 1
  fi
fi

# ----------------------------------------------------------------------------
# BEFORE state
# ----------------------------------------------------------------------------
say "BEFORE STATE — relevant lines:"
hr
echo "--- row builder (around line 786) ---"
sed -n '785,795p' "$TARGET"
echo ""
echo "--- counter (around line 873) ---"
sed -n '870,878p' "$TARGET"
hr

if ! confirm "Proceed with patch?"; then exit 1; fi

# ----------------------------------------------------------------------------
# Apply the patch via Python (defensive)
# ----------------------------------------------------------------------------
say "Applying patch..."

python3 <<'PYEOF'
import sys
from pathlib import Path

TARGET = "scripts/publish_woo_public_export.py"
src = Path(TARGET).read_text()

# ─── Patch 1: row builder ────────────────────────────────────────────────────
# Find the exact 3 lines we need to replace.
OLD_ROW_BUILDER = (
    '            "calibration_support_status": str(get(r, "calibration_support_status", default="supported")),\n'
    '            "accuracy_support_status": str(get(r, "accuracy_support_status", default="supported")),\n'
)
if OLD_ROW_BUILDER not in src:
    print("FATAL: row builder pattern not found at expected location.", file=sys.stderr)
    print("This patch was authored against a specific revision; the file has", file=sys.stderr)
    print("drifted. Manual inspection required around lines 786-787.", file=sys.stderr)
    sys.exit(2)

# Also need to find the market_superiority_claim_allowed line just below (line 790)
OLD_SUP_LINE = '            "market_superiority_claim_allowed": bool(get(r, "market_superiority_claim_allowed", default=False)),\n'
if OLD_SUP_LINE not in src:
    print("FATAL: market_superiority_claim_allowed line not found.", file=sys.stderr)
    sys.exit(3)

# The replacement injects the gating logic ABOVE the base dict, then references
# pre-computed values inside the dict. We replace the calibration+accuracy lines
# with references, and we leave the market_superiority_claim_allowed line
# referencing the same sup_allowed variable.

# Find the start of the row builder loop — look for "for _, r in df.iterrows():"
LOOP_HEADER = "    for _, r in df.iterrows():\n"
loop_idx = src.find(LOOP_HEADER)
if loop_idx < 0:
    print("FATAL: row builder loop header not found.", file=sys.stderr)
    sys.exit(4)

# Find the "base = {" inside this loop
base_idx = src.find("        base = {", loop_idx)
if base_idx < 0 or base_idx - loop_idx > 2000:
    print("FATAL: 'base = {' marker not found within reasonable distance of loop header.", file=sys.stderr)
    sys.exit(5)

# Insert the gating logic right before "base = {"
GATING_BLOCK = (
    '\n'
    '        # FW3 — Status flags gated on market_superiority_claim_allowed.\n'
    '        # When market superiority has not been independently validated\n'
    '        # against book lines (Brier/logloss/NLL/RPS deltas with sample-\n'
    '        # size support), calibration and accuracy claims must reflect\n'
    '        # that this is internal-OOF improvement only, not market-validated.\n'
    '        _sup_allowed = bool(get(r, "market_superiority_claim_allowed", default=False))\n'
    '        if _sup_allowed:\n'
    '            _cal_status = str(get(r, "calibration_support_status", default="supported"))\n'
    '            _acc_status = str(get(r, "accuracy_support_status", default="supported"))\n'
    '        else:\n'
    '            _cal_status = "internal_oof_improved_not_market_validated"\n'
    '            _acc_status = "unknown_pending_market_validation"\n'
)

# Replace the row builder fields
NEW_ROW_BUILDER = (
    '            "calibration_support_status": _cal_status,\n'
    '            "accuracy_support_status": _acc_status,\n'
)
NEW_SUP_LINE = '            "market_superiority_claim_allowed": _sup_allowed,\n'

# Apply edits in order: insert gating block, replace row builder lines.
new_src = src[:base_idx] + GATING_BLOCK + src[base_idx:]
new_src = new_src.replace(OLD_ROW_BUILDER, NEW_ROW_BUILDER)
new_src = new_src.replace(OLD_SUP_LINE, NEW_SUP_LINE)

# Verify replacement happened
if NEW_ROW_BUILDER not in new_src:
    print("FATAL: row builder replacement did not apply.", file=sys.stderr)
    sys.exit(6)
if "_sup_allowed = bool(" not in new_src:
    print("FATAL: gating block insertion did not apply.", file=sys.stderr)
    sys.exit(7)

# ─── Patch 2: counter at line 873-874 ────────────────────────────────────────
OLD_COUNTER = (
    '        "calibration_supported_rows": len(df),\n'
    '        "accuracy_supported_rows": len(df),\n'
)
if OLD_COUNTER not in new_src:
    print("FATAL: counter pattern at ~lines 873-874 not found.", file=sys.stderr)
    sys.exit(8)

NEW_COUNTER = (
    '        "calibration_supported_rows": sum(\n'
    '            1 for _r in rows\n'
    '            if str(_r.get("calibration_support_status", "")).lower() in ("supported", "calibrated")\n'
    '        ),\n'
    '        "accuracy_supported_rows": sum(\n'
    '            1 for _r in rows\n'
    '            if str(_r.get("accuracy_support_status", "")).lower() in ("supported", "accurate")\n'
    '        ),\n'
)

new_src = new_src.replace(OLD_COUNTER, NEW_COUNTER)
if "1 for _r in rows" not in new_src:
    print("FATAL: counter replacement did not apply.", file=sys.stderr)
    sys.exit(9)

# Verify file still parses as Python
import ast
try:
    ast.parse(new_src)
except SyntaxError as e:
    print(f"FATAL: edited file has Python syntax error: {e}", file=sys.stderr)
    print("Not writing. Original file untouched.", file=sys.stderr)
    sys.exit(10)

Path(TARGET).write_text(new_src)
print("OK: both patches applied and file re-parses as Python.")
PYEOF

EDIT_RC=$?
if [ $EDIT_RC -ne 0 ]; then
  err "Patch failed (exit code $EDIT_RC)."
  exit 1
fi

# ----------------------------------------------------------------------------
# AFTER state
# ----------------------------------------------------------------------------
hr
say "AFTER STATE — patched regions:"
echo "--- row builder ---"
grep -n -B 2 -A 15 "_sup_allowed = bool" "$TARGET" | head -40
echo ""
echo "--- counter ---"
grep -n -B 1 -A 8 'calibration_supported_rows": sum' "$TARGET" | head -25

# ----------------------------------------------------------------------------
# Diff
# ----------------------------------------------------------------------------
hr
say "Full diff vs HEAD:"
git --no-pager diff -- "$TARGET" | head -80

# ----------------------------------------------------------------------------
# Stage + HYBRID approve
# ----------------------------------------------------------------------------
hr
if ! confirm "approve diff $COMMIT_TAG"; then
  err "Not approved. Reverting."
  git checkout -- "$TARGET"
  exit 1
fi

git add "$TARGET"

COMMIT_MSG="Gate WoO public-export status flags on market_superiority_claim_allowed (FW3)

publish_woo_public_export.py had two related defects causing the
affiliate_dashboard.json contradiction where every row claimed
accuracy_support_status='supported' and calibration_support_status=
'supported' while market_superiority_claim_allowed=false.

Fixes:
  1. Row builder (formerly ~lines 786-787) defaulted these flags to
     'supported' when upstream rows omitted them. Now gated:
     - when market_superiority_claim_allowed is False (always today),
       force conservative status strings:
         calibration_support_status = 'internal_oof_improved_not_market_validated'
         accuracy_support_status = 'unknown_pending_market_validation'
     - when True (none currently), pass through upstream values
  2. Counter (formerly ~lines 873-874) hardcoded len(df) for
     calibration_supported_rows and accuracy_supported_rows
     regardless of actual status. Now computed from actual row data.

Aligns with MCP §5 step G and Acceptance Criteria §6 public claim policy:
'Not allowed until market scoring passes: market superior, beats the
market, superior calibration, or equivalent public/partner claims.'

tag: $COMMIT_TAG"

if ! git commit --author="$GIT_AUTHOR" -m "$COMMIT_MSG"; then
  err "git commit failed."
  exit 1
fi

NEW_SHA="$(git rev-parse --short HEAD)"
ok "committed $NEW_SHA"
hr

if ! confirm "approve push $COMMIT_TAG"; then
  warn "Push not approved. Commit is local at $NEW_SHA."
  warn "Push manually with: git push origin $CURRENT_BRANCH"
  exit 0
fi

if ! git push origin "$CURRENT_BRANCH"; then
  err "git push failed."
  exit 1
fi

git fetch origin
ORIGIN_SHA="$(git rev-parse --short "origin/$CURRENT_BRANCH")"
LOCAL_SHA="$(git rev-parse --short HEAD)"

hr
if [ "$LOCAL_SHA" = "$ORIGIN_SHA" ]; then
  ok "verified: origin/$CURRENT_BRANCH = $ORIGIN_SHA matches local $LOCAL_SHA"
else
  warn "local=$LOCAL_SHA, origin=$ORIGIN_SHA — investigate"
fi

say "FW3 patch done. Next regeneration of affiliate_dashboard.json will carry conservative status flags."
say ""
say "To regenerate today's dashboard with the new defaults:"
say "  python3 scripts/publish_woo_public_export.py --date 2026-05-12"
say "  (or whatever your normal regen command is)"
say ""
say "To verify the change is reflected:"
say "  python3 -c \"import json; d=json.load(open('public_export/wizard_of_odds/latest/affiliate_dashboard.json')); from collections import Counter; c=Counter((r['accuracy_support_status'], r['calibration_support_status']) for r in d); print(c)\""
