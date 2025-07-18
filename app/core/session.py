from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import config
import random

sqlalchemy_database_uri = config.settings.database_uri

async_engine = create_async_engine(sqlalchemy_database_uri,
                                   pool_timeout=30,
                                   pool_recycle=30 * 60
                                   )
async_session = async_sessionmaker(async_engine, expire_on_commit=False)

ro_async_engines = [create_async_engine(uri,
                                        pool_timeout=30,
                                        pool_recycle=30 * 60
                                        ) for uri in config.settings.ro_database_uris]

ro_async_sessions = [async_sessionmaker(i, expire_on_commit=False) for i in ro_async_engines]


def ro_async_session() -> async_sessionmaker:
    return random.choice(ro_async_sessions)()
