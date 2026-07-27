---
description: Implement a GitHub issue (or a freeform task) in a new worktree/branch and open a draft PR
argument-hint: <issue-number|task description> [--base <branch>]
---

Follow the exact same steps as `/pr $ARGUMENTS`, including its issue-mode/freeform-mode detection, with one difference: in step 5, open the pull request as a draft (`gh pr create --draft`) instead of ready-for-review. Pass through any `--base <branch>` flag from `$ARGUMENTS` unchanged.
