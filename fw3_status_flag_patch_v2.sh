#!/bin/bash
# ============================================================================
# fw3_status_flag_patch_v2.sh
#
# Same intent as v1 but uses pure line-replacement instead of trying to
# locate the `base = {` block. Three exact-line edits:
#
#   Edit 1: line ~786 — calibration_support_status: gate on market_superiority
#   Edit 2: line ~787 — accuracy_support_status: gate on market_superiority
#   Edit 3: lines ~873-874 — counter computes from `rows` instead of len(df)
#
# Run from repo root:
#   cd ~/repos/nba-player-props-model-pmf-fix
#   bash fw3_status_flag_patch_v2.sh
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
say "FW3 status-flag patch v2 for $TARGET"
hr

if [ ! -f "$TARGET" ]; then
  err "$TARGET not found. Are you in the repo root?"
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
say "Branch: $CURRENT_BRANCH"
say "HEAD  : $(git rev-parse --short HEAD)"

# Clear any leftover state from a failed v1 run (defensive — v1 should not
# have modified the file given it errored at exit code 5 before writing)
if ! git diff --quiet -- "$TARGET" || ! git diff --cached --quiet -- "$TARGET"; then
  warn "$TARGET has uncommitted changes from a previous run."
  git diff -- "$TARGET" | head -40
  if confirm "Discard those changes and start clean?"; then
    git checkout -- "$TARGET"
    ok "reverted $TARGET to HEAD"
  else
    if ! confirm "OK — stack v2 patch on top of existing changes?"; then
      exit 1
    fi
  fi
fi

# ----------------------------------------------------------------------------
# BEFORE state
# ----------------------------------------------------------------------------
say "BEFORE STATE — relevant lines:"
hr
echo "--- row builder (around line 786) ---"
grep -n -A 0 -B 0 'calibration_support_status.*get.*default="supported"' "$TARGET" | head -5
grep -n -A 0 -B 0 'accuracy_support_status.*get.*default="supported"' "$TARGET" | head -5
echo ""
echo "--- counter (around line 873) ---"
grep -n '"calibration_supported_rows": len(df)' "$TARGET" | head -5
grep -n '"accuracy_supported_rows": len(df)' "$TARGET" | head -5
hr

if ! confirm "Proceed with v2 patch (line-level replacement)?"; then exit 1; fi

# ----------------------------------------------------------------------------
# Apply the patch via Python
# ----------------------------------------------------------------------------
say "Applying patch..."

python3 <<'PYEOF'
import sys
from pathlib import Path

TARGET = "scripts/publish_woo_public_export.py"
src = Path(TARGET).read_text()
original = src

# ─── Edit 1: calibration_support_status line ─────────────────────────────────
OLD_CAL = '            "calibration_support_status": str(get(r, "calibration_support_status", default="supported")),\n'
NEW_CAL = (
    '            # FW3 — status flag gated on market_superiority_claim_allowed.\n'
    '            "calibration_support_status": (\n'
    '                str(get(r, "calibration_support_status", default="supported"))\n'
    '                if bool(get(r, "market_superiority_claim_allowed", default=False))\n'
    '                else "internal_oof_improved_not_market_validated"\n'
    '            ),\n'
)
n_cal = src.count(OLD_CAL)
if n_cal != 1:
    print(f"FATAL: expected exactly 1 occurrence of calibration_support_status default-supported line; found {n_cal}.", file=sys.stderr)
    sys.exit(2)
src = src.replace(OLD_CAL, NEW_CAL)

# ─── Edit 2: accuracy_support_status line ────────────────────────────────────
OLD_ACC = '            "accuracy_support_status": str(get(r, "accuracy_support_status", default="supported")),\n'
NEW_ACC = (
    '            "accuracy_support_status": (\n'
    '                str(get(r, "accuracy_support_status", default="supported"))\n'
    '                if bool(get(r, "market_superiority_claim_allowed", default=False))\n'
    '                else "unknown_pending_market_validation"\n'
    '            ),\n'
)
n_acc = src.count(OLD_ACC)
if n_acc != 1:
    print(f"FATAL: expected exactly 1 occurrence of accuracy_support_status default-supported line; found {n_acc}.", file=sys.stderr)
    sys.exit(3)
src = src.replace(OLD_ACC, NEW_ACC)

