---
description: Remove the git worktree Claude created earlier in this session
---

Remove the git worktree created during this session (e.g. via `/pr`, `/dpr`, or an ad hoc `git worktree add`), if one is still around.

1. **Check whether this session created a worktree.** Look back through the conversation for a `git worktree add worktrees/<branch-name> ...` step.
   - If `/pr` or `/dpr` already ran their own step 6 cleanup for it, there's nothing to do — tell the user it was already removed and stop.
   - If no worktree was created in this session at all, say so plainly (don't guess). Then ask the user which worktree they want removed, offering the output of `git worktree list` (run it from the repo root) to help them choose.

2. **If a worktree from this session is still present**, confirm it still exists with `git worktree list`. Then check for uncommitted or unpushed work inside it (`git -C worktrees/<branch-name> status`, and compare against its upstream if pushed). If there's anything not committed/pushed, show the user what would be lost and get explicit confirmation before proceeding.

3. **Remove it** with `git worktree remove worktrees/<branch-name>` from the repo root. Do not delete the branch (`--delete-branch` equivalent) unless the user explicitly asks for that too.

4. **Report back** what was removed (path and branch), or that nothing was removed and why.
