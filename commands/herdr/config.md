---
description: Orient on the Herdr config before changing settings or key bindings
---

The user wants to work on their Herdr config this session. Keep the following in mind for the rest of the session:

- **Edit `~/claude-config/herdr/config.toml`.** `~/.config/herdr/config.toml` is a symlink to it. Everything else in `~/.config/herdr/` (sockets, logs, `session.json`, session snapshots) is Herdr's own state, so leave it alone.
- **Look up options in the installed version, not the website.** `herdr --version` and `herdr --default-config` show every option the installed build supports and which `[section]` it belongs in. The online docs can be ahead of the installed release.
- **Validate, then apply.** Run `herdr config check` after every edit and fix anything it reports, then `herdr server reload-config` so the change takes effect without restarting Herdr.
- **Scripts that key bindings run** (`[[keys.command]]`) go in `~/claude-config/herdr/`, next to `pane-context.py`.
- **`~/claude-config` is a git repo** (`origin` is `https://github.com/akshadpai/claude-config`). Use the normal branch, commit and PR workflow, and confirm with the user before pushing. For anything else in that repo, see `/claude-config`.

Don't take any action yet beyond noting this. Wait for the user's actual request.
