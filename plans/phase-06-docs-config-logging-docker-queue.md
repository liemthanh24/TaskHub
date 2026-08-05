# Phase 06: API Docs + Config Polish + Logging + Docker + Queue

**Status:** Implemented ✅
**Mode:** interactive
**Branch:** day6
**Base:** day5 (chứa cả Day 5 RBAC + Day 6 caching/background)

> Đã hoàn thành toàn bộ 6 nhóm. 95 tests pass (day1–day6), code-review PASS (đã fix 1 major + các minor/nit).

## Objectives
Hoàn thiện production-readiness: API Documentation, fail-fast env validation, multi-environment, request-id logging, Docker (app + postgres + redis), in-process async queue.

## Nhóm 1: Multi-environment + Fail-fast (`app/core/config.py`)

### Thay đổi
| File | Change |
|------|--------|
| `app/core/config.py` | Thêm `APP_ENV` (dev/staging/prod), `validate()` gọi trong `__init__`, chọn env_file theo APP_ENV |

### Chi tiết
- Thêm field `APP_ENV: str = "dev"` (LOWERCASE, enum `Literal["dev", "test", "prod"]`)
- `model_config` env_file ưu tiên:
  - `APP_ENV=dev` → `.env.dev`
  - `APP_ENV=test` → `.env.test`
  - `APP_ENV=prod` → `.env.prod`
  - Fallback: nếu file tương ứng không tồn tại, dùng `.env` như cũ (không phá luồng hiện tại)
- Thêm method `validate()` gọi trong `__init__` (fail-fast khi khởi tạo Settings):
  - Nếu `APP_ENV == "prod"`:
    - `JWT_SECRET` không được là `"change-me-in-production"`
    - `DATABASE_URL` bắt buộc set (không phải SQLite default)
    - `ADMIN_PASSWORD` bắt buộc set
  - Luôn: `JWT_EXPIRE_MINUTES > 0`
- Giữ default an toàn cho dev; không đổi tên field cũ (backward compatible với `.env.example` + `_guard_settings` trong main.py — có thể refactor `_guard_settings` để gọi `settings.validate()` thay vì logic trùng)

### Files mới
- `.env.dev.example` (template dev), `.env.prod.example` (template prod: bắt buộc JWT_SECRET, DATABASE_URL postgres, ADMIN_PASSWORD)
- Cập nhật `.env.example` thêm `APP_ENV`

## Nhóm 2: API Documentation (`app/main.py` + schemas)

### Thay đổi
| File | Change |
|------|--------|
| `app/main.py` | `FastAPI(description=..., summary=..., openapi_tags=[...])` |
| `app/routers/auth.py`, `app/routers/tasks.py`, `app/routers/health.py` | Thêm `summary`, `description` cho từng endpoint |
| `app/schemas/auth.py`, `app/schemas/task.py` | Thêm `examples` qua `json_schema_extra` (ConfigDict) |

### Chi tiết
- `openapi_tags`: mô tả cho `auth`, `tasks`, `health`
- `FastAPI(...)`: thêm `description` (tiếng Việt, ngắn), `summary`, `openapi_tags`
- Mỗi endpoint có `summary` (cụm ngắn) + `description` (chi tiết quyền hạn, ví dụ)
- Schema examples:
  - `UserCreate`: email/password mẫu
  - `UserLogin`: mẫu
  - `TaskCreate`/`TaskUpdate`: title/description/due_date mẫu
  - `Token`, `Page`: mô tả trường
- KHÔNG đổi JSON response structure — chỉ thêm metadata OpenAPI (contract ổn định)

## Nhóm 3: Request-ID logging (`app/core/logging.py` + `app/main.py`)

### Thay đổi
| File | Change |
|------|--------|
| `app/core/logging.py` | Thêm `request_id_var` (ContextVar) + `RequestIdFilter` |
| `app/main.py` | Middleware set ContextVar trước khi gọi handler; filter request_id trong log |

### Chi tiết
- `request_id_var: ContextVar[str]` default `"-"`
- `RequestIdFilter(logging.Filter)`: thêm attribute `request_id` từ ContextVar vào mỗi log record
- `setup_logging()`: format mới `%(asctime)s | %(levelname)-7s | %(name)s | %(request_id)s | %(message)s`
- Middleware `add_request_context`: `request_id_var.set(request_id)` đầu request; reset sau
- **Quan trọng:** ContextVar không tự propagate vào BackgroundTasks/thread → trong `log_action` và queue worker, cần truyền `request_id` làm tham số (không dựa vào ContextVar ở đó)

## Nhóm 4: In-process async Queue (`app/core/queue.py` + worker)

### Thay đổi
| File | Change |
|------|--------|
| `app/core/queue.py` | Mới: `TaskQueue` (asyncio.Queue) + `start_worker()`/`stop_worker()` |
| `app/main.py` | Lifespan: khởi động worker, tắt worker lúc shutdown |
| `app/routers/tasks.py` | Chuyển `log_action` background task → enqueue job qua queue (vd: `{"type": "action_log", ...}`) |

