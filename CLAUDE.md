# GitHub Workflow

## Pull Requests

These are guidelines for PR descriptions **you write**. Don't hold other people's PRs to them: don't remark on another person's PR description format at all, in summaries as well as reviews.

Keep descriptions short. The default body is a `## Summary` heading, the bullets, and — for a PR that resolves an issue — a closing reference:

```
## Summary
- Course structure settings now reach the module generation prompt.
- The block-count target is clamped before the tolerance band is derived.
- An out-of-range block count now warns instead of raising.

**Resolves #372**
```

Guidelines:

- **Aim for 3 bullets or fewer**; go beyond that only when the change genuinely spans more distinct things. A trivial fix gets 1.
- **Don't report tests, changelog entries, or other routine scaffolding** — a bullet like "Added tests asserting the centered alignment" only belongs in a PR whose actual purpose was test (or changelog) work. Otherwise spend the bullets on the behaviour that changed.
- **Keep each bullet to one sentence** saying what changed. Avoid semicolon-chained clauses, parenthetical rationale, nested sub-bullets, and code walkthroughs.
- Describe *what changed*, not the investigation behind it. No narration of prior behaviour, no "previously X, so Y", no explanation of why the old code was wrong.
- **Add other sections only when the PR needs them**, such as a screen recording or screenshots of a UI change, a deploy or migration step the reviewer must know about, or test steps for a risky change. Test evidence that reviewers need, such as a test-call transcript, a results table, or before/after output, is one of those sections: put it in the PR body under its own heading, and don't cut it to keep the description short. Don't add boilerplate like "Background", "Motivation", or "Implementation details" by default.
- End an issue-linked PR with a bolded `**Resolves #1**` line (replace `1` with the actual issue number) so GitHub auto-closes the issue on merge. Omit the line entirely when there's no issue.

## Reviews

- For any problem flagged in a PR or review, verify it against the code before reporting it.
- Say whether the PR introduced the problem or it already existed on the base branch.

## Pushing to an existing PR

Before pushing to an existing PR branch, fetch and integrate the remote branch first. The user and other sessions update PR branches on GitHub, through the "Update branch" button and parallel sessions. Never force-push over them.

## Comments

- Keep PR comments and Linear comments short and easy to digest.
- When asked to change a comment that is already posted, edit it in place rather than posting another.
- Don't post comments or replies to GitHub or Linear unless asked.

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

# Working style

- **A question is not a go-ahead.** Questions like "should we…", "is it easy?", "are we ready to implement?" or "is this true?" get an answer only. Edit files, create branches, or commit only after an explicit instruction to.
- **Number findings, options and review comments.** The user replies by number, such as "do no. 3".

# Shell

The Bash tool runs zsh:

- Quote globs, as in `--include='*.ex'`.
- Write `"${VAR}:path"` rather than `$VAR:path`, because zsh treats `:l`, `:t`, `:r` and similar as modifiers.
- Use arrays rather than an unquoted space-separated variable for lists of files.
