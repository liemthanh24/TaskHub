from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskModel
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[TaskModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TaskModel)
