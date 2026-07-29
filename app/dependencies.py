from collections.abc import Generator


_tasks_store: dict[int, dict] = {}
_next_id: int = 1


def get_tasks_store() -> Generator[dict[int, dict], None, None]:
    yield _tasks_store


def get_next_id() -> Generator[int, None, None]:
    global _next_id
    current = _next_id
    _next_id += 1
    yield current


def reset_store():
    global _tasks_store, _next_id
    _tasks_store.clear()
    _next_id = 1
