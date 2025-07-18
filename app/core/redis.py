from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.core.config import settings

redis_client_ping = aioredis.from_url(
    f"{settings.redis_url}/{settings.REDIS_PING_DB}",
    ssl_cert_reqs=None
)

rediss = aioredis.from_url(
        url=f"rediss://{settings.CACHE_USER}:"
        f"{settings.CACHE_PASSWORD}@"
        f"{settings.CACHE_HOST}:"
        f"{settings.CACHE_PORT}"
    )

FastAPICache.init(RedisBackend(rediss), prefix="")
