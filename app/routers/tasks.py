from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.task import TaskRepository
from app.schemas.task import Page, Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_repo(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


@router.get("/", response_model=list[Task])
async def list_tasks(
    repo: TaskRepository = Depends(get_repo),
):
    return await repo.list()


@router.get("/page", response_model=Page)
async def paginate_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    repo: TaskRepository = Depends(get_repo),
):
    return await repo.paginate(page, per_page)


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    repo: TaskRepository = Depends(get_repo),
):
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    repo: TaskRepository = Depends(get_repo),
):
    task = await repo.create(**payload.model_dump())
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    repo: TaskRepository = Depends(get_repo),
):
    task = await repo.update(task_id, **payload.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    repo: TaskRepository = Depends(get_repo),
):
    deleted = await repo.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
