from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field

class MemoryConfig(BaseModel):
    """Configuration for Friday's memory subsystem."""
    enabled: bool = True
    provider: str = "mem0"
    storage_path: Path = Field(default_factory=lambda: Path(os.path.expanduser("~/.friday/memories")))
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    max_memories: int = 100
    prefetch_limit: int = 10
    ranking_limit: int = 5
    logging_enabled: bool = True
    mem0_api_key: str = ""

    @classmethod
    def from_env(cls) -> MemoryConfig:
        """Loads configuration from environment variables."""
        return cls(
            enabled=os.getenv("MEMORY_ENABLED", "true").lower() == "true",
            provider=os.getenv("MEMORY_PROVIDER", "mem0").lower(),
            storage_path=Path(os.getenv("MEMORY_STORAGE_PATH", os.path.expanduser("~/.friday/memories"))),
            cache_enabled=os.getenv("MEMORY_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("MEMORY_CACHE_TTL", "300")),
            max_memories=int(os.getenv("MEMORY_MAX_MEMORIES", "100")),
            prefetch_limit=int(os.getenv("MEMORY_PREFETCH_LIMIT", "10")),
            ranking_limit=int(os.getenv("MEMORY_RANKING_LIMIT", "5")),
            logging_enabled=os.getenv("MEMORY_LOGGING_ENABLED", "true").lower() == "true",
            mem0_api_key=os.getenv("MEM0_API_KEY", ""),
        )
