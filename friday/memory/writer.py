from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from friday.memory.models import MemoryEntry
from friday.memory.storage import MemoryStore

logger = logging.getLogger("friday-agent")

class MemoryWriter(ABC):
    """Abstract interface for writing memory entries."""

    @abstractmethod
    def write(self, entry: MemoryEntry) -> None:
        """Write a new memory entry to persistent storage."""
        pass

class BuiltinMemoryWriter(MemoryWriter):
    """Builtin memory writer that saves entries to local USER.md and MEMORY.md."""

    def __init__(self, storage_path: Path, store: MemoryStore) -> None:
        self.storage_path = storage_path
        self.store = store
        self.user_md_path = storage_path / "USER.md"
        self.memory_md_path = storage_path / "MEMORY.md"

    def write(self, entry: MemoryEntry) -> None:
        # Route based on category
        is_user = entry.category.lower() in ("user_profile", "user", "personal")
        target_path = self.user_md_path if is_user else self.memory_md_path

        # Load existing first to check duplicate
        existing = self.store.load(target_path)
        
        # Verify if identical content exists
        norm_new = " ".join(entry.content.lower().split())
        for ext in existing:
            if " ".join(ext.content.lower().split()) == norm_new:
                logger.debug(f"[BuiltinWriter] Skip write: Duplicate found in {target_path.name}")
                return

        # Add and save
        existing.append(entry)
        self.store.save(target_path, existing)
        logger.info(f"[Memory] Stored 1 fact in built-in memory: {target_path.name}")
