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
PROMPT = """Name a terminal tab, and the pane marked THIS PANE inside it, from what
the tab's panes are working on, shown below.

Reply with exactly two lines and nothing else:
TAB: <2 to 4 lowercase words>
PANE: <3 to 6 words>

Name the subject, not the activity: say what the PR, ticket or bug is about,
not that it is being summarized, reviewed or explained.
TAB covers the whole tab. Leave out "pr" and ticket numbers. Good tab names:
"presigned s3 uploads", "voice in mobile app", "gk cleanup".
PANE covers only THIS PANE. Start with its PR or ticket number when it has one.
Good pane names: "PR #15885 voicemail playback in call cards",
"PRDT-24803 gatekeeper cleanup", "Streamline booking card errors".

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
    sections = []
    for pane in herdr("pane", "list", "--workspace", tab["workspace_id"])["panes"]:
        if pane["tab_id"] != tab["tab_id"]:
            continue
        session = (pane.get("agent_session") or {}).get("value")
        transcripts = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session}.jsonl")) if session else []
        if transcripts:
            body = render_transcript(transcripts[0])[-CHARS_PER_PANE:]
        else:
            body = f"Terminal title: {pane.get('terminal_title_stripped') or pane.get('agent') or 'shell'}"
        marker = "THIS PANE" if pane["pane_id"] == pane_id else "Pane"
        sections.append(f"=== {marker} (cwd {pane.get('cwd')})\n{body}")
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
    names = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition(":")
        value = value.strip().strip("\"'.`")
        if key.strip().upper() in ("TAB", "PANE") and 0 < len(value) <= 60:
            names[key.strip().lower()] = value
    if not names:
        raise ValueError(f"unusable names from Haiku: {result.stdout!r}")
    names["tab"] = names.get("tab", "").lower()
    return names


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
