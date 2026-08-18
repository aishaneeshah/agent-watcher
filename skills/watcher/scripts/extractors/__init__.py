from .base import BaseExtractor, Turn
from .claude_code import ClaudeCodeExtractor
from .codex import CodexExtractor

REGISTRY: dict[str, type[BaseExtractor]] = {
    "claude-code": ClaudeCodeExtractor,
    "codex": CodexExtractor,
}


def auto_detect() -> BaseExtractor:
    """Return the right extractor based on environment signals.

    Strong signals (env vars set by the running harness) are checked before
    weak ones (a config directory merely existing on disk), since a dev
    machine commonly has both ~/.claude and ~/.codex regardless of which
    harness is currently running.
    """
    import os
    from pathlib import Path

    if os.environ.get("CLAUDE_CODE_SESSION_ID"):
        return ClaudeCodeExtractor()

    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    if codex_home.exists():
        return CodexExtractor()

    if (Path.home() / ".claude").exists():
        return ClaudeCodeExtractor()

    raise RuntimeError(
        "Could not auto-detect harness. Set WATCHER_HARNESS=claude-code|codex "
        "or implement a new extractor in scripts/extractors/."
    )


def get(harness: str) -> BaseExtractor:
    if harness not in REGISTRY:
        raise ValueError(f"Unknown harness '{harness}'. Available: {list(REGISTRY)}")
    return REGISTRY[harness]()
