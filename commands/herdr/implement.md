---
description: Hand the plan from this conversation to a new Claude agent in a split Herdr pane
argument-hint: [vertical|horizontal|right|down] [extra instructions]
allowed-tools: Bash(~/.claude/herdr/split-agent.py:*)
---

Hand off the plan worked out in this conversation to a new Claude agent in a split Herdr pane, which implements it while this session stays free for more planning.

If the first word of `$ARGUMENTS` is `vertical`, `horizontal`, `right` or `down`, it's the split direction: `vertical`/`right` opens the new pane beside this one, `horizontal`/`down` below it. Otherwise use `auto`, which picks based on this pane's size. Anything else in `$ARGUMENTS` is extra instruction for the implementing agent.

1. Find the plan. Use the most recent plan agreed in this conversation, including any plan file written in plan mode. If there's no clear plan, or it still has open questions, say so and stop instead of handing off something half-decided.
2. Write a self-contained brief to a Markdown file in your scratchpad directory. The new agent has none of this conversation, so the brief must stand on its own:
   - the goal, and the full plan with every decision made here;
   - the files, functions and commands it involves, with paths;
   - constraints and anything explicitly ruled out or left out of scope;
   - the extra instructions from `$ARGUMENTS`, if any;
   - how to verify the work, and what to do when done (for example commit, open a draft PR, or stop and report), as agreed here. If nothing was agreed, tell it to stop after verifying and report back without committing.
3. Run `~/.claude/herdr/split-agent.py <direction> <brief-file>`. It splits this pane without moving focus, starts Claude in the new pane in the same working directory, and submits the brief as its first prompt. If it exits with an error, show the error and stop.
4. Report the agent's name and pane ID from the script's output, and mention that `/herdr:pane <direction>` reads its progress back into this session. Don't wait for it to finish.
