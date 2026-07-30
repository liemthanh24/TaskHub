import pytest


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateTask:
    def test_create_task_valid(self, client):
        resp = client.post("/tasks", json={"title": "Test task"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] >= 1
        assert data["title"] == "Test task"
        assert data["completed"] is False
        assert data["description"] is None
        assert "created_at" in data

    def test_create_task_missing_title(self, client):
        resp = client.post("/tasks", json={})
        assert resp.status_code == 422

    def test_create_task_full_fields(self, client):
        resp = client.post("/tasks", json={
            "title": "Full task",
            "description": "Something",
            "due_date": "2026-08-01T00:00:00Z",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Full task"
        assert data["description"] == "Something"
        assert data["due_date"] is not None
        assert "2026-08-01" in data["due_date"]


class TestListTasks:
    def test_list_empty(self, client):
        resp = client.get("/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_multiple(self, client):
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        resp = client.get("/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        titles = [t["title"] for t in data]
        assert "Task 1" in titles
        assert "Task 2" in titles


class TestGetTask:
    def test_get_task_found(self, client):
        create_resp = client.post("/tasks", json={"title": "Find me"})
        task_id = create_resp.json()["id"]
        resp = client.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Find me"

    def test_get_task_not_found(self, client):
        resp = client.get("/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"


class TestUpdateTask:
    def test_update_task_valid(self, client):
        create_resp = client.post("/tasks", json={"title": "Original"})
        task_id = create_resp.json()["id"]
        resp = client.put(f"/tasks/{task_id}", json={"title": "Updated", "completed": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True

    def test_update_task_not_found(self, client):
        resp = client.put("/tasks/999", json={"title": "Nope"})
        assert resp.status_code == 404


class TestDeleteTask:
    def test_delete_task_valid(self, client):
        create_resp = client.post("/tasks", json={"title": "Delete me"})
        task_id = create_resp.json()["id"]
        resp = client.delete(f"/tasks/{task_id}")
        assert resp.status_code == 204

        resp = client.get("/tasks")
        assert resp.json() == []

    def test_delete_task_not_found(self, client):
        resp = client.delete("/tasks/999")
        assert resp.status_code == 404
