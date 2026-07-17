from __future__ import annotations

import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Any
from friday.memory.models import MemoryEntry

logger = logging.getLogger("friday-agent")

class MemoryExtractor(ABC):
    """Interface for extracting useful long-term facts from a conversation turn."""

    @abstractmethod
    async def extract(self, user_msg: str, assistant_msg: str) -> List[MemoryEntry]:
        """Extract a list of new facts/preferences as MemoryEntries from the exchange."""
        pass

class RuleBasedExtractor(MemoryExtractor):
    """A fast, rule-based extractor using regular expressions for common patterns."""

    def __init__(self) -> None:
        # Common pattern matching: "my X is Y", "i like X", "i prefer X", etc.
        self.patterns = [
            (re.compile(r"\bmy\s+(\w+)\s+is\s+([^.]+)", re.IGNORECASE), "personal"),
            (re.compile(r"\bi\s+(like|prefer|love)\s+([^.]+)", re.IGNORECASE), "preference"),
            (re.compile(r"\bi\s+(work\s+at|am\s+a)\s+([^.]+)", re.IGNORECASE), "work"),
        ]

    async def extract(self, user_msg: str, assistant_msg: str) -> List[MemoryEntry]:
        entries = []
        for regex, category in self.patterns:
            for match in regex.finditer(user_msg):
                content = match.group(0).strip()
                # Clean up punctuation
                content = re.sub(r'[.!?]+$', '', content)
                entries.append(MemoryEntry(content=content, category=category))
        
        return entries

class LLMMemoryExtractor(MemoryExtractor):
    """An LLM-driven extractor that extracts facts and outputs structured MemoryEntries."""

    def __init__(self, llm_executor: Callable[[str], Any]) -> None:
        """
        llm_executor: An async callable that takes a prompt and returns the string response.
        We inject this to remain completely decoupled from specific LLM client classes.
        """
        self.llm_executor = llm_executor

    async def extract(self, user_msg: str, assistant_msg: str) -> List[MemoryEntry]:
        prompt = f"""
Analyze the following exchange between a User and an Assistant.
Identify any new, useful long-term facts, preferences, habits, or personal information about the User.
Ignore temporary conversation, greetings, small talk, questions, or assistant answers.

Exchange:
User: "{user_msg}"
Assistant: "{assistant_msg}"

Output ONLY a valid JSON list of strings, each string being a single atomic fact.
Example:
[
  "The user's birthday is July 4",
  "The user prefers FastAPI over Flask"
]

If no long-term information was shared, output an empty list: []
JSON Output:
"""
        try:
            response_text = await self.llm_executor(prompt)
            # Find the JSON array inside the response
            match = re.search(r'\[\s*.*?\s*\]', response_text, re.DOTALL)
            if not match:
                return []
            
            facts = json.loads(match.group(0))
            if not isinstance(facts, list):
                return []

            entries = []
            for fact in facts:
                if isinstance(fact, str) and len(fact.strip()) > 5:
                    # Categorize basic facts
                    category = "preference" if "prefer" in fact.lower() or "like" in fact.lower() else "personal"
                    entries.append(MemoryEntry(content=fact.strip(), category=category))
            return entries
        except Exception as exc:
            logger.error(f"[LLMMemoryExtractor] Failed to extract facts: {exc}")
            return []
