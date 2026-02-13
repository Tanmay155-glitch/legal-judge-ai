"""
Caching Layer - Performance optimization through intelligent caching
Supports in-memory LRU cache and optional Redis backend
"""

import os
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
from collections import OrderedDict
from loguru import logger
import time


class LRUCache:
    """
    Simple in-memory LRU (Least Recently Used) cache.
    
    Features:
    - Fixed maximum size
    - Automatic eviction of least recently used items
    - TTL (Time To Live) support
    - Thread-safe operations
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
            default_ttl: Default TTL in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.hits = 0
        self.misses = 0
        
        logger.info(f"LRU Cache initialized: max_size={max_size}, ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        # Check TTL
        if self._is_expired(key):
            self.delete(key)
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override (seconds)
        """
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Evict least recently used
                oldest_key = next(iter(self.cache))
                self.delete(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = {
            "created": time.time(),
            "ttl": ttl or self.default_ttl
        }
    
    def delete(self, key: str):
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
            "total_requests": total_requests
        }
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.timestamps:
            return True
        
        ts_info = self.timestamps[key]
        if ts_info["ttl"] == 0:
            return False  # No expiration
        
        age = time.time() - ts_info["created"]
        return age > ts_info["ttl"]


class CacheManager:
    """
    Centralized cache management with multiple cache types.
    
    Cache Types:
    - query_embeddings: Cache for query embedding vectors (TTL: 1 hour)
    - search_results: Cache for frequent search queries (TTL: 30 minutes)
    - case_metadata: Cache for case law metadata (TTL: 24 hours)
    """
    
    def __init__(
        self,
        enable_redis: bool = False,
        redis_url: str = None
    ):
        """
        Initialize cache manager.
        
        Args:
            enable_redis: Whether to use Redis backend
            redis_url: Redis connection URL
        """
        self.enable_redis = enable_redis
        self.redis_client = None
        
        # Initialize in-memory caches
        self.query_embeddings_cache = LRUCache(max_size=1000, default_ttl=3600)  # 1 hour
        self.search_results_cache = LRUCache(max_size=500, default_ttl=1800)  # 30 minutes
        self.case_metadata_cache = LRUCache(max_size=2000, default_ttl=86400)  # 24 hours
        
        # Initialize Redis if enabled
        if enable_redis:
            try:
                import redis
                self.redis_client = redis.from_url(
                    redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
                )
                self.redis_client.ping()
                logger.info("Redis cache backend connected")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory only: {e}")
                self.enable_redis = False
        
        logger.info("Cache manager initialized")
    
    def cache_query_embedding(self, query: str, embedding: list, ttl: int = 3600):
        """
        Cache a query embedding.
        
        Args:
            query: Query text
            embedding: Embedding vector
            ttl: TTL in seconds
        """
        key = self._hash_key(f"query_emb:{query}")
        self.query_embeddings_cache.set(key, embedding, ttl)
        
        if self.enable_redis and self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(embedding)
                )
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
    
    def get_query_embedding(self, query: str) -> Optional[list]:
        """
        Get cached query embedding.
        
        Args:
            query: Query text
        
        Returns:
            Cached embedding or None
        """
        key = self._hash_key(f"query_emb:{query}")
        
        # Try in-memory first
        result = self.query_embeddings_cache.get(key)
        if result is not None:
            return result
        
        # Try Redis
        if self.enable_redis and self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    result = json.loads(cached)
                    # Populate in-memory cache
                    self.query_embeddings_cache.set(key, result)
                    return result
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        return None
    
    def cache_search_results(self, query: str, results: list, ttl: int = 1800):
        """
        Cache search results.
        
        Args:
            query: Search query
            results: Search results
            ttl: TTL in seconds
        """
        key = self._hash_key(f"search:{query}")
        self.search_results_cache.set(key, results, ttl)
    
    def get_search_results(self, query: str) -> Optional[list]:
        """
        Get cached search results.
        
        Args:
            query: Search query
        
        Returns:
            Cached results or None
        """
        key = self._hash_key(f"search:{query}")
        return self.search_results_cache.get(key)
    
    def cache_case_metadata(self, case_id: str, metadata: dict, ttl: int = 86400):
        """
        Cache case metadata.
        
        Args:
            case_id: Case document ID
            metadata: Case metadata
            ttl: TTL in seconds
        """
        key = f"case:{case_id}"
        self.case_metadata_cache.set(key, metadata, ttl)
    
    def get_case_metadata(self, case_id: str) -> Optional[dict]:
        """
        Get cached case metadata.
        
        Args:
            case_id: Case document ID
        
        Returns:
            Cached metadata or None
        """
        key = f"case:{case_id}"
        return self.case_metadata_cache.get(key)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics for all caches.
        
        Returns:
            Dictionary with stats for each cache
        """
        return {
            "query_embeddings": self.query_embeddings_cache.get_stats(),
            "search_results": self.search_results_cache.get_stats(),
            "case_metadata": self.case_metadata_cache.get_stats(),
            "redis_enabled": self.enable_redis
        }
    
    def clear_all(self):
        """Clear all caches."""
        self.query_embeddings_cache.clear()
        self.search_results_cache.clear()
        self.case_metadata_cache.clear()
        
        if self.enable_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")
    
    def _hash_key(self, key: str) -> str:
        """
        Hash a key for consistent cache keys.
        
        Args:
            key: Original key
        
        Returns:
            Hashed key
        """
        return hashlib.md5(key.encode()).hexdigest()


# Singleton instance
_cache_manager_instance = None


def get_cache_manager(enable_redis: bool = False) -> CacheManager:
    """
    Get or create the singleton CacheManager instance.
    
    Args:
        enable_redis: Whether to enable Redis (only used on first call)
    
    Returns:
        CacheManager instance
    """
    global _cache_manager_instance
    
    if _cache_manager_instance is None:
        enable_redis = enable_redis or os.getenv("ENABLE_REDIS_CACHE", "false").lower() == "true"
        _cache_manager_instance = CacheManager(enable_redis=enable_redis)
    
    return _cache_manager_instance


def cached(cache_type: str = "general", ttl: int = 3600):
    """
    Decorator for caching function results.
    
    Args:
        cache_type: Type of cache to use
        ttl: TTL in seconds
    
    Example:
        @cached(cache_type="search", ttl=1800)
        async def search_cases(query: str):
            # expensive operation
            return results
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cache_manager = get_cache_manager()
            
            if cache_type == "search":
                cached_result = cache_manager.get_search_results(cache_key)
            else:
                # Use general query embeddings cache
                cached_result = cache_manager.query_embeddings_cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if cache_type == "search":
                cache_manager.cache_search_results(cache_key, result, ttl)
            else:
                cache_manager.query_embeddings_cache.set(cache_key, result, ttl)
            
            logger.debug(f"Cache miss: {func.__name__}")
            return result
        
        return wrapper
    return decorator
