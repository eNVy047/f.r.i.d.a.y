from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List
from friday.memory.models import MemoryEntry

class MemoryRanker(ABC):
    """Interface for ranking and merging retrieved memory entries."""

    @abstractmethod
    def rank(self, entries: List[MemoryEntry], query: str, limit: int) -> List[MemoryEntry]:
        """Rank entries based on query relevance, remove duplicates, and limit output."""
        pass

class DefaultRanker(MemoryRanker):
    """A token-overlap based ranker that dedupes and scores relevance."""

    def rank(self, entries: List[MemoryEntry], query: str, limit: int) -> List[MemoryEntry]:
        if not entries:
            return []

        # Tokenize query for word overlap scoring
        query_words = set(re.findall(r'\w+', query.lower()))
        
        scored_entries = []
        seen_contents = set()
        
        for entry in entries:
            # Deduplicate by content normalized
            norm_content = " ".join(entry.content.lower().split())
            if norm_content in seen_contents:
                continue
            seen_contents.add(norm_content)

            # Score based on token overlap
            entry_words = set(re.findall(r'\w+', entry.content.lower()))
            overlap = query_words.intersection(entry_words)
            
            # Simple scoring: size of intersection. If query is empty, score is 1.0.
            score = len(overlap) / max(len(query_words), 1) if query_words else 1.0
            
            # Boost score if category matches query tokens
            if entry.category.lower() in query_words:
                score += 0.5
                
            scored_entries.append((entry, score))

        # Sort by score descending
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        return [entry for entry, score in scored_entries[:limit]]
