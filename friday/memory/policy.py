from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List
from friday.memory.models import MemoryEntry

logger = logging.getLogger("friday-agent")

class MemoryPolicy(ABC):
    """Interface for evaluating if a memory should be persisted, updated, or skipped."""

    @abstractmethod
    def evaluate(self, entry: MemoryEntry, existing_entries: List[MemoryEntry]) -> bool:
        """Evaluate the entry against existing memories. Returns True if it should be saved."""
        pass

class DefaultMemoryPolicy(MemoryPolicy):
    """Enforces duplicate detection, limits, and simple updates."""

    def __init__(self, max_memories: int = 100) -> None:
        self.max_memories = max_memories

    def evaluate(self, entry: MemoryEntry, existing_entries: List[MemoryEntry]) -> bool:
        # 1. Clean content check
        content = entry.content.strip()
        if not content or len(content) < 5:
            logger.debug("[MemoryPolicy] Rejected: entry too short or empty.")
            return False

        # 2. Limit check
        if len(existing_entries) >= self.max_memories:
            logger.warning(f"[MemoryPolicy] Max memory count ({self.max_memories}) reached. Skipping.")
            return False

        # 3. Duplicate check (normalization comparison)
        norm_new = " ".join(content.lower().split())
        for existing in existing_entries:
            norm_ext = " ".join(existing.content.lower().split())
            if norm_new == norm_ext:
                logger.info(f"[MemoryPolicy] Rejected: duplicate of existing memory: {existing.content}")
                return False

        return True
