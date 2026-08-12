---
description: Bring the current branch up to date with the latest changes on its base branch
argument-hint: [--base <branch>]
---

Sync the branch that's currently checked out with the latest changes from its base branch. This works on whatever worktree you're in — it does not create or remove worktrees.

If `$ARGUMENTS` contains `--base <branch>`, use `<branch>` as the base. Otherwise default to the repo's main/integration branch as defined in CLAUDE.md (e.g. `develop`), falling back to the current default branch (`git symbolic-ref --short refs/remotes/origin/HEAD`) if CLAUDE.md doesn't specify one — do not assume it's `main`.

Follow these steps:

1. **Confirm where you are.** Run `git rev-parse --show-toplevel` and `git branch --show-current`. If HEAD is detached, stop and tell the user. If the checked-out branch *is* the base branch, there's nothing to sync — say so and stop (a plain `git pull` is what they want, not this).

2. **Say which base branch you picked** and why (flag, CLAUDE.md, or repo default) before touching anything.

3. **Refuse a dirty tree.** Run `git status --porcelain`. If it's non-empty, stop, show the user what's uncommitted, and ask whether to commit or stash first — don't stash, discard, or commit anything on their behalf.

4. **Fetch, then check whether there's anything to do.** Run `git fetch origin <base-branch>`. If `git merge-base --is-ancestor origin/<base-branch> HEAD` succeeds, the branch already contains everything on the base — report "already up to date" and stop.

5. **Merge.** Run `git merge origin/<base-branch>`. This is deliberately a merge, not a rebase: the branch's existing commits are never rewritten, so the push in step 7 stays a plain push.

6. **Resolve any conflicts.** Read both sides and reconcile them so the branch's intent survives alongside the incoming changes — never blindly take `--ours` or `--theirs`. If a conflict is genuinely ambiguous, or spans logic you can't confidently reconcile, leave the merge in progress (don't `git merge --abort` on your own), explain the conflict, and hand it back to the user. Once resolved, `git add` the files and `git commit` with the default merge message. Then run the repo's build/typecheck/test command if there's an obvious one — a merge can resolve cleanly textually and still break the build.

7. **Push.** If the branch has an upstream, run `git push` — no force is needed, since nothing was rewritten. If it has no upstream, the branch was never published: say so and ask before running `git push -u origin <branch-name>`.

8. **Report back**: the base branch used and how it was chosen, what came in (`git log --oneline HEAD@{1}..HEAD` or the merge summary), any conflicts and how you resolved them, and the push result.

If anything is ambiguous — which base branch to use, how to resolve a conflict, whether to publish an unpushed branch — stop and ask rather than guessing.
