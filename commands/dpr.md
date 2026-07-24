---
description: Implement a GitHub issue in a new worktree/branch and open a draft PR
argument-hint: <issue-number> [--base <branch>]
---

Follow the exact same steps as `/pr $1`, with one difference: in step 5, open the pull request as a draft (`gh pr create --draft`) instead of ready-for-review. Pass through any `--base <branch>` flag from `$ARGUMENTS` unchanged.
