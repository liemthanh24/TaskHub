# Journal: Core Setup & Architecture

**Date:** 2026-07-29
**Phase:** 01

## Summary
Thiết lập Layered Architecture cho TaskHub với FastAPI.

## What was built
- `app/main.py` — FastAPI app instance + lifespan
- `app/routers/health.py` — GET /health endpoint
- `app/routers/tasks.py` — CRUD endpoints: list, get, create, update, delete
- `app/schemas/task.py` — Pydantic v2 schemas (TaskCreate, TaskUpdate, Task)
- `app/dependencies.py` — In-memory store via Depends()
- `tests/test_api.py` — 12 tests covering all endpoints + validation + 404

## Key decisions
- Layered: Router → Schema → Dependency → In-memory store
- Pydantic v2 without inheritance (avoid field ordering issues)
- `default_factory` for `created_at` (per-instance, not class-level)
- `get_next_id` increments before yield (concurrency-safe for in-memory)
- Auto-reset store between tests via `pytest.fixture(autouse=True)`

## Issues found & fixed
- Code review caught 3 issues: Task schema inheritance, created_at default, concurrency in next_id
- All fixed before finalization; 12/12 tests passing
