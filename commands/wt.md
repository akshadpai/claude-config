---
description: Run a task in a scratch worktree, commit the result, then remove the worktree (branch is kept)
argument-hint: <task description> [--base <branch>]
---

The entire `$ARGUMENTS`, minus the `--base <branch>` flag below, is a plain-text description of the task to do. If it's empty or too vague to act on, ask the user what to do before proceeding.

If `$ARGUMENTS` contains `--base <branch>`, use `<branch>` as the base for the new branch/worktree. Otherwise default to the repo's main/integration branch as defined in CLAUDE.md (e.g. `develop`), falling back to the current default branch if CLAUDE.md doesn't specify one — do not silently branch off whatever happens to be checked out.

Follow these steps:

1. **Confirm this is a git repository with the expected remote setup**; if not, stop and tell the user.

2. **Create the branch and worktree.**
   - Derive a short, lowercase, hyphen-separated branch name from the task description, per the branch naming convention in CLAUDE.md. There's no GitHub issue here, so no issue-number prefix.
   - Determine the base branch per the `--base` rule above. Make sure it's up to date locally (`git fetch origin <base-branch>`) before branching from it.
   - Create the `worktrees/` directory at the repo root if it doesn't exist.
   - If a worktree for this branch already exists under `worktrees/`, reuse it instead of creating a new one.
   - Otherwise create it with `git worktree add worktrees/<branch-name> -b <branch-name> <base-branch>`.

3. **Do the task inside the worktree.** Work entirely within `worktrees/<branch-name>`. Read the task description carefully and make the necessary changes. Run any relevant tests/checks that exist in the repo before proceeding.

4. **Commit any changes.** If the task modified any files, commit them with a concise message describing what was done (do not reference this command or the current task in code comments — only in the commit message). If nothing changed, skip this step.

5. **Remove the worktree.** `git worktree remove worktrees/<branch-name>` from the repo root. Do NOT delete the branch itself — it stays available for later checkout, review, or merging.

6. **Report back**: the branch name, a one-line summary of what was done, and note that the branch was left in place locally with no push and no PR opened (the user can push/open a PR themselves, or ask `/pr`-style tooling to pick it up).

Confirm with the user before doing anything ambiguous or destructive — don't guess at scope for an under-specified task.