# ─── Edit 3: counter lines (873-874) ─────────────────────────────────────────
OLD_COUNTER = (
    '        "calibration_supported_rows": len(df),\n'
    '        "accuracy_supported_rows": len(df),\n'
)
NEW_COUNTER = (
    '        # FW3 — counters now reflect actual row status, not len(df).\n'
    '        "calibration_supported_rows": sum(\n'
    '            1 for _r in rows\n'
    '            if str(_r.get("calibration_support_status", "")).lower() in ("supported", "calibrated")\n'
    '        ),\n'
    '        "accuracy_supported_rows": sum(\n'
    '            1 for _r in rows\n'
    '            if str(_r.get("accuracy_support_status", "")).lower() in ("supported", "accurate")\n'
    '        ),\n'
)
n_counter = src.count(OLD_COUNTER)
if n_counter != 1:
    print(f"FATAL: expected exactly 1 occurrence of counter len(df) block; found {n_counter}.", file=sys.stderr)
    sys.exit(4)
src = src.replace(OLD_COUNTER, NEW_COUNTER)

# ─── Verify file still parses as Python ──────────────────────────────────────
import ast
try:
    ast.parse(src)
except SyntaxError as e:
    print(f"FATAL: edited file has Python syntax error: {e}", file=sys.stderr)
    print("Not writing. Original file untouched.", file=sys.stderr)
    sys.exit(10)

# ─── Verify all three patches landed ─────────────────────────────────────────
markers = [
    'else "internal_oof_improved_not_market_validated"',
    'else "unknown_pending_market_validation"',
    '1 for _r in rows',
]
for m in markers:
    if m not in src:
        print(f"FATAL: post-edit verification failed — marker not found: {m!r}", file=sys.stderr)
        sys.exit(11)

# ─── Verify the old patterns are gone ────────────────────────────────────────
forbidden_after = [
    '"calibration_support_status": str(get(r, "calibration_support_status", default="supported")),',
    '"accuracy_support_status": str(get(r, "accuracy_support_status", default="supported")),',
    '"calibration_supported_rows": len(df),',
    '"accuracy_supported_rows": len(df),',
]
for f in forbidden_after:
    if f in src:
        print(f"FATAL: old pattern still present after edit: {f!r}", file=sys.stderr)
        sys.exit(12)

# Write
Path(TARGET).write_text(src)
print("OK: all three edits applied, file re-parses, old patterns absent.")
PYEOF

EDIT_RC=$?
if [ $EDIT_RC -ne 0 ]; then
  err "Patch failed (exit code $EDIT_RC)."
  err "$TARGET is unchanged."
  exit 1
fi

# ----------------------------------------------------------------------------
# AFTER state
# ----------------------------------------------------------------------------
hr
say "AFTER STATE — patched regions:"
echo "--- new calibration_support_status block ---"
grep -n -A 4 '"calibration_support_status": (' "$TARGET" | head -10
echo ""
echo "--- new accuracy_support_status block ---"
grep -n -A 4 '"accuracy_support_status": (' "$TARGET" | head -10
echo ""
echo "--- new counter block ---"
grep -n -A 3 'calibration_supported_rows": sum' "$TARGET" | head -8

# ----------------------------------------------------------------------------
# Diff
# ----------------------------------------------------------------------------
hr
say "Full diff vs HEAD:"
git --no-pager diff -- "$TARGET"

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
  1. Row builder lines for calibration_support_status and
     accuracy_support_status defaulted to 'supported' when upstream
     rows omitted them. Now gated inline:
     - when market_superiority_claim_allowed is False (always today),
       force conservative status strings:
         calibration_support_status = 'internal_oof_improved_not_market_validated'
         accuracy_support_status = 'unknown_pending_market_validation'
     - when True (none currently), pass through upstream values
  2. Counter for calibration_supported_rows and accuracy_supported_rows
     hardcoded len(df) regardless of actual status. Now computed from
     actual row data after the row builder runs.

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

say ""
say "FW3 patch landed. Next regeneration of affiliate_dashboard.json will"
say "carry conservative status flags."
say ""
say "To regenerate today's dashboard with the new defaults:"
say "  python3 scripts/publish_woo_public_export.py --date 2026-05-12"
say "  (or whatever your normal regen command is)"
