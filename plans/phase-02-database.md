# Phase 02: Database Integration (SQLAlchemy 2.x Async + Alembic)

**Status:** Draft
**Mode:** interactive
**Branch:** day2

## Objectives
Chuyển từ in-memory store sang SQLAlchemy 2.x async với SQLite, Repository Pattern, Alembic migration.

## Files to Create

| File | Purpose |
|------|---------|
| `app/database.py` | Engine, AsyncSessionLocal, get_db() |
| `app/models/__init__.py` | Package init |
| `app/models/base.py` | DeclarativeBase |
| `app/models/task.py` | TaskModel ORM |
| `app/repositories/__init__.py` | Package init |
| `app/repositories/base.py` | BaseRepository[T] generic CRUD + pagination |
| `app/repositories/task.py` | TaskRepository |
| `tests/day2/__init__.py` | Package init |
| `tests/day2/test_db.py` | Integration tests |

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Add sqlalchemy[asyncio], aiosqlite, alembic |
| `app/requirements.txt` | Add new deps |
| `app/main.py` | Add engine.dispose() in lifespan |
| `app/dependencies.py` | Add get_db(), keep reset_store() |
| `app/routers/tasks.py` | Switch to DB + repository |

## Architecture

```
Router → TaskRepository (CRUD) → AsyncSession → Engine → taskhub.db
         ↑ BaseRepository[T] (generic)
```

## Acceptance Criteria

1. `pytest tests/day1/` — 12 tests still pass (no regression)
2. `pytest tests/day2/` — new DB tests pass
3. POST /tasks → persists to SQLite file
4. Restart server → GET /tasks still returns data
5. Alembic: `alembic upgrade head` creates tasks table
6. Pagination works: GET /tasks?page=1&per_page=10

## Out of Scope
- Relationships (User → Task)
- PostgreSQL
- Async test fixtures with rollback
- alembic autogenerate (manual migration)

## Constraints
- SQLite + aiosqlite (dev)
- SQLAlchemy 2.x async (DeclarativeBase)
- Same API endpoints as Day 1 (backward compatible)
- Day 1 in-memory store kept for old tests
