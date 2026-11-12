#!/usr/bin/env python3
"""Name the current Herdr tab after what its panes are working on.

Run as a Claude Code Stop hook. It returns at once and does the work in a
detached child, so Claude never waits on it. A tab is named only while its
label is still Herdr's default number, or a label this script set; a tab you
renamed yourself is never touched. The name comes from Claude Haiku, given the
recent conversation of every Claude pane in the tab and the title of the rest.
"""

import fcntl
import glob
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback

STATE_FILE = os.path.expanduser("~/.cache/herdr-auto-name-tab.json")
LOG_FILE = os.path.expanduser("~/.cache/herdr-auto-name-tab.log")
MIN_SECONDS_BETWEEN_RENAMES = 300
CHARS_PER_PANE = 6_000
TOOL_RESULT_CHARS = 300
PROMPT = """Name a terminal tab from what its panes are working on, shown below.

Reply with the name only: 2 to 4 lowercase words, no quotes or punctuation.
Name the subject, not the activity: say what the PR, ticket or bug is about,
and leave out words like "pr", "summary", "review" and ticket numbers.
Good names: "presigned s3 uploads", "voice in mobile app", "gk cleanup",
"hide irrelevant app fields".

{context}"""


def herdr(*args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=10)
    result.check_returncode()
    return json.loads(result.stdout)["result"]


def render_transcript(path):
    lines = []
    for raw in open(path, encoding="utf-8"):
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
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
                case "tool_result":
                    result = block.get("content")
                    if isinstance(result, list):
                        result = "\n".join(b.get("text", "") for b in result if b.get("type") == "text")
                    lines.append(f"TOOL RESULT: {str(result or '').strip()[:TOOL_RESULT_CHARS]}")
    return "\n".join(lines)


def tab_context(tab):
    sections = []
    for pane in herdr("pane", "list", "--workspace", tab["workspace_id"])["panes"]:
        if pane["tab_id"] != tab["tab_id"]:
            continue
        session = (pane.get("agent_session") or {}).get("value")
        transcripts = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session}.jsonl")) if session else []
        body = render_transcript(transcripts[0])[-CHARS_PER_PANE:] if transcripts else ""
        title = pane.get("terminal_title_stripped") or pane.get("agent") or "shell"
        sections.append(f"=== Pane: {title} (cwd {pane.get('cwd')})\n{body}".strip())
    return "\n\n".join(sections)


def ask_haiku(context):
    env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_")}
    result = subprocess.run(
        [
            "claude",
            "-p",
            "--model",
            "haiku",
            "--settings",
            '{"disableAllHooks": true}',
            "--tools",
            "",
            "--strict-mcp-config",
            "--disable-slash-commands",
            "--no-session-persistence",
        ],
        input=PROMPT.format(context=context),
        capture_output=True,
        text=True,
        timeout=90,
        cwd=tempfile.gettempdir(),
        env=env,
    )
    result.check_returncode()
    name = result.stdout.strip().splitlines()[-1].strip().strip("\"'.`").lower()
    if not name or len(name) > 40:
        raise ValueError(f"unusable name from Haiku: {result.stdout!r}")
    return name


def claim(tab):
    """Reserve this tab for a rename. Returns False if it isn't ours to rename yet."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        state = json.loads(f.read() or "{}")
        entry = state.get(tab["tab_id"]) or {}
        label = tab["label"]
        if not label.isdigit() and label != entry.get("label"):
            return False
        if time.time() - entry.get("claimed_at", 0) < MIN_SECONDS_BETWEEN_RENAMES:
            return False
        state[tab["tab_id"]] = {"label": label, "claimed_at": time.time()}
        f.seek(0)
        f.truncate()
        json.dump(state, f)
    return True


def record(tab_id, label):
    with open(STATE_FILE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        state = json.loads(f.read() or "{}")
        state[tab_id] = {**state.get(tab_id, {}), "label": label}
        f.seek(0)
        f.truncate()
        json.dump(state, f)


def run():
    tab_id = herdr("pane", "get", os.environ["HERDR_PANE_ID"])["pane"]["tab_id"]
    tab = herdr("tab", "get", tab_id)["tab"]
    if not claim(tab):
        return
    name = ask_haiku(tab_context(tab))
    current = herdr("tab", "get", tab["tab_id"])["tab"]["label"]
    if current != tab["label"] or name == current:
        return
    record(tab["tab_id"], name)
    herdr("tab", "rename", tab["tab_id"], name)


if os.environ.get("HERDR_ENV") != "1" or not os.environ.get("HERDR_PANE_ID"):
    sys.exit(0)

if os.fork() == 0:
    os.setsid()
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    try:
        run()
    except Exception:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {traceback.format_exc()}\n")
    finally:
        os._exit(0)
