# agent-watcher

A pair of Claude Code skills — `watcher` and `goal-set` — that periodically check whether the coding agent has drifted from its stated goal, and intervene when it has.

## What it does

Run `/watcher` (or `/loop 5m /watcher`) and the watcher will:

1. Ensure a goal is set — if not, it asks you and sets it inline
2. Read `.claude/GOAL.md` — the live, versioned goal document
3. Extract the last 20 turns from the session transcript
4. Check four failure modes in order, stopping at the first match:
   - **Amendment** — user redirected the goal; watcher proposes a `/goal-set` update
   - **Mode violation** — mode is `brainstorm` but the agent is writing files
   - **Goal drift** — working outside declared scope or inside non-goals for 3+ turns
   - **Error loop** — same failed action repeated 5+ times
5. Emit a single tagged intervention, or stay completely silent

**Silence = the agent is on track.**

## Install

This repo holds two skills — `watcher` and `goal-set` — that install side by side. `goal.py` (goal read/write) lives under `watcher/scripts/` and is shared by both; `goal-set` references it by relative path, so the two must be installed together.

```bash
git clone https://github.com/aishaneeshah/agent-watcher ~/agent-watcher
ln -s ~/agent-watcher/skills/watcher ~/.claude/skills/watcher
ln -s ~/agent-watcher/skills/goal-set ~/.claude/skills/goal-set
```

Maintainers/contributors can instead run `scripts/link-skills.sh` from a checkout, which symlinks both skills into `~/.claude/skills` **and** `~/.agents/skills` (the shared path read by Codex, Cursor, and other Agent Skills-compatible harnesses) in one step.

The skills are picked up automatically once linked.

## Usage

Set the goal at the start of a session:

```
/goal-set "Implement the auth system" --mode implement --scope "auth,session" --non-goals "UI,database"
```

Start the watcher loop:

```
/loop 5m /watcher
```

Or check once manually:

```
/watcher
```

The watcher will ask you for a goal if none is set yet.

## Intervention tags

| Tag | Meaning |
|-----|---------|
| `[WATCHER:AMENDMENT]` | User redirected goal — proposes `/goal-set` update |
| `[WATCHER:MODE]` | Mode is `brainstorm` but code is being written |
| `[WATCHER]` | Goal drift — work outside declared scope/non-goals |
| `[WATCHER:LOOP]` | Same failure repeated 5+ times |
| `[WATCHER:ERROR]` | Could not read transcript |

## GOAL.md format

```yaml
current:
  statement: "Implement the auth system"
  mode: implement
  scope: ["auth", "session"]
  non_goals: ["UI", "database"]
  authorized_by: user
  session_id: "6d417bc0-..."
  updated_at: "2026-07-26T10:00:00+00:00"

history:
  - v1:
      statement: "Brainstorm auth approaches"
      mode: brainstorm
      authorized_by: user
      session_id: "..."
      reason: "updated by user"
      updated_at: "2026-07-26T09:00:00+00:00"
```

## Supported harnesses

| Harness | Transcript extraction | Notes |
|---------|------------------------|-------|
| Claude Code | `extractors/claude_code.py` | Reads `~/.claude/projects/*/*.jsonl`. Session id from `$CLAUDE_CODE_SESSION_ID`. |
| Codex CLI | `extractors/codex.py` | Reads `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl` (default `~/.codex`). Codex exposes no session-id env var, so it falls back to the most recently modified rollout file. |

`WATCHER_HARNESS` forces a specific extractor (`claude-code` or `codex`); otherwise `auto_detect()` picks one from environment signals, preferring the running harness's own env var over a config directory merely existing on disk.

## Adding support for another harness

Two independent things travel per harness:

- **Transcript extraction** — implement `BaseExtractor` in `skills/watcher/scripts/extractors/your_harness.py`, register it in `skills/watcher/scripts/extractors/__init__.py`, and set `WATCHER_HARNESS=your-harness` in your environment.
- **Skill metadata** — each skill's `agents/openai.yaml` sidecar (next to its `SKILL.md`) carries UI metadata for Codex-style harnesses (`display_name`, `short_description`). The instructions in `SKILL.md` itself are never duplicated per harness — only this thin sidecar varies.

## Rules

The watcher never:
- Implements, fixes, or adds anything to the codebase
- Summarizes what it read
- Emits more than one intervention type per run
- Triggers on a single misaligned turn (requires 3+ for drift, 5+ for loops)
