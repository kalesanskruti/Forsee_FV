import json
import logging
from typing import Any, Optional, Dict
from uuid import UUID
import redis
from datetime import timedelta

from core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Service for interacting with Redis cache.
    Provides tenant-scoped keys and generic JSON serialization.
    """
    
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            try:
                cls._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_timeout=5
                )
                cls._client.ping()
            except Exception as e:
                logger.warning(f"Failed to connect to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}: {e}. Falling back to No-Op Cache.")
                cls._client = MagicMockRedis()
        return cls._client

    @staticmethod
    def _gen_key(tenant_id: str, asset_id: str, category: str) -> str:
        if not tenant_id:
            from core import context
            ctx = context.get_context()
            if ctx and ctx.org_id:
                tenant_id = str(ctx.org_id)
            else:
                raise ValueError("tenant_id must be provided or available in context for cache operations")
        return f"tenant:{tenant_id}:asset:{asset_id}:{category}"

    @classmethod
    def get_json(cls, tenant_id: str, asset_id: str, category: str) -> Optional[Dict[str, Any]]:
        client = cls.get_client()
        key = cls._gen_key(tenant_id, asset_id, category)
        data = client.get(key)
        if data:
            return json.loads(data)
        return None

    @classmethod
    def set_json(cls, tenant_id: str, asset_id: str, category: str, data: Dict[str, Any], ttl_seconds: int = 3600):
        client = cls.get_client()
        key = cls._gen_key(tenant_id, asset_id, category)
        client.setex(key, timedelta(seconds=ttl_seconds), json.dumps(data))

    @classmethod
    def invalidate(cls, tenant_id: str, asset_id: str, category: str):
        client = cls.get_client()
        key = cls._gen_key(tenant_id, asset_id, category)
        client.delete(key)

class MagicMockRedis:
    """No-Op Redis mock for fallback."""
    def get(self, *args, **kwargs): return None
    def setex(self, *args, **kwargs): pass
    def delete(self, *args, **kwargs): pass
    def ping(self): pass
