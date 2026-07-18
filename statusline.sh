#!/usr/bin/env bash
# Claude Code status line — model/effort · git branch/worktree · token usage
# Reads session JSON on stdin (see https://code.claude.com/docs/en/statusline).

input=$(cat)

# --- Parse fields (jq, with safe fallbacks). Newline-delimited to survive
#     values that contain spaces (e.g. "Opus 4.8"). ---
jqget() { printf '%s' "$input" | jq -r "$1" 2>/dev/null; }
MODEL=$(jqget '.model.display_name // "?"')
EFFORT=$(jqget '.effort.level // "-"')
STYLE=$(jqget '.output_style.name // "-"')
CWD=$(jqget '.workspace.current_dir // .cwd // "."')
WORKTREE=$(jqget '.workspace.git_worktree // "-"')
IN_TOK=$(jqget '.context_window.total_input_tokens // 0')
OUT_TOK=$(jqget '.context_window.total_output_tokens // 0')
WIN=$(jqget '.context_window.context_window_size // 200000')
PCT=$(jqget '(.context_window.used_percentage // 0) | floor')

# --- ANSI colors ---
DIM=$'\033[2m'; RESET=$'\033[0m'; BOLD=$'\033[1m'
PURPLE=$'\033[38;5;141m'; CYAN=$'\033[38;5;80m'
GREEN=$'\033[38;5;114m'; YELLOW=$'\033[38;5;221m'; RED=$'\033[38;5;203m'
GREY=$'\033[38;5;245m'
SEP="${DIM}${GREY} │ ${RESET}"

# --- Segment 1: model + effort ---
seg_model="${PURPLE}${BOLD}✶ ${MODEL}${RESET}"
if [ "$EFFORT" != "-" ] && [ -n "$EFFORT" ]; then
  seg_model="${seg_model} ${DIM}${GREY}(${EFFORT})${RESET}"
fi

# --- Segment 2: git branch / worktree ---
seg_git=""
branch=$(cd "$CWD" 2>/dev/null && git symbolic-ref --short -q HEAD 2>/dev/null \
  || (cd "$CWD" 2>/dev/null && git rev-parse --short HEAD 2>/dev/null))
if [ -n "$branch" ]; then
  dirty=""
  if ! (cd "$CWD" 2>/dev/null && git diff --quiet --ignore-submodules HEAD 2>/dev/null); then
    dirty="${YELLOW}*${RESET}"
  fi
  seg_git="${CYAN} ${branch}${RESET}${dirty}"
  if [ "$WORKTREE" != "-" ] && [ -n "$WORKTREE" ]; then
    seg_git="${seg_git} ${DIM}${GREY}⌥${WORKTREE}${RESET}"
  fi
fi

# --- Segment 3: token usage + budget ---
fmt_tokens() {
  # integer tokens -> e.g. 45.2k
  awk -v n="$1" 'BEGIN{
    if (n>=1000000) printf "%.1fM", n/1000000;
    else if (n>=1000) printf "%.1fk", n/1000;
    else printf "%d", n;
  }'
}
USED=$(( ${IN_TOK:-0} + ${OUT_TOK:-0} ))
used_h=$(fmt_tokens "$USED")
win_h=$(fmt_tokens "$WIN")

# color by usage
pct=${PCT:-0}
if   [ "$pct" -ge 80 ]; then tcol="$RED"
elif [ "$pct" -ge 50 ]; then tcol="$YELLOW"
else tcol="$GREEN"; fi

seg_tok="${tcol}${used_h}${RESET}${DIM}${GREY}/${win_h}${RESET}"

# --- Assemble ---
line="${seg_model}"
[ -n "$seg_git" ] && line="${line}${SEP}${seg_git}"
line="${line}${SEP}${seg_tok}"
printf '%b' "$line"
