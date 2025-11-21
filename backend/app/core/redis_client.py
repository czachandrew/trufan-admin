import redis
from typing import Optional
from app.core.config import settings


class RedisClient:
    """Redis client for caching and session management."""

    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return self.client.get(key)

    def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set value in Redis with expiration."""
        return self.client.setex(key, expire, value)

    def delete(self, key: str) -> int:
        """Delete key from Redis."""
        return self.client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        return bool(self.client.exists(key))

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        return bool(self.client.expire(key, seconds))

    def incr(self, key: str) -> int:
        """Increment key value."""
        return self.client.incr(key)

    def close(self):
        """Close Redis connection."""
        self.client.close()


# Global Redis client instance
redis_client = RedisClient()
