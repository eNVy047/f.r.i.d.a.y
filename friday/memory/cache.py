from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Tuple
from friday.memory.models import MemoryEntry

logger = logging.getLogger("friday-agent")

class MemoryCache:
    """A lightweight in-memory cache with TTL expiration."""

    def __init__(self, enabled: bool = True, ttl: int = 300) -> None:
        self.enabled = enabled
        self.ttl = ttl
        self._cache: Dict[str, Tuple[float, List[MemoryEntry]]] = {}

    def get(self, key: str) -> Optional[List[MemoryEntry]]:
        """Get cached entries for a key if cache is enabled and not expired."""
        if not self.enabled:
            return None

        normalized_key = key.strip().lower()
        if normalized_key not in self._cache:
            return None

        timestamp, entries = self._cache[normalized_key]
        if time.time() - timestamp > self.ttl:
            # Expired
            logger.debug(f"[MemoryCache] Cache expired for key: {normalized_key}")
            del self._cache[normalized_key]
            return None

        logger.debug(f"[MemoryCache] Cache HIT for key: {normalized_key}")
        return entries

    def set(self, key: str, entries: List[MemoryEntry]) -> None:
        """Cache list of entries for a key."""
        if not self.enabled:
            return

        normalized_key = key.strip().lower()
        self._cache[normalized_key] = (time.time(), entries)
        logger.debug(f"[MemoryCache] Cached entries for key: {normalized_key}")

    def invalidate(self, key: str) -> None:
        """Invalidate a specific key."""
        normalized_key = key.strip().lower()
        if normalized_key in self._cache:
            del self._cache[normalized_key]
            logger.debug(f"[MemoryCache] Cache invalidated for key: {normalized_key}")

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        logger.info("[MemoryCache] Cache cleared.")
