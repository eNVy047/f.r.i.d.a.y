from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MemoryEntry(BaseModel):
    """Represents a single atomic long-term fact or memory entry."""
    id: Optional[str] = None
    content: str
    category: str = "general"
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievedMemory(BaseModel):
    """A memory entry retrieved from a provider with relevance score."""
    entry: MemoryEntry
    score: float = 1.0

class MemoryContext(BaseModel):
    """Bundled memory context retrieved during prefetch."""
    retrieved: List[RetrievedMemory] = Field(default_factory=list)
    formatted: str = ""
