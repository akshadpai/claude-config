---
description: Orient on ~/.claude as a git repo before working on Claude Code config files
---

`~/.claude` is a symlink to `~/claude-config`, which is a git repo tracked at `origin` (`https://github.com/akshadpai/claude-config`).

The user wants to work on their Claude Code config (commands, `CLAUDE.md`, settings, etc.) this session. Treat `~/claude-config` as a normal project repo for the rest of this session:

- Read and edit files there directly (they're plain files, not special-cased).
- Use normal git workflow for changes — `git -C ~/claude-config status/add/commit/push` (or `cd ~/claude-config` first) — same commit/push conventions as any other repo, including confirming with the user before pushing.
- If local may be behind the remote, consider running `/config-pull` first to sync.

Don't take any action yet beyond noting this — wait for the user's actual request.
