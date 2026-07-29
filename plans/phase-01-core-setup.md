# Phase 01: Core Setup & Architecture

**Status:** Completed
**Mode:** interactive

## Objectives
Thiết lập Layered Architecture với FastAPI + in-memory store + pytest.

## Files to Create

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config + dependencies |
| `requirements.txt` | Pin dependencies |
| `app/__init__.py` | Package init |
| `app/main.py` | FastAPI app instance + lifespan |
| `app/routers/__init__.py` | Package init |
| `app/routers/health.py` | GET /health endpoint |
| `app/routers/tasks.py` | CRUD endpoints cho tasks |
| `app/schemas/__init__.py` | Package init |
| `app/schemas/task.py` | Pydantic v2 schemas |
| `app/dependencies.py` | Dependency injection (in-memory store) |
| `tests/__init__.py` | Package init |
| `tests/test_api.py` | pytest + httpx tests |

## Architecture Layers

```
HTTP Request
    → Router (app/routers/tasks.py) — parse params, Depends()
    → Schema (app/schemas/task.py) — validate I/O
    → Dependency (app/dependencies.py) — inject store
    → In-memory dict store
    → Response (Pydantic model)
```

## Task Schema

```python
class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None

class Task(TaskCreate):
    id: int
    completed: bool = False
    created_at: datetime
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/tasks` | List all tasks |
| GET | `/tasks/{id}` | Get task by ID |
| POST | `/tasks` | Create task |
| PUT | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |

## Acceptance Criteria

1. `GET /health` returns `{"status": "ok"}`
2. `POST /tasks` with valid body creates task, returns 201
3. `POST /tasks` with missing title returns 422
4. `GET /tasks` returns list of tasks
5. `GET /tasks/1` returns task with id=1
6. `GET /tasks/999` returns 404
7. `PUT /tasks/1` updates task fields
8. `PUT /tasks/999` returns 404
9. `DELETE /tasks/1` removes task, returns 204
10. `DELETE /tasks/999` returns 404

## Out of Scope
- Authentication/authorization
- Database (PostgreSQL/SQLite)
- Frontend
- Pagination, filtering, sorting
- CORS middleware
- Rate limiting

## Constraints
- Python 3.11+
- FastAPI latest
- Pydantic v2 (`model_dump()`, `model_validate()`)
- pytest + httpx.TestClient
- In-memory store (dict)
