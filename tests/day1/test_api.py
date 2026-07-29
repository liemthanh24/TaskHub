import pytest
from fastapi.testclient import TestClient

from app.dependencies import reset_store
from app.main import app


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield


client = TestClient(app)


class TestHealth:
    def test_health_check(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateTask:
    def test_create_task_valid(self):
        resp = client.post("/tasks", json={"title": "Test task"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 1
        assert data["title"] == "Test task"
        assert data["completed"] is False
        assert data["description"] is None
        assert "created_at" in data

    def test_create_task_missing_title(self):
        resp = client.post("/tasks", json={})
        assert resp.status_code == 422

    def test_create_task_full_fields(self):
        resp = client.post("/tasks", json={
            "title": "Full task",
            "description": "Something",
            "due_date": "2026-08-01T00:00:00Z",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Full task"
        assert data["description"] == "Something"
        assert data["due_date"] == "2026-08-01T00:00:00Z"


class TestListTasks:
    def test_list_empty(self):
        resp = client.get("/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_multiple(self):
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        resp = client.get("/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"


class TestGetTask:
    def test_get_task_found(self):
        client.post("/tasks", json={"title": "Find me"})
        resp = client.get("/tasks/1")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Find me"

    def test_get_task_not_found(self):
        resp = client.get("/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"


class TestUpdateTask:
    def test_update_task_valid(self):
        client.post("/tasks", json={"title": "Original"})
        resp = client.put("/tasks/1", json={"title": "Updated", "completed": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True

    def test_update_task_not_found(self):
        resp = client.put("/tasks/999", json={"title": "Nope"})
        assert resp.status_code == 404


class TestDeleteTask:
    def test_delete_task_valid(self):
        client.post("/tasks", json={"title": "Delete me"})
        resp = client.delete("/tasks/1")
        assert resp.status_code == 204

        resp = client.get("/tasks")
        assert resp.json() == []

    def test_delete_task_not_found(self):
        resp = client.delete("/tasks/999")
        assert resp.status_code == 404
