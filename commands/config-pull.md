---
description: Pull the latest changes to your Claude Code config (~/.claude / claude-config repo)
---

Sync `~/claude-config` (symlinked to `~/.claude`) with its remote:

1. Run `git -C ~/claude-config status` to check for uncommitted local changes. If there are any, stop and tell the user — don't stash or discard anything without asking.
2. Run `git -C ~/claude-config pull` to fetch and merge the latest changes.
3. Report the result concisely: what changed (e.g. `git -C ~/claude-config log --oneline HEAD@{1}..HEAD` if the pull moved HEAD), or "already up to date" if nothing changed.

If the pull fails (merge conflict, diverged history, etc.), stop and show the user the error rather than trying to auto-resolve it.
