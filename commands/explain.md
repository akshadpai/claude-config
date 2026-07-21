---
description: Explain or analyze code read-only, without making any changes
argument-hint: <file, function, or question>
---

Investigate and explain the following, without editing, writing, or otherwise modifying any files: $ARGUMENTS

Guidelines:
- Use read-only tools only (Read, Grep, Glob, Bash for inspection like `git log`/`git show`/`cat`/`grep` — never `git commit`, `git add`, file edits, or any command that mutates state).
- If $ARGUMENTS names a file, function, or symbol, locate it first, then trace how it's used/called and why it's built the way it is.
- If $ARGUMENTS is a general question about the codebase, search broadly enough to answer accurately rather than guessing.
- Explain the "why" behind non-obvious design choices when you can find evidence for it (comments, commit history, related code) — don't invent rationale you can't support.
- End with a plain-language summary. Do not propose or make edits — if you spot a bug or improvement, mention it, but leave fixing it to a separate request.
