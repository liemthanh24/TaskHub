import logging

from tests.day5.conftest import headers


class TestBackgroundTasks:
    def test_create_logs_action(self, client, user_token, caplog):
        with caplog.at_level(logging.INFO, logger="taskhub.action"):
            resp = client.post("/tasks", json={"title": "A"}, headers=headers(user_token))
            task_id = resp.json()["id"]
            messages = [r.message for r in caplog.records]
        assert any(f"action=create task_id={task_id}" in m for m in messages)

    def test_update_logs_action(self, client, user_token, caplog):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        with caplog.at_level(logging.INFO, logger="taskhub.action"):
            client.put(f"/tasks/{task_id}", json={"title": "B"}, headers=headers(user_token))
            messages = [r.message for r in caplog.records]
        assert any(f"action=update task_id={task_id}" in m for m in messages)

    def test_delete_logs_action(self, client, user_token, caplog):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        with caplog.at_level(logging.INFO, logger="taskhub.action"):
            client.delete(f"/tasks/{task_id}", headers=headers(user_token))
            messages = [r.message for r in caplog.records]
        assert any(f"action=delete task_id={task_id}" in m for m in messages)
