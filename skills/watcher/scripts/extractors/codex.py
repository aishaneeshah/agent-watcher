import json
import os
from pathlib import Path

from .base import BaseExtractor, Turn


class CodexExtractor(BaseExtractor):
    """Extracts transcript turns from Codex CLI's rollout JSONL session files."""

    def _sessions_dir(self) -> Path:
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        return codex_home / "sessions"

    def detect_session_id(self) -> str | None:
        # Codex sandboxes subprocesses by default and doesn't expose a
        # documented session-id env var, so there's nothing reliable to read
        # here. get_recent_turns() falls back to the most recently modified
        # rollout file when session_id is None.
        return None

    def _find_rollout_file(self, session_id: str | None) -> Path | None:
        sessions_dir = self._sessions_dir()
        if not sessions_dir.exists():
            return None

        if session_id:
            matches = list(sessions_dir.glob(f"*/*/*/rollout-*{session_id}*.jsonl"))
            return matches[0] if matches else None

        candidates = sorted(
            sessions_dir.glob("*/*/*/rollout-*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None

    def get_recent_turns(self, session_id: str | None, n: int = 20) -> list[Turn]:
        jsonl_path = self._find_rollout_file(session_id)
        if jsonl_path is None:
            raise FileNotFoundError(
                f"No rollout JSONL transcript found under {self._sessions_dir()} "
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

                message = self._as_message(entry)
                if message is None:
                    continue

                role = message.get("role")
                if role not in ("user", "assistant"):
                    continue

                text = self._extract_text(message.get("content", ""))
                if text:
                    turns.append(
                        Turn(role=role, text=text, timestamp=entry.get("timestamp", ""))
                    )

        return turns[-n:]

    def _as_message(self, entry: dict) -> dict | None:
        """Normalize current (response_item-wrapped) and legacy rollout
        formats to a plain {"role": ..., "content": ...} message dict."""
        kind = entry.get("type")

        if kind == "response_item":
            payload = entry.get("payload", {})
            return payload if payload.get("type") == "message" else None

        if kind == "message":
            return entry

        return None

    def _extract_text(self, content) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = [
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") in ("text", "input_text", "output_text")
            ]
            return " ".join(t for t in texts if t).strip()
        return ""
