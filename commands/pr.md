---
description: Implement a GitHub issue in a new worktree/branch and open a PR
argument-hint: <issue-number> [--draft]
---

Resolve GitHub issue #$1 end to end: implement it, open a PR, and clean up.

If `$ARGUMENTS` contains `--draft`, open the PR as a draft (`gh pr create --draft`). Otherwise open it as a normal, ready-for-review PR.

Follow these steps:

1. **Read the issue.** Run `gh issue view $1` to get the title and body. Make sure you're in a git repository with a GitHub remote; if not, stop and tell the user.

2. **Create the branch and worktree.**
   - Branch name: `$1-<short-hyphenated-description>` derived from the issue title, per the branch naming convention in CLAUDE.md (lowercase, hyphen-separated, no prefix like `claude/` or `fix/`).
   - Create the `worktrees/` directory at the repo root if it doesn't exist.
   - If a worktree for this branch already exists under `worktrees/`, reuse it instead of creating a new one.
   - Otherwise create it with `git worktree add worktrees/<branch-name> -b <branch-name>`.

3. **Implement the fix inside the worktree.** Work entirely within `worktrees/<branch-name>`. Read the issue requirements carefully and make the necessary code changes to resolve it. Run any relevant tests/checks that exist in the repo before proceeding.

4. **Commit the changes** with a concise commit message describing the fix (do not reference the current task/issue number in code comments — only in the commit message and PR body).

5. **Push and open the PR.**
   - Push the branch: `git push -u origin <branch-name>`.
   - Create the PR with `gh pr create` (add `--draft` if requested per above). The PR body MUST include a closing reference in the exact form:

     ```
     Resolves #$1
     ```

   - Use a short, clear PR title and a body summarizing what changed and why, plus a test plan, per standard PR conventions.

6. **Clean up the worktree.** Once the PR is created successfully, remove the worktree with `git worktree remove worktrees/<branch-name>` so the branch is free to be checked out in the main worktree (e.g. for local testing). Do not delete the branch itself.

7. **Report back** the PR URL and a one-line summary of what was implemented.

Confirm with the user before pushing/creating the PR if anything about the issue's requirements is ambiguous — don't guess at scope for unclear issues.
