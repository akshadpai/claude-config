# GitHub Workflow

## Pull Requests

PR descriptions must be short. The body is exactly a `## Summary` heading, the bullets, and — for a PR that resolves an issue — a closing reference. Nothing else:

```
## Summary
- Course structure settings now reach the module generation prompt.
- The block-count target is clamped before the tolerance band is derived.
- An out-of-range block count now warns instead of raising.

**Resolves #372**
```

Rules:

- **5 bullets is the absolute maximum**, and 3-5 is the normal range. Fewer is better — a trivial fix gets 1.
- **Each bullet is exactly one sentence** saying what changed. No second sentence, no semicolon-chained clauses, no parenthetical rationale, no nested sub-bullets, no code walkthroughs.
- Describe *what changed*, not the investigation behind it. No narration of prior behaviour, no "previously X, so Y", no explanation of why the old code was wrong.
- **No other sections.** Never add "Note for the reviewer", "Testing", "Background", "Motivation", "Implementation details", "Follow-ups", or any heading beyond `## Summary`. Context that doesn't fit in the bullets belongs in a PR comment or a follow-up issue, not the body.
- End an issue-linked PR with a bolded `**Resolves #1**` line (replace `1` with the actual issue number) so GitHub auto-closes the issue on merge. Omit the line entirely when there's no issue.

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