### Chi tiết
- `TaskQueue`:
  - `asyncio.Queue` (maxsize configurable, default 100)
  - `enqueue(job: dict)` — put_nowait (nếu đầy → đánh rơi + log warning, không block response)
  - `worker()` — vòng lặp `await queue.get()`, xử lý job theo `type`; dispatch tới handler (hiện tại: `action_log`)
  - `start_worker()` → `asyncio.create_task(worker())`; `stop_worker()` → đặt sentinel `None` + cancel
- Router: `background_tasks.add_task(...)` hiện tại → thay bằng `await task_queue.enqueue({...})` trong endpoint, hoặc giữ BackgroundTasks để enqueue. Chọn: **enqueue trực tiếp trong endpoint** (KISS) — request_id lấy từ request.state truyền kèm vào job
- Job handler `action_log`: log `action task_id user_id request_id` — đây là ví dụ đơn giản chứng minh pattern queue; không thêm side effect khác

## Nhóm 5: Docker (`Dockerfile` + `docker-compose.yml`)

### Files mới
- `Dockerfile` — multi-stage:
  - Stage build: `python:3.12-slim`, copy `requirements.txt`, pip install
  - Stage runtime: copy site-packages + app; `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`
- `docker-compose.yml` — services:
  - `db`: `postgres:16-alpine`, env POSTGRES_*, healthcheck
  - `redis`: `redis:7-alpine`
  - `web`: build `.`, `depends_on` db+redis healthy, env `APP_ENV=prod` (hoặc `.env.prod`), `DATABASE_URL=postgresql+asyncpg://...`, `REDIS_URL=redis://redis:6379/0`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `.dockerignore`
- `requirements.txt`: thêm `asyncpg` (driver Postgres async) — cần cho compose; giữ aiosqlite cho dev

### Lưu ý
- Alembic migration khi chạy Docker: thêm `entrypoint` hoặc command `alembic upgrade head && uvicorn ...` trong compose web (gọn: dùng command override trong compose)
- README thêm mục "Chạy với Docker"

## Nhóm 6: Tests (`tests/day6/`)

### Files mới
| File | Tests |
|------|-------|
| `tests/day6/__init__.py` | Package init |
| `tests/day6/conftest.py` | Fixtures (client, settings override) |
| `tests/day6/test_config.py` | Fail-fast: APP_ENV=prod + JWT_SECRET default → raise; validate() từng điều kiện; env_file theo APP_ENV |
| `tests/day6/test_docs.py` | OpenAPI: `/openapi.json` có `info.description`, `tags`, `summary` endpoint, schema `examples` |
| `tests/day6/test_logging.py` | RequestIdFilter: tạo record → `request_id` attribute đúng; setup_logging format chứa `%(request_id)s` |
| `tests/day6/test_queue.py` | Queue: enqueue → worker xử lý; queue đầy → không block; sentinel stop worker |

### Lưu ý test
- `test_config`: dùng `monkeypatch.setenv` + `Settings(_env_file=None)` — không phá settings singleton toàn cục
- `test_queue`: dùng `asyncio.run` hoặc `pytest.mark.asyncio` (asyncio_mode=auto) — worker start/stop trong fixture
- Đảm bảo 75 test cũ (day1–day5) vẫn pass — không đổi contract response

## Acceptance Criteria

1. `APP_ENV=prod` + `JWT_SECRET=change-me-in-production` → app không khởi động (raise trước khi serve)
2. `APP_ENV=prod` + DATABASE_URL thiếu/ADMIN_PASSWORD rỗng → raise
3. `.env.dev` / `.env.prod` / `.env.test` được load theo `APP_ENV`
4. `/openapi.json` chứa `description`, `openapi_tags`, endpoint `summary`, schema `examples`
5. Mọi log record chứa `request_id`; request với header `X-Request-ID` → log dùng đúng ID đó
6. Task tạo/xóa → job xuất hiện trong queue worker (log `action=... request_id=...`)
7. `docker-compose up --build` → web + db(postgres) + redis chạy, `/health` trả 200, `/docs` mở được
8. 75 test cũ pass + test day6 mới pass (100%)
9. README cập nhật: APP_ENV, multi-env, Docker, queue

## Out of Scope
- Celery/Redis queue thật (chọn in-process asyncio queue)
- Rate limiting
- Migration Postgres riêng (dùng chung Alembic)
- Logging tới file/remote (chỉ stdout, có request_id)
- Redis thật trong test local (giữ fakeredis fallback)

## Constraints
- Không đổi response structure / endpoint contract (backward compatible)
- KISS/YAGNI: queue chỉ phục vụ log action làm ví dụ
- Giữ Python 3.12, FastAPI, SQLAlchemy async
- Dev/test không bắt buộc cài Redis thật (fakeredis fallback giữ nguyên)
