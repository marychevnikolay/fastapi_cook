from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass



engine = create_async_engine(
    settings.DB_URL, 
    echo=True, 
    future=True,
    #**engine_kwargs,

    poolclass=NullPool
)
SessionLocal = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
