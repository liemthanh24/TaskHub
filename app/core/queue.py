import asyncio
import logging
from contextlib import suppress

from app.core.logging import request_id_var

logger = logging.getLogger(__name__)


class TaskQueue:
    """In-process async job queue with a single consumer worker."""

    def __init__(self, maxsize: int = 100):
        self._maxsize = maxsize
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._worker_task: asyncio.Task | None = None

    async def enqueue(self, job: dict) -> bool:
        try:
            self._queue.put_nowait(job)
            return True
        except asyncio.QueueFull:
            logger.warning("Queue is full, dropping job %s", job)
            return False

    async def _process(self, job: dict) -> None:
        token = request_id_var.set(job.get("request_id", "-"))
        try:
            kind = job.get("type")
            if kind == "action_log":
                logger.info(
                    "action=%s task_id=%s user_id=%s",
                    job.get("action"),
                    job.get("task_id"),
                    job.get("user_id"),
                )
            else:
                logger.warning("Unknown job type: %s", kind)
        finally:
            request_id_var.reset(token)

    async def worker(self) -> None:
        logger.info("Queue worker started")
        while True:
            item = await self._queue.get()
            try:
                await self._process(item)
            except Exception:
                logger.exception("Failed to process job %s", item)

    def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self.worker())

    async def stop(self) -> None:
        if self._worker_task is None:
            return
        self._worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._worker_task
        self._worker_task = None
        logger.info("Queue worker stopped")

    async def reset(self) -> None:
        """Cancel any running worker and clear queued jobs (test isolation)."""
        if self._worker_task is not None:
            self._worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None
        self._queue = asyncio.Queue(maxsize=self._maxsize)


task_queue = TaskQueue()
