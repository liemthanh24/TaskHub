import logging
import time

from tests.day5.conftest import headers

LOGGER = "app.core.queue"


def _wait_for(caplog, predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if any(predicate(r.message) for r in caplog.records):
            return True
        time.sleep(0.05)
    return False


class TestBackgroundTasks:
    def test_create_logs_action(self, client, user_token, caplog):
        with caplog.at_level(logging.INFO, logger=LOGGER):
            task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        assert _wait_for(caplog, lambda m: f"action=create task_id={task_id}" in m)

    def test_update_logs_action(self, client, user_token, caplog):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        with caplog.at_level(logging.INFO, logger=LOGGER):
            client.put(f"/tasks/{task_id}", json={"title": "B"}, headers=headers(user_token))
        assert _wait_for(caplog, lambda m: f"action=update task_id={task_id}" in m)

    def test_delete_logs_action(self, client, user_token, caplog):
        task_id = client.post("/tasks", json={"title": "A"}, headers=headers(user_token)).json()["id"]
        with caplog.at_level(logging.INFO, logger=LOGGER):
            client.delete(f"/tasks/{task_id}", headers=headers(user_token))
        assert _wait_for(caplog, lambda m: f"action=delete task_id={task_id}" in m)
