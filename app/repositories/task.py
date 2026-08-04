from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskModel
from app.repositories.base import BaseRepository
from app.schemas.task import Page


class TaskRepository(BaseRepository[TaskModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TaskModel)

    async def list_for_user(self, user_id: int) -> list[TaskModel]:
        stmt = select(TaskModel).where(TaskModel.user_id == user_id).order_by(TaskModel.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, task_id: int, user_id: int) -> TaskModel | None:
        stmt = select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def paginate_for_user(self, user_id: int, page: int = 1, per_page: int = 10) -> Page:
        return await self.paginate(page=page, per_page=per_page, where=TaskModel.user_id == user_id)
