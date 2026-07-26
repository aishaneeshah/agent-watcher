from .base import BaseExtractor, Turn
from .claude_code import ClaudeCodeExtractor

REGISTRY: dict[str, type[BaseExtractor]] = {
    "claude-code": ClaudeCodeExtractor,
}


def auto_detect() -> BaseExtractor:
    """Return the right extractor based on environment signals."""
    import os
    from pathlib import Path

    if os.environ.get("CLAUDE_CODE_SESSION_ID") or (Path.home() / ".claude").exists():
        return ClaudeCodeExtractor()

    raise RuntimeError(
        "Could not auto-detect harness. Set WATCHER_HARNESS=claude-code "
        "or implement a new extractor in scripts/extractors/."
    )


def get(harness: str) -> BaseExtractor:
    if harness not in REGISTRY:
        raise ValueError(f"Unknown harness '{harness}'. Available: {list(REGISTRY)}")
    return REGISTRY[harness]()
