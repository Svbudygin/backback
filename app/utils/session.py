# from asyncio import TaskGroup 3.11
from asyncio import current_task
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
)

from app.core.session import async_session


@asynccontextmanager
async def get_session(external_session: Optional[AsyncSession] = None) -> AsyncSession:
    if external_session:
        yield external_session
    else:
        async with async_session() as session:
            yield session


class DBManager:
    def __init__(self, engine):
        self.async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
        self.scoped_session_factory = async_scoped_session(
            self.async_session_factory, scopefunc=current_task
        )

    def get_session(self) -> AsyncSession:
        return self.scoped_session_factory()

    # async def close_sessions(self, sessions):
    #     async with TaskGroup() as task_group:
    #         for session in sessions:
    #             task_group.create_task(session.close())

    async def __aenter__(self):
        self.session = self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_sessions([self.session])


def _get_current_task_id() -> int:
    return id(current_task())


# async def get_db_manager(engine) -> AsyncGenerator[DBManager, None]:
#     db_manager = DBManager(engine)
#     try:
#         yield db_manager
#     finally:
#         sessions = db_manager.scoped_session_factory.registry.registry.values()
#         await db_manager.close_sessions(sessions)
