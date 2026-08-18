import glob
import json
import os
from pathlib import Path

from .base import BaseExtractor, Turn


class ClaudeCodeExtractor(BaseExtractor):
    """Extracts transcript turns from Claude Code's JSONL session files."""

    def detect_session_id(self) -> str | None:
        # Primary: env var injected by Claude Code
        sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
        if sid:
            return sid

        # Fallback: read from .claude/GOAL.md if goal-set stored it there
        goal_path = Path(".claude/GOAL.md")
        if goal_path.exists():
            for line in goal_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("session_id:"):
                    value = line.split(":", 1)[1].strip().strip('"')
                    if value:
                        return value

        return None

    def _project_dir(self) -> Path:
        cwd = os.getcwd()
        key = cwd.replace("/", "-")  # leading dash intentionally kept
        return Path.home() / ".claude" / "projects" / key

    def get_recent_turns(self, session_id: str | None, n: int = 20) -> list[Turn]:
        project_dir = self._project_dir()

        if session_id:
            candidates = [project_dir / f"{session_id}.jsonl"]
        else:
            candidates = sorted(
                project_dir.glob("*.jsonl"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

        jsonl_path = next((p for p in candidates if p.exists()), None)
        if jsonl_path is None:
            raise FileNotFoundError(
                f"No JSONL transcript found in {project_dir} "
                f"(session_id={session_id!r})"
            )

        turns: list[Turn] = []
        with jsonl_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("isSidechain"):
                    continue

                kind = entry.get("type")
                ts = entry.get("timestamp", "")

                if kind == "user":
                    text = self._extract_user_text(entry)
                    if text:
                        turns.append(Turn(role="user", text=text, timestamp=ts))

                elif kind == "assistant":
                    text = self._extract_assistant_text(entry)
                    if text:
                        turns.append(Turn(role="assistant", text=text, timestamp=ts))

        return turns[-n:]

    def _extract_user_text(self, entry: dict) -> str:
        content = entry.get("message", {}).get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            # Skip turns that are purely tool results (intermediate plumbing)
            non_tool = [b for b in content if b.get("type") != "tool_result"]
            if not non_tool:
                return ""
            return " ".join(
                b.get("text", "") for b in non_tool if b.get("type") == "text"
            ).strip()
        return ""

    def _extract_assistant_text(self, entry: dict) -> str:
        content = entry.get("message", {}).get("content", [])
        if not isinstance(content, list):
            return ""
        # Only text blocks; skip thinking blocks
        return " ".join(
            b.get("text", "") for b in content if b.get("type") == "text"
        ).strip()
