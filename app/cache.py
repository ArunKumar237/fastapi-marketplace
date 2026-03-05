from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis, from_url

from app.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return from_url(settings.REDIS_URL, decode_responses=True)


async def ping_redis() -> bool:
    client = get_redis_client()
    return bool(await client.ping())
