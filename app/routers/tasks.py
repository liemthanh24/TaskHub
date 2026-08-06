from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.cache import cache
from app.core.queue import task_queue
from app.database import get_db
from app.models.task import TaskModel
from app.models.user import UserModel
from app.repositories.task import TaskRepository
from app.schemas.task import Page, Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

CACHE_TTL = 60


def get_repo(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def _serialize_task(task: TaskModel | Task) -> dict[str, Any]:
    return Task.model_validate(task).model_dump(mode="json")


async def _cached_value(key: str, builder: Callable[[], Awaitable[Any]]) -> Any:
    value = await cache.get(key)
    if value is not None:
        return value
    data = await builder()
    await cache.set(key, data, ex=CACHE_TTL)
    return data


async def invalidate_task_cache() -> None:
    for pattern in ("task:list:*", "task:page:*", "task:get:*"):
        keys = await cache.keys(pattern)
        if keys:
            await cache.delete(*keys)


async def _enqueue_action(request: Request, action: str, task_id: int | None, user_id: int) -> bool:
    return await task_queue.enqueue(
        {
            "type": "action_log",
            "action": action,
            "task_id": task_id,
            "user_id": user_id,
            "request_id": request.state.request_id,
        }
    )


@router.get("/all", response_model=list[Task], summary="Danh sách toàn bộ task (admin)")
async def list_all_tasks(
    admin: UserModel = Depends(require_role("admin")),
    repo: TaskRepository = Depends(get_repo),
) -> list[dict[str, Any]]:
    async def build() -> list[dict[str, Any]]:
        tasks = await repo.list()
        return [_serialize_task(t) for t in tasks]

    return await _cached_value("task:list:all", build)


@router.get("/", response_model=list[Task], summary="Danh sách task của user hiện tại")
async def list_tasks(
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> list[dict[str, Any]]:
    async def build() -> list[dict[str, Any]]:
        tasks = await repo.list_for_user(user.id)
        return [_serialize_task(t) for t in tasks]

    return await _cached_value(f"task:list:{user.id}", build)


@router.get("/page", response_model=Page, summary="Phân trang task của user hiện tại")
async def paginate_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> dict[str, Any]:
    async def build() -> dict[str, Any]:
        result = await repo.paginate_for_user(user.id, page, per_page)
        return {
            "items": [_serialize_task(t) for t in result.items],
            "total": result.total,
            "page": result.page,
            "per_page": result.per_page,
            "pages": result.pages,
        }

    return await _cached_value(f"task:page:{user.id}:{page}:{per_page}", build)


@router.get("/{task_id}", response_model=Task, summary="Chi tiết một task")
async def get_task(
    task_id: int,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> dict[str, Any]:
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if user.role != "admin" and task.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")

    async def build() -> dict[str, Any]:
        return _serialize_task(task)

    return await _cached_value(f"task:get:{task_id}", build)


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED, summary="Tạo task mới")
async def create_task(
    payload: TaskCreate,
    request: Request,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> TaskModel:
    task = await repo.create(user_id=user.id, **payload.model_dump())
    await invalidate_task_cache()
    await _enqueue_action(request, "create", task.id, user.id)
    return task


@router.put("/{task_id}", response_model=Task, summary="Cập nhật task")
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    request: Request,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> TaskModel:
    if user.role != "admin":
        owned = await repo.get_for_user(task_id, user.id)
        if not owned:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await repo.update(task_id, **payload.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await invalidate_task_cache()
    await _enqueue_action(request, "update", task.id, user.id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa task")
async def delete_task(
    task_id: int,
    request: Request,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> None:
    if user.role != "admin":
        owned = await repo.get_for_user(task_id, user.id)
        if not owned:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    deleted = await repo.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await invalidate_task_cache()
    await _enqueue_action(request, "delete", task_id, user.id)