import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config.settings import settings


class RedisCache:
    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()

    @property
    def client(self) -> aioredis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected")
        return self._redis

    async def set_json(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self.client.set(key, json.dumps(value), ex=ttl)

    async def get_json(self, key: str) -> Optional[Any]:
        data = await self.client.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def get_browse_exclude(self, user_id: int) -> list[int]:
        data = await self.get_json(f"browse_exclude:{user_id}")
        return data if isinstance(data, list) else []

    async def add_browse_exclude(self, user_id: int, profile_id: int) -> None:
        exclude = await self.get_browse_exclude(user_id)
        if profile_id not in exclude:
            exclude.append(profile_id)
        await self.set_json(f"browse_exclude:{user_id}", exclude, ttl=86400)

    async def clear_browse_exclude(self, user_id: int) -> None:
        await self.delete(f"browse_exclude:{user_id}")

    async def set_current_profile(self, user_id: int, profile_id: int) -> None:
        await self.set_json(f"current_profile:{user_id}", profile_id, ttl=3600)

    async def get_current_profile(self, user_id: int) -> Optional[int]:
        data = await self.get_json(f"current_profile:{user_id}")
        return int(data) if data is not None else None


redis_cache = RedisCache()
