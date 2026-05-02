"""Tests for common/mesh/session.py – distributed cache."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import time

from common.mesh.session import CacheEntry, DistributedCache, cache_key


class TestDistributedCache:
    def test_set_and_get(self):
        cache = DistributedCache()
        entry = CacheEntry(
            key_hash='abc123',
            reply='hello world',
            model='gpt-4',
            source_node='node-a',
            ttl=3600,
        )
        cache.set(entry)
        retrieved = cache.get('abc123')
        assert retrieved is not None
        assert retrieved.reply == 'hello world'
        assert retrieved.source_node == 'node-a'

    def test_get_miss(self):
        cache = DistributedCache()
        assert cache.get('nonexistent') is None

    def test_expired_entry(self):
        cache = DistributedCache()
        entry = CacheEntry(
            key_hash='expired',
            reply='data',
            model='gpt-4',
            source_node='node-a',
            ttl=0,
        )
        cache.set(entry)
        time.sleep(0.01)
        assert cache.get('expired') is None

    def test_invalidate(self):
        cache = DistributedCache()
        entry = CacheEntry(
            key_hash='to-remove',
            reply='data',
            model='gpt-4',
            source_node='node-a',
            ttl=3600,
        )
        cache.set(entry)
        cache.invalidate('to-remove')
        assert cache.get('to-remove') is None

    def test_size_and_keys(self):
        cache = DistributedCache()
        for i in range(10):
            entry = CacheEntry(
                key_hash=f'key-{i}',
                reply=f'data-{i}',
                model='gpt-4',
                source_node='node-a',
                ttl=3600,
            )
            cache.set(entry)
        assert cache.size() == 10
        assert len(cache.keys()) == 10


class TestCacheKey:
    def test_same_inputs_same_key(self):
        k1 = cache_key('hello', 'gpt-4', 'system prompt', 0.7)
        k2 = cache_key('hello', 'gpt-4', 'system prompt', 0.7)
        assert k1 == k2

    def test_different_inputs_different_keys(self):
        k1 = cache_key('hello', 'gpt-4', 'system prompt', 0.7)
        k2 = cache_key('world', 'gpt-4', 'system prompt', 0.7)
        assert k1 != k2

    def test_different_model_different_key(self):
        k1 = cache_key('hello', 'gpt-4', 'system prompt', 0.7)
        k2 = cache_key('hello', 'gpt-3.5', 'system prompt', 0.7)
        assert k1 != k2

    def test_different_temperature_different_key(self):
        k1 = cache_key('hello', 'gpt-4', 'system prompt', 0.7)
        k2 = cache_key('hello', 'gpt-4', 'system prompt', 0.8)
        assert k1 != k2

    def test_key_is_sha256(self):
        key = cache_key('test', 'model', 'sys', 0.5)
        assert len(key) == 64
        assert all(c in '0123456789abcdef' for c in key)



