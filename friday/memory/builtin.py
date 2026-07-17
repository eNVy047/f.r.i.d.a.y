from __future__ import annotations

import logging
from typing import List
from pathlib import Path
from friday.memory.models import MemoryEntry
from friday.memory.provider import MemoryProvider
from friday.memory.storage import MarkdownStore
from friday.memory.retriever import BuiltinMemoryRetriever
from friday.memory.writer import BuiltinMemoryWriter

logger = logging.getLogger("friday-agent")

class BuiltinMemory(MemoryProvider):
    """Local, file-backed memory provider (USER.md / MEMORY.md)."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self._name = "builtin"
        self.store = MarkdownStore()
        self.retriever = BuiltinMemoryRetriever(self.storage_path, self.store)
        self.writer = BuiltinMemoryWriter(self.storage_path, self.store)

    @property
    def name(self) -> str:
        return self._name

    def initialize(self, session_id: str, **kwargs) -> None:
        # Create directories if needed
        self.storage_path.mkdir(parents=True, exist_ok=True)
        # Touch files to ensure they exist
        (self.storage_path / "USER.md").touch(exist_ok=True)
        (self.storage_path / "MEMORY.md").touch(exist_ok=True)
        logger.info("[Memory] Loaded built-in memory files successfully.")

    def prefetch(self, query: str) -> List[MemoryEntry]:
        return self.retriever.retrieve(query)

    def sync_turn(self, user_msg: str, assistant_msg: str, extracted: List[MemoryEntry]) -> None:
        for entry in extracted:
            self.writer.write(entry)

    def shutdown(self) -> None:
        logger.info("[Memory] Built-in memory provider shutdown completed.")
