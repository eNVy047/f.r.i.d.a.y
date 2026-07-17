from __future__ import annotations

import os
import sys
import shutil
import tempfile
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Mock mem0 before any other imports to prevent network calls in constructor validation
sys.modules['mem0'] = MagicMock()

from friday.memory.models import MemoryEntry, MemoryContext
from friday.memory.config import MemoryConfig
from friday.memory.provider import MemoryProvider
from friday.memory.registry import ProviderRegistry
from friday.memory.ranker import DefaultRanker
from friday.memory.policy import DefaultMemoryPolicy
from friday.memory.cache import MemoryCache
from friday.memory.extractor import RuleBasedExtractor, LLMMemoryExtractor
from friday.memory.storage import MarkdownStore
from friday.memory.builtin import BuiltinMemory
from friday.memory.manager import MemoryManager
from friday.plugins.memory.mem0.provider import Mem0MemoryProvider

@pytest.fixture
def temp_storage():
    """Create a temporary directory for flat file persistence."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

# ===========================================================================
# 1. Models & Config Tests
# ===========================================================================

def test_models():
    entry = MemoryEntry(content="User prefers python", category="preference")
    assert entry.content == "User prefers python"
    assert entry.category == "preference"

def test_config():
    config = MemoryConfig(enabled=True, provider="mem0")
    assert config.enabled is True
    assert config.provider == "mem0"

# ===========================================================================
# 2. Registry Tests
# ===========================================================================

def test_registry():
    registry = ProviderRegistry()
    registry.register("mem0", Mem0MemoryProvider)
    
    cls = registry.get("mem0")
    assert cls == Mem0MemoryProvider
    
    assert registry.get("non_existent") is None

# ===========================================================================
# 3. Cache Tests
# ===========================================================================

def test_cache():
    cache = MemoryCache(enabled=True, ttl=10)
    entries = [MemoryEntry(content="Cache entry 1", category="test")]
    
    cache.set("query_key", entries)
    cached = cache.get("query_key")
    assert len(cached) == 1
    assert cached[0].content == "Cache entry 1"

    # Test cache invalidation
    cache.invalidate("query_key")
    assert cache.get("query_key") is None

# ===========================================================================
# 4. Ranker Tests
# ===========================================================================

def test_ranker():
    ranker = DefaultRanker()
    entries = [
        MemoryEntry(content="User likes FastAPI framework", category="coding"),
        MemoryEntry(content="Stark makes Iron Man suits", category="general"),
        MemoryEntry(content="Stark likes cheeseburgers", category="food"),
    ]
    
    # Query: "Stark cheeseburgers"
    ranked = ranker.rank(entries, "Stark cheeseburgers", limit=2)
    assert len(ranked) == 2
    # "Stark likes cheeseburgers" should be first because it matches both tokens
    assert "cheeseburgers" in ranked[0].content

# ===========================================================================
# 5. Policy Tests
# ===========================================================================

def test_policy():
    policy = DefaultMemoryPolicy(max_memories=2)
    existing = [
        MemoryEntry(content="Already exists", category="general"),
    ]
    
    # 1. Test standard entry
    new_entry = MemoryEntry(content="New entry is fine", category="general")
    assert policy.evaluate(new_entry, existing) is True

    # 2. Test duplicate entry
    duplicate_entry = MemoryEntry(content="Already exists", category="general")
    assert policy.evaluate(duplicate_entry, existing) is False

    # 3. Test max limits
    existing.append(new_entry)
    third_entry = MemoryEntry(content="Third entry", category="general")
    assert policy.evaluate(third_entry, existing) is False

# ===========================================================================
# 6. Extractor Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_rule_based_extractor():
    extractor = RuleBasedExtractor()
    entries = await extractor.extract("My name is Narayan and I like coding in python.", "Nice to meet you.")
    
    assert len(entries) >= 1
    assert any("Narayan" in e.content for e in entries)

@pytest.mark.asyncio
async def test_llm_extractor():
    async def mock_llm(prompt):
        return '["User prefers Python over Java", "User is Stark"]'
        
    extractor = LLMMemoryExtractor(llm_executor=mock_llm)
    entries = await extractor.extract("What language do you prefer?", "I prefer Python over Java.")
    
    assert len(entries) == 2
    assert entries[0].content == "User prefers Python over Java"

# ===========================================================================
# 7. Built-in Persistence Tests
# ===========================================================================

def test_builtin_memory_persistence(temp_storage):
    builtin = BuiltinMemory(storage_path=temp_storage)
    builtin.initialize(session_id="test_session")
    
    fact = MemoryEntry(content="Narayan prefers Stark Industry", category="general")
    builtin.sync_turn("query", "reply", [fact])
    
    # Verify loaded
    loaded = builtin.prefetch("Narayan")
    assert len(loaded) == 1
    assert loaded[0].content == "Narayan prefers Stark Industry"

# ===========================================================================
# 8. Mem0 Provider Tests (Mocked Client)
# ===========================================================================

def test_mem0_mocked_provider():
    provider = Mem0MemoryProvider()
    
    provider.initialize(session_id="session_123", mem0_api_key="fake_key", user_id="narayan")
    
    # Inject mocked client directly after initialize to prevent overwrite
    provider._client = MagicMock()
    provider._client.search.return_value = [
        {"memory": "Narayan has a cat named Stark", "id": "mem_01"}
    ]
    
    fetched = provider.prefetch("cat name")
    assert len(fetched) == 1
    assert fetched[0].content == "Narayan has a cat named Stark"
    
    # Mock add method
    provider.sync_turn("query", "reply", [MemoryEntry(content="Narayan works as developer", category="personal")])
    provider._client.add.assert_called_once_with("Narayan works as developer", user_id="narayan")

# ===========================================================================
# 9. MemoryManager E2E Orchestration Test
# ===========================================================================

@pytest.mark.asyncio
async def test_memory_manager_orchestration(temp_storage):
    config = MemoryConfig(enabled=True, provider="builtin", storage_path=temp_storage)
    registry = ProviderRegistry()
    builtin = BuiltinMemory(storage_path=temp_storage)
    ranker = DefaultRanker()
    
    async def mock_llm_extractor(prompt):
        return '["User prefers Python over Java"]'
    extractor = LLMMemoryExtractor(llm_executor=mock_llm_extractor)
    
    policy = DefaultMemoryPolicy(max_memories=10)
    cache = MemoryCache(enabled=True, ttl=10)
    
    manager = MemoryManager(
        config=config,
        registry=registry,
        builtin=builtin,
        ranker=ranker,
        extractor=extractor,
        policy=policy,
        cache=cache
    )
    
    manager.initialize(session_id="test_session")
    
    # E2E Sync Turn
    await manager.sync_turn("I really prefer Python over Java", "Understood.")
    
    # E2E Prefetch
    context = manager.prefetch("Python")
    assert context.formatted != ""
    assert "User prefers Python over Java" in context.formatted
    
    manager.shutdown()
