from __future__ import annotations

import logging
from typing import Dict, Type, Optional
from friday.memory.provider import MemoryProvider

logger = logging.getLogger("friday-agent")

class ProviderRegistry:
    """Programmatic registry for memory providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, Type[MemoryProvider]] = {}

    def register(self, name: str, provider_cls: Type[MemoryProvider]) -> None:
        """Register a memory provider class."""
        self._providers[name.lower()] = provider_cls
        logger.info(f"[Memory] Registered provider class for: {name.lower()}")

    def get(self, name: str) -> Optional[Type[MemoryProvider]]:
        """Retrieve a memory provider class by name."""
        return self._providers.get(name.lower())
