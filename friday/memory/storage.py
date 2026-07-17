from __future__ import annotations

import os
import tempfile
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from friday.memory.models import MemoryEntry

logger = logging.getLogger("friday-agent")

ENTRY_DELIMITER = "\n§\n"

class MemoryStore(ABC):
    """Abstract interface for memory persistence storage."""

    @abstractmethod
    def load(self, target_path: Path) -> List[MemoryEntry]:
        """Load list of memory entries from the target path."""
        pass

    @abstractmethod
    def save(self, target_path: Path, entries: List[MemoryEntry]) -> None:
        """Atomically save memory entries to the target path."""
        pass

class MarkdownStore(MemoryStore):
    """Concrete MemoryStore implementing markdown file parsing and saving with § delimiter."""

    def load(self, target_path: Path) -> List[MemoryEntry]:
        if not target_path.exists():
            return []

        try:
            content = target_path.read_text(encoding="utf-8")
            
            # Strip header if present
            if content.startswith("#"):
                lines = content.splitlines()
                if lines:
                    content = "\n".join(lines[1:])

            # Split by section sign delimiter
            raw_entries = content.split(ENTRY_DELIMITER)
            
            entries = []
            category = "user_profile" if target_path.name.lower() == "user.md" else "general"
            
            for raw in raw_entries:
                cleaned = raw.strip()
                # Skip markdown header comments or titles
                if not cleaned or cleaned.startswith("#"):
                    continue
                # Strip leading dash/bullet if any
                cleaned = cleaned.lstrip("- ").strip()
                if cleaned:
                    entries.append(MemoryEntry(content=cleaned, category=category))
            
            return entries
        except Exception as exc:
            logger.error(f"[MarkdownStore] Failed to load {target_path}: {exc}")
            return []

    def save(self, target_path: Path, entries: List[MemoryEntry]) -> None:
        try:
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            lines = []
            # Add header title
            filename = target_path.name
            lines.append(f"# Friday Stark Memory - {filename}\n")
            
            # Format each entry with a bullet point
            formatted_entries = []
            for entry in entries:
                formatted_entries.append(f"- {entry.content}")
            
            file_content = lines[0] + ENTRY_DELIMITER.join(formatted_entries)
            
            # Atomic replacement to avoid corruption
            temp_fd, temp_path = tempfile.mkstemp(
                dir=str(target_path.parent),
                prefix=f".{filename}-tmp-",
                text=True
            )
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                os.replace(temp_path, str(target_path))
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        except Exception as exc:
            logger.error(f"[MarkdownStore] Failed to save {target_path}: {exc}")
