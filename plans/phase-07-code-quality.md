# Phase 07: Code Quality + Lint/Type + Refactor + Performance + README

**Status:** Implemented ✅
**Mode:** interactive
**Branch:** day7
**Base:** day6

> Đã hoàn thành toàn bộ 6 nhóm. `ruff check .` 0 findings, `mypy app/` 0 errors, 103 tests pass (day1–day7). API contract giữ nguyên.

## Objectives
- Code review toàn bộ app: architecture, naming, code quality
- Ruff lint pass 100%, mypy không lỗi
- Refactor DRY: loại bỏ code trùng lặp
- Performance review
- README hoàn chỉnh

## Nhóm 1: Tooling — Ruff + Mypy (`pyproject.toml`, `requirements.txt`)

### Thay đổi
| File | Change |
|------|--------|
| `pyproject.toml` | Thêm `[tool.ruff]`, `[tool.mypy]`; version → 0.3.0; thêm ruff+mypy vào dev deps |
| `requirements.txt` | Thêm `ruff`, `mypy` (dev) |

### Chi tiết
- `[tool.ruff]`: `target-version = "py312"`, `line-length = 100`, `[tool.ruff.lint]` select `E,F,I,UP,B,SIM`
- `[tool.mypy]`: `python_version = "3.12"`, `strict = true` (nếu quá khắt khe với project học tập thì dùng `check_untyped_defs = true` + core hợp lý, avoid forcing perfect typing trên tests)
- Cài dev deps, chạy `ruff check .` → fix 100%; `mypy app/` → 0 error
- Không dùng `ruff check --fix` bừa trên toàn repo — xem từng rule, giữ style

## Nhóm 2: Xóa dead code (`app/dependencies.py`)
- Xóa `app/dependencies.py` (in-memory store Day 1, không còn import)
- Grep toàn repo xác nhận không còn tham chiếu
- Cập nhật README cấu trúc nếu nhắc tới

## Nhóm 3: Refactor DRY trong file (`app/routers/tasks.py` + `app/routers/auth.py`)

### Thay đổi
| File | Refactor |
|------|----------|
| `app/routers/tasks.py` | Tách helper `_cached_or_compute` để gộp pattern cache-get→serialize→set của `list_tasks`/`paginate_tasks`/`list_all_tasks`/`get_task` |
| `app/routers/auth.py` | Gộp pattern `get_repo` đã dùng chung (nếu lặp); kiểm tra schemas không trùng |

### Chi tiết
- Trong `tasks.py`: tạo `async def _get_cached(key, new_fn)` — lấy cache nếu hit, ngược lại chạy `new_fn()` trả về dữ liệu serialize, đặt cache, trả về. Các endpoint `/`, `/page`, `/all`, `/{id}` dùng chung → giảm lặp 3-4 lần.
- `_serialize_tasks(tasks)` helper: `[Task.model_validate(t).model_dump(mode="json") for t in tasks]` đang lặp 3 nơi → 1 chỗ.
- **KHÔNG đổi** public API response / endpoint contract.
- Giữ readsort `invalidate_task_cache`.

## Nhóm 4: Performance review + fixes nhỏ
- Audit: N+1 (hiện không có), `select` có đủ index? (tasks.user_id cần index — kiểm tra migration đã có chưa, thêm nếu thiếu qua Alembic)
- Cập nhật nếu cần: thêm index `ix_tasks_user_id` nếu chưa tồn tại
- Cache TTL/invalidate đã hợp lý (60s, theo-user)
- Note trong plan/report kết quả performance review

## Nhóm 5: Tests (`tests/day7/`)

### Files mới
| File | Tests |
|------|-------|
| `tests/day7/test_quality.py` | Lint-driven: import app CPython, openapi contract không đổi, một số smoke trên helper mới `_cached_or_compute` |

### Lưu ý
- Giữ 95 test cũ pass; thêm vài test nhẹ cho helper mới/refactor (nếu helper public)
- Chạy `ruff check .` 0 error, `mypy app/` 0 error trong CI/verify

## Acceptance Criteria

1. `ruff check .` → 0 findings (100% pass) ✅
2. `mypy app/` → 0 error ✅
3. Xóa được `app/dependencies.py` clean (không đụng import) ✅
4. Refactor DRY: tasks.py giảm code lặp rõ rệt, 95+ tests vẫn pass ✅ (103 tests)
5. Response/endpoint contract KHÔNG đổi (tests đảm bảo) ✅
6. README hoàn chỉnh: setup, env vars, docker compose up, tests, cấu trúc ✅
7. pyproject version = 0.3.0 ✅

## Ghi chú lệch so với plan gốc

- **E501 ở tests**: dùng `[tool.ruff.lint.per-file-ignores] "tests/**" = ["E501"]` thay vì sửa từng dòng test cũ (tránh churn không liên quan feature).
- **Alembic**: exclude khỏi ruff (`exclude = ["alembic"]`) — migration autogen, không phải code tay.
- **B008 (Depends/Query)**: khai báo qua `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls` — pattern FastAPI DI chuẩn, không phải bug.
- **Settings.validate → _validate**: đổi tên tránh override pydantic `BaseModel.validate`.
- **UP046 (Generic[T])**: giữ `Generic[T]` + `# noqa: UP046` để tương thích Python 3.11 (requires-python >=3.11).
- **Mapping BaseRepository→Page**: type-hoc `cast(list[Any], list(items))` thay vì đổi `Page.items` (nằm ngoài scope phase).

## Out of Scope
- Đổi DB engine/Postgres production (giữ SQLite)
- Rate limiting, thêm feature mới
- CI/CD pipeline thật
- Mypy strict tối đa — ưu tiên không lỗi + thực dụng

## Constraints
- KHÔNG đổi public API contract (response, endpoint, schema)
- Giữ pattern Repository + DI
- Dev/test vẫn dùng fakeredis fallback
- 95 tests cũ không được fail