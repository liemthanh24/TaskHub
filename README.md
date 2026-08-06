# TaskHub

Hệ thống quản lý công việc (Task Management API) — dự án học tập xây dựng API production-ready từng bước với FastAPI.

## Tech Stack

- **Framework:** FastAPI + Pydantic v2
- **Database:** SQLAlchemy 2.x (async) + SQLite/aiosqlite (dev) / PostgreSQL/asyncpg (prod, Docker)
- **Migration:** Alembic
- **Auth:** JWT (HS256, python-jose) + password hashing (passlib/bcrypt)
- **Cache:** fakeredis (in-memory, khi `REDIS_URL` rỗng) / Redis thật (khi set `REDIS_URL`)
- **Config:** pydantic-settings (multi-env theo `APP_ENV`)
- **Queue:** in-process asyncio queue (job log hành động)
- **Python:** 3.12

## Features

| # | Feature | Trạng thái |
|---|---------|-----------|
| 1 | Setup FastAPI + health check | ✅ |
| 2 | SQLAlchemy async + Repository Pattern + Alembic | ✅ |
| 3 | Config + structured logging | ✅ |
| 4 | JWT Authentication (register / login) | ✅ |
| 5 | Authorization & RBAC (roles admin/user, task ownership) | ✅ |
| 6 | Middleware (CORS, request-id, timing) + exception handler | ✅ |
| 7 | Caching (Redis/fakeredis) + Background Tasks | ✅ |
| 8 | API Documentation (OpenAPI tags, summaries, examples) | ✅ |
| 9 | Fail-fast env validation + multi-environment | ✅ |
| 10 | Request-ID logging | ✅ |
| 11 | In-process async queue | ✅ |
| 12 | Docker (multi-stage, app + Postgres + Redis) | ✅ |
| 13 | Code quality: Ruff (lint) + Mypy (type check) + DRY refactor | ✅ |

## Lint & Type Checking

```bash
ruff check .               # 0 findings
mypy app/                  # 0 errors
```

- **Ruff** (`[tool.ruff]`): target py312, line-length 100, rules `E,F,I,UP,B,SIM`. `alembic/` (migration autogen) được exclude; `tests/**` bỏ rule `E501`; `Depends`/`Query`/`require_role` khai báo immutable (pattern FastAPI chuẩn, không bị B008).
- **Mypy** (`[tool.mypy]`): check `app/` với `check_untyped_defs` + `disallow_untyped_defs`.
- Refactor DRY: pattern cache-get → serialize → cache-set gộp thành helper `_cached_value` + `_serialize_task` trong `app/routers/tasks.py`.

## API Endpoints

### Auth (`/auth`)
- `POST /auth/register` — đăng ký (trả JWT ngay)
- `POST /auth/login` — đăng nhập
- `GET /auth/me` — thông tin user hiện tại (yêu cầu token)

### Tasks (`/tasks`) — tất cả đều yêu cầu `Authorization: Bearer <token>`
- `GET /tasks` — danh sách task của user hiện tại (cache 60s)
- `GET /tasks/all` — toàn bộ task (chỉ admin)
- `GET /tasks/page?page=&per_page=` — phân trang (theo ownership)
- `GET /tasks/{id}` — chi tiết task (ownership check trước cache)
- `POST /tasks` — tạo task
- `PUT /tasks/{id}` — cập nhật task
- `DELETE /tasks/{id}` — xóa task

### Health (`/health`)
- `GET /health` — status check

## RBAC

- **user:** chỉ xem/sửa/xóa task có `user_id` của mình (vi phạm → 403/404)
- **admin:** quyền quản lý mọi task qua `/tasks/all`, override ownership check
- Register luôn tạo user thường (`role="user"`) — không cho tự đăng ký admin
- Admin khởi tạo qua env `ADMIN_EMAIL` + `ADMIN_PASSWORD` (seeder lúc startup)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m app.main              # chạy app (uvicorn nếu cần)
```

Dev-only tools (đã có trong `pyproject.toml` optional-dependencies `dev`):

```bash
pip install -e ".[dev]"
ruff check .
mypy app/
```

## Cấu hình môi trường (Multi-env)

Cấu hình qua `APP_ENV` (dev/test/prod) — app sẽ load file env tương ứng:

| APP_ENV | File env | Mục đích |
|---------|----------|----------|
| `dev` | `.env.dev` | Phát triển local (SQLite, DEBUG=true) |
| `test` | `.env.test` | Chạy test |
| `prod` | `.env.prod` | Production (bắt buộc secret, Postgres) |

Nếu file tương ứng chưa tồn tại, app fallback về `.env`. Template: `.env.example`, `.env.dev.example`, `.env.prod.example`.

> **Fail-fast:** khi `APP_ENV=prod`, app từ chối khởi động nếu thiếu `JWT_SECRET` (khác default), `DATABASE_URL` (không phải SQLite) hoặc `ADMIN_PASSWORD`.

## API Documentation

Truy cập Swagger UI tại `/docs`, ReDoc tại `/redoc`, schema tại `/openapi.json`.

## Logging

Mỗi log record chứa `request_id` để truy vết theo request (header `X-Request-ID` hoặc tự sinh UUID). Format: `time | level | logger | request_id | message`.

## Chạy với Docker

```bash
docker compose up --build
```

Khởi động 3 service: `web` (FastAPI), `db` (PostgreSQL 16), `redis` (Redis 7). Bắt buộc set `JWT_SECRET`, `ADMIN_PASSWORD` trong environment khi chạy prod.

```bash
JWT_SECRET=$(openssl rand -hex 32) ADMIN_PASSWORD=strongpass docker compose up --build
```

## Migrations

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Tests

```bash
python -m pytest tests/ -q
ruff check .                 # lint: 0 findings
mypy app/                    # type check: 0 errors
```

103 tests (day1–day7): health, CRUD, auth, RBAC/ownership, middleware, cache (hit/miss/invalidate), background tasks/queue, config fail-fast, API docs, request-id logging, code-quality (imports clean, API contract ổn định, dead code đã xóa).

## Cấu trúc

```
app/
├── api/deps.py          # get_current_user, require_role
├── core/                # config, security (JWT/bcrypt), logging, cache, queue
├── database.py          # engine, session, init_db
├── models/              # SQLAlchemy models (base, task, user)
├── repositories/        # Repository Pattern (base, task, user)
├── routers/             # auth, health, tasks
└── schemas/             # pydantic (auth, task)
alembic/                 # migrations
tests/day1..day7/        # pytest suites
plans/                   # phase plans
Dockerfile               # multi-stage build
docker-compose.yml       # web + db (Postgres) + redis
```

## Mục tiêu học tập (Roadmap)

- [x] **Day 1–2:** FastAPI setup, health check, SQLAlchemy async + Repository Pattern + Alembic
- [x] **Day 3:** Config đa môi trường, structured logging, JWT auth
- [x] **Day 4:** RBAC + ownership
- [x] **Day 5:** Middleware, caching, background queue
- [x] **Day 6:** Docker Compose + API documentation nâng cao
- [x] **Day 7:** Code quality — Ruff + Mypy, xóa dead code, DRY refactor, performance review
