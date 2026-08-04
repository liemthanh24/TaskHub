import json

from app.core.config import settings

if settings.REDIS_URL:
    from redis.asyncio import Redis

    _client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
else:
    from fakeredis import FakeAsyncRedis

    _client = FakeAsyncRedis(decode_responses=True)


class Cache:
    async def get(self, key: str):
        raw = await _client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value, ex: int | None = None):
        await _client.set(key, json.dumps(value, default=str), ex=ex)

    async def delete(self, *keys: str):
        if keys:
            await _client.delete(*keys)

    async def keys(self, pattern: str) -> list[str]:
        return [key async for key in _client.scan_iter(match=pattern)]

    async def flush(self):
        await _client.flushdb()


cache = Cache()
