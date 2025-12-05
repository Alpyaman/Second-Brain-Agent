"""
Response Cache for LLM Calls

This module provides caching functionality to reduce redundant API calls and save costs.

Features:
- In-memory caching with TTL
- Disk persistence for long-term caching
- Hash-based key generation
- Automatic cache cleanup
"""

import os
import json
import hashlib
import time
from typing import Any, Optional, Dict
from pathlib import Path
from datetime import datetime


class ResponseCache:
    """Cache for LLM responses to reduce redundant API calls."""

    def __init__(
        self,
        cache_dir: str = "./cache",
        ttl_hours: int = 24,
        enabled: bool = True
    ):
        """
        Initialize the response cache.

        Args:
            cache_dir: Directory to store cached responses
            ttl_hours: Time-to-live for cached entries in hours
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.enabled = enabled
        self.memory_cache: Dict[str, tuple[Any, float]] = {}

        # Create cache directory if it doesn't exist
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_key(self, prompt: str, model: str, temperature: float) -> str:
        """
        Generate a unique cache key from prompt, model, and temperature.

        Args:
            prompt: The input prompt
            model: Model name
            temperature: Temperature setting

        Returns:
            SHA256 hash of the input parameters
        """
        key_string = f"{prompt}:{model}:{temperature}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cached entry has expired."""
        return time.time() - timestamp > self.ttl_seconds

    def get(self, prompt: str, model: str, temperature: float) -> Optional[Any]:
        """
        Get a cached response if available and not expired.

        Args:
            prompt: The input prompt
            model: Model name
            temperature: Temperature setting

        Returns:
            Cached response or None if not found/expired
        """
        if not self.enabled:
            return None

        key = self._generate_key(prompt, model, temperature)

        # Check memory cache first
        if key in self.memory_cache:
            response, timestamp = self.memory_cache[key]
            if not self._is_expired(timestamp):
                return response
            else:
                # Remove expired entry from memory
                del self.memory_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                timestamp = data.get('timestamp', 0)
                if not self._is_expired(timestamp):
                    response = data.get('response')
                    # Add to memory cache for faster future access
                    self.memory_cache[key] = (response, timestamp)
                    return response
                else:
                    # Remove expired file
                    cache_file.unlink()
            except Exception as e:
                print(f"⚠️  Error reading cache file: {e}")

        return None

    def set(self, prompt: str, model: str, temperature: float, response: Any):
        """
        Store a response in the cache.

        Args:
            prompt: The input prompt
            model: Model name
            temperature: Temperature setting
            response: The LLM response to cache
        """
        if not self.enabled:
            return

        key = self._generate_key(prompt, model, temperature)
        timestamp = time.time()

        # Store in memory cache
        self.memory_cache[key] = (response, timestamp)

        # Store in disk cache
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'prompt': prompt[:500],  # Store first 500 chars for debugging
                    'model': model,
                    'temperature': temperature,
                    'response': response,
                    'timestamp': timestamp,
                    'created_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error writing cache file: {e}")

    def clear_expired(self):
        """Remove all expired entries from cache."""
        if not self.enabled:
            return

        # Clear expired memory cache entries
        expired_keys = [
            key for key, (_, timestamp) in self.memory_cache.items()
            if self._is_expired(timestamp)
        ]
        for key in expired_keys:
            del self.memory_cache[key]

        # Clear expired disk cache entries
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    timestamp = data.get('timestamp', 0)
                    if self._is_expired(timestamp):
                        cache_file.unlink()
                except Exception:
                    # If we can't read the file, delete it
                    cache_file.unlink()

    def clear_all(self):
        """Clear all cached entries."""
        self.memory_cache.clear()

        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}

        memory_count = len(self.memory_cache)
        disk_count = len(list(self.cache_dir.glob("*.json"))) if self.cache_dir.exists() else 0

        total_size = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size

        return {
            "enabled": True,
            "memory_entries": memory_count,
            "disk_entries": disk_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "ttl_hours": self.ttl_seconds / 3600,
            "cache_dir": str(self.cache_dir)
        }


# Global cache instance
_cache_instance: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """Get or create the global cache instance."""
    global _cache_instance

    if _cache_instance is None:
        # Read configuration from environment
        cache_dir = os.getenv("CACHE_DIR", "./cache")
        ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))
        enabled = os.getenv("ENABLE_RESPONSE_CACHE", "false").lower() in ("true", "1", "yes")

        _cache_instance = ResponseCache(
            cache_dir=cache_dir,
            ttl_hours=ttl_hours,
            enabled=enabled
        )

        if enabled:
            print(f"✓ Response caching enabled (TTL: {ttl_hours}h, Dir: {cache_dir})")

    return _cache_instance


def cached_llm_invoke(llm: Any, messages: list, cache_enabled: bool = True) -> Any:
    """
    Invoke LLM with caching support.

    Args:
        llm: LLM instance
        messages: Messages to send
        cache_enabled: Whether to use caching for this call

    Returns:
        LLM response (from cache or fresh API call)
    """
    cache = get_cache()

    if not cache.enabled or not cache_enabled:
        # No caching, make direct call
        return llm.invoke(messages)

    # Generate cache key from messages
    prompt = str(messages)
    model = getattr(llm, 'model', 'unknown')
    temperature = getattr(llm, 'temperature', 0.0)

    # Try to get from cache
    cached_response = cache.get(prompt, model, temperature)
    if cached_response is not None:
        print(f"✓ Using cached response (model: {model})")
        # Return a mock response object with the cached content
        class CachedResponse:
            def __init__(self, content):
                self.content = content
        return CachedResponse(cached_response)

    # Cache miss - make actual API call
    print(f"→ Making API call (model: {model})")
    response = llm.invoke(messages)

    # Cache the response
    cache.set(prompt, model, temperature, response.content)

    return response


def clear_cache():
    """Clear all cached responses."""
    cache = get_cache()
    cache.clear_all()
    print("✓ Cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = get_cache()
    return cache.get_stats()


def cleanup_expired_cache():
    """Remove expired cache entries."""
    cache = get_cache()
    cache.clear_expired()
    print("✓ Expired cache entries removed")