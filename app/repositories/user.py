from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserModel
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
