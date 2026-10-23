#!/usr/bin/env python3
"""Split the current Herdr pane, start Claude in the new pane, and send it a prompt.

Usage: split-agent.py <auto|right|down|vertical|horizontal> <prompt-file>

`vertical` puts the new pane beside this one (right) and `horizontal` puts it
below (down), matching Herdr's split_vertical / split_horizontal bindings.
`auto` splits right when the pane is wide enough for two readable columns,
otherwise down.
"""

import json
import os
import subprocess
import sys

DIRECTIONS = {"right": "right", "vertical": "right", "down": "down", "horizontal": "down"}
MIN_COLUMN_WIDTH = 100


def herdr(*args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"herdr {' '.join(args)} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)["result"]


if len(sys.argv) != 3 or (sys.argv[1] != "auto" and sys.argv[1] not in DIRECTIONS):
    sys.exit(f"usage: {os.path.basename(sys.argv[0])} <auto|{'|'.join(DIRECTIONS)}> <prompt-file>")

if os.environ.get("HERDR_ENV") != "1" or not os.environ.get("HERDR_PANE_ID"):
    sys.exit("Not running inside a Herdr pane.")

own_pane_id = os.environ["HERDR_PANE_ID"]
prompt = open(sys.argv[2], encoding="utf-8").read().strip()
if not prompt:
    sys.exit(f"{sys.argv[2]} is empty.")

if sys.argv[1] == "auto":
    layout = herdr("pane", "layout", "--pane", own_pane_id)["layout"]
    rect = next(pane["rect"] for pane in layout["panes"] if pane["pane_id"] == own_pane_id)
    direction = "right" if rect["width"] >= 2 * MIN_COLUMN_WIDTH else "down"
else:
    direction = DIRECTIONS[sys.argv[1]]

taken = {agent.get("name") for agent in herdr("agent", "list")["agents"]}
name = next(f"impl{n}" for n in range(1, 1000) if f"impl{n}" not in taken)

cwd = herdr("pane", "get", own_pane_id)["pane"].get("foreground_cwd") or os.getcwd()
new_pane_id = herdr("pane", "split", "--pane", own_pane_id, "--direction", direction, "--cwd", cwd, "--no-focus")[
    "pane"
]["pane_id"]
herdr("agent", "start", name, "--kind", "claude", "--pane", new_pane_id, "--timeout", "60000")
herdr("agent", "prompt", name, prompt)

print(f"Started Claude agent '{name}' in pane {new_pane_id} (split {direction}, cwd {cwd}).")
