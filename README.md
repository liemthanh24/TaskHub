# TaskHub

Hệ thống quản lý công việc (Task Management API) — dự án học tập xây dựng API production-ready từng bước với FastAPI.

## Tech Stack

- **Framework:** FastAPI + Pydantic v2
- **Database:** SQLAlchemy 2.x (async) + SQLite/aiosqlite (dev)
- **Migration:** Alembic
- **Auth:** JWT (HS256, python-jose) + password hashing (passlib/bcrypt)
- **Cache:** fakeredis (in-memory, khi `REDIS_URL` rỗng) / Redis thật (khi set `REDIS_URL`)
- **Config:** pydantic-settings (`.env`)
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
copy .env.example .env          # Windows (hoặc cp .env.example .env trên Linux)
python -m app.main              # chạy app (uvicorn nếu cần)
```

> **Bắt buộc:** set `JWT_SECRET` trong production (`DEBUG=false`). App sẽ từ chối khởi động nếu dùng secret mặc định khi không ở chế độ debug.

## Migrations

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Tests

```bash
python -m pytest tests/ -q
```

75 tests (day1–day5): health, CRUD, auth, RBAC/ownership, middleware, cache (hit/miss/invalidate), background tasks.

## Cấu trúc

```
app/
├── api/deps.py          # get_current_user, require_role
├── core/                # config, security (JWT/bcrypt), logging, cache
├── database.py          # engine, session, init_db
├── models/              # SQLAlchemy models (base, task, user)
├── repositories/        # Repository Pattern (base, task, user)
├── routers/             # auth, health, tasks
└── schemas/             # pydantic (auth, task)
alembic/                 # migrations
tests/day1..day5/        # pytest suites
plans/                   # phase plans
```
