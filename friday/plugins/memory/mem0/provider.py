from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from friday.memory.models import MemoryEntry
from friday.memory.provider import MemoryProvider

logger = logging.getLogger("friday-agent")

class Mem0MemoryProvider(MemoryProvider):
    """External Memory Provider integrating with Mem0 Platform / SDK."""

    def __init__(self) -> None:
        import os
        self._name = "mem0"
        self._client: Optional[Any] = None
        self._api_key: str = os.getenv("MEM0_API_KEY", "")
        self._user_id: str = "friday-user"

    @property
    def name(self) -> str:
        return self._name

    def initialize(self, session_id: str, **kwargs) -> None:
        import os
        self._api_key = kwargs.get("mem0_api_key") or os.getenv("MEM0_API_KEY") or ""
        self._user_id = kwargs.get("user_id") or "friday-user"

        if not self._api_key:
            logger.warning("[Mem0] API key is missing. Mem0 provider will operate in offline/mock mode.")
            return

        try:
            from mem0 import MemoryClient
            self._client = MemoryClient(api_key=self._api_key)
            logger.info("[Memory] Initialized provider: mem0")
        except ImportError:
            logger.error("[Mem0] mem0ai package not found. Run 'pip install mem0ai'")

    def prefetch(self, query: str) -> List[MemoryEntry]:
        if not self._client:
            return []

        logger.info(f"[Memory] Prefetch started for query: '{query}'")
        try:
            # Query Mem0 Cloud
            response = self._client.search(
                query=query,
                filters={"user_id": self._user_id},
                limit=5
            )
            
            results = []
            if isinstance(response, dict):
                results = response.get("results", [])
            elif isinstance(response, list):
                results = response

            entries = []
            for r in results:
                memory_text = r.get("memory") or r.get("content")
                if memory_text:
                    entries.append(
                        MemoryEntry(
                            content=memory_text,
                            category="mem0_preference",
                            metadata={"mem0_id": r.get("id")}
                        )
                    )
            logger.info(f"[Memory] Mem0 memories: {len(entries)}")
            return entries
        except Exception as exc:
            logger.error(f"[Mem0] Search query failed: {exc}", exc_info=True)
            return []

    def sync_turn(self, user_msg: str, assistant_msg: str, extracted: List[MemoryEntry]) -> None:
        if not self._client:
            return

        # Write each extracted memory to Mem0
        logger.info(f"[Memory] Writing Mem0 with {len(extracted)} facts")
        for entry in extracted:
            payload = {"content": entry.content, "user_id": self._user_id}
            logger.info(f"[Memory] Calling Mem0.add() with payload: {payload}")
            try:
                res = self._client.add(
                    entry.content,
                    user_id=self._user_id
                )
                logger.info(f"[Memory] Mem0 response: {res}")
            except Exception as exc:
                logger.error(f"[Mem0] Failed to write memory: {exc}", exc_info=True)
                raise exc

    def shutdown(self) -> None:
        logger.info("[Memory] Mem0 provider shutdown completed.")

