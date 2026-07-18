# GitHub Workflow

## Pull Requests

When creating a GitHub PR that resolves an issue, always include a closing reference in the PR body using the format:

**Resolves #1**

Replace `1` with the actual issue number. This should appear in the PR description so GitHub automatically closes the linked issue when the PR is merged.

## Branch Naming

When opening a branch related to a GitHub issue, use the following format:

```
<issue-number>-name-of-branch
```

For example, if the issue is #4 and the work is about adding authentication, the branch should be named:

```
4-add-authentication
```

Keep the branch name lowercase, hyphen-separated, and descriptive of the work being done. Do not prefix the branch name with `claude/` or `fix/` (or any other prefix) — it should start directly with the issue number.

# Git worktrees

Do not use `claude --worktree`.

When creating a worktree:

- Create it with `git worktree add`.
- Store all worktrees under `<repository-root>/worktrees/`.
- Create the `worktrees/` directory if it does not exist.
- Reuse an existing worktree for the branch if one already exists.
