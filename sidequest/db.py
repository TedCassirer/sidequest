"""Simple SQLite-based result storage."""

from typing import Optional, Any
from datetime import datetime

from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Declarative base class."""
    pass


class Result(Base):
    """ORM model representing stored quest results."""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    context_id: Mapped[str] = mapped_column(String, unique=True)
    quest_name: Mapped[str] = mapped_column(String)
    result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    timestamp: Mapped[str] = mapped_column(String)



class ResultDB:
    """Asynchronous database using SQLAlchemy."""

    def __init__(self, url: str = "sqlite+aiosqlite:///:memory:") -> None:
        self.engine: AsyncEngine = create_async_engine(url, future=True)
        self.session_factory = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def setup(self) -> None:
        await self._init_tables()

    async def _init_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def store(
        self, context_id: str, quest_name: str, result: Optional[Any], error: Optional[str]
    ) -> None:
        async with self.session_factory() as session:
            session.add(
                Result(
                    context_id=context_id,
                    quest_name=quest_name,
                    result=None if result is None else str(result),
                    error=error,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
            await session.commit()

    async def fetch_all(self) -> list[tuple]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(
                    Result.context_id,
                    Result.quest_name,
                    Result.result,
                    Result.error,
                    Result.timestamp,
                )
            )
            rows = result.all()
        return [tuple(row) for row in rows]

    async def fetch_result(self, context_id: str) -> Optional[Any]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Result.result).where(Result.context_id == context_id)
            )
            row = result.first()
            return None if row is None else row[0]
