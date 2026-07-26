---
name: goal-set
description: Initializes or updates .claude/GOAL.md for the current session. Run at the start of any task to give the watcher an anchor, or after a legitimate goal pivot. Usage: /goal-set "your goal here" --mode brainstorm|implement|debug|analyze|review --scope "a,b,c" --non-goals "x,y,z"
version: 1.0.0
argument-hint: '"Goal statement" [--mode brainstorm|implement|debug|analyze|review] [--scope "a,b,c"] [--non-goals "x,y,z"]'
allowed-tools: Bash, Read, Write
---

# Goal Set

Parse the user's arguments and write or update `.claude/GOAL.md`.

## Step 1 — Parse arguments

The user invoked this with: `$ARGUMENTS`

Parse as follows:
- **Statement**: everything before the first `--` flag (strip surrounding quotes). If empty, ask for it before continuing.
- **`--mode`**: one of `brainstorm`, `implement`, `debug`, `analyze`, `review`. Default: `implement`.
- **`--scope`**: comma-separated list. Default: empty.
- **`--non-goals`**: comma-separated list. Default: empty.

## Step 2 — Locate scripts

```bash
WATCHER_SCRIPTS="${WATCHER_SCRIPTS_DIR:-$HOME/.claude/skills/watcher/scripts}"
echo $WATCHER_SCRIPTS
```

## Step 3 — Write the goal

```bash
python3 "$WATCHER_SCRIPTS/goal.py" write \
  --statement "PARSED_STATEMENT" \
  --mode PARSED_MODE \
  --scope "PARSED_SCOPE" \
  --non-goals "PARSED_NON_GOALS" \
  --session-id "$CLAUDE_CODE_SESSION_ID"
```

The script handles creating `.claude/` if needed, appending the previous goal to history, and writing the new `current:` block.

## Step 4 — Confirm

Output whatever the script printed. Do not add anything else.
