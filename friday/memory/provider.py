from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from friday.memory.models import MemoryEntry

class MemoryProvider(ABC):
    """Abstract Base Class for memory providers (both built-in and external)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g. 'builtin', 'mem0')."""
        pass

    @abstractmethod
    def initialize(self, session_id: str, **kwargs) -> None:
        """Initialize the provider (e.g., connect, prepare storage, load caches)."""
        pass

    @abstractmethod
    def prefetch(self, query: str) -> List[MemoryEntry]:
        """Retrieve relevant memories matching the query."""
        pass

    @abstractmethod
    def sync_turn(self, user_msg: str, assistant_msg: str, extracted: List[MemoryEntry]) -> None:
        """Store/update memory entries after a conversation turn."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Perform cleanup and safe shutdown."""
        pass
