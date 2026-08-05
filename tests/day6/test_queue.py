import asyncio
import logging

import pytest

from app.core.queue import TaskQueue


@pytest.fixture
def queue():
    q = TaskQueue(maxsize=2)
    yield q
    asyncio.run(q.stop())


def test_enqueue_returns_true(queue):
    assert asyncio.run(queue.enqueue({"type": "action_log", "action": "create"})) is True


def test_queue_full_drops_job(queue):
    async def scenario():
        assert await queue.enqueue({"type": "action_log", "action": "a"}) is True
        assert await queue.enqueue({"type": "action_log", "action": "b"}) is True
        assert await queue.enqueue({"type": "action_log", "action": "c"}) is False
    asyncio.run(scenario())


def test_worker_processes_job(queue, caplog):
    caplog.set_level(logging.INFO, logger="app.core.queue")
    job = {"type": "action_log", "action": "create", "task_id": 7, "user_id": 3, "request_id": "REQ-1"}

    async def scenario():
        queue.start()
        await queue.enqueue(job)
        await asyncio.sleep(0.05)
        await queue.stop()

    asyncio.run(scenario())
    assert any("action=create task_id=7 user_id=3" in r.message for r in caplog.records)


def test_worker_unknown_job_logs_warning(queue, caplog):
    caplog.set_level(logging.INFO, logger="app.core.queue")

    async def scenario():
        queue.start()
        await queue.enqueue({"type": "unknown"})
        await asyncio.sleep(0.05)
        await queue.stop()

    asyncio.run(scenario())
    assert any("Unknown job type" in r.message for r in caplog.records)


def test_stop_returns_when_never_started(queue):
    asyncio.run(queue.stop())
