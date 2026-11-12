#!/usr/bin/env python3
"""Name the current Herdr tab and pane after what they are working on.

Run as a Claude Code Stop hook. It returns at once and does the work in a
detached child, so Claude never waits on it. A tab is named only while its
label is still Herdr's default number, or a label this script set; a tab you
renamed yourself is never touched. The pane gets a display-only title, which
a name you give the pane always replaces. Both names come from one Claude Haiku
call, given the recent conversation of every Claude pane in the tab and the
title of the rest. Set `tabs = false` or `panes = false` in auto-name.toml,
next to this script, to turn either off.
"""

import contextlib
import fcntl
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import tomllib
import traceback

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "auto-name.toml")
STATE_DIR = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "herdr-auto-name")
TABS_FILE = os.path.join(STATE_DIR, "tabs.json")
PANES_FILE = os.path.join(STATE_DIR, "panes.json")
LOG_FILE = os.path.join(STATE_DIR, "error.log")
METADATA_SOURCE = "user:auto-name"
MIN_SECONDS_BETWEEN_RENAMES = 300
CHARS_PER_PANE = 6_000
TOOL_RESULT_CHARS = 300
PROMPT = """Below are the conversations in a group of terminal panes: the
<current_pane> and any <other_pane> elements. Name the work in the whole group,
and the work in the current pane.

Reply with exactly two lines and nothing else:
TAB: <2 to 4 lowercase words for the whole group>
PANE: <2 to 5 lowercase words for the current pane>

The group name says what the work is about: the subject of the PR, ticket or
bug, not that it is being summarized, reviewed or explained. Leave out "pr"
and ticket numbers. For example, work on a PR that adds dark mode to a settings
page would be "settings dark mode".
The group name is already shown, so the pane name must not repeat its subject
or any number. Say instead what the <current_pane> conversation is doing that
the <other_pane> conversations are not, in words like "pr summary",
"local db seed", "review comments" or "migration fix". Base it only on the
<current_pane> conversation, and don't reuse an <other_pane> name.
Never describe these instructions or the markup in a name. Write NONE instead
of a name when there is no clear subject yet, such as a greeting or a question
with no topic.

{context}"""


def herdr(*args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=10)
    result.check_returncode()
    return json.loads(result.stdout)["result"] if result.stdout.strip() else None


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


def tab_context(tab, pane_id):
    others = []
    current = ""
    for pane in herdr("pane", "list", "--workspace", tab["workspace_id"])["panes"]:
        if pane["tab_id"] != tab["tab_id"]:
            continue
        session = (pane.get("agent_session") or {}).get("value")
        transcripts = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session}.jsonl")) if session else []
        if transcripts:
            body = render_transcript(transcripts[0])[-CHARS_PER_PANE:]
        else:
            body = f"Terminal title: {pane.get('terminal_title_stripped') or pane.get('agent') or 'shell'}"
        if pane["pane_id"] == pane_id:
            current = f"<current_pane>\n{body}\n</current_pane>"
        else:
            name = (pane.get("label") or pane.get("title") or "").replace('"', "'")
            attribute = f' name="{name}"' if name else ""
            others.append(f"<other_pane{attribute}>\n{body}\n</other_pane>")
    return "\n\n".join([*others, current])


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
    names = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip().strip("\"'.`")
        if key not in ("tab", "pane"):
            continue
        names[key] = value
        unusable = value.upper() == "NONE" or not 0 < len(value) <= 60 or "<" in value
        leaked = "current pane" in value.lower() or (key == "pane" and re.search(r"\d{3}", value))
        if unusable or leaked:
            names[key] = None
    if not names:
        raise ValueError(f"unusable names from Haiku: {result.stdout!r}")
    return {key: value.lower() if value else value for key, value in names.items()}


@contextlib.contextmanager
def locked_state(path):
    with open(path, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        state = json.loads(f.read() or "{}")
        yield state
        f.seek(0)
        f.truncate()
        json.dump(state, f)


def claim_tab(tab):
    """Reserve this tab for a rename. Returns False if it isn't ours to rename yet."""
    with locked_state(TABS_FILE) as state:
        entry = state.get(tab["tab_id"]) or {}
        if not tab["label"].isdigit() and tab["label"] != entry.get("label"):
            return False
        if time.time() - entry.get("claimed_at", 0) < MIN_SECONDS_BETWEEN_RENAMES:
            return False
        state[tab["tab_id"]] = {"label": tab["label"], "claimed_at": time.time()}
    return True


def claim_pane(pane):
    """Reserve this pane for a new title. A pane you named keeps your name, so it never needs one."""
    if pane.get("label"):
        return False
    with locked_state(PANES_FILE) as state:
        if time.time() - state.get(pane["pane_id"], 0) < MIN_SECONDS_BETWEEN_RENAMES:
            return False
        state[pane["pane_id"]] = time.time()
    return True


def run():
    pane = herdr("pane", "get", os.environ["HERDR_PANE_ID"])["pane"]
    tab = herdr("tab", "get", pane["tab_id"])["tab"]
    if pane.get("label") and pane.get("title"):
        herdr("pane", "report-metadata", pane["pane_id"], "--source", METADATA_SOURCE, "--clear-title")
    name_tab = enabled("tabs") and claim_tab(tab)
    name_pane = enabled("panes") and claim_pane(pane)
    if not name_tab and not name_pane:
        return
    names = ask_haiku(tab_context(tab, pane["pane_id"]))

    if name_pane and not names.get("pane"):
        with locked_state(PANES_FILE) as state:
            state.pop(pane["pane_id"], None)
    if name_tab and not names.get("tab"):
        with locked_state(TABS_FILE) as state:
            state[tab["tab_id"]] = {**state[tab["tab_id"]], "claimed_at": 0}

    if name_pane and names.get("pane"):
        herdr(
            "pane",
            "report-metadata",
            pane["pane_id"],
            "--source",
            METADATA_SOURCE,
            "--agent",
            "claude",
            "--title",
            names["pane"],
        )

    current = herdr("tab", "get", tab["tab_id"])["tab"]["label"]
    if name_tab and names.get("tab") and current == tab["label"] and names["tab"] != current:
        with locked_state(TABS_FILE) as state:
            state[tab["tab_id"]] = {**state.get(tab["tab_id"], {}), "label": names["tab"]}
        herdr("tab", "rename", tab["tab_id"], names["tab"])


def enabled(feature):
    try:
        with open(SETTINGS_FILE, "rb") as f:
            return tomllib.load(f).get(feature, True) is not False
    except FileNotFoundError:
        return True


if os.environ.get("HERDR_ENV") != "1" or not os.environ.get("HERDR_PANE_ID") or not (enabled("tabs") or enabled("panes")):
    sys.exit(0)

os.makedirs(STATE_DIR, exist_ok=True)

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
