#!/usr/bin/env bash
# PostToolUse hook (matcher: Bash).
#
# Records every git worktree this session creates into a per-session ledger, so
# the Stop hook can tell "a worktree I made and forgot to clean up" apart from
# the long-lived parallel worktrees a repo may keep on purpose.
#
# Never blocks a tool call: always exits 0.

set -uo pipefail

LEDGER_DIR="$HOME/.claude/worktree-sessions"

payload="$(cat)"
[ -n "$payload" ] || exit 0

command_text="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)" || exit 0
[ -n "$command_text" ] || exit 0

# Cheap reject before doing any real work — most Bash calls aren't worktree adds.
printf '%s' "$command_text" | grep -Eq 'worktree[[:space:]]+add' || exit 0

session_id="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null)"
[ -n "$session_id" ] || exit 0

cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$cwd" ] || cwd="$PWD"

# The target path is the first non-flag token after `add`. Splitting on shell
# separators first keeps `cd foo && git worktree add ...` working, and skipping
# the argument of -b/-B handles `git worktree add -b name path`.
paths="$(printf '%s' "$command_text" | tr ';&|\n' '\n\n\n\n' | awk '
  /worktree[[:space:]]+add/ {
    for (i = 1; i <= NF; i++) {
      if ($i == "add" && $(i - 1) == "worktree") {
        for (j = i + 1; j <= NF; j++) {
          if ($j ~ /^-/) { if ($j == "-b" || $j == "-B") j++; continue }
          print $j
          break
        }
      }
    }
  }')"
[ -n "$paths" ] || exit 0

mkdir -p "$LEDGER_DIR" 2>/dev/null || exit 0
ledger="$LEDGER_DIR/$session_id.txt"

while IFS= read -r raw; do
  [ -n "$raw" ] || continue

  case "$raw" in
    /*) resolved="$raw" ;;
    *)
      resolved="$cwd/$raw"
      # A compound command may have cd'd elsewhere before the add; fall back to
      # the repo root, which is where our own worktrees/<name> paths are rooted.
      if [ ! -d "$resolved" ]; then
        root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)"
        [ -n "$root" ] && [ -d "$root/$raw" ] && resolved="$root/$raw"
      fi
      ;;
  esac

  # Record even if the directory isn't there yet — PostToolUse normally runs
  # after a successful add, but the Stop hook re-checks existence anyway, so a
  # path that never materialized is simply never reported.
  if ! [ -f "$ledger" ] || ! grep -qxF "$resolved" "$ledger" 2>/dev/null; then
    printf '%s\n' "$resolved" >> "$ledger" 2>/dev/null || true
  fi
done <<< "$paths"

exit 0
