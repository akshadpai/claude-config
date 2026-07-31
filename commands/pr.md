---
description: Implement a GitHub issue (or a freeform task) in a new worktree/branch and open a PR
argument-hint: <issue-number|task description> [--draft] [--base <branch>]
---

Determine the mode from `$ARGUMENTS`:

- **Issue mode**: the first token is a plain number (e.g. `123`). The task is GitHub issue #$1.
- **Freeform mode**: the first token isn't a plain number — there is no GitHub issue. The *entire* `$ARGUMENTS`, minus the `--draft`/`--base <branch>` flags below, is a plain-text description of the task to implement directly.

If `$ARGUMENTS` contains `--draft`, open the PR as a draft (`gh pr create --draft`). Otherwise open it as a normal, ready-for-review PR.

If `$ARGUMENTS` contains `--base <branch>`, use `<branch>` as the base for the new branch/worktree and as the PR's target branch (`gh pr create --base <branch>`). Otherwise default to the repo's main/integration branch as defined in CLAUDE.md (e.g. `develop`), falling back to the current default branch if CLAUDE.md doesn't specify one — do not silently branch off whatever happens to be checked out.

In **issue mode**, any text in `$ARGUMENTS` beyond the issue number and the flags above is additional context/requirements from the user alongside the issue — read it before step 3 and factor it in; it supplements the issue body, it doesn't replace reading the issue itself. In **freeform mode**, that text (minus the flags) *is* the task — there's no separate issue body to supplement.

Follow these steps:

1. **Get the requirements.**
   - Issue mode: run `gh issue view $1` to get the title and body. Make sure you're in a git repository with a GitHub remote; if not, stop and tell the user.
   - Freeform mode: use the free-text description directly as the requirements. Still confirm you're in a git repository with a GitHub remote (needed for the worktree/branch/PR steps below); if not, stop and tell the user. No issue lookup is needed.

2. **Create the branch and worktree.**
   - Branch name: a lowercase, hyphen-separated, short-descriptive name per the branch naming convention in CLAUDE.md.
     - Issue mode: `$1-<short-hyphenated-description>` derived from the issue title.
     - Freeform mode: `<short-hyphenated-description>` derived from the task description (no issue-number prefix, since there is no issue).
   - Determine the base branch per the `--base` rule above. Make sure it's up to date locally (`git fetch origin <base-branch>`) before branching from it.
   - Create the `worktrees/` directory at the repo root if it doesn't exist.
   - If a worktree for this branch already exists under `worktrees/`, reuse it instead of creating a new one.
   - Otherwise create it with `git worktree add worktrees/<branch-name> -b <branch-name> <base-branch>`.

3. **Implement the fix inside the worktree.** Work entirely within `worktrees/<branch-name>`. Read the requirements carefully (the issue in issue mode, the free-text description in freeform mode) and make the necessary code changes to resolve them. Run any relevant tests/checks that exist in the repo before proceeding.

4. **Commit the changes** with a concise commit message describing the fix (do not reference the current task/issue number in code comments — only in the commit message and PR body).

5. **Push and open the PR.**
   - Push the branch: `git push -u origin <branch-name>`.
   - Create the PR with `gh pr create` (add `--draft` if requested per above, and `--base <base-branch>` if it differs from the repo default).
   - Use a short, clear PR title. The PR body MUST follow this format:

     ```
     ## Summary
     - <concise bullet point>
     - <concise bullet point>

     **Resolves #$1**
     ```

     - `## Summary` always comes first, followed by 1-5 concise bullet points describing what changed and why — scale the number of bullets to the complexity of the change (a trivial fix gets 1 bullet, a larger change gets up to 5).
     - Issue mode: end the body with a `**Resolves #$1**` line (bolded), so GitHub auto-closes the linked issue on merge.
     - Freeform mode: there's no issue to close, so omit the `Resolves #` line entirely.

6. **Clean up the worktree.** Once the PR is created successfully, remove the worktree with `git worktree remove worktrees/<branch-name>` so the branch is free to be checked out in the main worktree (e.g. for local testing). Do not delete the branch itself.

7. **Report back** the PR URL and a one-line summary of what was implemented.

Confirm with the user before pushing/creating the PR if anything about the requirements is ambiguous — don't guess at scope for unclear issues or under-specified freeform tasks.
