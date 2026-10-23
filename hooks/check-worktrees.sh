#!/usr/bin/env bash
# Stop hook.
#
# Blocks the turn from ending while a worktree this session created is still on
# disk. /pr and /dpr are told to remove theirs, but that step sits after the
# task's natural end point and gets skipped; nothing used to check.
#
# Blocks at most once per session, so a worktree deliberately kept (uncommitted
# work in it) can't wedge the turn.

set -uo pipefail

LEDGER_DIR="$HOME/.claude/worktree-sessions"

payload="$(cat)"
session_id="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)"
[ -n "$session_id" ] || exit 0

ledger="$LEDGER_DIR/$session_id.txt"
[ -f "$ledger" ] || exit 0

leftover=()
while IFS= read -r path; do
  [ -n "$path" ] || continue
  [ -d "$path" ] && leftover+=("$path")
done < "$ledger"

[ "${#leftover[@]}" -gt 0 ] || exit 0

# Already nagged once this session — mention it, don't block again.
sentinel="$LEDGER_DIR/$session_id.blocked"
if [ -f "$sentinel" ]; then
  printf '{"systemMessage": "Worktree still present: %s"}\n' "${leftover[*]}"
  exit 0
fi

: > "$sentinel" 2>/dev/null || true

{
  echo "This session created git worktrees that are still on disk:"
  for path in "${leftover[@]}"; do
    echo "  $path"
  done
  echo
  echo "For each one: run 'git -C <path> status --porcelain'."
  echo "  - Clean: remove it with 'git worktree remove <path>' (keep the branch)."
  echo "  - Uncommitted work: leave it and tell the user what's in it."
} >&2

exit 2
