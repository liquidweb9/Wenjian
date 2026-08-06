import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Under pytest, pool nothing: asyncpg connections are bound to the event loop
# that created them, and mixing TestClient portal loops with pytest-asyncio
# loops over a shared pool raises "Event loop is closed" / "another operation
# is in progress". A fresh connection per operation keeps each test isolated.
engine_kwargs = {"echo": settings.app_debug}
if os.getenv("WJ_TEST_NULL_POOL") == "1":
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **engine_kwargs)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
