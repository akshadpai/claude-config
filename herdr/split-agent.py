#!/usr/bin/env python3
"""Split the current Herdr pane, start Claude in the new pane, and send it a prompt.

Usage: split-agent.py [--model MODEL] [--effort EFFORT] <auto|right|down|vertical|horizontal> <prompt-file>

`vertical` puts the new pane beside this one (right) and `horizontal` puts it
below (down), matching Herdr's split_vertical / split_horizontal bindings.
`auto` splits right when the pane is wide enough for two readable columns,
otherwise down. `--model` and `--effort` are passed to `claude`; without them it
starts on the saved defaults.
"""

import argparse
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


parser = argparse.ArgumentParser()
parser.add_argument("direction", choices=["auto", *DIRECTIONS])
parser.add_argument("prompt_file")
parser.add_argument("--model")
parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
args = parser.parse_args()

if os.environ.get("HERDR_ENV") != "1" or not os.environ.get("HERDR_PANE_ID"):
    sys.exit("Not running inside a Herdr pane.")

own_pane_id = os.environ["HERDR_PANE_ID"]
prompt = open(args.prompt_file, encoding="utf-8").read().strip()
if not prompt:
    sys.exit(f"{args.prompt_file} is empty.")

if args.direction == "auto":
    layout = herdr("pane", "layout", "--pane", own_pane_id)["layout"]
    rect = next(pane["rect"] for pane in layout["panes"] if pane["pane_id"] == own_pane_id)
    direction = "right" if rect["width"] >= 2 * MIN_COLUMN_WIDTH else "down"
else:
    direction = DIRECTIONS[args.direction]

taken = {agent.get("name") for agent in herdr("agent", "list")["agents"]}
name = next(f"impl{n}" for n in range(1, 1000) if f"impl{n}" not in taken)

cwd = herdr("pane", "get", own_pane_id)["pane"].get("foreground_cwd") or os.getcwd()
new_pane_id = herdr("pane", "split", "--pane", own_pane_id, "--direction", direction, "--cwd", cwd, "--no-focus")[
    "pane"
]["pane_id"]
claude_args = [*(["--model", args.model] if args.model else []), *(["--effort", args.effort] if args.effort else [])]
herdr(
    "agent", "start", name, "--kind", "claude", "--pane", new_pane_id, "--timeout", "60000",
    *(["--", *claude_args] if claude_args else []),
)
herdr("agent", "prompt", name, prompt)

settings = " ".join(claude_args) or "default model and effort"
print(f"Started Claude agent '{name}' in pane {new_pane_id} (split {direction}, cwd {cwd}, {settings}).")
