from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Turn:
    role: str   # "user" | "assistant"
    text: str
    timestamp: str


class BaseExtractor(ABC):
    """Implement this to add support for a new harness."""

    @abstractmethod
    def detect_session_id(self) -> str | None:
        """Return the current session ID, or None if not detectable."""
        ...

    @abstractmethod
    def get_recent_turns(self, session_id: str | None, n: int = 20) -> list[Turn]:
        """Return the last n user/assistant turns for the given session."""
        ...
