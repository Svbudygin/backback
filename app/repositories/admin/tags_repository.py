from sqlalchemy import select

from app.core.session import async_session
from app.models.TagModel import TagModel


async def get_all():
    async with async_session() as session:
        return (await session.execute(select(TagModel).order_by(TagModel.name))).scalars().all()
