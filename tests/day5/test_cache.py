import asyncio
import time

from app.core.cache import cache
from app.core.config import settings
from tests.day5.conftest import headers


def flush():
    if not settings.REDIS_URL:
        asyncio.run(cache.flush())


class TestCacheCore:
    def test_set_get(self):
        flush()
        asyncio.run(cache.set("k", {"a": 1}, ex=60))
        assert asyncio.run(cache.get("k")) == {"a": 1}

    def test_get_missing(self):
        flush()
        assert asyncio.run(cache.get("missing")) is None

    def test_delete(self):
        flush()
        asyncio.run(cache.set("k", "v"))
        asyncio.run(cache.delete("k"))
        assert asyncio.run(cache.get("k")) is None

    def test_expiry(self):
        flush()
        asyncio.run(cache.set("k", "v", ex=1))
        time.sleep(1.1)
        assert asyncio.run(cache.get("k")) is None


class TestListCache:
    def test_list_cached(self, client, user_token):
        client.post("/tasks", json={"title": "A"}, headers=headers(user_token))
        first = client.get("/tasks", headers=headers(user_token))
        assert first.status_code == 200
        assert len(first.json()) == 1

        cached = asyncio.run(cache.get("task:list:1"))
        assert cached is not None
        assert cached[0]["title"] == "A"

    def test_list_invalidated_on_create(self, client, user_token):
        client.post("/tasks", json={"title": "A"}, headers=headers(user_token))
        client.get("/tasks", headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is not None

        client.post("/tasks", json={"title": "B"}, headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is None

    def test_list_invalidated_on_update(self, client, user_token):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        client.get("/tasks", headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is not None

        client.put(f"/tasks/{task_id}", json={"title": "A2"}, headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is None

    def test_list_invalidated_on_delete(self, client, user_token):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        client.get("/tasks", headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is not None

        client.delete(f"/tasks/{task_id}", headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is None


class TestGetCache:
    def test_get_task_cached(self, client, user_token):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        client.get(f"/tasks/{task_id}", headers=headers(user_token))
        cached = asyncio.run(cache.get(f"task:get:{task_id}"))
        assert cached is not None
        assert cached["title"] == "A"

    def test_get_invalidated_on_update(self, client, user_token):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        client.get(f"/tasks/{task_id}", headers=headers(user_token))
        assert asyncio.run(cache.get(f"task:get:{task_id}")) is not None

        client.put(f"/tasks/{task_id}", json={"title": "A2"}, headers=headers(user_token))
        assert asyncio.run(cache.get(f"task:get:{task_id}")) is None
