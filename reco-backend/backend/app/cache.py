import redis.asyncio as aioredis
import json
import hashlib
import os
from typing import Any, Optional, Callable
from functools import wraps

class RedisCache:
    def __init__(self, redis_url: str = None):
        if redis_url is None:
            host = os.environ.get("REDIS_HOST", "redis")
            port = int(os.environ.get("REDIS_PORT", "6379"))
            redis_url = f"redis://{host}:{port}"
        
        self.redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Lấy giá trị từ cache"""
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[CACHE_ERROR] Get failed: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Lưu giá trị vào cache
        ttl: time to live (giây), default 5 phút
        """
        try:
            data = json.dumps(value)
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            print(f"[CACHE_ERROR] Set failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Xóa key khỏi cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"[CACHE_ERROR] Delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Kiểm tra key có tồn tại không"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"[CACHE_ERROR] Exists check failed: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str):
        """Xóa tất cả keys matching pattern"""
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            print(f"[CACHE_ERROR] Pattern invalidation failed: {e}")
    
    async def close(self):
        """Đóng connection"""
        await self.redis.close()


def generate_cache_key(*args, **kwargs) -> str:
    """
    Tạo cache key từ arguments
    """
    # Convert args và kwargs thành string deterministic
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = ":".join(key_parts)
    
    # Hash để tránh key quá dài
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return key_hash


def cache_result(prefix: str, ttl: int = 300):
    """
    Decorator để cache kết quả của async function
    
    Usage:
        @cache_result("recommend:tracks", ttl=600)
        async def get_recommendations(user_id, limit):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Lấy cache instance từ kwargs hoặc args
            cache = kwargs.get('cache') or (args[0] if args and isinstance(args[0], RedisCache) else None)
            
            if not cache:
                # Không có cache, chạy function bình thường
                return await func(*args, **kwargs)
            
            # Tạo cache key
            cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"
            
            # Thử lấy từ cache
            cached = await cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Cache miss - chạy function
            result = await func(*args, **kwargs)
            
            # Lưu vào cache
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Cache strategies
class CacheStrategy:
    
    RECOMMENDATIONS = 600
     
    POPULAR_ITEMS = 3600
    
    SEARCH_RESULTS = 300
    
    USER_PLAYLISTS = 120
    
    ITEM_DETAILS = 86400
    
    SESSION = 1800


# Singleton instance
_cache_instance: Optional[RedisCache] = None

def get_cache() -> RedisCache:
    """Get cache singleton instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance