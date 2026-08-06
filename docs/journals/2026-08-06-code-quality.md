# Journal: Code Quality — Ruff + Mypy + DRY Refactor

**Date:** 2026-08-06
**Phase:** 07

## Summary
Nâng chất lượng code: thêm Ruff (lint) + Mypy (type check), xóa dead code, DRY refactor router tasks, performance review. Sống code sạch hoàn toàn, giữ nguyên API contract.

## What was built
- `pyproject.toml` — `[tool.ruff]` (py312, line-length 100, rules `E,F,I,UP,B,SIM`), `[tool.mypy]` (check_untyped_defs + disallow_untyped_defs), version `0.3.0`, thêm ruff+mypy vào dev deps
- `requirements.txt` — thêm `ruff>=0.8.0`, `mypy>=1.13.0`
- `app/routers/tasks.py` — refactor DRY: helper `_cached_value(key, builder)` + `_serialize_task()` thay pattern cache-get→serialize→set lặp 4 lần
- `tests/day7/test_quality.py` — 8 tests: import modules, API contract ổn định, xóa dead code, helper serialize

## Key decisions
- **Timezone `Settings.validate` → `_validate`**: tránh override pydantic `BaseModel.validate` (mypy override conflict)
- **B008 (fastapi Depends/Query)** handling: khai báo `extend-immutable-calls` thay vì xóa rule — FastAPI dependency injection là pattern chuẩn
- **Alembic exclude** khỏi ruff (version autogen); **tests E501** dùng `per-file-ignores` thay vì sửa hàng chục dòng test cũ — hạn chế churn không liên quan feature
- **A001/UP046** `Generic[T]`: giữ + `# noqa: UP046` cho tương thích Python 3.11 (không dùng PEP 695 syntax)
- Xóa `app/dependencies.py` — in-memory store Day 1 không còn được import bởi bất kỳ module nào

## Impact

- **Ruff:** 107 → 0 findings (19 auto-fix + 45 thủ công/config + per-file-ignore)
- **Mypy:** 35 → 0 errors (thêm return annotations, fix type-narrowing, cast Page items)
- **Tests:** 95 → 103 passed, không regression; endpoint/response contract giữ nguyên
- Giảm code lặp trong tasks.py nhờ helper cache chung

## Issues found & fixed

- Duplicate import `request_id_var` trong `app/core/queue.py` (do tách import không merge) — ruff F811 bắt
- Import block tách giữa file trong `app/api/deps.py` (lỗi E402) — hợp nhất lại
- `_serialize_task` nhận `Task | TaskModel` vì `Page.items` typed schema không phải model — mở rộng signature helper

## File tracking

- `app/api/deps.py` — type-narrow `raw_user_id`/`user_id`, `raise ... from None`
- `app/core/cache.py`, `app/core/logging.py`, `app/database.py`, `app/routers/health.py` — thêm return type annotations
- `app/main.py` — annotation middleware + lifespan + handler, wrap line >100
- `app/repositories/base.py` — annotation **kwargs, `where: ColumnElement[bool]`, `cast` cho Page