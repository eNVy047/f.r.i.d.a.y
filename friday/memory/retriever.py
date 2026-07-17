from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from friday.memory.models import MemoryEntry
from friday.memory.storage import MemoryStore

logger = logging.getLogger("friday-agent")

class MemoryRetriever(ABC):
    """Abstract interface for retrieving memory entries."""

    @abstractmethod
    def retrieve(self, query: str) -> List[MemoryEntry]:
        """Retrieve memories matching the query."""
        pass

class BuiltinMemoryRetriever(MemoryRetriever):
    """Builtin memory retriever that loads from local USER.md and MEMORY.md."""

    def __init__(self, storage_path: Path, store: MemoryStore) -> None:
        self.storage_path = storage_path
        self.store = store
        self.user_md_path = storage_path / "USER.md"
        self.memory_md_path = storage_path / "MEMORY.md"

    def retrieve(self, query: str) -> List[MemoryEntry]:
        # Load all entries
        user_entries = self.store.load(self.user_md_path)
        mem_entries = self.store.load(self.memory_md_path)
        all_entries = user_entries + mem_entries

        if not query or not query.strip():
            return all_entries

        # Filter entries loosely containing query words
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        if not query_words:
            return all_entries

        filtered = []
        for entry in all_entries:
            content_lower = entry.content.lower()
            if any(word in content_lower for word in query_words):
                filtered.append(entry)

        logger.debug(f"[BuiltinRetriever] Retrieved {len(filtered)} / {len(all_entries)} local memories.")
        return filtered
