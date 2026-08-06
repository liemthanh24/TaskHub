import math
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.schemas.task import Page

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):  # noqa: UP046
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **data: Any) -> T:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: int, **data: Any) -> T | None:
        obj = await self.session.get(self.model, id)
        if not obj:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        obj = await self.session.get(self.model, id)
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True

    async def paginate(
        self,
        page: int = 1,
        per_page: int = 10,
        where: ColumnElement[bool] | None = None,
    ) -> Page:
        total_stmt = select(func.count()).select_from(self.model)
        items_stmt = select(self.model).offset((page - 1) * per_page).limit(per_page)
        if where is not None:
            total_stmt = total_stmt.where(where)
            items_stmt = items_stmt.where(where)

        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar() or 0

        pages = max(1, math.ceil(total / per_page))

        result = await self.session.execute(items_stmt)
        items = result.scalars().all()

        return Page(
            items=cast(list[Any], list(items)),
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
