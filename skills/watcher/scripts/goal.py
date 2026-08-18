#!/usr/bin/env python3
"""
CLI: read or write .claude/GOAL.md for the current project.

Usage:
    python3 goal.py read
    python3 goal.py write --statement "..." [--mode MODE] [--scope "a,b"] [--non-goals "x,y"] [--session-id ID] [--reason TEXT]

Exit codes:
    0  success
    1  error
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


GOAL_PATH = Path(".claude/GOAL.md")
VALID_MODES = ("brainstorm", "implement", "debug", "analyze", "review")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_goal() -> dict | None:
    if not GOAL_PATH.exists():
        return None

    text = GOAL_PATH.read_text()
    current: dict = {}
    history_raw: list[str] = []
    in_current = False
    in_history = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "current:":
            in_current = True
            in_history = False
            continue
        if stripped == "history:":
            in_current = False
            in_history = True
            continue
        if in_current and stripped:
            if stripped.startswith("#"):
                continue
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                v = v.strip().strip('"')
                if v.startswith("[") and v.endswith("]"):
                    v = [i.strip().strip('"') for i in v[1:-1].split(",") if i.strip()]
                current[k.strip()] = v
        if in_history:
            history_raw.append(line)

    return {"current": current, "history_raw": "\n".join(history_raw)}


def write_goal(
    statement: str,
    mode: str,
    scope: list[str],
    non_goals: list[str],
    session_id: str | None,
    reason: str,
) -> None:
    existing = read_goal()
    history_block = "history: []"

    if existing and existing["current"].get("statement"):
        prev = existing["current"]
        prev_entry = f"""  - v{_next_version(existing['history_raw'])}:
      statement: "{prev.get('statement', '')}"
      mode: {prev.get('mode', 'implement')}
      authorized_by: {prev.get('authorized_by', 'user')}
      session_id: "{prev.get('session_id', '')}"
      reason: "{reason}"
      updated_at: "{prev.get('updated_at', '')}"
"""
        raw = existing["history_raw"].strip()
        if raw == "history: []" or not raw:
            history_block = f"history:\n{prev_entry}"
        else:
            # Strip the "history:" header from raw and append new entry
            lines = raw.splitlines()
            header = lines[0] if lines else "history:"
            rest = "\n".join(lines[1:])
            history_block = f"{header}\n{rest}\n{prev_entry}"

    scope_yaml = (
        "[" + ", ".join(f'"{s}"' for s in scope) + "]" if scope else "[]"
    )
    non_goals_yaml = (
        "[" + ", ".join(f'"{s}"' for s in non_goals) + "]" if non_goals else "[]"
    )
    session_line = f'  session_id: "{session_id}"' if session_id else '  session_id: ""'

    content = f"""current:
  statement: "{statement}"
  mode: {mode}
  scope: {scope_yaml}
  non_goals: {non_goals_yaml}
  authorized_by: user
{session_line}
  updated_at: "{now_iso()}"

{history_block}
"""
    GOAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOAL_PATH.write_text(content)


def _next_version(history_raw: str) -> int:
    import re
    versions = re.findall(r"- v(\d+):", history_raw)
    return (max(int(v) for v in versions) + 1) if versions else 1


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("read")

    w = sub.add_parser("write")
    w.add_argument("--statement", required=True)
    w.add_argument("--mode", default="implement", choices=VALID_MODES)
    w.add_argument("--scope", default="")
    w.add_argument("--non-goals", dest="non_goals", default="")
    w.add_argument("--session-id", dest="session_id", default=None)
    w.add_argument("--reason", default="updated by user")

    args = parser.parse_args()

    if args.cmd == "read":
        goal = read_goal()
        if goal is None:
            print("NO_GOAL")
            sys.exit(1)
        c = goal["current"]
        print(f"statement: {c.get('statement', '')}")
        print(f"mode: {c.get('mode', 'implement')}")
        print(f"scope: {c.get('scope', [])}")
        print(f"non_goals: {c.get('non_goals', [])}")
        print(f"session_id: {c.get('session_id', '')}")

    elif args.cmd == "write":
        scope = [s.strip() for s in args.scope.split(",") if s.strip()]
        non_goals = [s.strip() for s in args.non_goals.split(",") if s.strip()]
        session_id = args.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
        write_goal(
            statement=args.statement,
            mode=args.mode,
            scope=scope,
            non_goals=non_goals,
            session_id=session_id,
            reason=args.reason,
        )
        print(f"Goal set: \"{args.statement}\"")
        print(f"Mode: {args.mode} | Scope: {scope or 'any'} | Non-goals: {non_goals or 'none'}")
        print(f"Saved to {GOAL_PATH}")


if __name__ == "__main__":
    main()
