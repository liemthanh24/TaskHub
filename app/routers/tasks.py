import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.cache import cache
from app.database import get_db
from app.models.user import UserModel
from app.repositories.task import TaskRepository
from app.schemas.task import Page, Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

CACHE_TTL = 60
logger = logging.getLogger("taskhub.action")


def get_repo(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def log_action(action: str, task_id: int | None, user_id: int):
    logger.info("action=%s task_id=%s user_id=%s", action, task_id, user_id)


async def invalidate_task_cache():
    for pattern in ("task:list:*", "task:page:*", "task:get:*"):
        keys = await cache.keys(pattern)
        if keys:
            await cache.delete(*keys)


@router.get("/all", response_model=list[Task])
async def list_all_tasks(
    admin: UserModel = Depends(require_role("admin")),
    repo: TaskRepository = Depends(get_repo),
):
    cached = await cache.get("task:list:all")
    if cached is not None:
        return cached
    tasks = await repo.list()
    await cache.set("task:list:all", [Task.model_validate(t).model_dump(mode="json") for t in tasks], ex=CACHE_TTL)
    return tasks


@router.get("/", response_model=list[Task])
async def list_tasks(
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
):
    cached = await cache.get(f"task:list:{user.id}")
    if cached is not None:
        return cached
    tasks = await repo.list_for_user(user.id)
    await cache.set(f"task:list:{user.id}", [Task.model_validate(t).model_dump(mode="json") for t in tasks], ex=CACHE_TTL)
    return tasks


@router.get("/page", response_model=Page)
async def paginate_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
):
    cached = await cache.get(f"task:page:{user.id}:{page}:{per_page}")
    if cached is not None:
        return cached
    result = await repo.paginate_for_user(user.id, page, per_page)
    payload = {
        "items": [Task.model_validate(t).model_dump(mode="json") for t in result.items],
        "total": result.total,
        "page": result.page,
        "per_page": result.per_page,
        "pages": result.pages,
    }
    await cache.set(f"task:page:{user.id}:{page}:{per_page}", payload, ex=CACHE_TTL)
    return payload


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
):
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if user.role != "admin" and task.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")

    cached = await cache.get(f"task:get:{task_id}")
    if cached is not None:
        return cached
    await cache.set(f"task:get:{task_id}", Task.model_validate(task).model_dump(mode="json"), ex=CACHE_TTL)
    return task


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
):
    task = await repo.create(user_id=user.id, **payload.model_dump())
    await invalidate_task_cache()
    background_tasks.add_task(log_action, "create", task.id, user.id)
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    background_tasks: BackgroundTasks,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
):
    if user.role != "admin":
        owned = await repo.get_for_user(task_id, user.id)
        if not owned:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await repo.update(task_id, **payload.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await invalidate_task_cache()
    background_tasks.add_task(log_action, "update", task.id, user.id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    user: UserModel = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
):
    if user.role != "admin":
        owned = await repo.get_for_user(task_id, user.id)
        if not owned:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    deleted = await repo.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await invalidate_task_cache()
    background_tasks.add_task(log_action, "delete", task_id, user.id)
