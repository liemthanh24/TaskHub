import asyncio

from app.core.cache import cache
from tests.day4.conftest import headers


class TestOwnership:
    def test_user_cannot_get_other_users_task(self, client, user_token, user2_token):
        task_id = client.post("/tasks", json={"title": "Mine"}, headers=headers(user_token)).json()["id"]
        resp = client.get(f"/tasks/{task_id}", headers=headers(user2_token))
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Not your task"

    def test_user_cannot_update_other_users_task(self, client, user_token, user2_token):
        task_id = client.post("/tasks", json={"title": "Mine"}, headers=headers(user_token)).json()["id"]
        resp = client.put(f"/tasks/{task_id}", json={"title": "Hacked"}, headers=headers(user2_token))
        assert resp.status_code == 404

    def test_user_cannot_delete_other_users_task(self, client, user_token, user2_token):
        task_id = client.post("/tasks", json={"title": "Mine"}, headers=headers(user_token)).json()["id"]
        resp = client.delete(f"/tasks/{task_id}", headers=headers(user2_token))
        assert resp.status_code == 404

    def test_user_sees_only_own_tasks(self, client, user_token, user2_token):
        client.post("/tasks", json={"title": "A"}, headers=headers(user_token))
        client.post("/tasks", json={"title": "B"}, headers=headers(user2_token))
        resp = client.get("/tasks", headers=headers(user_token))
        titles = [t["title"] for t in resp.json()]
        assert titles == ["A"]


class TestCacheLeak:
    def test_get_cache_does_not_leak_other_users_task(self, client, user_token, user2_token):
        task_id = client.post("/tasks", json={"title": "Secret"}, headers=headers(user_token)).json()["id"]
        assert client.get(f"/tasks/{task_id}", headers=headers(user_token)).status_code == 200
        assert asyncio.run(cache.get(f"task:get:{task_id}")) is not None
        resp = client.get(f"/tasks/{task_id}", headers=headers(user2_token))
        assert resp.status_code == 403

    def test_list_cache_is_user_scoped(self, client, user_token, user2_token):
        client.post("/tasks", json={"title": "Mine only"}, headers=headers(user_token))
        client.get("/tasks", headers=headers(user_token))
        assert asyncio.run(cache.get("task:list:1")) is not None
        resp = client.get("/tasks", headers=headers(user2_token))
        assert resp.json() == []

    def test_page_cache_is_user_scoped(self, client, user_token, user2_token):
        client.post("/tasks", json={"title": "A"}, headers=headers(user_token))
        first = client.get("/tasks/page", headers=headers(user_token))
        assert first.status_code == 200
        assert first.json()["total"] == 1
        resp = client.get("/tasks/page", headers=headers(user2_token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestAdmin:
    def test_admin_sees_all_tasks(self, client, user_token, admin_token):
        client.post("/tasks", json={"title": "A"}, headers=headers(user_token))
        client.post("/tasks", json={"title": "B"}, headers=headers(user_token))
        resp = client.get("/tasks/all", headers=headers(admin_token))
        assert len(resp.json()) == 2

    def test_all_endpoint_requires_admin(self, client, user_token):
        resp = client.get("/tasks/all", headers=headers(user_token))
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Insufficient permissions"

    def test_admin_can_get_any_task(self, client, user_token, admin_token):
        task_id = client.post("/tasks", json={"title": "Mine"}, headers=headers(user_token)).json()["id"]
        resp = client.get(f"/tasks/{task_id}", headers=headers(admin_token))
        assert resp.status_code == 200

    def test_admin_can_update_any_task(self, client, user_token, admin_token):
        task_id = client.post("/tasks", json={"title": "Mine"}, headers=headers(user_token)).json()["id"]
        resp = client.put(f"/tasks/{task_id}", json={"title": "By admin"}, headers=headers(admin_token))
        assert resp.status_code == 200
        assert resp.json()["title"] == "By admin"

    def test_admin_can_delete_any_task(self, client, user_token, admin_token):
        task_id = client.post("/tasks", json={"title": "Mine"}, headers=headers(user_token)).json()["id"]
        resp = client.delete(f"/tasks/{task_id}", headers=headers(admin_token))
        assert resp.status_code == 204


class TestAuthGuard:
    def test_task_list_requires_token(self, client):
        resp = client.get("/tasks")
        assert resp.status_code == 401

    def test_invalid_token_rejected(self, client):
        resp = client.get("/tasks", headers=headers("not-a-real-token"))
        assert resp.status_code == 401

    def test_create_task_records_user_id(self, client, user_token):
        resp = client.post("/tasks", json={"title": "Owned"}, headers=headers(user_token))
        assert resp.status_code == 201
        assert resp.json()["user_id"] >= 1


class TestRegisterRole:
    def test_register_default_role_is_user(self, client):
        resp = client.post("/auth/register", json={"email": "u@example.com", "password": "secret123"})
        assert resp.status_code == 201
        token = resp.json()["access_token"]
        resp = client.get("/auth/me", headers=headers(token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "user"

    def test_register_cannot_escalate_to_admin(self, client):
        resp = client.post("/auth/register", json={"email": "evil@example.com", "password": "secret123", "role": "admin"})
        assert resp.status_code == 201
        token = resp.json()["access_token"]
        resp = client.get("/auth/me", headers=headers(token))
        assert resp.json()["role"] == "user"

    def test_admin_role_from_seeder(self, client, admin_token):
        resp = client.get("/auth/me", headers=headers(admin_token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"


class TestPagination:
    def test_page_returns_valid_shape(self, client, user_token):
        for i in range(3):
            client.post("/tasks", json={"title": f"T{i}"}, headers=headers(user_token))
        resp = client.get("/tasks/page?per_page=2", headers=headers(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["pages"] == 2
        assert len(data["items"]) == 2
        assert "user_id" in data["items"][0]
