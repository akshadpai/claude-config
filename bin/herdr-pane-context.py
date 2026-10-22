#!/usr/bin/env python3
"""Print the conversation of the agent in a neighbouring Herdr pane.

Usage: herdr-pane-context.py <up|down|left|right|top|bottom>

Claude panes are read from their session transcript; any other pane falls
back to Herdr's terminal scrollback.
"""

import glob
import json
import os
import subprocess
import sys

DIRECTIONS = {"up": "up", "top": "up", "down": "down", "bottom": "down", "left": "left", "right": "right"}
MAX_CHARS = 80_000
TOOL_RESULT_CHARS = 500


def herdr(*args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"herdr {' '.join(args)} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)["result"]


def truncate(text, limit):
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f" … [{len(text) - limit} more chars]"


def render_transcript(path):
    lines = []
    for raw in open(path, encoding="utf-8"):
        entry = json.loads(raw)
        if entry.get("type") not in ("user", "assistant") or entry.get("isMeta") or entry.get("isSidechain"):
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        speaker = "USER" if entry["type"] == "user" else "ASSISTANT"
        for block in content or []:
            match block.get("type"):
                case "text" if block["text"].strip():
                    lines.append(f"{speaker}: {block['text'].strip()}")
                case "tool_use":
                    lines.append(f"TOOL CALL {block['name']}: {truncate(json.dumps(block.get('input')), 300)}")
                case "tool_result":
                    result = block.get("content")
                    if isinstance(result, list):
                        result = "\n".join(b.get("text", "") for b in result if b.get("type") == "text")
                    lines.append(f"TOOL RESULT: {truncate(str(result or ''), TOOL_RESULT_CHARS)}")
    return "\n\n".join(lines)


if len(sys.argv) != 2 or sys.argv[1].lower() not in DIRECTIONS:
    sys.exit(f"usage: {os.path.basename(sys.argv[0])} <{'|'.join(DIRECTIONS)}>")

if os.environ.get("HERDR_ENV") != "1" or not os.environ.get("HERDR_PANE_ID"):
    sys.exit("Not running inside a Herdr pane.")

direction = DIRECTIONS[sys.argv[1].lower()]
neighbor_id = herdr("pane", "neighbor", "--pane", os.environ["HERDR_PANE_ID"], "--direction", direction)["neighbor"].get(
    "neighbor_pane_id"
)
if not neighbor_id:
    sys.exit(f"No pane {direction} of this one.")

pane = herdr("pane", "get", neighbor_id)["pane"]
session = pane.get("agent_session") or {}
transcripts = []
if pane.get("agent") == "claude" and session.get("value"):
    transcripts = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session['value']}.jsonl"))

print(f"Pane {neighbor_id} ({pane.get('agent') or 'shell'}): {pane.get('terminal_title_stripped', '')}")
print(f"cwd: {pane.get('cwd')}")

if transcripts:
    print(f"Source: Claude transcript {transcripts[0]}\n")
    text = render_transcript(transcripts[0])
else:
    print("Source: terminal scrollback (no Claude transcript found)\n")
    result = subprocess.run(
        ["herdr", "pane", "read", neighbor_id, "--source", "recent-unwrapped", "--lines", "1000"],
        capture_output=True,
        text=True,
    )
    text = result.stdout

if len(text) > MAX_CHARS:
    print(f"[Earlier conversation omitted; showing the last {MAX_CHARS} chars]\n")
    text = text[-MAX_CHARS:]
print(text)
