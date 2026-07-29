from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_next_id, get_tasks_store
from app.schemas.task import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[Task])
async def list_tasks(
    store: dict = Depends(get_tasks_store),
):
    return list(store.values())


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    store: dict = Depends(get_tasks_store),
):
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    store: dict = Depends(get_tasks_store),
    next_id: int = Depends(get_next_id),
):
    task = Task(id=next_id, **payload.model_dump())
    store[task.id] = task.model_dump()
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    store: dict = Depends(get_tasks_store),
):
    existing = store.get(task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updated = existing | payload.model_dump(exclude_unset=True)
    store[task_id] = updated
    return Task(**updated)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    store: dict = Depends(get_tasks_store),
):
    if task_id not in store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    del store[task_id]
